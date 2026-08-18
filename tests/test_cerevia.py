from __future__ import annotations
import unittest
import numpy as np

from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.pipeline import QualityGateError, evidence_manifest, finding, qc_eeg, run_pipeline, verify_manifest


class CereviaTests(unittest.TestCase):
    def _observation(self, value: float = 1.0, samples: int = 1024) -> EEGObservation:
        t = np.arange(samples) / 128.0
        data = np.vstack([value * np.sin(2 * np.pi * 10 * t), value * np.sin(2 * np.pi * 10 * t)])
        return EEGObservation.from_array(data, 128.0, ("C3", "C4"))

    def test_pipeline_has_complete_lineage_and_integrity(self):
        catalog, final, manifest = run_pipeline(self._observation())
        expected = ["raw-eeg-001", "qc-001", "filter-001", "epoch-001", "alpha-power-001", "analysis-001", "finding-001"]
        self.assertEqual(manifest["provenance_chain"], expected)
        self.assertEqual(final.provenance.content_hash, manifest["content_hash"])
        self.assertTrue(verify_manifest(manifest, catalog))
        self.assertEqual(len(manifest["manifest_hash"]), 64)
        self.assertEqual(catalog.validate_integrity(), [])

    def test_raw_data_mutation_is_rejected(self):
        raw = ingest_eeg("raw", self._observation(), "study", "sub-001", "ses-01")
        with self.assertRaises(TypeError):
            raw.payload["data"][0][0] = 99.0

    def test_catalog_rejects_overwrite(self):
        catalog = ArtifactCatalog()
        raw = ingest_eeg("raw", self._observation(), "study", "sub-001", "ses-01")
        catalog.add(raw)
        with self.assertRaises(ValueError):
            catalog.add(raw)

    def test_failed_qc_is_preserved_before_halting(self):
        observation = EEGObservation.from_array(np.array([[1.0, np.nan, 2.0, 3.0]]), 8.0, ("Cz",))
        with self.assertRaises(QualityGateError) as context:
            run_pipeline(observation)
        error = context.exception
        self.assertEqual(error.qc_artifact.artifact_id, "qc-001")
        self.assertIn("qc-001", error.catalog.ids())
        self.assertFalse(error.qc_artifact.payload["passed"])

    def test_parameter_tampering_is_detected(self):
        catalog, _, _ = run_pipeline(self._observation())
        filtered = catalog.get("filter-001")
        object.__setattr__(filtered.provenance, "parameters", {"low_hz": 99.0, "high_hz": 40.0})
        self.assertTrue(any("filter-001" in error for error in catalog.validate_integrity()))

    def test_deleted_upstream_artifact_is_detected(self):
        catalog, _, manifest = run_pipeline(self._observation())
        catalog.remove_for_test("raw-eeg-001")
        self.assertTrue(catalog.validate_integrity())
        self.assertFalse(verify_manifest(manifest, catalog))

    def test_parent_swap_is_detected(self):
        catalog, _, _ = run_pipeline(self._observation())
        replacement = ingest_eeg("raw-eeg-001", self._observation(2.0), "demo-001", "sub-001", "ses-01")
        catalog._items["raw-eeg-001"] = replacement
        self.assertTrue(any("filter-001" in error for error in catalog.validate_integrity()))

    def test_manifest_tampering_is_detected(self):
        catalog, _, manifest = run_pipeline(self._observation())
        tampered = dict(manifest)
        tampered["study_id"] = "tampered-study"
        self.assertFalse(verify_manifest(tampered, catalog))

    def test_environment_metadata_tampering_is_detected(self):
        catalog, _, _ = run_pipeline(self._observation())
        raw = catalog.get("raw-eeg-001")
        object.__setattr__(raw.provenance, "environment", {"python_version": "tampered"})
        self.assertTrue(any("raw-eeg-001" in error for error in catalog.validate_integrity()))

    def test_finding_requires_valid_evidence(self):
        catalog, final, _ = run_pipeline(self._observation())
        with self.assertRaises(ValueError):
            finding(catalog.get("analysis-001"), (catalog.get("qc-001"),), "fake-finding", "unsupported", catalog=catalog)
        with self.assertRaises(ValueError):
            finding(catalog.get("analysis-001"), (), "fake-finding", "unsupported")
        self.assertEqual(final.payload["status"], "PROVISIONAL")

    def test_malformed_neuroscience_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            ingest_eeg("raw", self._observation(), "study", "subject-001", "ses-01")
        with self.assertRaises(ValueError):
            ingest_eeg("raw", EEGObservation.from_array(np.ones((2, 8)), 0.0, ("Cz", "Cz")), "study", "sub-001", "ses-01")

    def test_old_finding_cannot_be_reused_against_new_dataset(self):
        first_catalog, _, _ = run_pipeline(self._observation(1.0))
        second_catalog, _, _ = run_pipeline(self._observation(2.0))
        with self.assertRaises(ValueError):
            finding(second_catalog.get("analysis-001"),
                    tuple(first_catalog.get(item) for item in ("raw-eeg-001", "qc-001", "filter-001", "epoch-001", "alpha-power-001")),
                    "stale-finding", "stale", catalog=second_catalog)

    def test_upstream_identity_changes_downstream_identity(self):
        first = ingest_eeg("raw-a", self._observation(1.0), "study", "sub-001", "ses-01")
        second = ingest_eeg("raw-b", self._observation(2.0), "study", "sub-001", "ses-01")
        self.assertNotEqual(first.provenance.content_hash, second.provenance.content_hash)
        first_derived = first.derive("derived-a", "checkpoint", {"value": first.payload["data"]}, {}, "checkpoint", (first,))
        second_derived = second.derive("derived-b", "checkpoint", {"value": second.payload["data"]}, {}, "checkpoint", (second,))
        self.assertNotEqual(first_derived.provenance.content_hash, second_derived.provenance.content_hash)


if __name__ == "__main__":
    unittest.main()

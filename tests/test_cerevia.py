from __future__ import annotations
import unittest
import numpy as np

from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.pipeline import QualityGateError, evidence_manifest, qc_eeg, run_pipeline, verify_manifest


class CereviaTests(unittest.TestCase):
    def test_pipeline_has_complete_lineage_and_integrity(self):
        t = np.arange(1024) / 128.0
        data = np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)])
        catalog, final, manifest = run_pipeline(EEGObservation.from_array(data, 128.0, ("C3", "C4")))
        self.assertEqual(manifest["provenance_chain"], ["raw-eeg-001", "qc-001", "filter-001", "epoch-001", "alpha-power-001", "analysis-001", "finding-001"])
        self.assertEqual(final.provenance.content_hash, manifest["content_hash"])
        self.assertTrue(verify_manifest(manifest))
        self.assertEqual(len(manifest["manifest_hash"]), 64)
        for artifact in catalog.all():
            self.assertTrue(artifact.provenance.environment["python_version"])

    def test_payload_is_genuinely_immutable(self):
        observation = EEGObservation.from_array(np.ones((1, 8)), 8.0, ("Cz",))
        raw = ingest_eeg("raw", observation, "study", "sub-001", "ses-01")
        with self.assertRaises(TypeError):
            raw.payload["data"][0][0] = 99.0
        with self.assertRaises(TypeError):
            raw.metadata["study_id"] = "changed"

    def test_catalog_rejects_overwrite(self):
        observation = EEGObservation.from_array(np.ones((1, 8)), 8.0, ("Cz",))
        catalog = ArtifactCatalog()
        raw = ingest_eeg("raw", observation, "study", "sub-001", "ses-01")
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

    def test_quality_gate_rejects_nonfinite_samples(self):
        observation = EEGObservation.from_array(np.array([[1.0, np.nan, 2.0, 3.0]]), 8.0, ("Cz",))
        raw = ingest_eeg("raw", observation, "study", "sub-001", "ses-01")
        _, report = qc_eeg(raw, "qc")
        self.assertFalse(report.passed)
        self.assertIn("non-finite", report.errors[0])

    def test_pseudonymous_identifier_is_required(self):
        observation = EEGObservation.from_array(np.ones((1, 8)), 8.0, ("Cz",))
        with self.assertRaises(ValueError):
            ingest_eeg("raw", observation, "study", "person-name", "ses-01")

    def test_manifest_tampering_is_detected(self):
        _, _, manifest = run_pipeline(EEGObservation.from_array(np.ones((1, 1024)), 128.0, ("Cz",)))
        tampered = dict(manifest)
        tampered["study_id"] = "tampered-study"
        self.assertFalse(verify_manifest(tampered))

    def test_changed_upstream_identity_changes_downstream_identity(self):
        first = EEGObservation.from_array(np.ones((1, 8)), 8.0, ("Cz",))
        second = EEGObservation.from_array(np.full((1, 8), 2.0), 8.0, ("Cz",))
        first_raw = ingest_eeg("raw-a", first, "study", "sub-001", "ses-01")
        second_raw = ingest_eeg("raw-b", second, "study", "sub-001", "ses-01")
        self.assertNotEqual(first_raw.provenance.content_hash, second_raw.provenance.content_hash)
        first_derived = first_raw.derive("derived-a", "checkpoint", {"value": first_raw.payload["data"]}, {}, "checkpoint", (first_raw,))
        second_derived = second_raw.derive("derived-b", "checkpoint", {"value": second_raw.payload["data"]}, {}, "checkpoint", (second_raw,))
        self.assertNotEqual(first_derived.provenance.content_hash, second_derived.provenance.content_hash)


if __name__ == "__main__":
    unittest.main()

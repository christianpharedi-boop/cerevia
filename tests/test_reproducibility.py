from __future__ import annotations
from dataclasses import replace
import unittest
import numpy as np

from cerevia.neuro.eeg import EEGObservation, ingest_eeg
from cerevia.analysis.reproducibility import AnalysisSpecification, execute_analysis, verify_rerun
from cerevia.core.artifacts import ArtifactCatalog


class ReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        t = np.arange(1024) / 128.0
        observation = EEGObservation.from_array(
            np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)]),
            128.0,
            ("C3", "C4"),
        )
        self.raw = ingest_eeg("raw-repro", observation, "study-001", "sub-001", "ses-01")
        self.specification = AnalysisSpecification.for_eeg(self.raw)

    def _execute(self, specification: AnalysisSpecification | None = None):
        catalog = ArtifactCatalog()
        catalog.add(self.raw)
        return execute_analysis(specification or self.specification, catalog), catalog

    def test_exact_rerun_has_identical_execution_identity(self):
        first, _ = self._execute()
        second, _ = self._execute()
        self.assertTrue(verify_rerun(first, second))
        self.assertEqual(first.final_content_hash, second.final_content_hash)
        self.assertEqual(first.execution_identity, second.execution_identity)
        self.assertNotEqual(first.manifest_hash, second.manifest_hash)

    def test_input_hash_mismatch_is_rejected(self):
        bad = replace(self.specification, input_artifacts=({"artifact_id": "raw-repro", "content_hash": "0" * 64},))
        with self.assertRaises(ValueError):
            self._execute(bad)

    def test_parameter_change_changes_specification_and_result_identity(self):
        parameters = dict(self.specification.parameters)
        parameters["null_value"] = 1.0
        changed = replace(self.specification, parameters=parameters)
        first, _ = self._execute()
        second, _ = self._execute(changed)
        self.assertNotEqual(first.specification_hash, second.specification_hash)
        self.assertNotEqual(first.execution_identity, second.execution_identity)

    def test_environment_mismatch_is_rejected(self):
        changed = replace(self.specification, software_environment={"python_version": "0.0.0"})
        with self.assertRaises(ValueError):
            self._execute(changed)


if __name__ == "__main__":
    unittest.main()

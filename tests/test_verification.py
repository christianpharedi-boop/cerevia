from __future__ import annotations
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cerevia.verification.bundle import verify_bundle, verify_bundle_file


class IndependentVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle_path = Path(__file__).parents[1] / "examples" / "bids_eeg" / "verification_bundle.json"

    def test_real_bundle_verifies_without_original_catalog(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.0 proof first")
        report = verify_bundle_file(self.bundle_path)
        self.assertTrue(report.verified, report.failures)
        self.assertEqual(report.final_finding_id, "aware-finding-001")

    def test_fresh_process_verifies_exported_bundle(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.0 proof first")
        script = self.bundle_path.parents[0] / "verify_bundle.py"
        env = {**os.environ, "PYTHONPATH": str(self.bundle_path.parents[2])}
        process = subprocess.run([sys.executable, str(script), str(self.bundle_path)], text=True,
                                 capture_output=True, env=env)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn('"verified": true', process.stdout)

    def test_artifact_payload_corruption_is_detected(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.0 proof first")
        bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        corrupted = copy.deepcopy(bundle)
        corrupted["artifacts"][0]["payload"]["samples"] = [999]
        report = verify_bundle(corrupted)
        self.assertFalse(report.verified)
        self.assertTrue(any("content identity mismatch" in failure for failure in report.failures))

    def test_claim_corruption_is_detected(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.0 proof first")
        bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        corrupted = copy.deepcopy(bundle)
        claim = next(item for item in corrupted["artifacts"] if item["artifact_id"] == "aware-claim-001")
        claim["payload"]["statement"] = "tampered scientific claim"
        report = verify_bundle(corrupted)
        self.assertFalse(report.verified)
        self.assertTrue(any("aware-claim-001" in failure for failure in report.failures))

    def test_manifest_corruption_is_detected(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.0 proof first")
        bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        corrupted = copy.deepcopy(bundle)
        corrupted["manifest"]["content_hash"] = "0" * 64
        report = verify_bundle(corrupted)
        self.assertFalse(report.verified)
        self.assertIn("manifest hash mismatch", report.failures)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cerevia.pilot.kit import AgreementReport, BlindExchangeAnswer, compare_answers


class PilotKitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1]
        cls.script = cls.root / "examples/pilot/pilot_proof.py"

    def run_proof(self) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pilot.json"
            result = subprocess.run([sys.executable, str(self.script), "--output", str(output)], cwd=self.root, check=True, capture_output=True, text=True)
            return json.loads(result.stdout)

    def test_pilot_is_explicitly_prepared_not_externally_executed(self):
        result = self.run_proof()
        self.assertEqual(result["pilot_status"], "PREPARED_NOT_EXECUTED_EXTERNALLY")
        self.assertTrue(result["external_participant_required"])

    def test_valid_and_adversarial_scenarios_agree(self):
        result = self.run_proof()
        self.assertEqual(set(result["scenarios"]), {"valid", "altered_bundle_hash", "stale_revocation", "wrong_recipient"})
        self.assertTrue(all(report["agreement"] for report in result["agreement"].values()))
        self.assertTrue(result["answers"]["valid"]["institution_a"]["package_authentic"])
        for scenario in ("altered_bundle_hash", "stale_revocation", "wrong_recipient"):
            self.assertFalse(result["answers"][scenario]["institution_a"]["package_authentic"])

    def test_privacy_boundary_excludes_bundle_payload(self):
        result = self.run_proof()
        self.assertFalse(result["privacy_boundary"]["bundle_embedded"])
        self.assertFalse(result["privacy_boundary"]["sensitive_payloads_in_package"])
        self.assertTrue(result["privacy_boundary"]["bundle_locator"].startswith("out-of-band://"))

    def test_comparison_reports_disagreement(self):
        left = BlindExchangeAnswer("x", True, True, ("a",), "statement", {}, 1, ("raw",), ("finding",), (), ())
        right = BlindExchangeAnswer("x", True, False, ("a",), "statement", {}, 1, ("raw",), (), ("finding",), ())
        report = compare_answers(left, right)
        self.assertFalse(report.agreement)
        self.assertIn("bundle_verified", report.disagreements)
        self.assertIsInstance(report, AgreementReport)


if __name__ == "__main__":
    unittest.main()

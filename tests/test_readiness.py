from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1]
        cls.checker = cls.root / "examples/pilot/check_readiness.py"
        cls.checklist = cls.root / "docs/pilot/readiness.json"

    def test_readiness_checker_reports_handoff_ready_but_external_pending(self):
        result = subprocess.run([sys.executable, str(self.checker)], cwd=self.root, check=True, capture_output=True, text=True)
        report = json.loads(result.stdout)
        self.assertTrue(report["ready_for_external_handoff"])
        self.assertEqual(report["pending_external"], ["external_institution"])
        self.assertEqual(report["missing_handoff_artifacts"], [])

    def test_checklist_forbids_claiming_external_use(self):
        checklist = json.loads(self.checklist.read_text(encoding="utf-8"))
        self.assertEqual(checklist["architecture_status"], "FROZEN_PENDING_EXTERNAL_VALIDATION")
        self.assertFalse(checklist["claims_of_external_use_permitted"])
        self.assertEqual(sum(item["status"] == "COMPLETE" for item in checklist["checks"]), 9)


if __name__ == "__main__":
    unittest.main()

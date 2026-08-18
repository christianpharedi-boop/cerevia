from __future__ import annotations

import json
import unittest
from pathlib import Path

from cerevia.observatory import ObservatorySnapshot


class ObservatoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.snapshot = ObservatorySnapshot.from_files(root / "examples/bids_eeg/verification_bundle.json", root / "examples/bids_eeg/sentinel_result.json")

    def test_finding_and_verification_are_read_only_views(self):
        finding = self.snapshot.get_finding()
        self.assertEqual(finding["finding"]["artifact_id"], "aware-finding-001")
        self.assertEqual(finding["status"], "AFFECTED / INVESTIGATE")
        self.assertTrue(finding["verification"]["verified"])
        finding["finding"]["payload"]["statement"] = "local mutation"
        self.assertNotEqual(self.snapshot.get_finding()["finding"]["payload"].get("statement"), "local mutation")

    def test_lineage_contains_finding_to_raw_observation(self):
        lineage = self.snapshot.get_lineage()
        self.assertEqual(lineage["node_ids"][0], "aware-finding-001")
        self.assertIn("aware-claim-001", lineage["node_ids"])
        self.assertIn("aware-inference-001", lineage["node_ids"])
        self.assertIn("raw-rec-02-MIvsRest-run-0", lineage["node_ids"])

    def test_supporting_evidence_and_impact(self):
        support = self.snapshot.get_supporting_evidence()
        self.assertEqual(support["claim_id"], "aware-claim-001")
        self.assertTrue(support["evidence"])
        impact = self.snapshot.impact_of("raw-rec-02-MIvsRest-run-0")
        self.assertIn("aware-finding-001", impact["affected_finding_ids"])
        self.assertEqual(impact["statuses"]["aware-finding-001"], "AFFECTED / INVESTIGATE")

    def test_history_supports_as_of_queries(self):
        current = self.snapshot.get_history()
        historical = self.snapshot.get_history(as_of="2026-08-18T00:00:30+00:00")
        self.assertGreaterEqual(len(current["events"]), len(historical["events"]))
        self.assertTrue(any(item["event_type"] == "bundle_created" for item in historical["events"]))
        self.assertFalse(any(item["event_type"] == "independent_verification" for item in historical["events"]))

    def test_serialized_observatory_contract_is_json_safe(self):
        serialized = self.snapshot.to_dict()
        json.dumps(serialized)
        self.assertEqual(serialized["observatory_version"], "1.2.0")
        self.assertEqual(serialized["graph_hash"], self.snapshot.graph_hash)


if __name__ == "__main__":
    unittest.main()

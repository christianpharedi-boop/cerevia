from __future__ import annotations

import json
import unittest
from pathlib import Path

from cerevia.domain.earthspace import build_earthspace_chain
from cerevia.observatory import ObservatorySnapshot
from cerevia.sentinel.security import run_attack_suite
from cerevia.verification.bundle import build_bundle, verify_bundle


class EarthSpaceTransplantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.observations = root / "examples/earthspace/data/usgs_earthquakes_2024-01-01_m5.json"
        cls.catalog, cls.finding, cls.execution, cls.artifacts = build_earthspace_chain(cls.observations)
        cls.bundle = build_bundle(cls.execution["manifest"], cls.execution["specification"], cls.execution["specification_hash"], cls.catalog, cls.execution["execution_identity"])

    def test_shared_bundle_verifier_accepts_spatial_temporal_chain(self):
        report = verify_bundle(self.bundle)
        self.assertTrue(report.verified, report.failures)
        self.assertEqual(report.final_finding_id, "earthspace-finding-001")

    def test_shared_sentinel_attack_suite_detects_all_attacks(self):
        report = run_attack_suite(self.bundle)
        self.assertEqual(report.status, "VERIFIED")
        self.assertEqual(len(report.attacks), 13)
        self.assertTrue(all(item.detected for item in report.attacks))

    def test_shared_observatory_traverses_spatial_temporal_dependencies(self):
        snapshot = ObservatorySnapshot.from_bundle(self.bundle)
        lineage = snapshot.get_lineage()
        self.assertIn("earthspace-raw-observations-001", lineage["node_ids"])
        self.assertIn("earthspace-derived-product-001", lineage["node_ids"])
        self.assertEqual(snapshot.impact_of("earthspace-raw-observations-001")["affected_finding_ids"], ["earthspace-finding-001"])

    def test_bundle_is_json_serializable(self):
        json.dumps(self.bundle)


if __name__ == "__main__":
    unittest.main()

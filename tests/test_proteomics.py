from __future__ import annotations

import json
import unittest
from pathlib import Path

from cerevia.adapters.proteomics import build_proteomics_chain
from cerevia.observatory import ObservatorySnapshot
from cerevia.sentinel.security import run_attack_suite
from cerevia.verification.bundle import build_bundle, verify_bundle


class ProteomicsTransplantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.assay = root / "examples/transplants/data/hela_proteins_subset.csv"
        cls.catalog, cls.finding, cls.execution, cls.artifacts = build_proteomics_chain(cls.assay)
        cls.bundle = build_bundle(cls.execution["manifest"], cls.execution["specification"], cls.execution["specification_hash"], cls.catalog, cls.execution["execution_identity"])

    def test_shared_bundle_verifier_accepts_proteomics_chain(self):
        report = verify_bundle(self.bundle)
        self.assertTrue(report.verified, report.failures)
        self.assertEqual(report.final_finding_id, "proteomics-finding-001")

    def test_shared_sentinel_attack_suite_detects_all_attacks(self):
        report = run_attack_suite(self.bundle)
        self.assertEqual(report.status, "VERIFIED")
        self.assertEqual(len(report.attacks), 13)
        self.assertTrue(all(item.detected for item in report.attacks))

    def test_shared_observatory_is_domain_agnostic(self):
        snapshot = ObservatorySnapshot.from_bundle(self.bundle)
        lineage = snapshot.get_lineage()
        self.assertIn("proteomics-raw-assay-001", lineage["node_ids"])
        self.assertEqual(snapshot.impact_of("proteomics-raw-assay-001")["affected_finding_ids"], ["proteomics-finding-001"])
        self.assertEqual(snapshot.get_finding()["finding"]["kind"], "finding")

    def test_bundle_is_json_serializable(self):
        json.dumps(self.bundle)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cerevia.interoperability.cross_domain import compose_cross_domain_bundle, impact_after_revocation, load_bundle
from cerevia.observatory import ObservatorySnapshot
from cerevia.verification.bundle import verify_bundle_file, write_bundle


class CrossDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.paths = {
            "neuroscience": root / "examples/neuro/verification_bundle.json",
            "proteomics": root / "examples/transplants/proteomics_bundle.json",
            "earthspace": root / "examples/transplants/earthspace_bundle.json",
        }
        cls.bundles = {domain: load_bundle(path) for domain, path in cls.paths.items()}
        cls.bundle, cls.catalog, cls.ids = compose_cross_domain_bundle(cls.bundles)

    def test_fresh_file_verification_accepts_composed_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cross-domain.json"
            write_bundle(self.bundle, path)
            report = verify_bundle_file(path)
        self.assertTrue(report.verified, report.failures)
        self.assertEqual(report.final_finding_id, "cross-domain-finding-001")

    def test_final_claim_preserves_each_domain_lineage(self):
        specification = self.bundle["specification"]
        self.assertEqual(set(specification["domain_evidence"]), {"neuroscience", "proteomics", "earthspace"})
        for evidence in specification["domain_evidence"].values():
            self.assertTrue(evidence["source_id"])
            self.assertTrue(evidence["source_lineage"])
            self.assertTrue(evidence["source_content_hash"])

    def test_selective_proteomics_revocation_does_not_invalidate_other_domain_findings(self):
        result = impact_after_revocation(self.bundle, self.ids["proteomics"].artifact_id)
        affected = set(result["impact"]["affected_node_ids"])
        self.assertIn("proteomics-finding-001", affected)
        self.assertIn("cross-domain-finding-001", affected)
        self.assertNotIn("aware-finding-001", affected)
        self.assertNotIn("earthspace-finding-001", affected)
        self.assertEqual(result["finding_status"], "AFFECTED / INVESTIGATE")

    def test_observatory_reconstructs_all_three_domain_nodes(self):
        snapshot = ObservatorySnapshot.from_bundle(self.bundle)
        lineage = snapshot.get_lineage()
        self.assertIn("raw-rec-02-MIvsRest-run-0", lineage["node_ids"])
        self.assertIn("proteomics-raw-assay-001", lineage["node_ids"])
        self.assertIn("earthspace-raw-observations-001", lineage["node_ids"])
        json.dumps(snapshot.to_dict())


if __name__ == "__main__":
    unittest.main()

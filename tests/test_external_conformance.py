from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cerevia.interoperability.cross_domain import load_bundle
from cerevia.observatory import ObservatorySnapshot


class ExternalConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1]
        cls.external = cls.root / "examples/external_impl/standalone_protocol.py"
        cls.cross_bundle = cls.root / "examples/cross_domain/cross_domain_bundle.json"
        cls.eeg_bundle = cls.root / "examples/bids_eeg/verification_bundle.json"

    def run_external(self, *args: str) -> dict:
        result = subprocess.run([sys.executable, str(self.external), *args], cwd=self.root, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_external_implementation_does_not_import_cerevia(self):
        source = self.external.read_text(encoding="utf-8")
        self.assertNotIn("import cerevia", source)
        self.assertNotIn("from cerevia", source)

    def test_external_producer_bundle_is_verified_by_both_implementations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "external-bundle.json"
            produced = self.run_external("produce", str(path))
            self.assertTrue(produced["verification"]["verified"])
            external_report = self.run_external("verify", str(path))
            self.assertTrue(external_report["verified"], external_report)
            from cerevia.verification.bundle import verify_bundle_file
            internal_report = verify_bundle_file(path)
            self.assertTrue(internal_report.verified, internal_report.failures)

    def test_external_verifier_accepts_cerevia_bundles(self):
        eeg_report = self.run_external("verify", str(self.eeg_bundle))
        cross_report = self.run_external("verify", str(self.cross_bundle))
        self.assertTrue(eeg_report["verified"], eeg_report)
        self.assertTrue(cross_report["verified"], cross_report)

    def test_external_and_cerevia_agree_on_selective_revocation(self):
        subject = "proteomics-raw-assay-001"
        external = self.run_external("impact", str(self.cross_bundle), "--subject", subject)
        internal = ObservatorySnapshot.from_bundle(load_bundle(self.cross_bundle)).impact_of(subject)
        self.assertEqual(external["affected_finding_ids"], internal["affected_finding_ids"])
        self.assertNotIn("aware-finding-001", external["affected_finding_ids"])
        self.assertNotIn("earthspace-finding-001", external["affected_finding_ids"])


if __name__ == "__main__":
    unittest.main()

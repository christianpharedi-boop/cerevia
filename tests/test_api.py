from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from cerevia.api.app import ReadOnlyStore, create_app
from cerevia.interoperability.cross_domain import load_bundle


class ProtocolAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).parents[1]
        cls.bundle_path = root / "examples/substrate_stress_tests/cross_domain_bundle.json"
        cls.bundle = load_bundle(cls.bundle_path)
        cls.client = TestClient(create_app(ReadOnlyStore(cls.bundle_path)))

    def test_health_declares_read_only_boundary(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["storage"], "read_only_out_of_band")
        self.assertEqual(response.json()["institutional_exchange_api"], "separate_future_boundary")

    def test_verify_and_verify_bundle_are_same_contract(self):
        first = self.client.post("/verify", json={"bundle": self.bundle})
        second = self.client.post("/verify/bundle", json={"bundle": self.bundle})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertTrue(first.json()["verified"])

    def test_finding_observatory_routes(self):
        finding_id = self.bundle["manifest"]["final_finding_id"]
        for suffix in ("", "/lineage", "/evidence", "/verification", "/history"):
            response = self.client.get(f"/findings/{finding_id}{suffix}")
            self.assertEqual(response.status_code, 200, (suffix, response.text))
        lineage = self.client.get(f"/findings/{finding_id}/lineage").json()
        self.assertIn("node_ids", lineage)
        evidence = self.client.get(f"/findings/{finding_id}/evidence").json()
        self.assertIn("evidence", evidence)

    def test_impact_revocations_and_attestations(self):
        response = self.client.post("/impact", json={"artifact_id": "proteomics-raw-assay-001"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("affected_finding_ids", response.json())
        self.assertEqual(self.client.get("/revocations").status_code, 200)
        self.assertEqual(self.client.get("/attestations").status_code, 200)

    def test_unknown_finding_and_unconfigured_store_are_explicit(self):
        self.assertEqual(self.client.get("/findings/not-a-finding").status_code, 404)
        no_store = TestClient(create_app(ReadOnlyStore()))
        self.assertEqual(no_store.get("/findings/anything").status_code, 503)


if __name__ == "__main__":
    unittest.main()

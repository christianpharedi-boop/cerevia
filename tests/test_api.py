from __future__ import annotations

import json
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
        cls.neuro_bundle = json.loads((root / "examples/neuro/verification_bundle.json").read_text(encoding="utf-8"))
        cls.neuro_sentinel = json.loads((root / "examples/neuro/sentinel_result.json").read_text(encoding="utf-8"))

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

    def test_sentinel_flags_are_not_echoed_as_server_verified(self):
        response = self.client.post(
            "/verify",
            json={
                "bundle": self.bundle,
                "sentinel": {
                    "sentinel_status": "VERIFIED",
                    "attestation_verified": True,
                    "transparency_log_verified": True,
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("sentinel_status", body)
        self.assertNotIn("attestation_verified", body)
        self.assertNotIn("transparency_log_verified", body)
        self.assertEqual(body["sentinel"]["client_reported"]["attestation_verified"], True)
        self.assertFalse(body["sentinel"]["server_verified"]["attestation_verified"])
        self.assertFalse(body["sentinel"]["server_verified"]["transparency_log_verified"])
        self.assertFalse(body["sentinel"]["server_verified"]["sentinel_verified"])

    def test_finding_verification_names_its_bundle_scope(self):
        finding_id = self.bundle["manifest"]["final_finding_id"]
        body = self.client.get(f"/findings/{finding_id}/verification").json()
        self.assertEqual(body["finding_id"], finding_id)
        self.assertEqual(body["verification_scope"], "finding_lineage_within_bundle")
        self.assertIn(finding_id, body["lineage_node_ids"])
        self.assertIn("verified", body["bundle_verification"])

    def test_valid_sentinel_is_verified_server_side(self):
        response = TestClient(create_app(ReadOnlyStore())).post(
            "/verify", json={"bundle": self.neuro_bundle, "sentinel": self.neuro_sentinel}
        )
        self.assertEqual(response.status_code, 200)
        server = response.json()["sentinel"]["server_verified"]
        self.assertTrue(server["bundle_verified"])
        self.assertTrue(server["attestation_verified"])
        self.assertTrue(server["transparency_log_verified"])
        self.assertTrue(server["sentinel_verified"])

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

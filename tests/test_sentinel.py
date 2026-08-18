from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.core.hashing import hash_object
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphNode, NodeType
from cerevia.sentinel.security import (RevocationRegistry, SentinelEvent, TransparencyLog,
                                       create_attestation, run_attack_suite, verify_attestation)
from cerevia.verification.bundle import verify_bundle


class SentinelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle_path = Path(__file__).parents[1] / "examples" / "bids_eeg" / "verification_bundle.json"

    def test_real_attack_suite_detects_every_declared_attack(self):
        if not self.bundle_path.exists():
            self.skipTest("run the real V1.1 proof first")
        bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        report = run_attack_suite(bundle)
        self.assertEqual(report.status, "VERIFIED")
        self.assertTrue(all(result.detected for result in report.attacks))
        self.assertEqual(len(report.attacks), 13)

    def test_signed_attestation_detects_signature_tampering(self):
        bundle = {"bundle": "example"}
        report = verify_bundle({"bundle_type": "CEREVIA INDEPENDENT VERIFICATION BUNDLE", "manifest": {}, "specification": {}, "specification_hash": hash_object({}), "artifacts": []})
        key = Ed25519PrivateKey.generate()
        attestation = create_attestation(hash_object(bundle), "verifier-a", hash_object({}), report, key, timestamp="2026-08-18T00:00:00+00:00")
        self.assertTrue(verify_attestation(attestation))
        tampered = type(attestation)(**{**attestation.__dict__, "verifier_id": "forged-verifier"})
        self.assertFalse(verify_attestation(tampered))

    def test_transparency_log_is_append_only_and_hash_linked(self):
        log = TransparencyLog().append("bundle_created", "bundle-1", "hash-1", timestamp="2026-08-18T00:00:00+00:00")
        log = log.append("independent_verification", "bundle-1", "hash-1", timestamp="2026-08-18T00:01:00+00:00")
        self.assertTrue(log.verify())
        first = log.events[0]
        corrupted = SentinelEvent(first.sequence, first.event_type, first.subject_id, "changed", first.timestamp,
                                  first.details, first.previous_event_hash, first.event_hash)
        self.assertFalse(TransparencyLog((corrupted, log.events[1])).verify())
        self.assertEqual(log.events[1].previous_event_hash, log.events[0].event_hash)

    def test_revocation_propagates_to_dependent_claim_and_finding(self):
        graph = EvidenceGraph()
        for node_id, node_type in (("raw", NodeType.ARTIFACT), ("analysis", NodeType.ANALYSIS),
                                   ("inference", NodeType.INFERENCE), ("claim", NodeType.CLAIM),
                                   ("finding", NodeType.FINDING)):
            graph.add_node(GraphNode(node_id, node_type, {}))
        graph.add_edge("analysis", "raw", EdgeType.DERIVED_FROM)
        graph.add_edge("inference", "analysis", EdgeType.INFERRED_FROM)
        graph.add_edge("claim", "inference", EdgeType.DERIVED_FROM)
        graph.add_edge("finding", "claim", EdgeType.DERIVED_FROM)
        registry, record = RevocationRegistry().revoke("raw", "source dataset corruption", graph)
        self.assertEqual(record.status, "REVOKED")
        self.assertTrue({"raw", "analysis", "inference", "claim", "finding"}.issubset(record.affected_nodes))
        self.assertEqual(registry.status_for("finding"), "AFFECTED / INVESTIGATE")


if __name__ == "__main__":
    unittest.main()

"""V1.4 Earth/Space domain-transplant proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.core.hashing import hash_object
from cerevia.domain.earthspace import build_earthspace_chain
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphNode, NodeType
from cerevia.observatory import ObservatorySnapshot
from cerevia.sentinel.security import RevocationRegistry, TransparencyLog, create_attestation, run_attack_suite, verify_attestation
from cerevia.verification.bundle import build_bundle, verify_bundle, write_bundle


def graph_from_manifest(manifest: dict) -> EvidenceGraph:
    graph = EvidenceGraph()
    for node in manifest["evidence_graph"]["nodes"]:
        graph.add_node(GraphNode(node["node_id"], NodeType(node["node_type"]), node.get("attributes", {})))
    for edge in manifest["evidence_graph"]["edges"]:
        graph.add_edge(edge["source"], edge["target"], EdgeType(edge["relation"]), edge.get("attributes", {}))
    return graph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("observations", type=Path)
    parser.add_argument("--bundle", type=Path, default=Path("examples/earthspace/earthspace_bundle.json"))
    parser.add_argument("--sentinel", type=Path, default=Path("examples/earthspace/earthspace_sentinel.json"))
    args = parser.parse_args()

    catalog, finding, execution, artifacts = build_earthspace_chain(args.observations)
    bundle = build_bundle(execution["manifest"], execution["specification"], execution["specification_hash"], catalog, execution["execution_identity"])
    write_bundle(bundle, args.bundle)
    report = verify_bundle(bundle)
    attacks = run_attack_suite(bundle)
    key = Ed25519PrivateKey.generate()
    bundle_hash = hash_object(bundle)
    attestation = create_attestation(bundle_hash, "cerevia-v1.4-earthspace", execution["specification_hash"], report, key, verifier_software="cerevia-sentinel-1.3.0", timestamp="2026-08-18T00:00:00+00:00")
    log = TransparencyLog().append("bundle_created", finding.artifact_id, bundle_hash, {"domain": "earthspace"}, timestamp="2026-08-18T00:00:00+00:00")
    log = log.append("independent_verification", finding.artifact_id, bundle_hash, {"result": "VERIFIED" if report.verified else "INVESTIGATE", "domain": "earthspace"}, timestamp="2026-08-18T00:01:00+00:00")
    registry, revocation = RevocationRegistry().revoke(artifacts["raw"].artifact_id, "demonstration Earth/Space source revocation", graph_from_manifest(execution["manifest"]))
    sentinel = {"sentinel_status": attacks.status, "original_verification": report.to_dict(), "attestation": attestation.__dict__, "attestation_verified": verify_attestation(attestation), "transparency_log": log.to_dict(), "transparency_log_verified": log.verify(), "revocation": revocation.__dict__, "revocation_registry": registry.to_dict(), "affected_finding_ids": sorted(node for node in revocation.affected_nodes if node == finding.artifact_id), "attack_count": len(attacks.attacks), "detected_attack_count": sum(item.detected for item in attacks.attacks)}
    args.sentinel.write_text(json.dumps(sentinel, indent=2, sort_keys=True), encoding="utf-8")
    observatory = ObservatorySnapshot.from_bundle(bundle, sentinel)
    print(json.dumps({"sentinel": sentinel, "observatory": {"finding": observatory.get_finding(), "lineage": observatory.get_lineage(), "impact": observatory.impact_of(artifacts["raw"].artifact_id), "history": observatory.get_history()}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the V1.1 Sentinel extensions over a local V1.0 bundle."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.core.hashing import hash_object
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphEdge, GraphNode, NodeType
from cerevia.sentinel.security import RevocationRegistry, TransparencyLog, create_attestation, run_attack_suite, verify_attestation
from cerevia.verification.bundle import verify_bundle_file


def graph_from_manifest(manifest: dict) -> EvidenceGraph:
    graph = EvidenceGraph()
    graph_data = manifest["evidence_graph"]
    for node in graph_data["nodes"]:
        graph.add_node(GraphNode(node["node_id"], NodeType(node["node_type"]), node.get("attributes", {})))
    for edge in graph_data["edges"]:
        graph.add_edge(edge["source"], edge["target"], EdgeType(edge["relation"]), edge.get("attributes", {}))
    return graph


def main(path: str) -> None:
    bundle_path = Path(path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    original = verify_bundle_file(bundle_path)
    sentinel = run_attack_suite(bundle)
    key = Ed25519PrivateKey.generate()
    attestation = create_attestation(hash_object(bundle), "cerevia-sentinel-local", bundle["specification_hash"], original, key, timestamp="2026-08-18T00:00:00+00:00")
    log = TransparencyLog().append("bundle_created", bundle["manifest"]["final_finding_id"], hash_object(bundle), timestamp="2026-08-18T00:00:00+00:00")
    log = log.append("independent_verification", bundle["manifest"]["final_finding_id"], hash_object(bundle), {"result": "VERIFIED"}, timestamp="2026-08-18T00:01:00+00:00")
    graph = graph_from_manifest(bundle["manifest"])
    raw_id = next(record["artifact_id"] for record in bundle["artifacts"] if record["kind"] == "raw_eeg")
    registry, revocation = RevocationRegistry().revoke(raw_id, "demonstration source revocation", graph)
    result = {"sentinel_status": sentinel.status, "original_verification": original.to_dict(),
              "attestation": attestation.__dict__, "attestation_verified": verify_attestation(attestation),
              "transparency_log": log.to_dict(), "transparency_log_verified": log.verify(),
              "revocation": revocation.__dict__, "revocation_registry": registry.to_dict(),
              "affected_finding_ids": [node_id for node_id in revocation.affected_nodes if graph.nodes[node_id].node_type == NodeType.FINDING],
              "attack_count": len(sentinel.attacks), "detected_attack_count": sum(item.detected for item in sentinel.attacks)}
    output_path = bundle_path.with_name("sentinel_result.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide a verification_bundle.json path")
    main(sys.argv[1])

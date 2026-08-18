"""Standalone V2.0 reference implementation.

This file intentionally has no dependency on the CEREVIA package. It implements only the
serialized V1.6 protocol surface: canonical hashing, artifact identities,
manifest/bundle verification, graph invalidation, and a small producer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "1.0"
BUNDLE_TYPE = "CEREVIA INDEPENDENT VERIFICATION BUNDLE"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def artifact_record(artifact_id: str, kind: str, payload: Any, metadata: dict[str, Any], operation: str, parameters: dict[str, Any], parents: list[dict[str, str]], software_version: str = "external-impl-1.0.0") -> dict[str, Any]:
    environment = {"implementation": "external-reference", "protocol_version": PROTOCOL_VERSION}
    provenance = {"artifact_id": artifact_id, "parent_artifacts": [parent["artifact_id"] for parent in parents], "operation": operation, "parameters": parameters, "software_version": software_version, "environment": environment, "timestamp": "2026-08-18T00:00:00+00:00", "content_hash": "", "creator": "independent-implementation"}
    provenance["content_hash"] = digest({"artifact_id": artifact_id, "kind": kind, "payload": payload, "metadata": metadata, "operation": operation, "parameters": parameters, "software_version": software_version, "environment": environment, "parents": parents})
    return {"artifact_id": artifact_id, "kind": kind, "payload": payload, "metadata": metadata, "provenance": provenance}


def graph_for(records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    node_type = {"analysis": "Analysis", "multimodal_inference": "Inference", "claim": "Claim", "finding": "Finding"}
    for record in records:
        artifact_id = record["artifact_id"]
        nodes[artifact_id] = {"node_id": artifact_id, "node_type": node_type.get(record["kind"], "Artifact"), "attributes": {"kind": record["kind"], "content_hash": record["provenance"]["content_hash"], "operation": record["provenance"]["operation"]}}
        transform_id = f"transformation:{artifact_id}"
        nodes[transform_id] = {"node_id": transform_id, "node_type": "Transformation", "attributes": {"operation": record["provenance"]["operation"], "content_hash": record["provenance"]["content_hash"]}}
        add_edge(edges, artifact_id, transform_id, "GENERATED_BY", {})
        relation = "INFERRED_FROM" if record["kind"] == "multimodal_inference" else "DERIVED_FROM"
        for parent_id in record["provenance"]["parent_artifacts"]:
            add_edge(edges, artifact_id, parent_id, relation, {})
        if record["kind"] == "finding":
            payload = record["payload"]
            if payload.get("analysis_id") in nodes:
                add_edge(edges, payload["analysis_id"], artifact_id, "SUPPORTS", {})
            for evidence_id in payload.get("evidence", []):
                if evidence_id in nodes:
                    add_edge(edges, evidence_id, artifact_id, "SUPPORTS", {})
    return {"nodes": sorted(nodes.values(), key=lambda item: item["node_id"]), "edges": sorted(edges.values(), key=lambda item: item["edge_id"])}


def add_edge(edges: dict[str, dict[str, Any]], source: str, target: str, relation: str, attributes: dict[str, Any]) -> None:
    edge_id = digest({"source": source, "target": target, "relation": relation, "attributes": attributes})
    edges[edge_id] = {"edge_id": edge_id, "source": source, "target": target, "relation": relation, "attributes": attributes}


def build_manifest(records: list[dict[str, Any]], final_id: str) -> dict[str, Any]:
    by_id = {record["artifact_id"]: record for record in records}
    chain: list[str] = []
    visiting: set[str] = set()

    def visit(artifact_id: str) -> None:
        if artifact_id in visiting:
            return
        visiting.add(artifact_id)
        for parent_id in by_id[artifact_id]["provenance"]["parent_artifacts"]:
            visit(parent_id)
        chain.append(artifact_id)

    visit(final_id)
    graph = graph_for(records)
    manifest = {"manifest_type": "CEREVIA EVIDENCE MANIFEST", "manifest_version": "1.1.0", "study_id": "external-protocol-proof", "final_finding_id": final_id, "artifact_count": len(chain), "artifacts": [{key: value for key, value in by_id[artifact_id].items() if key != "payload"} for artifact_id in chain], "provenance_chain": chain, "content_hash": by_id[final_id]["provenance"]["content_hash"], "evidence_graph": graph}
    manifest["evidence_graph_hash"] = digest(graph)
    manifest["manifest_hash"] = digest(manifest)
    return manifest


def produce_bundle() -> dict[str, Any]:
    raw = artifact_record("external-source-001", "raw_external_observation", {"observation": "independent protocol fixture", "value": 42}, {"domain": "external-demo", "source": "third-party-team"}, "external_ingest", {"format": "json"}, [])
    analysis = artifact_record("external-analysis-001", "analysis", {"estimand": "declared_fixture_value", "value": 42}, {"domain": "external-demo"}, "external_analysis", {"method": "deterministic_identity_check"}, [{"artifact_id": raw["artifact_id"], "content_hash": raw["provenance"]["content_hash"]}])
    inference = artifact_record("external-inference-001", "multimodal_inference", {"analysis_id": analysis["artifact_id"], "result": {"value_matches_declaration": True}}, {"domain": "external-demo"}, "external_inference", {"rule": "value_equals_42"}, [{"artifact_id": analysis["artifact_id"], "content_hash": analysis["provenance"]["content_hash"]}])
    claim_payload = {"claim_type": "scientific_claim", "hypothesis": "The external fixture retains its declared value.", "statement": "The independent implementation preserved the declared fixture value through its analysis chain.", "inference_id": inference["artifact_id"], "inference_content_hash": inference["provenance"]["content_hash"], "evidence": [raw["artifact_id"]], "evidence_content_hashes": [raw["provenance"]["content_hash"]], "assumptions": ["The fixture is interpreted as supplied."], "uncertainty": {"type": "descriptive_fixture", "not_estimated": True}, "experimental_context": {"domain": "external-demo", "implementation": "independent"}, "method": "deterministic_identity_check", "validation": {"status": "QUALIFIED", "reasons": ["bound to declared evidence and method"], "claim_type": "scientific_claim", "permissible": True}, "claim_status": "QUALIFIED", "computed_result": inference["payload"]}
    claim = artifact_record("external-claim-001", "claim", claim_payload, {"domain": "external-demo", "status": "QUALIFIED"}, "validate_scientific_claim", {}, [{"artifact_id": inference["artifact_id"], "content_hash": inference["provenance"]["content_hash"]}, {"artifact_id": raw["artifact_id"], "content_hash": raw["provenance"]["content_hash"]}], software_version="external-impl-1.0.0")
    finding_payload = {"finding_id": "external-finding-001", "statement": claim_payload["statement"], "evidence": [raw["artifact_id"]], "evidence_content_hashes": [raw["provenance"]["content_hash"]], "analysis_id": claim["artifact_id"], "statistical_result": analysis["payload"], "status": "QUALIFIED", "claim_status": "QUALIFIED"}
    finding = artifact_record("external-finding-001", "finding", finding_payload, {"domain": "external-demo", "status": "QUALIFIED", "evidence_count": 1}, "record_finding", {}, [{"artifact_id": claim["artifact_id"], "content_hash": claim["provenance"]["content_hash"]}, {"artifact_id": raw["artifact_id"], "content_hash": raw["provenance"]["content_hash"]}])
    records = [raw, analysis, inference, claim, finding]
    specification = {"domain": "external-demo", "method": "external_protocol_proof", "protocol_version": PROTOCOL_VERSION, "implementation": "independent-reference", "uncertainty": {"type": "descriptive_fixture", "not_estimated": True}}
    specification_hash = digest(specification)
    manifest = build_manifest(records, finding["artifact_id"])
    execution_identity = digest({"specification_hash": specification_hash, "analysis_id": analysis["artifact_id"], "inference_id": inference["artifact_id"], "finding_id": finding["artifact_id"], "final_content_hash": finding["provenance"]["content_hash"]})
    return {"bundle_type": BUNDLE_TYPE, "bundle_version": "1.0.0", "manifest": manifest, "specification": specification, "specification_hash": specification_hash, "execution_identity": execution_identity, "artifacts": records, "producer": {"implementation": "independent-reference", "protocol_version": PROTOCOL_VERSION}}


def verify_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    checks: list[str] = []
    failures: list[str] = []
    if bundle.get("bundle_type") != BUNDLE_TYPE:
        failures.append("invalid bundle type")
    manifest = bundle.get("manifest", {})
    unsigned_manifest = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    if manifest.get("manifest_hash") == digest(unsigned_manifest):
        checks.append("manifest_hash")
    else:
        failures.append("manifest hash mismatch")
    if bundle.get("specification_hash") == digest(bundle.get("specification", {})):
        checks.append("specification_hash")
    else:
        failures.append("specification hash mismatch")
    records = {record.get("artifact_id"): record for record in bundle.get("artifacts", [])}
    for record in bundle.get("artifacts", []):
        parents = [{"artifact_id": parent_id, "content_hash": records[parent_id]["provenance"]["content_hash"]} for parent_id in record["provenance"].get("parent_artifacts", []) if parent_id in records]
        if len(parents) != len(record["provenance"].get("parent_artifacts", [])):
            failures.append(f"{record.get('artifact_id')}: missing parent")
            continue
        expected = digest({"artifact_id": record["artifact_id"], "kind": record["kind"], "payload": record.get("payload"), "metadata": record.get("metadata", {}), "operation": record["provenance"]["operation"], "parameters": record["provenance"].get("parameters", {}), "software_version": record["provenance"].get("software_version"), "environment": record["provenance"].get("environment", {}), "parents": parents})
        if expected == record["provenance"].get("content_hash"):
            checks.append(f"artifact:{record['artifact_id']}:content_hash")
        else:
            failures.append(f"{record.get('artifact_id')}: content identity mismatch")
    final_id = manifest.get("final_finding_id")
    final = records.get(final_id)
    if final is None or final.get("kind") != "finding":
        failures.append("final artifact is not a finding")
    else:
        checks.append("finding_role")
        if final["provenance"]["content_hash"] != manifest.get("content_hash"):
            failures.append("manifest final content hash mismatch")
        claim = records.get(final.get("payload", {}).get("analysis_id"))
        if claim is None or claim.get("kind") != "claim":
            failures.append("finding claim role")
        else:
            inference = records.get(claim.get("payload", {}).get("inference_id"))
            if inference is None or inference.get("kind") != "multimodal_inference":
                failures.append("claim inference role")
            for evidence_id, evidence_hash in zip(claim.get("payload", {}).get("evidence", []), claim.get("payload", {}).get("evidence_content_hashes", [])):
                if evidence_id not in records or records[evidence_id]["provenance"]["content_hash"] != evidence_hash:
                    failures.append(f"claim evidence mismatch: {evidence_id}")
            if not claim.get("payload", {}).get("uncertainty", {}).get("type"):
                failures.append("claim uncertainty declaration missing")
    graph = manifest.get("evidence_graph")
    if manifest.get("evidence_graph_hash") == digest(graph):
        checks.append("evidence_graph_hash")
    else:
        failures.append("evidence graph hash mismatch")
    return {"verified": not failures, "checks": checks, "failures": failures, "final_finding_id": final_id}


def impact(bundle: dict[str, Any], subject_id: str) -> dict[str, Any]:
    graph = bundle["manifest"]["evidence_graph"]
    affected = {subject_id}
    changed = True
    while changed:
        changed = False
        for edge in graph.get("edges", []):
            if edge["relation"] in {"DERIVED_FROM", "INFERRED_FROM", "RECORDED_DURING", "ASSOCIATED_WITH", "ANALYZED_BY"} and edge["target"] in affected and edge["source"] not in affected:
                affected.add(edge["source"])
                changed = True
            if edge["relation"] == "SUPPORTS" and edge["source"] in affected and edge["target"] not in affected:
                affected.add(edge["target"])
                changed = True
    findings = sorted(node["node_id"] for node in graph.get("nodes", []) if node["node_id"] in affected and node["node_type"] == "Finding")
    return {"subject_id": subject_id, "affected_node_ids": sorted(affected), "affected_finding_ids": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("produce", "verify", "impact"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--subject")
    args = parser.parse_args()
    if args.command == "produce":
        args.path.write_text(json.dumps(produce_bundle(), indent=2, sort_keys=True), encoding="utf-8")
        result = {"produced": True, "path": str(args.path), "verification": verify_bundle(json.loads(args.path.read_text()))}
    else:
        bundle = json.loads(args.path.read_text())
        result = verify_bundle(bundle) if args.command == "verify" else impact(bundle, args.subject or "external-source-001")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("verified", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

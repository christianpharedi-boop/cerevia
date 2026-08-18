"""V1.5 cross-domain evidence composition.

This module composes independently serialized domain bundles without adding a
new identity, provenance, verifier, or claim semantics layer.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from cerevia.analysis.claims import create_claim_artifact
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import hash_object, thaw
from cerevia.core.provenance import Artifact, Provenance
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphNode, NodeType
from cerevia.observatory import ObservatorySnapshot
from cerevia.pipeline import evidence_manifest
from cerevia.sentinel.security import RevocationRegistry
from cerevia.verification.bundle import build_bundle, verify_bundle


def _artifact_from_record(record: dict[str, Any]) -> Artifact:
    p = record["provenance"]
    provenance = Provenance(p["artifact_id"], tuple(p.get("parent_artifacts", [])), p["operation"], p.get("parameters", {}), p["software_version"], p.get("environment", {}), p["timestamp"], p["content_hash"], p.get("creator", "cerevia"))
    return Artifact(record["artifact_id"], record["kind"], record.get("payload"), record.get("metadata", {}), provenance)


def _graph_from_manifest(manifest: dict[str, Any]) -> EvidenceGraph:
    graph = EvidenceGraph()
    serialized = manifest.get("evidence_graph", {})
    for node in serialized.get("nodes", []):
        graph.add_node(GraphNode(node["node_id"], NodeType(node["node_type"]), deepcopy(node.get("attributes", {}))))
    for edge in serialized.get("edges", []):
        graph.add_edge(edge["source"], edge["target"], EdgeType(edge["relation"]), deepcopy(edge.get("attributes", {})))
    return graph


def _domain_of(record: dict[str, Any]) -> str:
    metadata = record.get("metadata", {})
    payload = record.get("payload", {}) if isinstance(record.get("payload"), dict) else {}
    return str(metadata.get("domain") or payload.get("experimental_context", {}).get("domain") or "unknown")


def _add_records(catalog: ArtifactCatalog, records: list[dict[str, Any]]) -> None:
    pending = {_record["artifact_id"]: _record for _record in records}
    while pending:
        progressed = False
        for artifact_id, record in list(pending.items()):
            artifact = _artifact_from_record(record)
            if all(parent_id in catalog.ids() for parent_id in artifact.provenance.parent_artifacts):
                catalog.add(artifact)
                del pending[artifact_id]
                progressed = True
        if not progressed:
            raise ValueError(f"cross-domain bundle contains unresolved parent references: {sorted(pending)}")


def compose_cross_domain_bundle(domain_bundles: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], ArtifactCatalog, dict[str, Artifact]]:
    """Compose independent domain bundles into one independently verifiable chain."""
    if set(domain_bundles) != {"neuroscience", "proteomics", "earthspace"}:
        raise ValueError("V1.5 requires neuroscience, proteomics, and earthspace bundles")
    source_reports = {domain: verify_bundle(bundle) for domain, bundle in domain_bundles.items()}
    failures = {domain: report.failures for domain, report in source_reports.items() if not report.verified}
    if failures:
        raise ValueError(f"source bundles must independently verify: {failures}")

    catalog = ArtifactCatalog()
    records: list[dict[str, Any]] = []
    domain_findings: dict[str, Artifact] = {}
    domain_sources: dict[str, Artifact] = {}
    for domain, bundle in domain_bundles.items():
        records.extend(deepcopy(bundle["artifacts"]))
        final_id = bundle["manifest"]["final_finding_id"]
        final_record = next(record for record in bundle["artifacts"] if record["artifact_id"] == final_id)
        domain_findings[domain] = _artifact_from_record(final_record)
        source_candidates = [record for record in bundle["artifacts"] if record.get("kind", "").startswith("raw_")]
        if not source_candidates:
            raise ValueError(f"no raw domain source found for {domain}")
        domain_sources[domain] = _artifact_from_record(source_candidates[0])
    _add_records(catalog, records)
    domain_findings = {domain: catalog.get(artifact.artifact_id) for domain, artifact in domain_findings.items()}
    domain_sources = {domain: catalog.get(artifact.artifact_id) for domain, artifact in domain_sources.items()}

    evidence_by_domain = {domain: {"finding_id": finding.artifact_id, "finding_content_hash": finding.provenance.content_hash, "source_id": domain_sources[domain].artifact_id, "source_content_hash": domain_sources[domain].provenance.content_hash, "source_lineage": [item.artifact_id for item in catalog.lineage(domain_sources[domain].artifact_id)]} for domain, finding in domain_findings.items()}
    cross_analysis = Artifact.derive("cross-domain-analysis-001", "analysis", {"analysis_type": "declared_cross_domain_evidence_composition", "relationship": "three independently verified domain findings are jointly inspected for provenance completeness; no scientific relation is inferred", "domains": sorted(domain_bundles), "evidence_by_domain": evidence_by_domain}, {"domain": "cross-domain", "domain_count": 3}, "compose_cross_domain_evidence", tuple(domain_findings.values()), {"relationship": "provenance_composition_only"})
    catalog.add(cross_analysis)

    cross_inference = Artifact.derive("cross-domain-inference-001", "multimodal_inference", {"analysis_id": cross_analysis.artifact_id, "result": {"all_domain_findings_present": True, "domain_count": len(domain_findings), "relationship_type": "evidence_composition_without_domain_claim"}}, {"domain": "cross-domain", "domains": sorted(domain_bundles)}, "infer_cross_domain_composition", (cross_analysis,), {"decision_rule": "all_three_domain_findings_present"})
    catalog.add(cross_inference)

    uncertainty = {"type": "composition_only_no_cross_domain_effect_estimate", "not_estimated": True, "reason": "V1.5 verifies provenance interoperability rather than asserting a biological or geophysical relationship"}
    claim_statement = "The neuroscience, proteomics, and Earth/Space findings can participate in one independently verifiable evidence composition while retaining domain-specific identities and lineages."
    claim = create_claim_artifact("cross-domain-claim-001", cross_inference, tuple(domain_findings.values()), "Independent domain findings can be composed without erasing their provenance.", claim_statement, ("Each source domain bundle was independently verified before composition",), uncertainty, {"domain": "cross-domain", "domains": sorted(domain_bundles), "evidence_by_domain": evidence_by_domain}, "cross_domain_provenance_composition", catalog=catalog)
    catalog.add(claim)

    finding_payload = {"finding_id": "cross-domain-finding-001", "statement": claim_statement, "evidence": [finding.artifact_id for finding in domain_findings.values()], "evidence_content_hashes": [finding.provenance.content_hash for finding in domain_findings.values()], "analysis_id": claim.artifact_id, "statistical_result": cross_analysis.payload, "status": claim.payload["claim_status"], "claim_status": claim.payload["claim_status"], "domain_evidence": evidence_by_domain}
    finding = Artifact.derive("cross-domain-finding-001", "finding", finding_payload, {"domain": "cross-domain", "status": claim.payload["claim_status"], "evidence_count": len(domain_findings)}, "record_cross_domain_finding", (claim,) + tuple(domain_findings.values()), {"claim_policy": "composition_does_not_auto_convert_to_truth"})
    catalog.add(finding)

    specification = {"domain": "cross-domain", "method": "cross_domain_provenance_composition", "domains": sorted(domain_bundles), "source_bundle_manifest_hashes": {domain: bundle["manifest"]["manifest_hash"] for domain, bundle in domain_bundles.items()}, "domain_evidence": evidence_by_domain, "uncertainty": uncertainty}
    manifest = evidence_manifest("cross-domain-v1.5", finding, catalog)
    execution_identity = hash_object({"specification_hash": hash_object(specification), "analysis_id": cross_analysis.artifact_id, "inference_id": cross_inference.artifact_id, "finding_id": finding.artifact_id, "final_content_hash": finding.provenance.content_hash})
    bundle = build_bundle(manifest, specification, hash_object(specification), catalog, execution_identity)
    bundle["source_domain_reports"] = {domain: report.to_dict() for domain, report in source_reports.items()}
    return bundle, catalog, {"neuroscience": domain_sources["neuroscience"], "proteomics": domain_sources["proteomics"], "earthspace": domain_sources["earthspace"], "finding": finding}


def load_bundle(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def selective_impact(bundle: dict[str, Any], subject_id: str) -> dict[str, Any]:
    snapshot = ObservatorySnapshot.from_bundle(bundle)
    return snapshot.impact_of(subject_id)


def impact_after_revocation(bundle: dict[str, Any], subject_id: str, reason: str = "cross-domain selective revocation") -> dict[str, Any]:
    """Return Observatory impact and statuses after revoking one serialized subject."""
    graph = _graph_from_manifest(bundle["manifest"])
    registry, record = RevocationRegistry().revoke(subject_id, reason, graph)
    sentinel = {"sentinel_status": "VERIFIED", "revocation": record.__dict__, "revocation_registry": registry.to_dict()}
    snapshot = ObservatorySnapshot.from_bundle(bundle, sentinel)
    return {"revocation": record.__dict__, "impact": snapshot.impact_of(subject_id), "finding_status": snapshot.status_for(bundle["manifest"]["final_finding_id"])}


def compose_from_files(paths: dict[str, str | Path]) -> dict[str, Any]:
    bundles = {domain: load_bundle(path) for domain, path in paths.items()}
    bundle, _, _ = compose_cross_domain_bundle(bundles)
    return bundle

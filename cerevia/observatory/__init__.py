"""CEREVIA V1.2 read-only Observatory contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from cerevia.core.hashing import hash_object
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphEdge, GraphNode, NodeType
from cerevia.sentinel.security import RevocationRecord, SentinelEvent
from cerevia.verification.bundle import VerificationReport, verify_bundle


_UPSTREAM_RELATIONS = {
    EdgeType.DERIVED_FROM,
    EdgeType.INFERRED_FROM,
    EdgeType.RECORDED_DURING,
    EdgeType.ASSOCIATED_WITH,
    EdgeType.ANALYZED_BY,
}


def _graph_from_manifest(manifest: dict[str, Any]) -> EvidenceGraph:
    """Reconstruct the graph from the self-contained manifest projection."""
    serialized = manifest.get("evidence_graph", {})
    graph = EvidenceGraph()
    for item in serialized.get("nodes", []):
        graph.add_node(GraphNode(item["node_id"], NodeType(item["node_type"]), deepcopy(item.get("attributes", {}))))
    for item in serialized.get("edges", []):
        graph.add_edge(item["source"], item["target"], EdgeType(item["relation"]), deepcopy(item.get("attributes", {})))
    return graph


def _event_from_dict(item: dict[str, Any]) -> SentinelEvent:
    return SentinelEvent(**deepcopy(item))


def _revocation_from_dict(item: dict[str, Any]) -> RevocationRecord:
    return RevocationRecord(item["subject_id"], item["reason"], item["revoked_at"], tuple(item.get("affected_nodes", ())), item.get("status", "REVOKED"))


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class ObservatorySnapshot:
    """A read-only query surface over one immutable bundle and optional Sentinel state.

    The constructor deep-copies supplied records. Query methods return copies, and
    there are intentionally no methods that mutate evidence, graph, or Sentinel state.
    """

    _bundle: dict[str, Any]
    _sentinel: dict[str, Any]
    _graph: EvidenceGraph
    _verification: VerificationReport

    @classmethod
    def from_bundle(cls, bundle: dict[str, Any], sentinel_result: dict[str, Any] | None = None) -> "ObservatorySnapshot":
        snapshot_bundle = deepcopy(bundle)
        sentinel = deepcopy(sentinel_result or {})
        return cls(snapshot_bundle, sentinel, _graph_from_manifest(snapshot_bundle.get("manifest", {})), verify_bundle(snapshot_bundle))

    @classmethod
    def from_files(cls, bundle_path: str | Path, sentinel_path: str | Path | None = None) -> "ObservatorySnapshot":
        bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        sentinel = json.loads(Path(sentinel_path).read_text(encoding="utf-8")) if sentinel_path else None
        return cls.from_bundle(bundle, sentinel)

    @property
    def graph_hash(self) -> str:
        return self._graph.graph_hash

    @property
    def final_finding_id(self) -> str | None:
        return self._bundle.get("manifest", {}).get("final_finding_id")

    def _record(self, node_id: str) -> dict[str, Any] | None:
        for record in self._bundle.get("artifacts", []):
            if record.get("artifact_id") == node_id:
                return deepcopy(record)
        return None

    def _node(self, node_id: str) -> dict[str, Any]:
        if node_id not in self._graph.nodes:
            raise KeyError(node_id)
        node = self._graph.nodes[node_id]
        return {"node_id": node.node_id, "node_type": node.node_type.value, "attributes": deepcopy(node.attributes), "artifact": self._record(node_id)}

    def _finding_claim_id(self, finding_id: str) -> str | None:
        record = self._record(finding_id)
        if not record or record.get("kind") != "finding":
            return None
        return record.get("payload", {}).get("analysis_id")

    def _lineage_ids(self, finding_id: str) -> list[str]:
        if finding_id not in self._graph.nodes:
            raise KeyError(finding_id)
        discovered: set[str] = set()
        ordered: list[str] = []
        frontier = [finding_id]
        while frontier:
            current = frontier.pop(0)
            if current in discovered:
                continue
            discovered.add(current)
            ordered.append(current)
            outgoing = [edge for edge in self._graph.edges.values() if edge.source == current and edge.relation in _UPSTREAM_RELATIONS]
            incoming_support = [edge for edge in self._graph.edges.values() if edge.target == current and edge.relation == EdgeType.SUPPORTS]
            next_ids = [edge.target for edge in sorted(outgoing, key=lambda e: (e.relation.value, e.target))]
            next_ids.extend(edge.source for edge in sorted(incoming_support, key=lambda e: e.source))
            frontier.extend(node_id for node_id in next_ids if node_id not in discovered)
        return ordered

    def get_finding(self, finding_id: str | None = None) -> dict[str, Any]:
        """Return a finding, its current verification status, and revocation status."""
        identifier = finding_id or self.final_finding_id
        if not identifier:
            raise KeyError("finding_id")
        record = self._record(identifier)
        if not record or record.get("kind") != "finding":
            raise KeyError(identifier)
        return {
            "finding": record,
            "verification": self.get_verification(),
            "status": self.status_for(identifier),
            "claim_id": self._finding_claim_id(identifier),
        }

    def get_lineage(self, finding_id: str | None = None) -> dict[str, Any]:
        identifier = finding_id or self.final_finding_id
        if not identifier:
            raise KeyError("finding_id")
        node_ids = self._lineage_ids(identifier)
        edges = [edge for edge in self._graph.edges.values() if edge.source in node_ids and edge.target in node_ids]
        return {"finding_id": identifier, "node_ids": node_ids, "nodes": [self._node(node_id) for node_id in node_ids], "edges": [self._edge(edge) for edge in sorted(edges, key=lambda e: e.edge_id)]}

    def get_supporting_evidence(self, claim_or_finding_id: str | None = None) -> dict[str, Any]:
        identifier = claim_or_finding_id or self.final_finding_id
        if not identifier:
            raise KeyError("claim_or_finding_id")
        record = self._record(identifier)
        if record and record.get("kind") == "finding":
            identifier = self._finding_claim_id(identifier) or identifier
            record = self._record(identifier)
        if not record or record.get("kind") != "claim":
            raise KeyError(identifier)
        payload = record.get("payload", {})
        evidence_ids = list(payload.get("evidence", []))
        evidence = []
        for index, evidence_id in enumerate(evidence_ids):
            item = self._record(evidence_id) or (self._node(evidence_id) if evidence_id in self._graph.nodes else {"artifact_id": evidence_id})
            if index < len(payload.get("evidence_content_hashes", [])):
                item["declared_content_hash"] = payload["evidence_content_hashes"][index]
            evidence.append(item)
        return {"claim_id": identifier, "claim": record, "evidence": evidence}

    def get_verification(self) -> dict[str, Any]:
        result = self._verification.to_dict()
        if self._sentinel:
            result["sentinel_status"] = self._sentinel.get("sentinel_status")
            result["attestation_verified"] = self._sentinel.get("attestation_verified")
            result["transparency_log_verified"] = self._sentinel.get("transparency_log_verified")
        return result

    def get_attestations(self, subject_id: str | None = None) -> list[dict[str, Any]]:
        attestation = self._sentinel.get("attestation")
        if not attestation:
            return []
        if subject_id and subject_id not in {self.final_finding_id, attestation.get("subject_bundle_hash")}:
            return []
        return [deepcopy(attestation)]

    def _events(self) -> list[dict[str, Any]]:
        return [deepcopy(event) for event in self._sentinel.get("transparency_log", {}).get("events", [])]

    def _revocations(self) -> list[dict[str, Any]]:
        registry = self._sentinel.get("revocation_registry", {})
        return [deepcopy(record) for record in registry.get("records", [])]

    def get_revocations(self, subject_id: str | None = None) -> list[dict[str, Any]]:
        records = self._revocations()
        if subject_id:
            records = [record for record in records if subject_id == record.get("subject_id") or subject_id in record.get("affected_nodes", [])]
        return records

    def get_history(self, subject_id: str | None = None, as_of: str | None = None) -> dict[str, Any]:
        identifier = subject_id or self.final_finding_id
        related = set(self._lineage_ids(identifier)) if identifier and identifier in self._graph.nodes else ({identifier} if identifier else set())
        events = [event for event in self._events() if not related or event.get("subject_id") in related]
        revocations = [record for record in self._revocations() if not related or record.get("subject_id") in related or bool(related.intersection(record.get("affected_nodes", [])))]
        if as_of:
            cutoff = _timestamp(as_of)
            events = [event for event in events if _timestamp(event["timestamp"]) <= cutoff]
            revocations = [record for record in revocations if _timestamp(record["revoked_at"]) <= cutoff]
        timeline = [{"event_type": event["event_type"], "subject_id": event["subject_id"], "timestamp": event["timestamp"], "status": event.get("details", {}).get("result"), "event": event} for event in events]
        timeline.extend({"event_type": "revocation", "subject_id": record["subject_id"], "timestamp": record["revoked_at"], "status": record["status"], "event": record} for record in revocations)
        timeline.sort(key=lambda item: (item["timestamp"], item["event_type"], item["subject_id"]))
        return {"subject_id": identifier, "as_of": as_of, "events": timeline}

    def impact_of(self, artifact_id: str) -> dict[str, Any]:
        if artifact_id not in self._graph.nodes:
            raise KeyError(artifact_id)
        affected = sorted(self._graph.invalidate(artifact_id))
        findings = sorted(node_id for node_id in affected if self._graph.nodes[node_id].node_type == NodeType.FINDING)
        return {"subject_id": artifact_id, "affected_node_ids": affected, "affected_finding_ids": findings, "statuses": {node_id: self.status_for(node_id) for node_id in affected}}

    def status_for(self, node_id: str) -> str:
        for record in self._revocations():
            if node_id in record.get("affected_nodes", []):
                return "AFFECTED / INVESTIGATE"
        return self._sentinel.get("sentinel_status") or ("VERIFIED" if self._verification.verified else "INVESTIGATE")

    @staticmethod
    def _edge(edge: GraphEdge) -> dict[str, Any]:
        return {"edge_id": edge.edge_id, "source": edge.source, "target": edge.target, "relation": edge.relation.value, "attributes": deepcopy(edge.attributes)}

    def to_dict(self) -> dict[str, Any]:
        return {"observatory": "CEREVIA OBSERVATORY", "observatory_version": "1.2.0", "graph_hash": self.graph_hash, "finding": self.get_finding(), "lineage": self.get_lineage(), "supporting_evidence": self.get_supporting_evidence(), "verification": self.get_verification(), "attestations": self.get_attestations(), "revocations": self.get_revocations(), "history": self.get_history(), "impact": self.impact_of(self.final_finding_id) if self.final_finding_id else None}


__all__ = ["ObservatorySnapshot"]

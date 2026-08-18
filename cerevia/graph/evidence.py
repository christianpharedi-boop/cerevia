"""CEREVIA V0.5 typed evidence graph.

The graph is an in-memory, deterministic projection of ontology entities and
content-addressed artifacts. It adds graph queries without replacing the
existing immutable artifact catalog.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import hash_object, thaw
from cerevia.study.ontology import NeuroscienceOntology


class NodeType(StrEnum):
    STUDY = "Study"
    PARTICIPANT = "Participant"
    SESSION = "Session"
    RECORDING = "Recording"
    EVENT = "Event"
    ARTIFACT = "Artifact"
    TRANSFORMATION = "Transformation"
    FEATURE = "Feature"
    ANALYSIS = "Analysis"
    FINDING = "Finding"


class EdgeType(StrEnum):
    GENERATED_BY = "GENERATED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    RECORDED_DURING = "RECORDED_DURING"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    ANALYZED_BY = "ANALYZED_BY"
    SUPPORTS = "SUPPORTS"


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    attributes: dict[str, Any]


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source: str
    target: str
    relation: EdgeType
    attributes: dict[str, Any]


class EvidenceGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, GraphEdge] = {}

    def add_node(self, node: GraphNode) -> GraphNode:
        if node.node_id in self.nodes and self.nodes[node.node_id] != node:
            raise ValueError(f"graph node already exists with different identity: {node.node_id}")
        self.nodes[node.node_id] = node
        return node

    def add_edge(self, source: str, target: str, relation: EdgeType, attributes: dict[str, Any] | None = None) -> GraphEdge:
        if source not in self.nodes or target not in self.nodes:
            raise ValueError("graph edges require registered source and target nodes")
        edge_id = hash_object({"source": source, "target": target, "relation": relation.value, "attributes": attributes or {}})
        edge = GraphEdge(edge_id, source, target, relation, attributes or {})
        if edge_id in self.edges and self.edges[edge_id] != edge:
            raise ValueError(f"graph edge identity collision: {edge_id}")
        self.edges[edge_id] = edge
        return edge

    def _edges_from(self, node_id: str, relations: set[EdgeType] | None = None) -> Iterable[GraphEdge]:
        return (edge for edge in self.edges.values() if edge.source == node_id and (relations is None or edge.relation in relations))

    def _edges_to(self, node_id: str, relations: set[EdgeType] | None = None) -> Iterable[GraphEdge]:
        return (edge for edge in self.edges.values() if edge.target == node_id and (relations is None or edge.relation in relations))

    def supports_finding(self, finding_id: str) -> set[str]:
        """Return all graph nodes that support a finding, including upstream evidence."""
        if finding_id not in self.nodes:
            raise KeyError(finding_id)
        supported: set[str] = set()
        frontier = [edge.source for edge in self._edges_to(finding_id, {EdgeType.SUPPORTS})]
        while frontier:
            node_id = frontier.pop()
            if node_id in supported:
                continue
            supported.add(node_id)
            frontier.extend(edge.target for edge in self._edges_from(node_id, {EdgeType.ANALYZED_BY, EdgeType.ASSOCIATED_WITH, EdgeType.RECORDED_DURING, EdgeType.DERIVED_FROM}))
        return supported

    def downstream(self, node_id: str) -> set[str]:
        """Return every node that may be affected if node_id is invalidated."""
        if node_id not in self.nodes:
            raise KeyError(node_id)
        affected: set[str] = set()
        frontier = [edge.source for edge in self._edges_to(node_id, {EdgeType.DERIVED_FROM, EdgeType.RECORDED_DURING, EdgeType.ASSOCIATED_WITH, EdgeType.ANALYZED_BY})]
        while frontier:
            current = frontier.pop()
            if current in affected:
                continue
            affected.add(current)
            frontier.extend(edge.source for edge in self._edges_to(current, {EdgeType.DERIVED_FROM, EdgeType.RECORDED_DURING, EdgeType.ASSOCIATED_WITH, EdgeType.ANALYZED_BY}))
            frontier.extend(edge.target for edge in self._edges_from(current, {EdgeType.SUPPORTS}))
        return affected

    def findings_depending_on(self, node_id: str) -> set[str]:
        return {candidate for candidate in self.downstream(node_id) if self.nodes[candidate].node_type == NodeType.FINDING}

    def invalidate(self, node_id: str) -> set[str]:
        """Compute the invalidation closure without mutating the graph."""
        return {node_id} | self.downstream(node_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"node_id": node.node_id, "node_type": node.node_type.value, "attributes": thaw(node.attributes)}
                for node in sorted(self.nodes.values(), key=lambda item: item.node_id)
            ],
            "edges": [
                {"edge_id": edge.edge_id, "source": edge.source, "target": edge.target,
                 "relation": edge.relation.value, "attributes": thaw(edge.attributes)}
                for edge in sorted(self.edges.values(), key=lambda item: item.edge_id)
            ],
        }

    @property
    def graph_hash(self) -> str:
        return hash_object(self.to_dict())


def _ontology_node(graph: EvidenceGraph, node_id: str, node_type: NodeType, entity: Any) -> None:
    graph.add_node(GraphNode(node_id, node_type, thaw(entity.__dict__)))


def project_evidence_graph(catalog: ArtifactCatalog, ontology: NeuroscienceOntology | None = None) -> EvidenceGraph:
    graph = EvidenceGraph()
    if ontology is not None:
        for study in ontology.studies.values():
            _ontology_node(graph, study.study_id, NodeType.STUDY, study)
        for participant in ontology.participants.values():
            _ontology_node(graph, participant.participant_id, NodeType.PARTICIPANT, participant)
            graph.add_edge(participant.participant_id, participant.study_id, EdgeType.ASSOCIATED_WITH)
        for session in ontology.sessions.values():
            _ontology_node(graph, session.session_id, NodeType.SESSION, session)
            graph.add_edge(session.session_id, session.participant_id, EdgeType.ASSOCIATED_WITH)
        for recording in ontology.recordings.values():
            _ontology_node(graph, recording.recording_id, NodeType.RECORDING, recording)
            graph.add_edge(recording.recording_id, recording.session_id, EdgeType.RECORDED_DURING)
            for channel in recording.channels:
                channel_id = f"{recording.recording_id}:{channel.channel_id}"
                graph.add_node(GraphNode(channel_id, NodeType.RECORDING, thaw(channel.__dict__)))
                graph.add_edge(channel_id, recording.recording_id, EdgeType.ASSOCIATED_WITH)
        for event in ontology.events.values():
            _ontology_node(graph, event.event_id, NodeType.EVENT, event)
            graph.add_edge(event.event_id, event.recording_id, EdgeType.RECORDED_DURING)
        for epoch in ontology.epochs.values():
            _ontology_node(graph, epoch.epoch_id, NodeType.ARTIFACT, epoch)
            graph.add_edge(epoch.epoch_id, epoch.recording_id, EdgeType.RECORDED_DURING)
        for feature in ontology.features.values():
            _ontology_node(graph, feature.feature_id, NodeType.FEATURE, feature)
            if feature.artifact_id in graph.nodes:
                graph.add_edge(feature.feature_id, feature.artifact_id, EdgeType.ASSOCIATED_WITH)
            for epoch_id in feature.epoch_ids:
                if epoch_id in graph.nodes:
                    graph.add_edge(feature.feature_id, epoch_id, EdgeType.ASSOCIATED_WITH)
        for analysis in ontology.analyses.values():
            _ontology_node(graph, analysis.analysis_id, NodeType.ANALYSIS, analysis)
            if analysis.artifact_id in graph.nodes:
                graph.add_edge(analysis.analysis_id, analysis.artifact_id, EdgeType.ASSOCIATED_WITH)
            for feature_id in analysis.feature_ids:
                if feature_id in graph.nodes:
                    graph.add_edge(analysis.analysis_id, feature_id, EdgeType.ANALYZED_BY)
        for finding in ontology.findings.values():
            _ontology_node(graph, finding.finding_id, NodeType.FINDING, finding)
            graph.add_edge(finding.analysis_id, finding.finding_id, EdgeType.SUPPORTS)
            if finding.artifact_id in graph.nodes:
                graph.add_edge(finding.finding_id, finding.artifact_id, EdgeType.ASSOCIATED_WITH)

    for artifact in catalog.all():
        artifact_node_type = {"analysis": NodeType.ANALYSIS, "multimodal_inference": NodeType.ANALYSIS, "finding": NodeType.FINDING}.get(artifact.kind, NodeType.ARTIFACT)
        graph.add_node(GraphNode(artifact.artifact_id, artifact_node_type, {
            "kind": artifact.kind, "content_hash": artifact.provenance.content_hash,
            "operation": artifact.provenance.operation,
        }))
        transform_id = f"transformation:{artifact.artifact_id}"
        graph.add_node(GraphNode(transform_id, NodeType.TRANSFORMATION, {
            "operation": artifact.provenance.operation, "content_hash": artifact.provenance.content_hash,
        }))
        graph.add_edge(artifact.artifact_id, transform_id, EdgeType.GENERATED_BY)
        for parent_id in artifact.provenance.parent_artifacts:
            if parent_id in graph.nodes:
                graph.add_edge(artifact.artifact_id, parent_id, EdgeType.DERIVED_FROM)
        metadata = thaw(artifact.metadata)
        for key in ("recording_id", "session_id", "participant_id", "study_id"):
            target = metadata.get(key)
            if target in graph.nodes:
                graph.add_edge(artifact.artifact_id, target, EdgeType.RECORDED_DURING if key == "recording_id" else EdgeType.ASSOCIATED_WITH)
        for associated_id in metadata.get("associated_artifact_ids", []):
            if associated_id in graph.nodes:
                graph.add_edge(artifact.artifact_id, associated_id, EdgeType.ASSOCIATED_WITH)
        if artifact.kind == "finding":
            payload = thaw(artifact.payload)
            analysis_id = payload.get("analysis_id")
            if analysis_id in graph.nodes:
                graph.add_edge(analysis_id, artifact.artifact_id, EdgeType.SUPPORTS)
            for evidence_id in payload.get("evidence", []):
                if evidence_id in graph.nodes:
                    graph.add_edge(evidence_id, artifact.artifact_id, EdgeType.SUPPORTS)
    return graph

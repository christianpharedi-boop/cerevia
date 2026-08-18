from __future__ import annotations
import unittest

from cerevia.neuro.eeg import EEGObservation
from cerevia.graph.evidence import EdgeType, EvidenceGraph, GraphNode, NodeType, project_evidence_graph
from cerevia.pipeline import run_pipeline, verify_manifest
from cerevia.study.ontology import NeuroscienceOntology, Participant, Session, Study
import numpy as np


class EvidenceGraphTests(unittest.TestCase):
    def test_manual_graph_requires_registered_endpoints(self):
        graph = EvidenceGraph()
        graph.add_node(GraphNode("raw", NodeType.ARTIFACT, {}))
        with self.assertRaises(ValueError):
            graph.add_edge("raw", "missing", EdgeType.DERIVED_FROM)

    def test_pipeline_graph_answers_support_and_invalidation_queries(self):
        t = np.arange(1024) / 128.0
        observation = EEGObservation.from_array(
            np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)]),
            128.0,
            ("C3", "C4"),
        )
        catalog, final, manifest = run_pipeline(observation)
        graph = project_evidence_graph(catalog)
        support = graph.supports_finding(final.artifact_id)
        self.assertIn("raw-eeg-001", support)
        self.assertIn("analysis-001", support)
        self.assertIn("filter-001", graph.downstream("raw-eeg-001"))
        self.assertIn("finding-001", graph.findings_depending_on("raw-eeg-001"))
        self.assertIn("finding-001", graph.invalidate("filter-001"))
        self.assertEqual(manifest["evidence_graph_hash"], graph.graph_hash)
        self.assertTrue(verify_manifest(manifest, catalog))

    def test_ontology_projection_retains_context_nodes(self):
        t = np.arange(1024) / 128.0
        observation = EEGObservation.from_array(
            np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)]),
            128.0,
            ("C3", "C4"),
        )
        catalog, _, _ = run_pipeline(observation)
        ontology = NeuroscienceOntology()
        ontology.add_study(Study("demo-001", "Graph study"))
        ontology.add_participant(Participant("sub-001", "demo-001"))
        ontology.add_session(Session("ses-01", "demo-001", "sub-001", "rest", "baseline"))
        graph = project_evidence_graph(catalog, ontology)
        self.assertEqual(graph.nodes["demo-001"].node_type, NodeType.STUDY)
        self.assertEqual(graph.nodes["sub-001"].node_type, NodeType.PARTICIPANT)
        self.assertIn("ses-01", graph.nodes)


if __name__ == "__main__":
    unittest.main()

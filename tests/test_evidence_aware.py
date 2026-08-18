from __future__ import annotations
import unittest
import numpy as np

from cerevia.analysis.evidence_aware import EvidenceAwareAnalysisSpecification, execute_evidence_aware_analysis
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.environment import fingerprint
from cerevia.core.provenance import Artifact
from cerevia.graph.evidence import NodeType, EdgeType, project_evidence_graph
from cerevia.multimodal.evidence import BehavioralEvent, align_behavioral_events, ingest_behavioral_events
from cerevia.pipeline import finding
from cerevia.study.ontology import Channel, Modality, Recording


class EvidenceAwareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recording = Recording("eeg-v08", "ses-01", Modality.EEG, (Channel("c3", "C3"),), 100.0, "dots", "", "edf", "sub-001", 10.0)
        self.raw = Artifact.derive("raw-v08", "raw_eeg", {"samples": [1, 2, 3]}, {"participant_id": "sub-001", "session_id": "ses-01", "task": "dots"}, "test")
        self.behavior = ingest_behavioral_events("behavior-v08", (BehavioralEvent("event-v08", "sub-001", "ses-01", "dots", "stimulus", 1.0),), "study-v08")
        self.alignment, _ = align_behavioral_events("alignment-v08", self.recording, self.behavior, self.raw)
        self.catalog = ArtifactCatalog()
        for artifact in (self.raw, self.behavior, self.alignment):
            self.catalog.add(artifact)
        env = fingerprint()
        self.specification = EvidenceAwareAnalysisSpecification(
            input_artifacts=(
                {"artifact_id": self.raw.artifact_id, "content_hash": self.raw.provenance.content_hash},
                {"artifact_id": self.behavior.artifact_id, "content_hash": self.behavior.provenance.content_hash},
            ),
            alignment_artifacts=({"artifact_id": self.alignment.artifact_id, "content_hash": self.alignment.provenance.content_hash},),
            hypothesis="The declared EEG and behavioral observations support a context-bound provisional comparison.",
            experimental_conditions={"task": "dots", "condition": "stimulus"},
            comparison={"left": "observed", "right": "declared_null", "null_value": 0.0},
            method="context_bound_descriptive_inference",
            parameters={"version": 1},
            assumptions=("timestamps share recording seconds", "observations are pseudonymized"),
            output_definitions={"effect": {"type": "descriptive", "unit": "arbitrary"}},
            uncertainty={"type": "not_estimated", "reason": "V0.8 proof declares uncertainty without overstating precision"},
            software_environment=env,
            expected_outputs=("analysis-v08", "inference-v08", "finding-v08"),
        )

    def test_specification_requires_scientific_fields(self):
        with self.assertRaises(ValueError):
            EvidenceAwareAnalysisSpecification(
                input_artifacts=self.specification.input_artifacts,
                alignment_artifacts=self.specification.alignment_artifacts,
                hypothesis="", experimental_conditions={"task": "dots"}, comparison={"left": "a"},
                method="method", parameters={}, assumptions=("one",), output_definitions={"x": 1},
                uncertainty={"type": "unknown"}, software_environment=fingerprint(), expected_outputs=("a", "b", "c"))

    def test_execution_preserves_analysis_inference_and_uncertainty(self):
        result = execute_evidence_aware_analysis(self.specification, self.catalog, "study-v08")
        self.assertEqual(result.analysis_artifact_id, "analysis-v08")
        self.assertEqual(result.inference_artifact_id, "inference-v08")
        self.assertEqual(result.finding_artifact_id, "finding-v08")
        graph = project_evidence_graph(self.catalog)
        self.assertEqual(graph.nodes["analysis-v08"].node_type, NodeType.ANALYSIS)
        self.assertEqual(graph.nodes["inference-v08"].node_type, NodeType.INFERENCE)
        self.assertTrue(any(edge.relation == EdgeType.INFERRED_FROM and edge.source == "inference-v08" for edge in graph.edges.values()))
        self.assertEqual(self.catalog.get("inference-v08").payload["uncertainty"]["type"], "not_estimated")
        self.assertIn("finding-v08", graph.findings_depending_on("behavior-v08"))

    def test_changed_input_hash_is_rejected(self):
        tampered = EvidenceAwareAnalysisSpecification(
            input_artifacts=({"artifact_id": self.raw.artifact_id, "content_hash": "0" * 64},) + self.specification.input_artifacts[1:],
            alignment_artifacts=self.specification.alignment_artifacts,
            hypothesis=self.specification.hypothesis, experimental_conditions=self.specification.experimental_conditions,
            comparison=self.specification.comparison, method=self.specification.method, parameters=self.specification.parameters,
            assumptions=self.specification.assumptions, output_definitions=self.specification.output_definitions,
            uncertainty=self.specification.uncertainty, software_environment=self.specification.software_environment,
            expected_outputs=("analysis-t", "inference-t", "finding-t"))
        with self.assertRaises(ValueError):
            execute_evidence_aware_analysis(tampered, self.catalog)

    def test_disconnected_alignment_is_rejected(self):
        unrelated = Artifact.derive("raw-unrelated", "raw_eeg", {"x": 1}, {"participant_id": "sub-001", "session_id": "ses-01", "task": "dots"}, "test")
        unrelated_alignment = Artifact.derive("alignment-unrelated", "cross_modal_alignment", {"x": 1}, {}, "test", parents=(unrelated,))
        self.catalog.add(unrelated)
        self.catalog.add(unrelated_alignment)
        bad = EvidenceAwareAnalysisSpecification(
            input_artifacts=self.specification.input_artifacts,
            alignment_artifacts=({"artifact_id": unrelated_alignment.artifact_id, "content_hash": unrelated_alignment.provenance.content_hash},),
            hypothesis=self.specification.hypothesis, experimental_conditions=self.specification.experimental_conditions,
            comparison=self.specification.comparison, method=self.specification.method, parameters=self.specification.parameters,
            assumptions=self.specification.assumptions, output_definitions=self.specification.output_definitions,
            uncertainty=self.specification.uncertainty, software_environment=self.specification.software_environment,
            expected_outputs=("analysis-bad", "inference-bad", "finding-bad"))
        with self.assertRaises(ValueError):
            execute_evidence_aware_analysis(bad, self.catalog)


if __name__ == "__main__":
    unittest.main()

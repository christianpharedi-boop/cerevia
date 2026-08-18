from __future__ import annotations
import unittest
import numpy as np

from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.study.ontology import (
    Analysis, Channel, Epoch, Event, Feature, Finding, Modality, NeuroscienceOntology,
    Participant, Recording, Session, Study,
)


class OntologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ontology = NeuroscienceOntology()
        self.ontology.add_study(Study("study-001", "Demo cognitive EEG", "Ontology integration test"))
        self.ontology.add_participant(Participant("sub-001", "study-001"))
        self.ontology.add_session(Session("ses-01", "study-001", "sub-001", "oddball", "target"))
        channels = (Channel("ch-c3", "C3", unit="uV"), Channel("ch-c4", "C4", unit="uV"))
        self.ontology.add_recording(Recording("rec-001", "ses-01", Modality.EEG, channels, 128.0, "oddball", "target"))

    def test_context_preserves_experimental_meaning(self):
        context = self.ontology.context_for_recording("rec-001")
        self.assertEqual(context["participant_id"], "sub-001")
        self.assertEqual(context["task"], "oddball")
        self.assertEqual(context["condition"], "target")
        self.assertEqual(context["modality"], "EEG")

    def test_entity_hierarchy_requires_registered_parents(self):
        with self.assertRaises(ValueError):
            self.ontology.add_recording(Recording("rec-bad", "ses-missing", Modality.EEG, (Channel("ch", "Cz"),), 128.0))
        event = self.ontology.add_event(Event("event-001", "rec-001", 32, "stimulus"))
        epoch = self.ontology.add_epoch(Epoch("epoch-001", "rec-001", 0, 128, event.event_id, "target"))
        feature = self.ontology.add_feature(Feature("feature-001", "alpha-power-001", "rec-001", "alpha power", (epoch.epoch_id,)))
        analysis = self.ontology.add_analysis(Analysis("analysis-ontology-001", "analysis-001", (feature.feature_id,), "mean alpha power", "oddball", "target"))
        finding = self.ontology.add_finding(Finding("finding-ontology-001", "finding-001", analysis.analysis_id, "Target trials show alpha power."))
        self.assertEqual(finding.status, "PROVISIONAL")

    def test_ontology_entities_are_immutable_and_unique(self):
        with self.assertRaises(ValueError):
            self.ontology.add_study(Study("study-001", "Duplicate"))
        with self.assertRaises(ValueError):
            self.ontology.add_participant(Participant("sub-001", "study-001", pseudonymized=False))

    def test_eeg_artifact_carries_recording_context(self):
        observation = EEGObservation.from_array(np.ones((2, 8)), 128.0, ("C3", "C4"))
        artifact = ingest_eeg("raw-context", observation, "study-001", "sub-001", "ses-01", self.ontology.recordings["rec-001"])
        self.assertEqual(artifact.metadata["recording_id"], "rec-001")
        self.assertEqual(artifact.metadata["task"], "oddball")
        self.assertEqual(artifact.metadata["condition"], "target")

    def test_context_mismatch_is_rejected(self):
        observation = EEGObservation.from_array(np.ones((2, 8)), 128.0, ("C3", "C4"))
        with self.assertRaises(ValueError):
            ingest_eeg("raw-context", observation, "study-001", "sub-001", "ses-01",
                        Recording("rec-other", "ses-01", Modality.MEG,
                                  (Channel("ch-c3", "C3"), Channel("ch-c4", "C4")), 128.0))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import os
from pathlib import Path
import unittest
import numpy as np

from cerevia.neuro.eeg import EEGObservation, ingest_eeg
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.graph.evidence import project_evidence_graph
from cerevia.multimodal.evidence import BehavioralEvent, align_behavioral_events, ingest_behavioral_events, multimodal_analysis
from cerevia.pipeline import epoch_eeg, filter_eeg, finding, qc_eeg, spectral_power
from cerevia.study.ontology import Channel, Modality, Recording


class MultimodalTests(unittest.TestCase):
    def setUp(self) -> None:
        t = np.arange(1024) / 128.0
        observation = EEGObservation.from_array(
            np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)]),
            128.0, ("C3", "C4"))
        self.raw = ingest_eeg("raw-mm-test", observation, "study-mm", "sub-001", "ses-01")
        self.recording = Recording(
            "rec-mm-test", "ses-01", Modality.EEG,
            (Channel("c3", "C3"), Channel("c4", "C4")), 128.0, "task", "MI",
            participant_id="sub-001", duration_seconds=8.0)
        self.events = (
            BehavioralEvent("beh-1", "sub-001", "ses-01", "task", "MI", 1.0, condition="MI"),
            BehavioralEvent("beh-2", "sub-001", "ses-01", "task", "Rest", 3.0, condition="Rest"),
        )

    def test_alignment_requires_shared_session(self):
        behavioral = ingest_behavioral_events("beh-test", self.events, "study-mm")
        other = Recording("rec-other", "ses-02", Modality.EEG, self.recording.channels, 128.0, "task", "MI", participant_id="sub-001", duration_seconds=8.0)
        with self.assertRaises(ValueError):
            align_behavioral_events("align-bad", other, behavioral, self.raw)

    def test_multimodal_analysis_preserves_parents_and_graph_dependency(self):
        catalog = ArtifactCatalog()
        raw = catalog.add(self.raw)
        qc, report = qc_eeg(raw, "qc-mm")
        catalog.add(qc)
        filtered = catalog.add(filter_eeg(raw, "filter-mm", qc=qc))
        epochs = catalog.add(epoch_eeg(filtered, "epoch-mm"))
        feature = catalog.add(spectral_power(epochs, "feature-mm"))
        behavioral = catalog.add(ingest_behavioral_events("behavior-mm", self.events, "study-mm"))
        alignment, _ = align_behavioral_events("alignment-mm", self.recording, behavioral, self.raw)
        catalog.add(alignment)
        analysis = catalog.add(multimodal_analysis("analysis-mm", feature, behavioral, alignment, "provisional"))
        final = catalog.add(finding(analysis, (raw, qc, filtered, epochs, feature, behavioral, alignment), "finding-mm", "provisional", catalog=catalog))
        graph = project_evidence_graph(catalog)
        self.assertEqual(set(analysis.provenance.parent_artifacts), {"feature-mm", "behavior-mm", "alignment-mm"})
        self.assertIn("finding-mm", graph.findings_depending_on("behavior-mm"))
        self.assertIn("analysis-mm", graph.supports_finding(final.artifact_id))

    @unittest.skipUnless(os.environ.get("CEREVIA_BIDS_EDF"), "set CEREVIA_BIDS_EDF to run real multimodal signal test")
    def test_real_run_is_available_for_v06(self):
        self.assertTrue(Path(os.environ["CEREVIA_BIDS_EDF"]).exists())

    def test_wrong_participant_and_task_are_rejected(self):
        wrong_participant = ingest_behavioral_events(
            "beh-wrong-participant",
            (BehavioralEvent("bad-p", "sub-999", "ses-01", "task", "MI", 1.0),),
            "study-mm")
        with self.assertRaises(ValueError):
            align_behavioral_events("align-bad-p", self.recording, wrong_participant, self.raw)
        wrong_task = ingest_behavioral_events(
            "beh-wrong-task",
            (BehavioralEvent("bad-t", "sub-001", "ses-01", "different-task", "MI", 1.0),),
            "study-mm")
        with self.assertRaises(ValueError):
            align_behavioral_events("align-bad-task", self.recording, wrong_task, self.raw)

    def test_negative_onsets_are_rejected(self):
        with self.assertRaises(ValueError):
            BehavioralEvent("bad-negative", "sub-001", "ses-01", "task", "MI", -1.0)

    def test_out_of_range_event_and_invalid_tolerance_are_rejected(self):
        outside = ingest_behavioral_events(
            "beh-outside", (BehavioralEvent("bad-outside", "sub-001", "ses-01", "task", "MI", 9.0),), "study-mm")
        with self.assertRaises(ValueError):
            align_behavioral_events("align-outside", self.recording, outside, self.raw)
        behavioral = ingest_behavioral_events("beh-tolerance", self.events, "study-mm")
        with self.assertRaises(ValueError):
            align_behavioral_events("align-tolerance", self.recording, behavioral, self.raw, tolerance_seconds=-0.1)

    def test_alignment_identity_changes_when_behavioral_or_eeg_parent_changes(self):
        behavioral = ingest_behavioral_events("beh-identity", self.events, "study-mm")
        first, _ = align_behavioral_events("align-identity", self.recording, behavioral, self.raw)
        changed_events = ingest_behavioral_events(
            "beh-identity-2", (BehavioralEvent("beh-new", "sub-001", "ses-01", "task", "MI", 1.5),), "study-mm")
        second, _ = align_behavioral_events("align-identity-2", self.recording, changed_events, self.raw)
        self.assertNotEqual(first.provenance.content_hash, second.provenance.content_hash)
        changed_raw = ingest_eeg(
            "raw-mm-test-2",
            EEGObservation.from_array(
                np.vstack([np.sin(2 * np.pi * 11 * np.arange(1024) / 128.0), np.sin(2 * np.pi * 11 * np.arange(1024) / 128.0)]),
                128.0, ("C3", "C4")),
            "study-mm", "sub-001", "ses-01")
        third, _ = align_behavioral_events("align-identity-3", self.recording, behavioral, changed_raw)
        self.assertNotEqual(first.provenance.content_hash, third.provenance.content_hash)

    def test_event_to_sample_mapping_is_deterministic(self):
        behavioral = ingest_behavioral_events("beh-map", self.events, "study-mm")
        first, context_a = align_behavioral_events("align-map-a", self.recording, behavioral, self.raw)
        second, context_b = align_behavioral_events("align-map-b", self.recording, behavioral, self.raw)
        self.assertEqual(context_a.event_sample_map, context_b.event_sample_map)
        self.assertEqual(first.payload["event_sample_map"], second.payload["event_sample_map"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import os
from pathlib import Path
import unittest
import numpy as np

from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.graph.evidence import project_evidence_graph
from cerevia.multimodal.evidence import BehavioralEvent, align_behavioral_events, ingest_behavioral_events, multimodal_analysis
from cerevia.pipeline import epoch_eeg, filter_eeg, finding, qc_eeg, spectral_power
from cerevia.study.ontology import Channel, Modality, Recording


class MultimodalTests(unittest.TestCase):
    def setUp(self) -> None:
        t = np.arange(1024) / 128.0
        observation = EEGObservation.from_array(np.vstack([np.sin(2 * np.pi * 10 * t), np.sin(2 * np.pi * 10 * t)]), 128.0, ("C3", "C4"))
        self.raw = ingest_eeg("raw-mm-test", observation, "study-mm", "sub-001", "ses-01")
        self.recording = Recording("rec-mm-test", "ses-01", Modality.EEG,
                                   (Channel("c3", "C3"), Channel("c4", "C4")), 128.0, "task", "MI")
        self.events = (BehavioralEvent("beh-1", "sub-001", "ses-01", "task", "MI", 1.0, condition="MI"),
                       BehavioralEvent("beh-2", "sub-001", "ses-01", "task", "Rest", 3.0, condition="Rest"))

    def test_alignment_requires_shared_session(self):
        behavioral = ingest_behavioral_events("beh-test", self.events, "study-mm")
        other = Recording("rec-other", "ses-02", Modality.EEG, self.recording.channels, 128.0, "task", "MI")
        with self.assertRaises(ValueError):
            align_behavioral_events("align-bad", other, behavioral)

    def test_multimodal_analysis_preserves_parents_and_graph_dependency(self):
        catalog = ArtifactCatalog()
        raw = catalog.add(self.raw)
        qc, report = qc_eeg(raw, "qc-mm")
        catalog.add(qc)
        filtered = catalog.add(filter_eeg(raw, "filter-mm", qc=qc))
        epochs = catalog.add(epoch_eeg(filtered, "epoch-mm"))
        feature = catalog.add(spectral_power(epochs, "feature-mm"))
        behavioral = catalog.add(ingest_behavioral_events("behavior-mm", self.events, "study-mm"))
        alignment, _ = align_behavioral_events("alignment-mm", self.recording, behavioral)
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


if __name__ == "__main__":
    unittest.main()

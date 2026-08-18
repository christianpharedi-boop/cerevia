from __future__ import annotations
import gzip
import json
import os
import tempfile
import unittest
from pathlib import Path

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.provenance import Artifact
from cerevia.graph.evidence import project_evidence_graph
from cerevia.multimodal.evidence import BehavioralEvent, align_behavioral_events, ingest_behavioral_events
from cerevia.neuro.eye_tracking import align_eeg_eye, ingest_eye_tracking, load_eye_tracking_run, three_stream_inference
from cerevia.study.ontology import Channel, Modality, Recording
from cerevia.pipeline import finding


class EyeTrackingTests(unittest.TestCase):
    def _make_eye_files(self, root: Path) -> tuple[Path, Path]:
        data = root / "sub-01_ses-01_task-dots_recording-eye1_physio.tsv"
        sidecar = root / "sub-01_ses-01_task-dots_recording-eye1_physio.json"
        data.write_text("0.000\t10\t20\n0.002\t11\t21\n0.004\t12\t22\n", encoding="utf-8")
        sidecar.write_text(json.dumps({"SamplingFrequency": 500.0, "Columns": ["time", "L-GAZE-X", "L-GAZE-Y"], "PhysioType": "eyetrack"}), encoding="utf-8")
        return data, sidecar

    def test_eye_tracking_observation_is_independently_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            data, sidecar = self._make_eye_files(Path(directory))
            run = load_eye_tracking_run(data, sidecar, "sub-001", "ses-01", "dots")
            artifact = ingest_eye_tracking("eye-001", run, "study-001")
            self.assertEqual(run.sample_count, 3)
            self.assertEqual(run.sampling_frequency_hz, 500.0)
            self.assertEqual(artifact.kind, "eye_tracking")
            self.assertTrue(artifact.metadata["independent_observation"])

    def test_eeg_eye_alignment_rejects_context_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            data, sidecar = self._make_eye_files(Path(directory))
            run = load_eye_tracking_run(data, sidecar, "sub-001", "ses-01", "dots")
            eye_recording = run.to_recording()
            eye = ingest_eye_tracking("eye-002", run, "study-001")
            eeg_recording = Recording("eeg-001", "ses-01", Modality.EEG, (Channel("c3", "C3"),), 500.0, "other-task", "", "edf", "sub-001", 1.0)
            eeg = Artifact.derive("raw-eeg-001", "raw_eeg", {"sample": [1]}, {"participant_id": "sub-001", "session_id": "ses-01", "task": "other-task"}, "test")
            with self.assertRaises(ValueError):
                align_eeg_eye("align-bad", eeg_recording, eye_recording, eeg, eye)

    def test_three_stream_inference_preserves_independent_observations(self):
        eeg_recording = Recording("eeg-003", "ses-01", Modality.EEG, (Channel("c3", "C3"),), 500.0, "dots", "", "edf", "sub-001", 2.0)
        eye_recording = Recording("eye-003", "ses-01", Modality.EYE_TRACKING, (Channel("gaze-x", "L-GAZE-X", "eye_tracking", "pixel"),), 500.0, "dots", "", "tsv", "sub-001", 2.0)
        raw = Artifact.derive("raw-eeg-003", "raw_eeg", {"sample": [1]}, {"participant_id": "sub-001", "session_id": "ses-01", "task": "dots"}, "test")
        feature = Artifact.derive("feature-003", "spectral_power", [1.0, 2.0], {"participant_id": "sub-001", "session_id": "ses-01", "task": "dots", "eeg_parent_artifact_id": raw.artifact_id}, "test", parents=(raw,))
        events = (BehavioralEvent("event-003", "sub-001", "ses-01", "dots", "stimulus", 0.5),)
        behavior = ingest_behavioral_events("behavior-003", events, "study-001")
        eye = Artifact.derive("eye-003-artifact", "eye_tracking", {"sample_count": 3}, {"participant_id": "sub-001", "session_id": "ses-01", "task": "dots"}, "test")
        eeg_behavior, _ = align_behavioral_events("align-behavior-003", eeg_recording, behavior, raw)
        eeg_eye = align_eeg_eye("align-eye-003", eeg_recording, eye_recording, raw, eye)
        inference = three_stream_inference("inference-003", feature, behavior, eye, eeg_behavior, eeg_eye, "provisional three-stream result")
        self.assertEqual(inference.kind, "multimodal_inference")
        self.assertEqual(set(inference.provenance.parent_artifacts), {"feature-003", "behavior-003", "eye-003-artifact", "align-behavior-003", "align-eye-003"})
        catalog = ArtifactCatalog()
        for artifact in (raw, feature, behavior, eye, eeg_behavior, eeg_eye, inference):
            catalog.add(artifact)
        final = catalog.add(finding(inference, (raw, feature, behavior, eye, eeg_behavior, eeg_eye), "finding-003", "provisional", catalog=catalog))
        graph = project_evidence_graph(catalog)
        self.assertIn(final.artifact_id, graph.findings_depending_on(eye.artifact_id))

    @unittest.skipUnless(os.environ.get("CEREVIA_EYE_TSV"), "set CEREVIA_EYE_TSV for real EEGEyeNet proof")
    def test_real_eye_tracking_file_is_available(self):
        self.assertTrue(Path(os.environ["CEREVIA_EYE_TSV"]).exists())


if __name__ == "__main__":
    unittest.main()

"""Ingest the real OpenNeuro EEGEyeNet eye stream and test context-safe relationships."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.multimodal.eye_tracking import load_eye_tracking_run, ingest_eye_tracking, align_eeg_eye
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.study.ontology import Channel, Modality, Recording
from cerevia.core.provenance import Artifact


def main(data_path: str, sidecar_path: str) -> None:
    run = load_eye_tracking_run(data_path, sidecar_path, "sub-EP10", "ses-01", "dots", "eye1")
    eye_recording = run.to_recording()
    eye_artifact = ingest_eye_tracking("eye-observation-001", run, "ds005872")
    catalog = ArtifactCatalog()
    catalog.add(eye_artifact)

    # A deliberately incompatible EEG context demonstrates that cross-modal relationships
    # cannot be asserted merely because both files are labeled as neuroscience data.
    eeg_recording = Recording("rec-incompatible", "ses-01", Modality.EEG,
                              (Channel("c3", "C3"),), 125.0, "MIvsRest", "MI",
                              participant_id="sub-02", duration_seconds=125.0)
    eeg_artifact = Artifact.derive("raw-incompatible", "raw_eeg", {"source": "separate_dataset"},
                                   {"participant_id": "sub-02", "session_id": "ses-01", "task": "MIvsRest"},
                                   "external_fixture")
    try:
        align_eeg_eye("rejected-alignment", eeg_recording, eye_recording, eeg_artifact, eye_artifact)
    except ValueError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("incompatible EEG-eye context was accepted")

    result = {
        "dataset_id": "doi:10.18112/openneuro.ds005872.v1.0.0",
        "participant_id": run.participant_id, "session_id": run.session_id, "task": run.task,
        "recording_id": eye_recording.recording_id, "source_sha256": run.source_sha256,
        "sample_count": run.sample_count, "sampling_frequency_hz": run.sampling_frequency_hz,
        "duration_seconds": run.duration_seconds, "columns": list(run.columns),
        "eye_artifact_id": eye_artifact.artifact_id, "eye_content_hash": eye_artifact.provenance.content_hash,
        "independent_observation": True, "incompatible_alignment_rejected": rejection,
    }
    Path(__file__).with_name("openneuro_eye_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("provide eye-tracking TSV and matching physio JSON sidecar")
    main(sys.argv[1], sys.argv[2])

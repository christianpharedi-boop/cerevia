"""CEREVIA V0.7 eye-tracking observation and three-stream relationships."""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from cerevia.core.hashing import thaw
from cerevia.core.provenance import Artifact
from cerevia.study.ontology import Channel, Modality, Recording


@dataclass(frozen=True)
class EyeTrackingRun:
    data_path: Path
    sidecar_path: Path
    participant_id: str
    session_id: str
    task: str
    recording: str
    sampling_frequency_hz: float
    columns: tuple[str, ...]
    duration_seconds: float
    sample_count: int
    source_sha256: str

    @property
    def recording_id(self) -> str:
        label = f"-recording-{self.recording}" if self.recording else ""
        return f"eye-{self.participant_id.removeprefix('sub-')}-{self.task}{label}"

    def to_recording(self) -> Recording:
        channels = tuple(Channel(f"eye-{name.lower().replace('_', '-')}", name, "eye_tracking", "pixel") for name in self.columns if name != "time")
        return Recording(self.recording_id, self.session_id, Modality.EYE_TRACKING, channels,
                         self.sampling_frequency_hz, self.task, "", self.data_path.suffix.lstrip("."),
                         self.participant_id, self.duration_seconds)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8-sig", newline="") if path.name.endswith(".gz") else path.open("r", encoding="utf-8-sig", newline="")


def load_eye_tracking_run(data_path: str | Path, sidecar_path: str | Path, participant_id: str,
                          session_id: str, task: str, recording: str = "eye1") -> EyeTrackingRun:
    data = Path(data_path)
    sidecar = Path(sidecar_path)
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    if metadata.get("PhysioType") != "eyetrack":
        raise ValueError("eye-tracking sidecar must declare PhysioType=eyetrack")
    frequency = float(metadata.get("SamplingFrequency", 0.0))
    if not np.isfinite(frequency) or frequency <= 0:
        raise ValueError("eye-tracking SamplingFrequency must be finite and positive")
    columns = tuple(metadata.get("Columns", ()))
    if "time" not in columns or len(columns) < 2:
        raise ValueError("eye-tracking sidecar must define time and at least one signal column")
    if not data.exists():
        raise FileNotFoundError(data)
    previous = None
    count = 0
    last = 0.0
    with _open_text(data) as handle:
        for line_number, line in enumerate(handle, 1):
            values = line.rstrip("\n\r").split("\t")
            if len(values) != len(columns):
                raise ValueError(f"eye-tracking row {line_number} has {len(values)} columns, expected {len(columns)}")
            timestamp = float(values[0])
            if not np.isfinite(timestamp) or (previous is not None and timestamp < previous):
                raise ValueError("eye-tracking time column must be finite and monotonic")
            for value in values[1:]:
                parsed = float(value)
                if not np.isfinite(parsed):
                    raise ValueError("eye-tracking signal values must be finite")
            previous, last = timestamp, timestamp
            count += 1
    if count < 2:
        raise ValueError("eye-tracking stream must contain at least two samples")
    expected_duration = (count - 1) / frequency
    if abs(last - expected_duration) > max(1.0 / frequency, 0.005):
        raise ValueError("eye-tracking timestamps are inconsistent with SamplingFrequency")
    return EyeTrackingRun(data, sidecar, participant_id, session_id, task, recording,
                          frequency, columns, last, count, _sha256(data))


def ingest_eye_tracking(artifact_id: str, run: EyeTrackingRun, study_id: str) -> Artifact:
    payload = {
        "sample_count": run.sample_count,
        "sampling_frequency_hz": run.sampling_frequency_hz,
        "duration_seconds": run.duration_seconds,
        "columns": list(run.columns),
        "source_sha256": run.source_sha256,
    }
    metadata = {
        "study_id": study_id, "participant_id": run.participant_id, "session_id": run.session_id,
        "task": run.task, "recording_id": run.recording_id, "modality": Modality.EYE_TRACKING.value,
        "source_path": str(run.data_path), "source_sha256": run.source_sha256,
        "sidecar_path": str(run.sidecar_path), "independent_observation": True,
    }
    return Artifact.derive(artifact_id, "eye_tracking", payload, metadata,
                           "ingest_eye_tracking", parameters={"sampling_frequency_hz": run.sampling_frequency_hz,
                                                               "columns": list(run.columns)})


def align_eeg_eye(artifact_id: str, eeg_recording: Recording, eye_recording: Recording,
                  eeg_artifact: Artifact, eye_artifact: Artifact, tolerance_seconds: float = 0.020) -> Artifact:
    if eeg_artifact.kind != "raw_eeg" or eye_artifact.kind != "eye_tracking":
        raise ValueError("EEG-eye alignment requires raw_eeg and eye_tracking observations")
    if tolerance_seconds < 0 or not np.isfinite(tolerance_seconds):
        raise ValueError("alignment tolerance must be finite and non-negative")
    fields = ("participant_id", "session_id", "task")
    mismatches = {field: (getattr(eeg_recording, field), getattr(eye_recording, field)) for field in fields
                  if getattr(eeg_recording, field) != getattr(eye_recording, field)}
    if mismatches:
        raise ValueError(f"EEG and eye-tracking context mismatch: {mismatches}")
    overlap = min(eeg_recording.duration_seconds or 0.0, eye_recording.duration_seconds or 0.0)
    if overlap <= 0:
        raise ValueError("EEG-eye alignment requires a positive common recording interval")
    payload = {
        "modality_a": "EEG", "modality_b": "eye_tracking", "eeg_recording_id": eeg_recording.recording_id,
        "eye_recording_id": eye_recording.recording_id, "timebase": "recording_seconds",
        "tolerance_seconds": tolerance_seconds, "overlap_duration_seconds": overlap,
        "semantics": "validated_shared_context_and_common_recording_timebase",
    }
    metadata = {
        "participant_id": eeg_recording.participant_id, "session_id": eeg_recording.session_id,
        "task": eeg_recording.task, "modalities": ["EEG", "eye_tracking"],
        "associated_artifact_ids": [eeg_artifact.artifact_id, eye_artifact.artifact_id],
        "eeg_content_hash": eeg_artifact.provenance.content_hash,
        "eye_content_hash": eye_artifact.provenance.content_hash,
    }
    return Artifact.derive(artifact_id, "cross_modal_alignment", payload, metadata, "align_eeg_eye",
                           parents=(eeg_artifact, eye_artifact),
                           parameters={"tolerance_seconds": tolerance_seconds, "timebase": "recording_seconds"})


def three_stream_inference(artifact_id: str, eeg_feature: Artifact, behavioral_artifact: Artifact,
                           eye_artifact: Artifact, eeg_behavior_alignment: Artifact,
                           eeg_eye_alignment: Artifact, statement: str) -> Artifact:
    required = ("spectral_power", "behavioral_events", "eye_tracking", "cross_modal_alignment", "cross_modal_alignment")
    actual = (eeg_feature.kind, behavioral_artifact.kind, eye_artifact.kind,
              eeg_behavior_alignment.kind, eeg_eye_alignment.kind)
    if actual != required:
        raise ValueError(f"three-stream inference requires {required}, received {actual}")
    eeg_values = np.asarray(thaw(eeg_feature.payload), dtype=float)
    result = {
        "statement": statement, "status": "PROVISIONAL", "observations": ["EEG", "behavioral", "eye_tracking"],
        "inference_type": "three_stream_observation_integration",
        "mean_eeg_feature": float(eeg_values.mean()),
        "eeg_behavior_alignment_id": eeg_behavior_alignment.artifact_id,
        "eeg_eye_alignment_id": eeg_eye_alignment.artifact_id,
        "claim_policy": "multimodal_computation_does_not_auto_convert_to_truth",
    }
    return Artifact.derive(artifact_id, "multimodal_inference", result,
                           {"status": "PROVISIONAL", "modalities": ["EEG", "behavioral", "eye_tracking"],
                            "associated_artifact_ids": [eeg_feature.artifact_id, behavioral_artifact.artifact_id,
                                                         eye_artifact.artifact_id, eeg_behavior_alignment.artifact_id,
                                                         eeg_eye_alignment.artifact_id],
                            "independent_observations": [eeg_artifact_id(eeg_feature), behavioral_artifact.artifact_id,
                                                          eye_artifact.artifact_id]},
                           "three_stream_inference",
                           parents=(eeg_feature, behavioral_artifact, eye_artifact,
                                    eeg_behavior_alignment, eeg_eye_alignment),
                           parameters={"method": "declared_three_stream_integration"})


def eeg_artifact_id(feature_artifact: Artifact) -> str:
    parents = thaw(feature_artifact.metadata).get("eeg_parent_artifact_id")
    return parents or feature_artifact.artifact_id

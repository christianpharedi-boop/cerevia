"""Minimal EEG observation model for CEREVIA V0.1.2."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import math
import re
import numpy as np
from cerevia.core.provenance import Artifact
from cerevia.study.ontology import Recording


@dataclass(frozen=True)
class EEGObservation:
    data: tuple[tuple[float, ...], ...]
    sampling_rate_hz: float
    channel_names: tuple[str, ...]
    events: tuple[tuple[int, str], ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "data": [list(row) for row in self.data],
            "sampling_rate_hz": self.sampling_rate_hz,
            "channel_names": list(self.channel_names),
            "events": [list(event) for event in self.events],
        }

    @classmethod
    def from_array(cls, data: np.ndarray, sampling_rate_hz: float,
                   channel_names: tuple[str, ...], events: tuple[tuple[int, str], ...] = ()) -> "EEGObservation":
        array = np.asarray(data, dtype=float)
        if array.ndim != 2:
            raise ValueError("EEG data must be channels x samples")
        if array.shape[0] != len(channel_names):
            raise ValueError("channel_names must match channel count")
        return cls(tuple(tuple(float(x) for x in row) for row in array), float(sampling_rate_hz), tuple(channel_names), tuple(events))

    def array(self) -> np.ndarray:
        return np.asarray(self.data, dtype=float)


def validate_observation_metadata(observation: EEGObservation, study_id: str, participant_id: str, session_id: str) -> None:
    errors: list[str] = []
    if not study_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", study_id):
        errors.append("study_id must be a non-empty identifier")
    if not re.fullmatch(r"sub-[A-Za-z0-9][A-Za-z0-9._-]*", participant_id):
        errors.append("participant_id must be an immutable pseudonymous identifier such as sub-001")
    if not re.fullmatch(r"ses-[A-Za-z0-9][A-Za-z0-9._-]*", session_id):
        errors.append("session_id must be an identifier such as ses-01")
    if not math.isfinite(observation.sampling_rate_hz) or observation.sampling_rate_hz <= 0:
        errors.append("sampling_rate_hz must be finite and positive")
    if not observation.channel_names or any(not name.strip() for name in observation.channel_names):
        errors.append("channel_names must contain non-empty names")
    if len(set(observation.channel_names)) != len(observation.channel_names):
        errors.append("channel_names must be unique")
    if errors:
        raise ValueError("invalid EEG metadata: " + "; ".join(errors))


def ingest_eeg(artifact_id: str, observation: EEGObservation, study_id: str, participant_id: str, session_id: str,
               recording: Recording | None = None) -> Artifact:
    validate_observation_metadata(observation, study_id, participant_id, session_id)
    if recording is not None:
        if recording.session_id != session_id or recording.modality.value != "EEG":
            raise ValueError("EEG recording context must reference the same session and EEG modality")
        if recording.sampling_rate_hz is not None and recording.sampling_rate_hz != observation.sampling_rate_hz:
            raise ValueError("recording and observation sampling rates must match")
        if tuple(channel.name for channel in recording.channels) != observation.channel_names:
            raise ValueError("recording channel names must match the observation")
    metadata = {"study_id": study_id, "participant_id": participant_id, "session_id": session_id,
                "immutable": True, "sampling_rate_hz": observation.sampling_rate_hz,
                "channel_names": list(observation.channel_names)}
    if recording is not None:
        metadata.update({"recording_id": recording.recording_id, "modality": recording.modality.value,
                         "task": recording.task, "condition": recording.condition})
    return Artifact.derive(artifact_id, "raw_eeg", observation.as_payload(), metadata,
                           "ingest_eeg", parameters={"source_type": "EEGObservation", "ontology_bound": recording is not None})

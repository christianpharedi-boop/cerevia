"""Minimal EEG observation model for CEREVIA V0.1."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
from cerevia.core.provenance import Artifact


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
        return cls(tuple(tuple(float(x) for x in row) for row in array), float(sampling_rate_hz), channel_names, events)

    def array(self) -> np.ndarray:
        return np.asarray(self.data, dtype=float)


def ingest_eeg(artifact_id: str, observation: EEGObservation, study_id: str, participant_id: str, session_id: str) -> Artifact:
    if not participant_id.startswith("sub-"):
        raise ValueError("participant_id must be an immutable pseudonymous identifier such as sub-001")
    return Artifact.derive(
        artifact_id, "raw_eeg", observation.as_payload(),
        {"study_id": study_id, "participant_id": participant_id, "session_id": session_id,
         "immutable": True, "sampling_rate_hz": observation.sampling_rate_hz,
         "channel_names": list(observation.channel_names)},
        "ingest_eeg", parameters={"source_type": "EEGObservation"})

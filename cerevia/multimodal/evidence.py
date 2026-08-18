"""CEREVIA V0.6 EEG plus behavioral-event evidence."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pyedflib

from cerevia.core.provenance import Artifact
from cerevia.core.hashing import thaw
from cerevia.study.ontology import Recording


@dataclass(frozen=True)
class BehavioralEvent:
    event_id: str
    participant_id: str
    session_id: str
    task: str
    label: str
    onset_seconds: float
    duration_seconds: float = 0.0
    condition: str = ""
    value: str = ""

    def __post_init__(self) -> None:
        if not self.event_id or not self.participant_id.startswith("sub-") or not self.session_id.startswith("ses-"):
            raise ValueError("behavioral event requires stable participant/session identifiers")
        if not self.task.strip() or not self.label.strip():
            raise ValueError("behavioral event task and label must be non-empty")
        if not np.isfinite(self.onset_seconds) or self.onset_seconds < 0:
            raise ValueError("behavioral event onset must be finite and non-negative")
        if not np.isfinite(self.duration_seconds) or self.duration_seconds < 0:
            raise ValueError("behavioral event duration must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CrossModalAlignment:
    alignment_id: str
    participant_id: str
    session_id: str
    task: str
    eeg_recording_id: str
    behavioral_artifact_id: str
    matched_event_ids: tuple[str, ...]
    tolerance_seconds: float
    timebase: str = "recording_seconds"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_edf_behavioral_events(path: str | Path, participant_id: str, session_id: str, task: str) -> tuple[BehavioralEvent, ...]:
    """Extract non-technical EDF annotations as behavioral events."""
    reader = pyedflib.EdfReader(str(path))
    try:
        onsets, durations, labels = reader.readAnnotations()
    finally:
        reader.close()
    return tuple(
        BehavioralEvent(
            event_id=f"beh-{index:04d}", participant_id=participant_id, session_id=session_id, task=task,
            label=str(label), onset_seconds=float(onset), duration_seconds=float(duration),
            condition={"OVTK_GDF_Right": "MI", "OVTK_GDF_Tongue": "Rest"}.get(str(label), ""),
        )
        for index, (onset, duration, label) in enumerate(zip(onsets, durations, labels), 1)
        if str(label) not in {"OVTK_StimulationId_ExperimentStart", "OVTK_StimulationId_ExperimentStop"}
    )


def ingest_behavioral_events(artifact_id: str, events: Iterable[BehavioralEvent], study_id: str,
                             source_path: str | Path | None = None) -> Artifact:
    event_tuple = tuple(events)
    if not event_tuple:
        raise ValueError("behavioral evidence requires at least one event")
    ids = {event.event_id for event in event_tuple}
    if len(ids) != len(event_tuple):
        raise ValueError("behavioral event IDs must be unique")
    context = {(event.participant_id, event.session_id, event.task) for event in event_tuple}
    if len(context) != 1:
        raise ValueError("behavioral events must share participant, session, and task context")
    metadata: dict[str, Any] = {"study_id": study_id, "participant_id": event_tuple[0].participant_id,
                                "session_id": event_tuple[0].session_id, "task": event_tuple[0].task,
                                "modality": "behavioral", "event_count": len(event_tuple), "immutable": True}
    if source_path is not None:
        source = Path(source_path)
        metadata.update({"source_path": str(source), "source_sha256": _sha256(source)})
    return Artifact.derive(artifact_id, "behavioral_events", {"events": [event.to_dict() for event in event_tuple]},
                           metadata, "ingest_behavioral_events", parameters={"event_count": len(event_tuple)})


def align_behavioral_events(artifact_id: str, recording: Recording, behavioral_artifact: Artifact,
                            tolerance_seconds: float = 0.020) -> tuple[Artifact, CrossModalAlignment]:
    if behavioral_artifact.kind != "behavioral_events":
        raise ValueError("alignment requires behavioral_events artifact")
    if tolerance_seconds < 0 or not np.isfinite(tolerance_seconds):
        raise ValueError("alignment tolerance must be finite and non-negative")
    metadata = thaw(behavioral_artifact.metadata)
    if metadata.get("session_id") != recording.session_id:
        raise ValueError("EEG and behavioral evidence must share session context")
    events = tuple(thaw(behavioral_artifact.payload)["events"])
    if not events:
        raise ValueError("behavioral artifact contains no events")
    matched = tuple(event["event_id"] for event in events if event["onset_seconds"] >= 0)
    alignment = CrossModalAlignment(artifact_id, metadata["participant_id"], recording.session_id,
                                    metadata["task"], recording.recording_id, behavioral_artifact.artifact_id,
                                    matched, tolerance_seconds)
    artifact = Artifact.derive(artifact_id, "cross_modal_alignment", alignment.to_dict(),
                               {"participant_id": alignment.participant_id, "session_id": alignment.session_id,
                                "task": alignment.task, "modalities": ["EEG", "behavioral"],
                                "behavioral_artifact_id": behavioral_artifact.artifact_id,
                                "recording_id": recording.recording_id, "matched_event_count": len(matched)},
                               "align_eeg_behavioral", parents=(behavioral_artifact,),
                               parameters={"tolerance_seconds": tolerance_seconds, "timebase": alignment.timebase})
    return artifact, alignment


def multimodal_analysis(artifact_id: str, eeg_feature: Artifact, behavioral_artifact: Artifact,
                        alignment_artifact: Artifact, statement: str) -> Artifact:
    if eeg_feature.kind != "spectral_power" or behavioral_artifact.kind != "behavioral_events" \
            or alignment_artifact.kind != "cross_modal_alignment":
        raise ValueError("multimodal analysis requires spectral power, behavioral events, and alignment artifacts")
    events = thaw(behavioral_artifact.payload)["events"]
    labels = [event["label"] for event in events]
    counts = {label: labels.count(label) for label in sorted(set(labels))}
    eeg_values = np.asarray(thaw(eeg_feature.payload), dtype=float)
    alignment = thaw(alignment_artifact.payload)
    result = {
        "statement": statement, "status": "PROVISIONAL", "modalities": ["EEG", "behavioral"],
        "eeg_feature_id": eeg_feature.artifact_id, "behavioral_artifact_id": behavioral_artifact.artifact_id,
        "alignment_artifact_id": alignment_artifact.artifact_id,
        "matched_event_count": len(alignment["matched_event_ids"]), "behavioral_label_counts": counts,
        "mean_eeg_feature": float(eeg_values.mean()), "event_timebase": alignment["timebase"],
        "claim_policy": "multimodal_computation_does_not_auto_convert_to_truth",
    }
    return Artifact.derive(artifact_id, "multimodal_analysis", result,
                           {"status": "PROVISIONAL", "modalities": ["EEG", "behavioral"],
                            "participant_id": thaw(behavioral_artifact.metadata)["participant_id"],
                            "session_id": thaw(behavioral_artifact.metadata)["session_id"],
                            "task": thaw(behavioral_artifact.metadata)["task"],
                            "associated_artifact_ids": [eeg_feature.artifact_id, behavioral_artifact.artifact_id,
                                                         alignment_artifact.artifact_id]},
                           "multimodal_analysis", parents=(eeg_feature, behavioral_artifact, alignment_artifact),
                           parameters={"method": "mean_eeg_feature_by_aligned_behavioral_events"})

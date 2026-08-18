"""CEREVIA V0.2 neuroscience ontology.

This module is a domain layer. It does not replace the V0.1.2 evidence core;
it supplies structured experimental context that can be bound to evidence artifacts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
import math
import re
from typing import Any


_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SUBJECT_ID = re.compile(r"sub-[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_SESSION_ID = re.compile(r"ses-[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def _require_id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{label} must be a non-empty stable identifier")
    return value


class Modality(StrEnum):
    EEG = "EEG"
    MEG = "MEG"
    FMRI = "fMRI"
    ECOG = "ECoG"
    EMG = "EMG"
    ECG = "ECG"
    EOG = "EOG"
    EYE_TRACKING = "eye_tracking"
    BEHAVIORAL = "behavioral"


@dataclass(frozen=True)
class Study:
    study_id: str
    title: str
    description: str = ""
    protocol_version: str = "0.2"

    def __post_init__(self) -> None:
        _require_id(self.study_id, "study_id")
        if not self.title.strip():
            raise ValueError("study title must be non-empty")


@dataclass(frozen=True)
class Participant:
    participant_id: str
    study_id: str
    pseudonymized: bool = True

    def __post_init__(self) -> None:
        if not _SUBJECT_ID.fullmatch(self.participant_id):
            raise ValueError("participant_id must be pseudonymous, for example sub-001")
        _require_id(self.study_id, "study_id")
        if not self.pseudonymized:
            raise ValueError("CEREVIA requires pseudonymized participant identifiers")


@dataclass(frozen=True)
class Session:
    session_id: str
    study_id: str
    participant_id: str
    task: str
    condition: str
    visit_label: str = ""

    def __post_init__(self) -> None:
        if not _SESSION_ID.fullmatch(self.session_id):
            raise ValueError("session_id must be an identifier such as ses-01")
        _require_id(self.study_id, "study_id")
        if not _SUBJECT_ID.fullmatch(self.participant_id):
            raise ValueError("participant_id must be pseudonymous")
        if not self.task.strip() or not self.condition.strip():
            raise ValueError("session task and condition must be non-empty")


@dataclass(frozen=True)
class Channel:
    channel_id: str
    name: str
    channel_type: str = "signal"
    unit: str = "arbitrary"
    reference: str = "unknown"

    def __post_init__(self) -> None:
        _require_id(self.channel_id, "channel_id")
        if not self.name.strip():
            raise ValueError("channel name must be non-empty")


@dataclass(frozen=True)
class Recording:
    recording_id: str
    session_id: str
    modality: Modality
    channels: tuple[Channel, ...]
    sampling_rate_hz: float | None = None
    task: str = ""
    condition: str = ""
    source_format: str = ""

    def __post_init__(self) -> None:
        _require_id(self.recording_id, "recording_id")
        if not _SESSION_ID.fullmatch(self.session_id):
            raise ValueError("recording session_id must be an identifier such as ses-01")
        if not self.channels:
            raise ValueError("recording must define at least one channel")
        if len({channel.channel_id for channel in self.channels}) != len(self.channels):
            raise ValueError("recording channel IDs must be unique")
        if self.sampling_rate_hz is not None and (not math.isfinite(self.sampling_rate_hz) or self.sampling_rate_hz <= 0):
            raise ValueError("sampling_rate_hz must be finite and positive")


@dataclass(frozen=True)
class Event:
    event_id: str
    recording_id: str
    onset_sample: int
    label: str
    duration_samples: int = 0
    value: str = ""

    def __post_init__(self) -> None:
        _require_id(self.event_id, "event_id")
        _require_id(self.recording_id, "recording_id")
        if self.onset_sample < 0 or self.duration_samples < 0:
            raise ValueError("event sample positions and duration must be non-negative")
        if not self.label.strip():
            raise ValueError("event label must be non-empty")


@dataclass(frozen=True)
class Epoch:
    epoch_id: str
    recording_id: str
    start_sample: int
    end_sample: int
    event_id: str | None = None
    condition: str = ""

    def __post_init__(self) -> None:
        _require_id(self.epoch_id, "epoch_id")
        _require_id(self.recording_id, "recording_id")
        if self.start_sample < 0 or self.end_sample <= self.start_sample:
            raise ValueError("epoch must have a positive interval")


@dataclass(frozen=True)
class Feature:
    feature_id: str
    artifact_id: str
    recording_id: str
    name: str
    epoch_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_id(self.feature_id, "feature_id")
        _require_id(self.artifact_id, "artifact_id")
        _require_id(self.recording_id, "recording_id")
        if not self.name.strip():
            raise ValueError("feature name must be non-empty")


@dataclass(frozen=True)
class Analysis:
    analysis_id: str
    artifact_id: str
    feature_ids: tuple[str, ...]
    method: str
    task: str
    condition: str

    def __post_init__(self) -> None:
        _require_id(self.analysis_id, "analysis_id")
        _require_id(self.artifact_id, "artifact_id")
        if not self.feature_ids or not self.method.strip():
            raise ValueError("analysis requires features and a method")
        if not self.task.strip() or not self.condition.strip():
            raise ValueError("analysis must retain experimental task and condition")


@dataclass(frozen=True)
class Finding:
    finding_id: str
    artifact_id: str
    analysis_id: str
    statement: str
    status: str = "PROVISIONAL"

    def __post_init__(self) -> None:
        _require_id(self.finding_id, "finding_id")
        _require_id(self.artifact_id, "artifact_id")
        _require_id(self.analysis_id, "analysis_id")
        if not self.statement.strip():
            raise ValueError("finding statement must be non-empty")
        if self.status not in {"PROVISIONAL", "SUPPORTED", "REJECTED", "REPRODUCED", "SUPERSEDED"}:
            raise ValueError("unsupported finding status")


@dataclass
class NeuroscienceOntology:
    studies: dict[str, Study] = field(default_factory=dict)
    participants: dict[str, Participant] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    recordings: dict[str, Recording] = field(default_factory=dict)
    events: dict[str, Event] = field(default_factory=dict)
    epochs: dict[str, Epoch] = field(default_factory=dict)
    features: dict[str, Feature] = field(default_factory=dict)
    analyses: dict[str, Analysis] = field(default_factory=dict)
    findings: dict[str, Finding] = field(default_factory=dict)

    def _add(self, collection: dict[str, Any], key: str, value: Any) -> Any:
        if key in collection:
            raise ValueError(f"ontology entity already exists and is immutable: {key}")
        collection[key] = value
        return value

    def add_study(self, study: Study) -> Study:
        return self._add(self.studies, study.study_id, study)

    def add_participant(self, participant: Participant) -> Participant:
        if participant.study_id not in self.studies:
            raise ValueError("participant must reference a registered study")
        return self._add(self.participants, participant.participant_id, participant)

    def add_session(self, session: Session) -> Session:
        if session.study_id not in self.studies or session.participant_id not in self.participants:
            raise ValueError("session must reference registered study and participant")
        return self._add(self.sessions, session.session_id, session)

    def add_recording(self, recording: Recording) -> Recording:
        if recording.session_id not in self.sessions:
            raise ValueError("recording must reference a registered session")
        return self._add(self.recordings, recording.recording_id, recording)

    def add_event(self, event: Event) -> Event:
        if event.recording_id not in self.recordings:
            raise ValueError("event must reference a registered recording")
        return self._add(self.events, event.event_id, event)

    def add_epoch(self, epoch: Epoch) -> Epoch:
        if epoch.recording_id not in self.recordings:
            raise ValueError("epoch must reference a registered recording")
        if epoch.event_id is not None and epoch.event_id not in self.events:
            raise ValueError("epoch event_id must reference a registered event")
        return self._add(self.epochs, epoch.epoch_id, epoch)

    def add_feature(self, feature: Feature) -> Feature:
        if feature.recording_id not in self.recordings:
            raise ValueError("feature must reference a registered recording")
        if any(epoch_id not in self.epochs for epoch_id in feature.epoch_ids):
            raise ValueError("feature references an unregistered epoch")
        return self._add(self.features, feature.feature_id, feature)

    def add_analysis(self, analysis: Analysis) -> Analysis:
        if any(feature_id not in self.features for feature_id in analysis.feature_ids):
            raise ValueError("analysis references an unregistered feature")
        return self._add(self.analyses, analysis.analysis_id, analysis)

    def add_finding(self, finding: Finding) -> Finding:
        if finding.analysis_id not in self.analyses:
            raise ValueError("finding must reference a registered ontology analysis")
        return self._add(self.findings, finding.finding_id, finding)

    def context_for_recording(self, recording_id: str) -> dict[str, Any]:
        recording = self.recordings[recording_id]
        session = self.sessions[recording.session_id]
        participant = self.participants[session.participant_id]
        study = self.studies[session.study_id]
        return {
            "study_id": study.study_id,
            "participant_id": participant.participant_id,
            "session_id": session.session_id,
            "recording_id": recording.recording_id,
            "modality": recording.modality.value,
            "task": session.task,
            "condition": session.condition,
            "channel_ids": [channel.channel_id for channel in recording.channels],
        }

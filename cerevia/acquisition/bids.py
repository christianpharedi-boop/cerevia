"""BIDS EEG interoperability adapter for CEREVIA V0.3."""
from __future__ import annotations
from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import pyedflib

from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.core.provenance import Artifact
from cerevia.study.ontology import Channel, Event, Modality, NeuroscienceOntology, Recording

_BIDS_EEG = re.compile(
    r"^sub-(?P<participant>[A-Za-z0-9]+)(?:_ses-(?P<session>[A-Za-z0-9]+))?_task-(?P<task>[A-Za-z0-9]+)"
    r"(?:_acq-(?P<acq>[A-Za-z0-9]+))?(?:_run-(?P<run>[0-9]+))?_eeg\.(?P<extension>edf|bdf|set)$"
)


@dataclass(frozen=True)
class BIDSRun:
    dataset_root: Path
    data_path: Path
    dataset_description: dict[str, Any]
    sidecar: dict[str, Any]
    channels: tuple[dict[str, str], ...]
    events: tuple[dict[str, str], ...]
    participant_id: str
    session_id: str
    task: str
    run: str | None

    @property
    def dataset_id(self) -> str:
        return self.dataset_description.get("DatasetDOI", self.dataset_root.name)

    @property
    def source_sha256(self) -> str:
        digest = hashlib.sha256()
        with self.data_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def to_recording(self) -> Recording:
        channel_objects = tuple(
            Channel(f"ch-{index:03d}", row["name"], row.get("type", "signal"), row.get("units", "arbitrary"))
            for index, row in enumerate(self.channels, 1)
        )
        return Recording(
            recording_id=self.recording_id,
            session_id=self.session_id,
            modality=Modality.EEG,
            channels=channel_objects,
            sampling_rate_hz=float(self.sidecar["SamplingFrequency"]),
            task=self.task,
            condition=self.task,
            source_format=self.data_path.suffix.lstrip("."),
            participant_id=self.participant_id,
            duration_seconds=self.duration_seconds,
        )

    @property
    def recording_id(self) -> str:
        run = f"-run-{self.run}" if self.run else ""
        return f"rec-{self.participant_id.removeprefix('sub-')}-{self.task}{run}"

    @property
    def duration_seconds(self) -> float:
        if self.data_path.suffix.lower() not in {".edf", ".bdf"}:
            raise ValueError("recording duration requires EDF/BDF signal support")
        reader = pyedflib.EdfReader(str(self.data_path))
        try:
            return float(reader.file_duration)
        finally:
            reader.close()

    def to_observation(self) -> EEGObservation:
        if self.data_path.suffix.lower() not in {".edf", ".bdf"}:
            raise ValueError("V0.3 currently supports signal reads for EDF and BDF; SET requires a future adapter")
        reader = pyedflib.EdfReader(str(self.data_path))
        try:
            labels = tuple(reader.getLabel(index).strip() for index in range(reader.signals_in_file))
            samples = [reader.readSignal(index).tolist() for index in range(reader.signals_in_file)]
            lengths = {len(row) for row in samples}
            if len(lengths) != 1:
                raise ValueError("BIDS EEG channels have unequal sample counts")
            sampling_rate = float(reader.getSampleFrequency(0))
            return EEGObservation.from_array(samples, sampling_rate, labels)
        finally:
            reader.close()

    def ontology_events(self) -> tuple[Event, ...]:
        result: list[Event] = []
        sampling_rate = float(self.sidecar["SamplingFrequency"])
        for index, row in enumerate(self.events, 1):
            onset = float(row["onset"])
            if onset < 0:
                continue
            result.append(Event(f"event-{index:04d}", self.recording_id, round(onset * sampling_rate),
                                row.get("trial_type", row.get("event", "event")), value=row.get("value", "")))
        return tuple(result)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_tsv(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle, delimiter="\t"))


def load_bids_eeg_run(data_path: str | Path) -> BIDSRun:
    data_path = Path(data_path).resolve()
    match = _BIDS_EEG.match(data_path.name)
    if not match:
        raise ValueError(f"not a supported BIDS EEG filename: {data_path.name}")
    dataset_root = data_path
    while dataset_root != dataset_root.parent and not (dataset_root / "dataset_description.json").exists():
        dataset_root = dataset_root.parent
    if not (dataset_root / "dataset_description.json").exists():
        raise ValueError("BIDS dataset_description.json not found")
    description = _read_json(dataset_root / "dataset_description.json")
    sidecar_path = data_path.with_name(data_path.name.replace("_eeg." + match.group("extension"), "_eeg.json"))
    channels_path = data_path.with_name(data_path.name.replace("_eeg." + match.group("extension"), "_channels.tsv"))
    events_path = data_path.with_name(data_path.name.replace("_eeg." + match.group("extension"), "_events.tsv"))
    if not events_path.exists():
        events_path = dataset_root / f"task-{match.group('task')}_events.tsv"
    if not sidecar_path.exists() or not channels_path.exists():
        raise ValueError("BIDS EEG run requires matching _eeg.json and _channels.tsv files")
    sidecar = _read_json(sidecar_path)
    required = {"EEGReference", "SamplingFrequency", "EEGChannelCount", "RecordingType"}
    missing = sorted(required - set(sidecar))
    if missing:
        raise ValueError(f"BIDS EEG sidecar missing required fields: {missing}")
    channels = _read_tsv(channels_path)
    if len(channels) != int(sidecar["EEGChannelCount"]):
        raise ValueError("BIDS EEGChannelCount does not match channels.tsv")
    if not {"name", "type", "units"}.issubset(channels[0] if channels else set()):
        raise ValueError("channels.tsv must define name, type, and units")
    return BIDSRun(dataset_root, data_path, description, sidecar, channels, _read_tsv(events_path),
                   f"sub-{match.group('participant')}", f"ses-{match.group('session') or '01'}",
                   match.group("task"), match.group("run"))


def ingest_bids_eeg(run: BIDSRun, ontology: NeuroscienceOntology) -> tuple[Artifact, Recording]:
    recording = run.to_recording()
    session = ontology.sessions.get(run.session_id)
    if session is None:
        raise ValueError(f"ontology session is not registered: {run.session_id}")
    if session.participant_id != run.participant_id or session.task != run.task:
        raise ValueError("BIDS run does not match ontology participant or task context")
    observation = run.to_observation()
    artifact = ingest_eeg(
        f"raw-{recording.recording_id}", observation, session.study_id, run.participant_id, run.session_id,
        recording=recording,
        metadata_extra={"bids_dataset_id": run.dataset_id, "bids_source_sha256": run.source_sha256,
                        "bids_version": run.dataset_description.get("BIDSVersion"),
                        "source_path": str(run.data_path.relative_to(run.dataset_root))},
    )
    return artifact, recording

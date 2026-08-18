"""Ingest one real OpenNeuro BIDS EEG run.

Usage:
  PYTHONPATH=. python3 examples/bids_eeg/ingest_openneuro.py /home/ubuntu/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.acquisition.bids import ingest_bids_eeg, load_bids_eeg_run
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.pipeline import evidence_manifest, verify_manifest
from cerevia.study.ontology import NeuroscienceOntology, Participant, Session, Study


def main(path: str) -> None:
    run = load_bids_eeg_run(path)
    ontology = NeuroscienceOntology()
    ontology.add_study(Study("ds003810", run.dataset_description["Name"], "OpenNeuro BIDS EEG interoperability proof"))
    ontology.add_participant(Participant(run.participant_id, "ds003810"))
    ontology.add_session(Session(run.session_id, "ds003810", run.participant_id, run.task, run.task))
    for event in run.ontology_events():
        # Events are registered after the recording is known below.
        pass
    artifact, recording = ingest_bids_eeg(run, ontology)
    ontology.add_recording(recording)
    for event in run.ontology_events():
        ontology.add_event(event)
    catalog = ArtifactCatalog()
    catalog.add(artifact)
    manifest = evidence_manifest("ds003810", artifact, catalog)
    output = {
        "dataset_id": run.dataset_id,
        "source": str(run.data_path),
        "source_sha256": run.source_sha256,
        "participant_id": run.participant_id,
        "session_id": run.session_id,
        "recording_id": recording.recording_id,
        "modality": recording.modality.value,
        "channels": len(recording.channels),
        "events": len(run.ontology_events()),
        "sampling_rate_hz": recording.sampling_rate_hz,
        "artifact_id": artifact.artifact_id,
        "manifest_verified": verify_manifest(manifest, catalog),
        "manifest_hash": manifest["manifest_hash"],
    }
    destination = Path(__file__).with_name("openneuro_ingest_result.json")
    destination.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide the path to a BIDS _eeg.edf file")
    main(sys.argv[1])

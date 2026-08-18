"""Run the V0.6 EEG plus behavioral-event proof on a real OpenNeuro EDF."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.acquisition.bids import ingest_bids_eeg, load_bids_eeg_run
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.graph.evidence import project_evidence_graph
from cerevia.multimodal.evidence import (
    align_behavioral_events, extract_edf_behavioral_events, ingest_behavioral_events, multimodal_analysis,
)
from cerevia.pipeline import evidence_manifest, filter_eeg, finding, qc_eeg, epoch_eeg, spectral_power, verify_manifest
from cerevia.study.ontology import Event, NeuroscienceOntology, Participant, Session, Study


def main(path: str) -> None:
    run = load_bids_eeg_run(path)
    ontology = NeuroscienceOntology()
    ontology.add_study(Study("ds003810", run.dataset_description["Name"], "V0.6 multimodal evidence proof"))
    ontology.add_participant(Participant(run.participant_id, "ds003810"))
    ontology.add_session(Session(run.session_id, "ds003810", run.participant_id, run.task, "MIvsRest"))
    raw, recording = ingest_bids_eeg(run, ontology)
    ontology.add_recording(recording)

    events = extract_edf_behavioral_events(path, run.participant_id, run.session_id, run.task)
    for index, event in enumerate(events[:20], 1):
        ontology.add_event(Event(f"event-{index:04d}", recording.recording_id,
                                 round(event.onset_seconds * recording.sampling_rate_hz), event.label,
                                 round(event.duration_seconds * recording.sampling_rate_hz), event.value))

    catalog = ArtifactCatalog()
    raw = catalog.add(raw)
    qc, report = qc_eeg(raw, "mm-qc-001")
    catalog.add(qc)
    if not report.passed:
        raise ValueError(f"QC failed: {report.errors}")
    filtered = catalog.add(filter_eeg(raw, "mm-filter-001", qc=qc))
    epochs = catalog.add(epoch_eeg(filtered, "mm-epoch-001"))
    feature = catalog.add(spectral_power(epochs, "mm-alpha-power-001"))
    behavioral = catalog.add(ingest_behavioral_events("behavioral-events-001", events, "ds003810", path))
    alignment, alignment_context = align_behavioral_events("alignment-001", recording, behavioral)
    catalog.add(alignment)
    multimodal = catalog.add(multimodal_analysis(
        "multimodal-analysis-001", feature, behavioral, alignment,
        "EEG alpha-band power is evaluated in the shared context of EDF behavioral events.",
    ))
    final = catalog.add(finding(
        multimodal, (raw, qc, filtered, epochs, feature, behavioral, alignment), "multimodal-finding-001",
        "The declared EEG feature and behavioral-event evidence produce a provisional multimodal result.", catalog=catalog,
    ))
    manifest = evidence_manifest("ds003810", final, catalog, ontology)
    graph = project_evidence_graph(catalog, ontology)
    result = {
        "dataset_id": run.dataset_id, "source_sha256": run.source_sha256,
        "recording_id": recording.recording_id, "behavioral_event_count": len(events),
        "matched_event_count": len(alignment_context.matched_event_ids),
        "modalities": ["EEG", "behavioral"], "multimodal_analysis_id": multimodal.artifact_id,
        "finding_id": final.artifact_id, "manifest_verified": verify_manifest(manifest, catalog),
        "manifest_hash": manifest["manifest_hash"], "evidence_graph_hash": graph.graph_hash,
        "graph_node_count": len(graph.nodes), "graph_edge_count": len(graph.edges),
        "findings_depending_on_behavioral": sorted(graph.findings_depending_on(behavioral.artifact_id)),
    }
    Path(__file__).with_name("multimodal_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide the path to a BIDS _eeg.edf file")
    main(sys.argv[1])

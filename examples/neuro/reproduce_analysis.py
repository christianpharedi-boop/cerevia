"""Execute and rerun a reproducible analysis on a real OpenNeuro BIDS EEG run."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.neuro.bids import ingest_bids_eeg, load_bids_eeg_run
from cerevia.analysis.reproducibility import AnalysisSpecification, execute_analysis, verify_rerun
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.graph.evidence import project_evidence_graph
from cerevia.study.ontology import NeuroscienceOntology, Participant, Session, Study


def main(path: str) -> None:
    run = load_bids_eeg_run(path)
    ontology = NeuroscienceOntology()
    ontology.add_study(Study("ds003810", run.dataset_description["Name"], "V0.4 reproducibility proof"))
    ontology.add_participant(Participant(run.participant_id, "ds003810"))
    ontology.add_session(Session(run.session_id, "ds003810", run.participant_id, run.task, run.task))
    raw, recording = ingest_bids_eeg(run, ontology)
    ontology.add_recording(recording)
    specification = AnalysisSpecification.for_eeg(raw)

    first_catalog = ArtifactCatalog()
    first_catalog.add(raw)
    first = execute_analysis(specification, first_catalog, "ds003810-reproducibility")

    second_catalog = ArtifactCatalog()
    second_catalog.add(raw)
    second = execute_analysis(specification, second_catalog, "ds003810-reproducibility")

    graph = project_evidence_graph(first_catalog)
    result = {
        "dataset_id": run.dataset_id,
        "source_sha256": run.source_sha256,
        "recording_id": recording.recording_id,
        "specification_hash": first.specification_hash,
        "first_final_content_hash": first.final_content_hash,
        "second_final_content_hash": second.final_content_hash,
        "rerun_identical": verify_rerun(first, second),
        "first_manifest_hash": first.manifest_hash,
        "second_manifest_hash": second.manifest_hash,
        "execution_identity": first.execution_identity,
        "output_artifact_ids": list(first.output_artifact_ids),
        "graph_hash": graph.graph_hash,
        "graph_node_count": len(graph.nodes),
        "graph_edge_count": len(graph.edges),
        "supported_evidence_node_count": len(graph.supports_finding(first.final_artifact_id)),
        "invalidation_node_count": len(graph.invalidate("raw-" + recording.recording_id)),
    }
    destination = Path(__file__).with_name("reproducibility_result.json")
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide the path to a BIDS _eeg.edf file")
    main(sys.argv[1])

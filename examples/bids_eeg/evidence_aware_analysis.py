"""Run V0.8 evidence-aware analysis on the real ds003810 EEG plus EDF events."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.acquisition.bids import load_bids_eeg_run, ingest_bids_eeg
from cerevia.analysis.evidence_aware import EvidenceAwareAnalysisSpecification, execute_evidence_aware_analysis
from cerevia.verification.bundle import build_bundle, write_bundle, verify_bundle
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.environment import fingerprint
from cerevia.multimodal.evidence import align_behavioral_events, extract_edf_behavioral_events, ingest_behavioral_events
from cerevia.pipeline import epoch_eeg, filter_eeg, qc_eeg, spectral_power, evidence_manifest
from cerevia.study.ontology import NeuroscienceOntology, Participant, Session, Study


def main(path: str) -> None:
    run = load_bids_eeg_run(path)
    ontology = NeuroscienceOntology()
    ontology.add_study(Study("ds003810", run.dataset_description["Name"], "V0.8 evidence-aware proof"))
    ontology.add_participant(Participant(run.participant_id, "ds003810"))
    ontology.add_session(Session(run.session_id, "ds003810", run.participant_id, run.task, "MIvsRest"))
    raw, recording = ingest_bids_eeg(run, ontology)
    catalog = ArtifactCatalog()
    raw = catalog.add(raw)
    qc, report = qc_eeg(raw, "aware-qc-001")
    catalog.add(qc)
    if not report.passed:
        raise ValueError(report.errors)
    filtered = catalog.add(filter_eeg(raw, "aware-filter-001", qc=qc))
    epochs = catalog.add(epoch_eeg(filtered, "aware-epoch-001"))
    feature = catalog.add(spectral_power(epochs, "aware-alpha-power-001"))
    events = extract_edf_behavioral_events(path, run.participant_id, run.session_id, run.task)
    behavior = catalog.add(ingest_behavioral_events("aware-behavior-001", events, "ds003810", path))
    alignment, _ = align_behavioral_events("aware-alignment-001", recording, behavior, raw)
    catalog.add(alignment)
    specification = EvidenceAwareAnalysisSpecification(
        input_artifacts=tuple({"artifact_id": artifact.artifact_id, "content_hash": artifact.provenance.content_hash}
                              for artifact in (raw, feature, behavior)),
        alignment_artifacts=({"artifact_id": alignment.artifact_id, "content_hash": alignment.provenance.content_hash},),
        hypothesis="The declared EEG alpha-band feature is evaluated in the same experimental context as the recorded behavioral events.",
        experimental_conditions={"dataset": run.dataset_id, "task": run.task, "participant": run.participant_id, "session": run.session_id},
        comparison={"left": "observed alpha-band feature", "right": "declared descriptive baseline", "null_value": 0.0},
        method="evidence_aware_descriptive_multimodal_inference",
        parameters={"band_hz": [8.0, 12.0], "event_timebase": "recording_seconds"},
        assumptions=("EEG and behavioral timestamps share recording seconds", "all source identifiers are pseudonymous", "the result is descriptive and not causal"),
        output_definitions={"mean_spectral_feature": {"type": "descriptive_mean", "unit": "arbitrary"}},
        uncertainty={"type": "not_estimated", "reason": "V0.8 declares uncertainty without overstating a confidence interval"},
        software_environment=fingerprint(),
        expected_outputs=("aware-analysis-001", "aware-inference-001", "aware-claim-001", "aware-finding-001"),
    )
    result = execute_evidence_aware_analysis(specification, catalog, "ds003810")
    manifest = evidence_manifest("ds003810", catalog.get(result.finding_artifact_id), catalog)
    bundle = build_bundle(manifest, specification.to_dict(), specification.specification_hash, catalog)
    bundle_path = Path(__file__).with_name("verification_bundle.json")
    write_bundle(bundle, bundle_path)
    verification = verify_bundle(bundle)
    output = {"dataset_id": run.dataset_id, "source_sha256": run.source_sha256, "behavioral_event_count": len(events),
              "specification_hash": result.specification_hash, "analysis_artifact_id": result.analysis_artifact_id,
              "inference_artifact_id": result.inference_artifact_id, "claim_artifact_id": result.claim_artifact_id,
              "finding_artifact_id": result.finding_artifact_id,
              "final_content_hash": result.final_content_hash, "manifest_hash": result.manifest_hash,
              "execution_identity": result.execution_identity, "bundle_path": str(bundle_path),
              "independent_verification": verification.to_dict(),
              "uncertainty": specification.to_dict()["uncertainty"]}
    Path(__file__).with_name("evidence_aware_result.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide a BIDS EEG EDF path")
    main(sys.argv[1])

"""Proteomics domain adapter for the CEREVIA V1.3 transplant proof.

The adapter understands protein-expression columns. Identity, lineage,
verification, claim qualification, attestation, revocation, and history remain
provided by the shared CEREVIA layers.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from cerevia.analysis.claims import create_claim_artifact
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import hash_object
from cerevia.core.provenance import Artifact
from cerevia.pipeline import evidence_manifest

SOURCE_URL = "https://github.com/jeffsocal/tidyproteomics/blob/main/docs/reference/table_proteins_expression_knockdown-control.csv"
SOURCE_COMMIT = "5aff0b888a3412441283b13506c299cec470b1f"


def _number(value: str) -> float | None:
    if value in {"", "NA", "NaN", "nan"}:
        return None
    return float(value)


def load_protein_assay(path: str | Path) -> list[dict[str, Any]]:
    """Load a public protein-level table without introducing a new identity system."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"protein", "abundance_control_1", "abundance_control_2", "abundance_control_3",
                "abundance_knockdown_1", "abundance_knockdown_2", "abundance_knockdown_3"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("proteomics assay requires protein identifiers and six abundance columns")
    for row in rows:
        for key in required - {"protein"}:
            _number(row[key])
    return rows


def _mean(values: list[float | None]) -> float:
    finite = [value for value in values if value is not None]
    if not finite:
        raise ValueError("protein has no finite abundance observations")
    return sum(finite) / len(finite)


def build_proteomics_chain(path: str | Path, study_id: str = "proteomics-hela-subset") -> tuple[ArtifactCatalog, Artifact, dict[str, Any], dict[str, Any]]:
    """Create a complete raw-assay-to-finding chain and its reusable specification."""
    rows = load_protein_assay(path)
    source_hash = hash_object({"source_url": SOURCE_URL, "source_commit": SOURCE_COMMIT, "fixture_sha256": Path(path).read_bytes().hex()})
    raw = Artifact.derive("proteomics-raw-assay-001", "raw_proteomics_assay", rows,
                          {"study_id": study_id, "source_url": SOURCE_URL, "source_commit": SOURCE_COMMIT,
                           "source_identity": source_hash, "row_count": len(rows), "domain": "proteomics"},
                          "ingest_proteomics_assay", parameters={"format": "csv", "identifier": "protein"})
    catalog = ArtifactCatalog()
    catalog.add(raw)

    finite_rows = [row for row in rows if any(_number(row[key]) is not None for key in ("abundance_control_1", "abundance_control_2", "abundance_control_3", "abundance_knockdown_1", "abundance_knockdown_2", "abundance_knockdown_3"))]
    qc = Artifact.derive("proteomics-qc-001", "proteomics_qc", {"passed": bool(finite_rows), "row_count": len(rows), "finite_rows": len(finite_rows), "required_columns": sorted({"protein", "abundance_control_1", "abundance_control_2", "abundance_control_3", "abundance_knockdown_1", "abundance_knockdown_2", "abundance_knockdown_3"})}, {"quality_gate": True}, "quality_control_proteomics", (raw,), {"policy": "protein_identifier_and_finite_abundance"})
    catalog.add(qc)
    if not finite_rows:
        raise ValueError("proteomics quality gate failed")

    processed = Artifact.derive("proteomics-processing-001", "proteomics_processed_assay", [{"protein": row["protein"], "control": [_number(row[f"abundance_control_{i}"]) for i in range(1, 4)], "knockdown": [_number(row[f"abundance_knockdown_{i}"]) for i in range(1, 4)]} for row in finite_rows], {"study_id": study_id, "operation": "select_protein_abundance_columns"}, "process_proteomics_assay", (raw, qc), {"columns": "six abundance replicates"})
    catalog.add(processed)

    quant_rows = []
    for row in finite_rows:
        control = [_number(row[f"abundance_control_{i}"]) for i in range(1, 4)]
        knockdown = [_number(row[f"abundance_knockdown_{i}"]) for i in range(1, 4)]
        control_mean = _mean(control)
        knockdown_mean = _mean(knockdown)
        quant_rows.append({"protein": row["protein"], "control_mean": control_mean, "knockdown_mean": knockdown_mean, "log2_ratio": float(__import__("math").log2((knockdown_mean + 1e-12) / (control_mean + 1e-12)))} )
    quantification = Artifact.derive("proteomics-quantification-001", "protein_quantification", quant_rows, {"study_id": study_id, "metric": "mean_abundance_and_log2_ratio", "protein_count": len(quant_rows)}, "quantify_protein_abundance", (processed,), {"pseudocount": 1e-12})
    catalog.add(quantification)

    ratios = [item["log2_ratio"] for item in quant_rows]
    mean_ratio = sum(ratios) / len(ratios)
    analysis = Artifact.derive("proteomics-analysis-001", "analysis", {"analysis_type": "descriptive_protein_response", "estimand": "mean_log2_knockdown_control_ratio", "mean_log2_ratio": mean_ratio, "protein_count": len(ratios)}, {"study_id": study_id, "domain": "proteomics"}, "analyze_protein_quantification", (quantification,), {"comparison": "knockdown_vs_control"})
    catalog.add(analysis)

    inference = Artifact.derive("proteomics-inference-001", "multimodal_inference", {"analysis_id": analysis.artifact_id, "result": {"direction": "higher" if mean_ratio > 0 else "lower_or_equal", "mean_log2_ratio": mean_ratio}}, {"study_id": study_id, "domain": "proteomics"}, "infer_proteomic_response", (analysis,), {"decision_rule": "sign_of_mean_log2_ratio"})
    catalog.add(inference)

    uncertainty = {"type": "descriptive_no_sampling_model", "not_estimated": True, "reason": "fixture demonstrates evidence plumbing rather than population inference"}
    statement = "The public HeLa protein-expression subset has the stated descriptive mean log2 knockdown/control response under the declared processing and quantification contract."
    assumptions = ("protein identifiers are stable within the source table",)
    experimental_context = {"study_id": study_id, "domain": "proteomics"}
    claim = create_claim_artifact("proteomics-claim-001", inference, (raw, quantification), "The knockdown condition changes protein abundance relative to control.", statement, assumptions, uncertainty, experimental_context, "descriptive_protein_response", catalog=catalog)
    catalog.add(claim)
    validation = claim.payload["validation"]

    finding_payload = {"finding_id": "proteomics-finding-001", "statement": statement, "evidence": [raw.artifact_id, quantification.artifact_id], "evidence_content_hashes": [raw.provenance.content_hash, quantification.provenance.content_hash], "analysis_id": claim.artifact_id, "statistical_result": analysis.payload, "status": claim.payload["claim_status"], "claim_status": claim.payload["claim_status"]}
    finding = Artifact.derive("proteomics-finding-001", "finding", finding_payload, {"study_id": study_id, "status": claim.payload["claim_status"], "evidence_count": 2}, "record_finding", (claim, raw, quantification), {"claim_policy": "computation_does_not_auto_convert_to_truth"})
    catalog.add(finding)

    specification = {"domain": "proteomics", "method": "descriptive_protein_response", "source_commit": SOURCE_COMMIT, "study_id": study_id, "inputs": [raw.artifact_id], "outputs": ["protein_quantification", "analysis", "inference", "claim", "finding"], "uncertainty": uncertainty}
    manifest = evidence_manifest(study_id, finding, catalog)
    execution_identity = hash_object({"specification_hash": hash_object(specification), "analysis_id": analysis.artifact_id, "inference_id": inference.artifact_id, "finding_id": finding.artifact_id, "final_content_hash": finding.provenance.content_hash})
    return catalog, finding, {"specification": specification, "specification_hash": hash_object(specification), "execution_identity": execution_identity, "manifest": manifest}, {"raw": raw, "qc": qc, "processed": processed, "quantification": quantification, "analysis": analysis, "inference": inference, "claim": claim, "finding": finding}

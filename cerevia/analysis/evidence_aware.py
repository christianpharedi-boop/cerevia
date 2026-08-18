"""V0.8 evidence-aware analysis and inference execution."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.environment import fingerprint
from cerevia.core.hashing import freeze, hash_object, thaw
from cerevia.core.provenance import Artifact
from cerevia.analysis.claims import create_claim_artifact
from cerevia.pipeline import evidence_manifest, finding


@dataclass(frozen=True)
class EvidenceAwareAnalysisSpecification:
    input_artifacts: tuple[dict[str, str], ...]
    alignment_artifacts: tuple[dict[str, str], ...]
    hypothesis: str
    experimental_conditions: dict[str, Any]
    comparison: dict[str, Any]
    method: str
    parameters: dict[str, Any]
    assumptions: tuple[str, ...]
    output_definitions: dict[str, Any]
    uncertainty: dict[str, Any]
    software_environment: dict[str, str]
    expected_outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.input_artifacts:
            raise ValueError("evidence-aware analysis requires input artifacts")
        if not self.alignment_artifacts:
            raise ValueError("evidence-aware analysis requires explicit alignment artifacts")
        for field_name in ("hypothesis", "method"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if not self.experimental_conditions:
            raise ValueError("experimental_conditions must be declared")
        if not self.comparison:
            raise ValueError("comparison must be declared")
        if not self.assumptions:
            raise ValueError("assumptions must be declared")
        if not self.output_definitions:
            raise ValueError("output_definitions must be declared")
        if not self.uncertainty:
            raise ValueError("uncertainty must be declared")
        if not self.expected_outputs:
            raise ValueError("expected_outputs must be declared")
        object.__setattr__(self, "input_artifacts", tuple(freeze(item) for item in self.input_artifacts))
        object.__setattr__(self, "alignment_artifacts", tuple(freeze(item) for item in self.alignment_artifacts))
        object.__setattr__(self, "experimental_conditions", freeze(self.experimental_conditions))
        object.__setattr__(self, "comparison", freeze(self.comparison))
        object.__setattr__(self, "parameters", freeze(self.parameters))
        object.__setattr__(self, "assumptions", tuple(self.assumptions))
        object.__setattr__(self, "output_definitions", freeze(self.output_definitions))
        object.__setattr__(self, "uncertainty", freeze(self.uncertainty))
        object.__setattr__(self, "software_environment", freeze(self.software_environment))
        object.__setattr__(self, "expected_outputs", tuple(self.expected_outputs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_artifacts": thaw(self.input_artifacts),
            "alignment_artifacts": thaw(self.alignment_artifacts),
            "hypothesis": self.hypothesis,
            "experimental_conditions": thaw(self.experimental_conditions),
            "comparison": thaw(self.comparison),
            "method": self.method,
            "parameters": thaw(self.parameters),
            "assumptions": list(self.assumptions),
            "output_definitions": thaw(self.output_definitions),
            "uncertainty": thaw(self.uncertainty),
            "software_environment": thaw(self.software_environment),
            "expected_outputs": list(self.expected_outputs),
        }

    @property
    def specification_hash(self) -> str:
        return hash_object(self.to_dict())


@dataclass(frozen=True)
class EvidenceAwareResult:
    specification_hash: str
    analysis_artifact_id: str
    inference_artifact_id: str
    claim_artifact_id: str
    finding_artifact_id: str
    final_content_hash: str
    manifest_hash: str
    execution_identity: str


def _validate_ref(catalog: ArtifactCatalog, reference: dict[str, str]) -> Artifact:
    artifact_id = reference["artifact_id"]
    artifact = catalog.get(artifact_id)
    if artifact.provenance.content_hash != reference["content_hash"]:
        raise ValueError(f"artifact content hash mismatch for {artifact_id}")
    return artifact


def _check_environment(specification: EvidenceAwareAnalysisSpecification) -> None:
    current = fingerprint()
    expected = thaw(specification.software_environment)
    mismatches = {key: (expected[key], current.get(key)) for key in expected if current.get(key) != expected[key]}
    if mismatches:
        raise ValueError(f"analysis environment does not match specification: {mismatches}")


def execute_evidence_aware_analysis(specification: EvidenceAwareAnalysisSpecification,
                                    catalog: ArtifactCatalog,
                                    study_id: str = "evidence-aware-study") -> EvidenceAwareResult:
    _check_environment(specification)
    inputs = tuple(_validate_ref(catalog, thaw(reference)) for reference in specification.input_artifacts)
    alignments = tuple(_validate_ref(catalog, thaw(reference)) for reference in specification.alignment_artifacts)
    for alignment in alignments:
        if alignment.kind != "cross_modal_alignment":
            raise ValueError("alignment_artifacts must reference cross_modal_alignment artifacts")
        parents = set(alignment.provenance.parent_artifacts)
        if not parents.intersection({artifact.artifact_id for artifact in inputs}):
            raise ValueError(f"alignment {alignment.artifact_id} is disconnected from declared inputs")
    declared = thaw(specification.expected_outputs)
    if len(declared) != 4:
        raise ValueError("expected_outputs must contain analysis, inference, claim, and finding IDs")
    analysis_id, inference_id, claim_id, finding_id = declared
    analysis_payload = {
        "hypothesis": specification.hypothesis,
        "experimental_conditions": thaw(specification.experimental_conditions),
        "comparison": thaw(specification.comparison),
        "method": specification.method,
        "parameters": thaw(specification.parameters),
        "assumptions": list(specification.assumptions),
        "output_definitions": thaw(specification.output_definitions),
        "uncertainty": thaw(specification.uncertainty),
        "specification_hash": specification.specification_hash,
    }
    analysis = catalog.add(Artifact.derive(
        analysis_id, "evidence_aware_analysis", analysis_payload,
        {"study_id": study_id, "analysis_role": "declared_method_and_hypothesis",
         "input_artifact_ids": [artifact.artifact_id for artifact in inputs],
         "alignment_artifact_ids": [artifact.artifact_id for artifact in alignments]},
        "declare_evidence_aware_analysis", parents=inputs + alignments,
        parameters={"specification_hash": specification.specification_hash}))
    feature_inputs = [artifact for artifact in inputs if artifact.kind == "spectral_power"]
    computed_outputs = {}
    if feature_inputs:
        computed_outputs["mean_spectral_feature"] = float(np.asarray(thaw(feature_inputs[0].payload), dtype=float).mean())
    inference_payload = {
        "analysis_id": analysis.artifact_id, "hypothesis": specification.hypothesis,
        "method": specification.method, "comparison": thaw(specification.comparison),
        "outputs": thaw(specification.output_definitions), "computed_outputs": computed_outputs,
        "uncertainty": thaw(specification.uncertainty),
        "status": "PROVISIONAL", "inference_role": "computed_from_declared_observations_and_alignments",
    }
    inference = catalog.add(Artifact.derive(
        inference_id, "multimodal_inference", inference_payload,
        {"study_id": study_id, "analysis_artifact_id": analysis.artifact_id,
         "associated_artifact_ids": [artifact.artifact_id for artifact in inputs + alignments],
         "status": "PROVISIONAL"},
        "execute_evidence_aware_inference", parents=(analysis,) + inputs + alignments,
        parameters={"specification_hash": specification.specification_hash}))
    claim = catalog.add(create_claim_artifact(
        claim_id, inference, (analysis,) + inputs + alignments,
        specification.hypothesis, specification.hypothesis,
        tuple(specification.assumptions), thaw(specification.uncertainty),
        thaw(specification.experimental_conditions), specification.method, catalog=catalog))
    final = catalog.add(finding(
        claim, (claim, inference, analysis) + inputs + alignments, finding_id,
        specification.hypothesis, catalog=catalog))
    if catalog.validate_integrity():
        raise RuntimeError("evidence-aware analysis produced an integrity-invalid artifact graph")
    manifest = evidence_manifest(study_id, final, catalog)
    execution_identity = hash_object({
        "specification_hash": specification.specification_hash,
        "analysis_id": analysis.artifact_id, "inference_id": inference.artifact_id,
        "finding_id": final.artifact_id, "final_content_hash": final.provenance.content_hash,
    })
    return EvidenceAwareResult(specification.specification_hash, analysis.artifact_id, inference.artifact_id,
                               claim.artifact_id, final.artifact_id, final.provenance.content_hash,
                               manifest["manifest_hash"], execution_identity)

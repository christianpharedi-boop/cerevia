"""CEREVIA V0.9 claim validation and qualified scientific claims."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import freeze, hash_object, thaw
from cerevia.core.provenance import Artifact


@dataclass(frozen=True)
class ClaimValidation:
    status: str
    reasons: tuple[str, ...]
    claim_type: str = "scientific_claim"

    @property
    def permissible(self) -> bool:
        return self.status in {"PROVISIONAL", "QUALIFIED"}

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "reasons": list(self.reasons), "claim_type": self.claim_type,
                "permissible": self.permissible}


def validate_claim(inference: Artifact, evidence: tuple[Artifact, ...], hypothesis: str,
                   statement: str, assumptions: tuple[str, ...], uncertainty: dict[str, Any],
                   experimental_context: dict[str, Any], method: str) -> ClaimValidation:
    reasons: list[str] = []
    if inference.kind not in {"analysis", "multimodal_analysis", "multimodal_inference"}:
        return ClaimValidation("INVALID", ("claim requires a valid analysis or inference artifact",))
    if not evidence:
        return ClaimValidation("INVALID", ("claim requires supporting evidence",))
    if not hypothesis.strip() or not statement.strip():
        return ClaimValidation("INVALID", ("claim requires hypothesis and statement",))
    if not assumptions:
        return ClaimValidation("INVALID", ("claim requires explicit assumptions",))
    if not uncertainty:
        return ClaimValidation("INVALID", ("claim requires an uncertainty declaration",))
    if not experimental_context:
        return ClaimValidation("INVALID", ("claim requires experimental context",))
    if not method.strip():
        return ClaimValidation("INVALID", ("claim requires a method",))
    uncertainty_type = uncertainty.get("type")
    if not uncertainty_type:
        return ClaimValidation("INVALID", ("uncertainty requires a type",))
    if uncertainty_type == "not_estimated":
        reasons.append("uncertainty was not estimated; claim remains qualified")
        return ClaimValidation("QUALIFIED", tuple(reasons))
    reasons.append("claim is bound to declared evidence, method, assumptions, context, and uncertainty")
    return ClaimValidation("PROVISIONAL", tuple(reasons))


def create_claim_artifact(artifact_id: str, inference: Artifact, evidence: tuple[Artifact, ...],
                          hypothesis: str, statement: str, assumptions: tuple[str, ...],
                          uncertainty: dict[str, Any], experimental_context: dict[str, Any],
                          method: str, catalog: ArtifactCatalog | None = None) -> Artifact:
    validation = validate_claim(inference, evidence, hypothesis, statement, assumptions, uncertainty,
                                experimental_context, method)
    if not validation.permissible:
        raise ValueError(f"scientific claim is not permissible: {validation.reasons}")
    if catalog is not None:
        if catalog.validate_integrity():
            raise ValueError("cannot validate a claim against an integrity-invalid catalog")
        lineage_ids = {item.artifact_id for item in catalog.lineage(inference.artifact_id)}
        if not {item.artifact_id for item in evidence}.issubset(lineage_ids):
            raise ValueError("claim evidence must belong to inference lineage")
        for item in evidence:
            if catalog.get(item.artifact_id).provenance.content_hash != item.provenance.content_hash:
                raise ValueError("claim evidence content does not match catalog")
    payload = {
        "claim_type": validation.claim_type, "hypothesis": hypothesis, "statement": statement,
        "inference_id": inference.artifact_id,
        "inference_content_hash": inference.provenance.content_hash,
        "evidence": [item.artifact_id for item in evidence],
        "evidence_content_hashes": [item.provenance.content_hash for item in evidence],
        "assumptions": list(assumptions), "uncertainty": thaw(freeze(uncertainty)),
        "experimental_context": thaw(freeze(experimental_context)), "method": method,
        "validation": validation.to_dict(), "claim_status": validation.status,
        "computed_result": thaw(inference.payload),
    }
    return Artifact.derive(
        artifact_id, "claim", payload,
        {"status": validation.status, "claim_type": validation.claim_type,
         "inference_id": inference.artifact_id, "experimental_context": experimental_context},
        "validate_scientific_claim", parents=(inference,) + evidence,
        parameters={"validation_hash": hash_object(validation.to_dict())})

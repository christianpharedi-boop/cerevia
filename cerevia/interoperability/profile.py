"""Frozen V1.6 Evidence Interoperability Profile contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SPEC_VERSION = "1.0"


@dataclass(frozen=True)
class EvidenceInteroperabilityProfile:
    """Machine-readable declaration of a CEREVIA-compatible adapter."""

    domain: str
    adapter_version: str
    supported_artifact_types: tuple[str, ...]
    input_contract: str
    output_contract: tuple[str, ...]
    identity_semantics: str
    lineage_semantics: str
    verification_requirements: tuple[str, ...]
    source_artifact_id: str
    final_finding_id: str
    specification_version: str = SPEC_VERSION

    def __post_init__(self) -> None:
        if self.specification_version != SPEC_VERSION:
            raise ValueError(f"unsupported interoperability specification: {self.specification_version}")
        required = {"domain": self.domain, "adapter_version": self.adapter_version, "input_contract": self.input_contract, "identity_semantics": self.identity_semantics, "lineage_semantics": self.lineage_semantics, "source_artifact_id": self.source_artifact_id, "final_finding_id": self.final_finding_id}
        if any(not value for value in required.values()):
            raise ValueError("profile required fields cannot be empty")
        if not self.supported_artifact_types or "finding" not in self.supported_artifact_types:
            raise ValueError("profile must declare supported finding artifacts")
        if not self.output_contract or not self.verification_requirements:
            raise ValueError("profile output and verification requirements cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["supported_artifact_types"] = list(self.supported_artifact_types)
        data["output_contract"] = list(self.output_contract)
        data["verification_requirements"] = list(self.verification_requirements)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceInteroperabilityProfile":
        return cls(domain=data["domain"], adapter_version=data["adapter_version"], supported_artifact_types=tuple(data["supported_artifact_types"]), input_contract=data["input_contract"], output_contract=tuple(data["output_contract"]), identity_semantics=data["identity_semantics"], lineage_semantics=data["lineage_semantics"], verification_requirements=tuple(data["verification_requirements"]), source_artifact_id=data["source_artifact_id"], final_finding_id=data["final_finding_id"], specification_version=data.get("specification_version", SPEC_VERSION))

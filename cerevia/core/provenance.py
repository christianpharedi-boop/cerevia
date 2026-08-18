"""Machine-readable provenance records and lineage traversal."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from .hashing import freeze, hash_object, thaw


@dataclass(frozen=True)
class Provenance:
    artifact_id: str
    parent_artifacts: tuple[str, ...]
    operation: str
    parameters: dict[str, Any]
    software_version: str
    environment: dict[str, str]
    timestamp: str
    content_hash: str
    creator: str

    @classmethod
    def create(cls, artifact_id: str, parent_artifacts: tuple[str, ...], operation: str,
               parameters: dict[str, Any], content_hash: str, software_version: str = "1.6.0",
               creator: str = "cerevia", environment: dict[str, str] | None = None) -> "Provenance":
        if environment is None:
            from .environment import fingerprint
            environment = fingerprint()
        return cls(artifact_id, parent_artifacts, operation, freeze(parameters), software_version,
                   freeze(environment), datetime.now(timezone.utc).isoformat(), content_hash, creator)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "parent_artifacts": list(self.parent_artifacts),
            "operation": self.operation,
            "parameters": thaw(self.parameters),
            "software_version": self.software_version,
            "environment": thaw(self.environment),
            "timestamp": self.timestamp,
            "content_hash": self.content_hash,
            "creator": self.creator,
        }


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    kind: str
    payload: Any
    metadata: dict[str, Any]
    provenance: Provenance

    @classmethod
    def derive(cls, artifact_id: str, kind: str, payload: Any, metadata: dict[str, Any],
               operation: str, parents: tuple["Artifact", ...] = (), parameters: dict[str, Any] | None = None,
               environment: dict[str, str] | None = None, software_version: str = "1.6.0") -> "Artifact":
        from .environment import fingerprint
        immutable_payload = freeze(payload)
        immutable_metadata = freeze(metadata)
        immutable_parameters = freeze(parameters or {})
        computational_environment = environment or fingerprint()
        parent_ids = tuple(parent.artifact_id for parent in parents)
        parent_refs = [{"artifact_id": parent.artifact_id, "content_hash": parent.provenance.content_hash} for parent in parents]
        content_hash = hash_object({
            "artifact_id": artifact_id,
            "kind": kind,
            "payload": immutable_payload,
            "metadata": immutable_metadata,
            "operation": operation,
            "parameters": immutable_parameters,
            "software_version": software_version,
            "environment": computational_environment,
            "parents": parent_refs,
        })
        provenance = Provenance.create(artifact_id, parent_ids, operation, thaw(immutable_parameters), content_hash,
                                       software_version=software_version, environment=computational_environment)
        return cls(artifact_id, kind, immutable_payload, immutable_metadata, provenance)

    def to_dict(self, include_payload: bool = True) -> dict[str, Any]:
        result = {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "metadata": thaw(self.metadata),
            "provenance": self.provenance.to_dict(),
        }
        if include_payload:
            result["payload"] = thaw(self.payload)
        return result


def lineage(artifact: Artifact, catalog: dict[str, Artifact]) -> list[Artifact]:
    """Return the artifact and all ancestors in deterministic parent-first order."""
    ordered: list[Artifact] = []
    seen: set[str] = set()

    def visit(node: Artifact) -> None:
        if node.artifact_id in seen:
            return
        seen.add(node.artifact_id)
        for parent_id in node.provenance.parent_artifacts:
            if parent_id not in catalog:
                raise ValueError(f"orphaned provenance: {node.artifact_id} references {parent_id}")
            visit(catalog[parent_id])
        ordered.append(node)

    visit(artifact)
    return ordered

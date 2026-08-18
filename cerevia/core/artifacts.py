"""Artifact catalog enforcing immutable, traceable state."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .hashing import freeze, hash_object
from .provenance import Artifact, lineage


@dataclass
class ArtifactCatalog:
    _items: dict[str, Artifact] = field(default_factory=dict)

    def add(self, artifact: Artifact) -> Artifact:
        if artifact.artifact_id in self._items:
            raise ValueError(f"artifact already exists and is immutable: {artifact.artifact_id}")
        for parent_id in artifact.provenance.parent_artifacts:
            if parent_id not in self._items:
                raise ValueError(f"parent artifact must be registered first: {parent_id}")
        self._items[artifact.artifact_id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Artifact:
        return self._items[artifact_id]

    def remove_for_test(self, artifact_id: str) -> None:
        """Remove an artifact to simulate storage loss in adversarial tests."""
        del self._items[artifact_id]

    def all(self) -> tuple[Artifact, ...]:
        return tuple(self._items.values())

    def lineage(self, artifact_id: str) -> list[Artifact]:
        return lineage(self.get(artifact_id), self._items)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._items)

    def validate_integrity(self) -> list[str]:
        """Recompute each artifact identity and verify all parent references."""
        errors: list[str] = []
        for artifact in self._items.values():
            for parent_id in artifact.provenance.parent_artifacts:
                if parent_id not in self._items:
                    errors.append(f"{artifact.artifact_id}: missing parent {parent_id}")
            parent_refs = []
            for parent_id in artifact.provenance.parent_artifacts:
                parent = self._items.get(parent_id)
                if parent is not None:
                    parent_refs.append({"artifact_id": parent.artifact_id, "content_hash": parent.provenance.content_hash})
            expected = hash_object({
                "artifact_id": artifact.artifact_id,
                "kind": artifact.kind,
                "payload": artifact.payload,
                "metadata": artifact.metadata,
                "operation": artifact.provenance.operation,
                "parameters": artifact.provenance.parameters,
                "software_version": artifact.provenance.software_version,
                "environment": artifact.provenance.environment,
                "parents": parent_refs,
            })
            if expected != artifact.provenance.content_hash:
                errors.append(f"{artifact.artifact_id}: content identity mismatch")
        return errors

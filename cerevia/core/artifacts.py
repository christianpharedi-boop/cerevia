"""Artifact catalog enforcing immutable, traceable state."""
from __future__ import annotations
from dataclasses import dataclass, field
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

    def all(self) -> tuple[Artifact, ...]:
        return tuple(self._items.values())

    def lineage(self, artifact_id: str) -> list[Artifact]:
        return lineage(self.get(artifact_id), self._items)

    def ids(self) -> tuple[str, ...]:
        return tuple(self._items)

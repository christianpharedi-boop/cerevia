"""Content-addressable hashing and immutable serialization utilities."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze(value: Any) -> Any:
    """Recursively convert common containers into immutable equivalents."""
    if isinstance(value, dict):
        return MappingProxyType({str(key): freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Return a JSON-compatible mutable view without changing the stored object."""
    if isinstance(value, (dict, MappingProxyType)):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(thaw(item) for item in value)
    return value


def _jsonable(value: Any) -> Any:
    return thaw(value)


def canonical_json(value: Any) -> bytes:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def hash_object(value: Any) -> str:
    return sha256_bytes(canonical_json(value))

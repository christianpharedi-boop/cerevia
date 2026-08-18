"""Minimal LOD ingestion and quality-control primitives.

This module intentionally does not assume a particular external file format.
A source-specific parser should normalize data into the canonical schema below.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class LODRecord:
    epoch: date
    lod_ms: float
    quality_flag: str


def validate_lod(records: Iterable[LODRecord]) -> list[str]:
    """Return validation errors without modifying input records."""
    errors: list[str] = []
    seen = set()

    for index, record in enumerate(records, 1):
        if record.epoch in seen:
            errors.append(f"record {index}: duplicate epoch {record.epoch}")
        seen.add(record.epoch)

        if record.quality_flag.strip() == "":
            errors.append(f"record {index}: missing quality flag")

        if record.lod_ms != record.lod_ms:
            errors.append(f"record {index}: NaN LOD value")

    return errors

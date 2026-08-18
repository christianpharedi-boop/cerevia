"""Canonical strict parser for the IERS EOP 20 C04 ASCII product."""
from __future__ import annotations

import math
from datetime import date, timedelta
from pathlib import Path

MJD_ORIGIN = date(1858, 11, 17)


def parse_file(path: Path) -> tuple[list[dict], list[str], str]:
    """Parse C04 rows without silently repairing source data."""
    rows: list[dict] = []
    errors: list[str] = []
    headers: list[str] = []
    for line_number, raw in enumerate(path.read_text(encoding="ascii", errors="strict").splitlines(), 1):
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("#"):
            headers.append(line)
            continue
        fields = line.split()
        if len(fields) < 20:
            errors.append(f"line {line_number}: expected 20 fields, found {len(fields)}")
            continue
        try:
            epoch = date(int(fields[0]), int(fields[1]), int(fields[2]))
            mjd = float(fields[4])
            lod_s = float(fields[12])
            lod_error_s = float(fields[19])
        except (ValueError, IndexError) as exc:
            errors.append(f"line {line_number}: invalid required field: {exc}")
            continue
        if not all(math.isfinite(value) for value in (mjd, lod_s, lod_error_s)):
            errors.append(f"line {line_number}: non-finite MJD, LOD, or LOD error")
            continue
        expected_mjd = (epoch - MJD_ORIGIN).days
        if abs(mjd - expected_mjd) > 0.01:
            errors.append(f"line {line_number}: MJD/date mismatch ({mjd} vs {expected_mjd})")
        if lod_error_s < 0:
            errors.append(f"line {line_number}: negative LOD formal error")
        rows.append({"date": epoch, "mjd": mjd, "lod_s": lod_s, "lod_error_s": lod_error_s})
    return rows, errors, "\n".join(headers)


def validate_rows(
    rows: list[dict],
    expected_records: int | None = None,
    expected_start: str | None = None,
    expected_end: str | None = None,
) -> list[str]:
    """Validate ordering, uniqueness, cadence, and optional frozen expectations."""
    errors: list[str] = []
    dates = [row["date"] for row in rows]
    if not rows:
        return ["no parseable data rows found"]
    if expected_records is not None and len(rows) != expected_records:
        errors.append(f"record-count mismatch ({len(rows)} parsed vs {expected_records} expected)")
    if expected_start and str(dates[0]) != expected_start:
        errors.append(f"first-date mismatch ({dates[0]} vs {expected_start})")
    if expected_end and str(dates[-1]) != expected_end:
        errors.append(f"last-date mismatch ({dates[-1]} vs {expected_end})")
    if dates != sorted(dates):
        errors.append("dates are not monotonically increasing")
    if len(dates) != len(set(dates)):
        errors.append("duplicate dates detected")
    gaps = [(a, b) for a, b in zip(dates, dates[1:]) if b - a != timedelta(days=1)]
    if gaps:
        errors.append(f"cadence gaps or irregular intervals detected ({len(gaps)} intervals)")
    return errors


def header_identifies_c04(header: str) -> bool:
    return "EOP" in header and "C04" in header


def rows_to_lod_records(rows: list[dict]):
    """Normalize strict C04 rows into the project LODRecord representation."""
    from rotation.lod import LODRecord

    return [
        LODRecord(row["date"], row["lod_s"] * 1000.0, f"formal_error={row['lod_error_s']:g}")
        for row in rows
    ]

"""Independent verification entry point: no original in-memory catalog is required."""
from __future__ import annotations
import json
from pathlib import Path
import sys

from cerevia.verification.bundle import verify_bundle_file


def main(path: str) -> int:
    report = verify_bundle_file(path)
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.verified else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("provide a verification_bundle.json path")
    raise SystemExit(main(sys.argv[1]))

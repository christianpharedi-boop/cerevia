"""Run the smallest complete CEREVIA neuroscience verification path.

Usage from the repository root::

    python3 examples/neuro/quickstart.py

The fixture is intentionally synthetic and contains no participant data. The
quickstart demonstrates independent verification of a serialized EEG/BIDS
provenance bundle before users connect their own BIDS-derived artifacts.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path(__file__).with_name("verification_bundle.json")
VERIFIER = Path(__file__).with_name("verify_bundle.py")


def main() -> int:
    result = subprocess.run(
        [sys.executable, str(VERIFIER), str(BUNDLE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT)},
        check=False,
    )
    if result.stdout:
        report = json.loads(result.stdout)
        status = "VERIFIED" if report.get("verified") else "INVESTIGATE"
        print(f"CEREVIA neuroscience quickstart: {status}")
        print(f"Bundle: {BUNDLE.relative_to(ROOT)}")
        print(f"Final finding: {report.get('final_finding_id', 'none')}")
        print(f"Checks passed: {len(report.get('checks', []))}")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode == 0:
        print("Next: inspect examples/neuro/observatory_query.py or connect a BIDS EEG run.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

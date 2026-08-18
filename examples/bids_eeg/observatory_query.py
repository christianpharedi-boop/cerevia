"""Reference read-only Observatory query for a serialized Sentinel bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cerevia.observatory import ObservatorySnapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Query a CEREVIA evidence bundle through the read-only Observatory")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--sentinel", type=Path)
    parser.add_argument("--finding")
    parser.add_argument("--as-of", dest="as_of")
    parser.add_argument("--impact-of")
    args = parser.parse_args()

    snapshot = ObservatorySnapshot.from_files(args.bundle, args.sentinel)
    if args.impact_of:
        result = snapshot.impact_of(args.impact_of)
    else:
        result = {
            "finding": snapshot.get_finding(args.finding),
            "lineage": snapshot.get_lineage(args.finding),
            "supporting_evidence": snapshot.get_supporting_evidence(args.finding),
            "verification": snapshot.get_verification(),
            "attestations": snapshot.get_attestations(),
            "revocations": snapshot.get_revocations(),
            "history": snapshot.get_history(args.finding, args.as_of),
        }
    result = {"observatory": "CEREVIA OBSERVATORY", "observatory_version": "1.2.0", "graph_hash": snapshot.graph_hash, **result}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

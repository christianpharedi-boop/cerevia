"""Validate the repository-side external pilot readiness checklist."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checklist", type=Path, default=Path("docs/pilot/readiness.json"))
    args = parser.parse_args()
    root = Path(__file__).parents[2]
    checklist = json.loads(args.checklist.read_text(encoding="utf-8"))
    required = ["docs/evidence-interoperability-v1.md", "examples/external_impl/standalone_protocol.py", "docs/institutional-exchange-v2.1.md", "examples/pilot/pilot_proof.py", "docs/external-institutional-pilot-v2.2.md", "docs/pilot/30-minute-quickstart.md", "docs/pilot/external-result-template.json"]
    missing = [path for path in required if not (root / path).exists()]
    complete = [item["id"] for item in checklist["checks"] if item["status"] == "COMPLETE"]
    pending = [item["id"] for item in checklist["checks"] if item["status"] == "PENDING_EXTERNAL"]
    result = {"architecture_status": checklist["architecture_status"], "complete_count": len(complete), "pending_external": pending, "missing_handoff_artifacts": missing, "ready_for_external_handoff": not missing and pending == ["external_institution"] and checklist["claims_of_external_use_permitted"] is False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_external_handoff"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

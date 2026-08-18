"""V1.5 cross-domain evidence composition proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cerevia.interoperability.cross_domain import compose_cross_domain_bundle, impact_after_revocation, load_bundle
from cerevia.observatory import ObservatorySnapshot
from cerevia.verification.bundle import verify_bundle_file, write_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--neuroscience", type=Path, default=Path("examples/neuro/verification_bundle.json"))
    parser.add_argument("--proteomics", type=Path, default=Path("examples/transplants/proteomics_bundle.json"))
    parser.add_argument("--earthspace", type=Path, default=Path("examples/transplants/earthspace_bundle.json"))
    parser.add_argument("--output", type=Path, default=Path("examples/substrate_stress_tests/cross_domain_bundle.json"))
    args = parser.parse_args()

    source_paths = {"neuroscience": args.neuroscience, "proteomics": args.proteomics, "earthspace": args.earthspace}
    bundles = {domain: load_bundle(path) for domain, path in source_paths.items()}
    bundle, _, identifiers = compose_cross_domain_bundle(bundles)
    write_bundle(bundle, args.output)
    report = verify_bundle_file(args.output)
    snapshot = ObservatorySnapshot.from_files(args.output)

    impacts = {domain: snapshot.impact_of(identifiers[domain].artifact_id) for domain in ("neuroscience", "proteomics", "earthspace")}
    revocations = {domain: impact_after_revocation(bundle, identifiers[domain].artifact_id, f"selective {domain} revocation") for domain in ("neuroscience", "proteomics", "earthspace")}
    result = {"cross_domain_verification": report.to_dict(), "source_domain_reports": bundle.get("source_domain_reports"), "finding": snapshot.get_finding(), "lineage": snapshot.get_lineage(), "supporting_evidence": snapshot.get_supporting_evidence(), "impacts": impacts, "selective_revocations": revocations, "domain_evidence": bundle["specification"]["domain_evidence"]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

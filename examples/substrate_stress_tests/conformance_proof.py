"""V1.6 Evidence Interoperability conformance proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cerevia.interoperability.conformance import validate_cross_domain_composition, validate_profiles
from cerevia.interoperability.cross_domain import compose_cross_domain_bundle, load_bundle
from cerevia.interoperability.reference_profiles import REFERENCE_PROFILES
from cerevia.verification.bundle import write_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--neuroscience", type=Path, default=Path("examples/neuro/verification_bundle.json"))
    parser.add_argument("--proteomics", type=Path, default=Path("examples/transplants/proteomics_bundle.json"))
    parser.add_argument("--earthspace", type=Path, default=Path("examples/transplants/earthspace_bundle.json"))
    parser.add_argument("--output", type=Path, default=Path("examples/substrate_stress_tests/conformance_cross_domain_bundle.json"))
    args = parser.parse_args()
    paths = {"neuroscience": args.neuroscience, "proteomics": args.proteomics, "earthspace": args.earthspace}
    bundles = {domain: load_bundle(path) for domain, path in paths.items()}
    domain_results = validate_profiles(REFERENCE_PROFILES, bundles)
    cross_bundle, _, _ = compose_cross_domain_bundle(bundles)
    write_bundle(cross_bundle, args.output)
    cross_result = validate_cross_domain_composition(cross_bundle, REFERENCE_PROFILES)
    output = {"specification_version": "1.0", "profiles": {domain: REFERENCE_PROFILES[domain].to_dict() for domain in sorted(REFERENCE_PROFILES)}, "domain_conformance": {domain: result.to_dict() for domain, result in domain_results.items()}, "cross_domain_conformance": cross_result.to_dict(), "conformant": all(result.conformant for result in domain_results.values()) and cross_result.conformant}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["conformant"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

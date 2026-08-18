"""V2.2 External Institutional Pilot preparation proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.core.hashing import hash_object
from cerevia.institutional.exchange import AuditLog, ExchangePolicy, InstitutionKeyRing, create_exchange_package
from cerevia.interoperability.cross_domain import load_bundle
from cerevia.pilot.kit import compare_answers, extract_exchange_answer, mutate_exchange_package


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=Path("examples/cross_domain/cross_domain_bundle.json"))
    parser.add_argument("--output", type=Path, default=Path("examples/pilot/pilot_results.json"))
    args = parser.parse_args()
    bundle = load_bundle(args.bundle)
    private = Ed25519PrivateKey.generate()
    keys = InstitutionKeyRing("institution-a")
    keys.add_public_key("institution-a-key-001", private.public_key())
    policy = ExchangePolicy(retention_until="2030-01-01T00:00:00+00:00", access_class="restricted", allowed_domains=("cross-domain",))
    audit = AuditLog()
    audit.append("package_prepared", "institution-a", "pilot-valid", {"bundle_hash": hash_object(bundle)})
    package = create_exchange_package(bundle, "institution-a", "institution-b", "institution-a-key-001", private, policy, "out-of-band://institution-a/cross-domain-v1.5", {"status": "checked", "checked_at": "2026-08-18T00:00:00+00:00"}, audit.head, package_id="pilot-valid")
    scenarios = {"valid": package, "altered_bundle_hash": mutate_exchange_package(package, "altered_bundle_hash").package, "stale_revocation": mutate_exchange_package(package, "stale_revocation").package, "wrong_recipient": mutate_exchange_package(package, "wrong_recipient").package}
    answers: dict[str, dict[str, object]] = {}
    agreements: dict[str, dict[str, object]] = {}
    for scenario_id, scenario_package in scenarios.items():
        answer_a = extract_exchange_answer(scenario_id, scenario_package, bundle, keys, "institution-b", audit, ("proteomics-raw-assay-001",))
        answer_b = extract_exchange_answer(scenario_id, scenario_package, bundle, keys, "institution-b", audit, ("proteomics-raw-assay-001",))
        answers[scenario_id] = {"institution_a": answer_a.to_dict(), "institution_b": answer_b.to_dict()}
        agreements[scenario_id] = compare_answers(answer_a, answer_b).to_dict()
    result = {"pilot_status": "PREPARED_NOT_EXECUTED_EXTERNALLY", "bundle_hash": hash_object(bundle), "scenarios": sorted(scenarios), "answers": answers, "agreement": agreements, "privacy_boundary": {"bundle_embedded": False, "bundle_locator": package.bundle_locator, "sensitive_payloads_in_package": False}, "external_participant_required": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(item["agreement"] for item in agreements.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

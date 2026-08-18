"""V2.1 blind institutional exchange simulation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.institutional.exchange import AuditLog, ExchangePolicy, InstitutionKeyRing, create_exchange_package, verify_exchange_package
from cerevia.interoperability.cross_domain import load_bundle
from cerevia.verification.bundle import verify_bundle_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=Path("examples/substrate_stress_tests/cross_domain_bundle.json"))
    parser.add_argument("--package", type=Path, default=Path("examples/institutional_pilot/exchange_package.json"))
    parser.add_argument("--audit", type=Path, default=Path("examples/institutional_pilot/audit_log.json"))
    args = parser.parse_args()

    bundle = load_bundle(args.bundle)
    sender_key = Ed25519PrivateKey.generate()
    sender_keys = InstitutionKeyRing("institution-a")
    sender_keys.add_public_key("institution-a-key-001", sender_key.public_key())
    policy = ExchangePolicy(retention_until="2030-01-01T00:00:00+00:00", access_class="restricted", allowed_domains=("cross-domain",))
    audit = AuditLog()
    audit.append("package_prepared", "institution-a", "exchange-0001", {"bundle_hash": __import__("cerevia.core.hashing", fromlist=["hash_object"]).hash_object(bundle)})
    package = create_exchange_package(bundle, "institution-a", "institution-b", "institution-a-key-001", sender_key, policy, "s3://institution-a/evidence/cross-domain-v1.5.json", {"status": "checked", "registry_hash": "none", "checked_at": "2026-08-18T00:00:00+00:00"}, audit.head)
    args.package.write_text(json.dumps(package.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    args.audit.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    received = verify_exchange_package(package, bundle, sender_keys, "institution-b", audit_log=audit)
    rotated_key = Ed25519PrivateKey.generate()
    sender_keys.rotate("institution-a-key-001", "institution-a-key-002", rotated_key.public_key(), "2026-08-18T01:00:00+00:00")
    audit.append("key_rotated_and_package_prepared", "institution-a", "exchange-0002", {"replaces": "institution-a-key-001"}, "2026-08-18T01:00:00+00:00")
    rotated_package = create_exchange_package(bundle, "institution-a", "institution-b", "institution-a-key-002", rotated_key, policy, package.bundle_locator, package.revocation_snapshot, audit.head, package_id="exchange-0002")
    rotated_received = verify_exchange_package(rotated_package, bundle, sender_keys, "institution-b", audit_log=audit)
    old_key_rejected = not verify_exchange_package(package, bundle, sender_keys, "institution-b", audit_log=audit)["verified"]
    independent_bundle_report = verify_bundle_file(args.bundle)
    result = {"exchange_verified": received["verified"], "exchange_report": received, "rotated_exchange_verified": rotated_received["verified"], "rotated_exchange_report": rotated_received, "old_key_rejected_after_rotation": old_key_rejected, "bundle_verified": independent_bundle_report.verified, "privacy_boundary": {"bundle_locator": package.bundle_locator, "inline_payload_present": "bundle" in package.to_dict(), "access_class": policy.access_class, "evidence_location": policy.evidence_location}, "key_lifecycle": {"institution_id": sender_keys.institution_id, "active_key_ids": [key_id for key_id, record in sender_keys.records.items() if record.status == "active"], "retired_key_ids": [key_id for key_id, record in sender_keys.records.items() if record.status == "retired"], "rotatable": True}, "audit": audit.to_dict()}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["exchange_verified"] and result["rotated_exchange_verified"] and result["old_key_rejected_after_rotation"] and result["bundle_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cerevia.core.hashing import hash_object
from cerevia.institutional.exchange import AuditLog, ExchangePolicy, InstitutionKeyRing, create_exchange_package, verify_exchange_package
from cerevia.interoperability.cross_domain import load_bundle


class InstitutionalExchangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).parents[1]
        cls.bundle = load_bundle(cls.root / "examples/cross_domain/cross_domain_bundle.json")

    def make_exchange(self):
        private = Ed25519PrivateKey.generate()
        keys = InstitutionKeyRing("institution-a")
        keys.add_public_key("key-001", private.public_key())
        policy = ExchangePolicy(retention_until="2030-01-01T00:00:00+00:00", access_class="restricted", allowed_domains=("cross-domain",))
        audit = AuditLog()
        audit.append("package_prepared", "institution-a", "package-001", {"bundle_hash": hash_object(self.bundle)})
        package = create_exchange_package(self.bundle, "institution-a", "institution-b", "key-001", private, policy, "s3://institution-a/package-001.json", {"status": "checked"}, audit.head)
        return private, keys, policy, audit, package

    def test_signed_exchange_verifies_without_inline_payload(self):
        _, keys, _, audit, package = self.make_exchange()
        result = verify_exchange_package(package, self.bundle, keys, "institution-b", audit_log=audit)
        self.assertTrue(result["verified"], result)
        self.assertNotIn("bundle", package.to_dict())
        self.assertIn("signature", result["checks"])
        self.assertIn("revocation_snapshot", result["checks"])

    def test_key_rotation_retires_old_signer_and_accepts_new_signer(self):
        _, keys, policy, audit, old_package = self.make_exchange()
        new_private = Ed25519PrivateKey.generate()
        keys.rotate("key-001", "key-002", new_private.public_key(), "2026-08-18T01:00:00+00:00")
        audit.append("key_rotated", "institution-a", "package-002", {"replaces": "key-001"}, "2026-08-18T01:00:00+00:00")
        new_package = create_exchange_package(self.bundle, "institution-a", "institution-b", "key-002", new_private, policy, "s3://institution-a/package-002.json", {"status": "checked"}, audit.head, package_id="package-002")
        self.assertTrue(verify_exchange_package(new_package, self.bundle, keys, "institution-b", audit_log=audit)["verified"])
        self.assertFalse(verify_exchange_package(old_package, self.bundle, keys, "institution-b", audit_log=audit)["verified"])
        self.assertEqual(keys.get("key-001").status, "retired")

    def test_tampered_audit_and_expired_retention_are_rejected(self):
        private, keys, _, audit, package = self.make_exchange()
        tampered_audit = copy.deepcopy(audit)
        tampered_audit.events[0].details["bundle_hash"] = "tampered"  # type: ignore[index]
        self.assertFalse(verify_exchange_package(package, self.bundle, keys, "institution-b", audit_log=tampered_audit)["verified"])
        expired = ExchangePolicy(retention_until="2020-01-01T00:00:00+00:00", access_class="restricted", allowed_domains=("cross-domain",))
        expired_package = create_exchange_package(self.bundle, "institution-a", "institution-b", "key-001", private, expired, "s3://institution-a/expired.json", {"status": "checked"}, audit.head)
        expired_result = verify_exchange_package(expired_package, self.bundle, keys, "institution-b", audit_log=audit)
        self.assertFalse(expired_result["verified"])
        self.assertIn("retention expired", expired_result["failures"])

    def test_disallowed_domain_is_rejected(self):
        private, keys, _, audit, _ = self.make_exchange()
        policy = ExchangePolicy(retention_until="2030-01-01T00:00:00+00:00", access_class="restricted", allowed_domains=("neuroscience",))
        package = create_exchange_package(self.bundle, "institution-a", "institution-b", "key-001", private, policy, "s3://institution-a/wrong-domain.json", {"status": "checked"}, audit.head)
        result = verify_exchange_package(package, self.bundle, keys, "institution-b", audit_log=audit)
        self.assertFalse(result["verified"])
        self.assertIn("bundle domain is not allowed by policy", result["failures"])


if __name__ == "__main__":
    unittest.main()

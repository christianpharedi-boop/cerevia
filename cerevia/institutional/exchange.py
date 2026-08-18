"""V2.1 Institutional Exchange Profile.

The exchange layer signs protocol metadata and references evidence bundles by
content hash. It deliberately does not copy raw scientific payloads into the
trust envelope.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from cerevia.core.hashing import hash_object
from cerevia.sentinel.security import RevocationRegistry
from cerevia.verification.bundle import verify_bundle

EXCHANGE_VERSION = "1.0"
ACCESS_CLASSES = {"public", "restricted", "confidential"}


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


@dataclass(frozen=True)
class ExchangePolicy:
    retention_until: str
    access_class: str = "restricted"
    evidence_location: str = "out_of_band"
    require_bundle_verification: bool = True
    require_revocation_check: bool = True
    require_audit_events: bool = True
    sensitive_payloads_prohibited: bool = True
    allowed_domains: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.access_class not in ACCESS_CLASSES:
            raise ValueError(f"unsupported access class: {self.access_class}")
        if self.evidence_location != "out_of_band":
            raise ValueError("institutional trust envelopes must reference evidence out of band")
        datetime.fromisoformat(self.retention_until.replace("Z", "+00:00"))

    def to_dict(self) -> dict[str, Any]:
        return {"retention_until": self.retention_until, "access_class": self.access_class, "evidence_location": self.evidence_location, "require_bundle_verification": self.require_bundle_verification, "require_revocation_check": self.require_revocation_check, "require_audit_events": self.require_audit_events, "sensitive_payloads_prohibited": self.sensitive_payloads_prohibited, "allowed_domains": list(self.allowed_domains)}


@dataclass(frozen=True)
class KeyRecord:
    key_id: str
    institution_id: str
    public_key: str
    status: str = "active"
    valid_from: str = "2026-01-01T00:00:00+00:00"
    valid_until: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"key_id": self.key_id, "institution_id": self.institution_id, "public_key": self.public_key, "status": self.status, "valid_from": self.valid_from, "valid_until": self.valid_until}


@dataclass
class InstitutionKeyRing:
    institution_id: str
    records: dict[str, KeyRecord] = field(default_factory=dict)

    def add_public_key(self, key_id: str, public_key: Ed25519PublicKey, valid_from: str = "2026-01-01T00:00:00+00:00") -> KeyRecord:
        record = KeyRecord(key_id, self.institution_id, _b64(public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)), "active", valid_from)
        self.records[key_id] = record
        return record

    def rotate(self, old_key_id: str, new_key_id: str, new_public_key: Ed25519PublicKey, effective_at: str) -> KeyRecord:
        old = self.records.get(old_key_id)
        if old is None:
            raise KeyError(old_key_id)
        self.records[old_key_id] = KeyRecord(old.key_id, old.institution_id, old.public_key, "retired", old.valid_from, effective_at)
        return self.add_public_key(new_key_id, new_public_key, effective_at)

    def get(self, key_id: str) -> KeyRecord:
        return self.records[key_id]

    def to_dict(self) -> dict[str, Any]:
        return {"institution_id": self.institution_id, "keys": [record.to_dict() for record in self.records.values()]}


@dataclass(frozen=True)
class ExchangePackage:
    exchange_version: str
    package_id: str
    sender_institution_id: str
    recipient_institution_id: str
    signer_key_id: str
    bundle_sha256: str
    bundle_locator: str
    policy: dict[str, Any]
    protocol_metadata: dict[str, Any]
    revocation_snapshot: dict[str, Any]
    audit_head: str | None
    signature: str

    def unsigned_dict(self) -> dict[str, Any]:
        return {"exchange_version": self.exchange_version, "package_id": self.package_id, "sender_institution_id": self.sender_institution_id, "recipient_institution_id": self.recipient_institution_id, "signer_key_id": self.signer_key_id, "bundle_sha256": self.bundle_sha256, "bundle_locator": self.bundle_locator, "policy": self.policy, "protocol_metadata": self.protocol_metadata, "revocation_snapshot": self.revocation_snapshot, "audit_head": self.audit_head}

    def to_dict(self) -> dict[str, Any]:
        data = self.unsigned_dict()
        data["signature"] = self.signature
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExchangePackage":
        return cls(data["exchange_version"], data["package_id"], data["sender_institution_id"], data["recipient_institution_id"], data["signer_key_id"], data["bundle_sha256"], data["bundle_locator"], data["policy"], data["protocol_metadata"], data.get("revocation_snapshot", {}), data.get("audit_head"), data["signature"])


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    actor_institution_id: str
    package_id: str
    timestamp: str
    previous_hash: str | None
    details: dict[str, Any]
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "event_type": self.event_type, "actor_institution_id": self.actor_institution_id, "package_id": self.package_id, "timestamp": self.timestamp, "previous_hash": self.previous_hash, "details": self.details, "event_hash": self.event_hash}


@dataclass
class AuditLog:
    events: list[AuditEvent] = field(default_factory=list)

    def append(self, event_type: str, actor_institution_id: str, package_id: str, details: dict[str, Any], timestamp: str = "2026-08-18T00:00:00+00:00") -> AuditEvent:
        previous_hash = self.events[-1].event_hash if self.events else None
        event_id = f"audit-{len(self.events) + 1:04d}"
        unsigned = {"event_id": event_id, "event_type": event_type, "actor_institution_id": actor_institution_id, "package_id": package_id, "timestamp": timestamp, "previous_hash": previous_hash, "details": details}
        event = AuditEvent(event_id, event_type, actor_institution_id, package_id, timestamp, previous_hash, details, hash_object(unsigned))
        self.events.append(event)
        return event

    @property
    def head(self) -> str | None:
        return self.events[-1].event_hash if self.events else None

    def verify(self) -> bool:
        previous = None
        for event in self.events:
            unsigned = {"event_id": event.event_id, "event_type": event.event_type, "actor_institution_id": event.actor_institution_id, "package_id": event.package_id, "timestamp": event.timestamp, "previous_hash": previous, "details": event.details}
            if event.previous_hash != previous or event.event_hash != hash_object(unsigned):
                return False
            previous = event.event_hash
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"events": [event.to_dict() for event in self.events], "head": self.head}


def create_exchange_package(bundle: dict[str, Any], sender_institution_id: str, recipient_institution_id: str, key_id: str, private_key: Ed25519PrivateKey, policy: ExchangePolicy, bundle_locator: str, revocation_snapshot: dict[str, Any] | None = None, audit_head: str | None = None, package_id: str = "exchange-0001") -> ExchangePackage:
    if policy.sensitive_payloads_prohibited and any("payload" in record for record in []):
        raise ValueError("sensitive payloads must remain outside the exchange envelope")
    unsigned = {"exchange_version": EXCHANGE_VERSION, "package_id": package_id, "sender_institution_id": sender_institution_id, "recipient_institution_id": recipient_institution_id, "signer_key_id": key_id, "bundle_sha256": hash_object(bundle), "bundle_locator": bundle_locator, "policy": policy.to_dict(), "protocol_metadata": {"bundle_type": bundle.get("bundle_type"), "bundle_version": bundle.get("bundle_version"), "protocol": "CEREVIA Evidence Interoperability v1.0"}, "revocation_snapshot": revocation_snapshot or {}, "audit_head": audit_head}
    signature = _b64(private_key.sign(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")))
    return ExchangePackage(EXCHANGE_VERSION, package_id, sender_institution_id, recipient_institution_id, key_id, unsigned["bundle_sha256"], bundle_locator, unsigned["policy"], unsigned["protocol_metadata"], unsigned["revocation_snapshot"], audit_head, signature)


def verify_exchange_package(package: ExchangePackage, bundle: dict[str, Any], key_ring: InstitutionKeyRing, recipient_institution_id: str, now: str = "2026-08-18T00:00:00+00:00", audit_log: AuditLog | None = None) -> dict[str, Any]:
    checks: list[str] = []
    failures: list[str] = []
    if package.exchange_version != EXCHANGE_VERSION:
        failures.append("unsupported exchange version")
    if package.recipient_institution_id != recipient_institution_id:
        failures.append("recipient institution mismatch")
    try:
        record = key_ring.get(package.signer_key_id)
    except KeyError:
        failures.append("unknown signer key")
        record = None
    if record is not None and record.institution_id != package.sender_institution_id:
        failures.append("signer institution mismatch")
    if record is not None and record.status != "active":
        failures.append("signer key is not active")
    public_key = Ed25519PublicKey.from_public_bytes(_unb64(record.public_key)) if record is not None else None
    try:
        if public_key is None:
            raise ValueError("no public key")
        public_key.verify(_unb64(package.signature), json.dumps(package.unsigned_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        checks.append("signature")
    except Exception:
        failures.append("signature invalid")
    if package.bundle_sha256 != hash_object(bundle):
        failures.append("bundle hash mismatch")
    else:
        checks.append("bundle_hash")
    policy = package.policy
    try:
        ExchangePolicy(**{key: policy[key] for key in ("retention_until", "access_class", "evidence_location", "require_bundle_verification", "require_revocation_check", "require_audit_events", "sensitive_payloads_prohibited", "allowed_domains")})
        checks.append("policy")
    except Exception as exc:
        failures.append(f"policy invalid: {exc}")
    retention = datetime.fromisoformat(policy["retention_until"].replace("Z", "+00:00"))
    if datetime.fromisoformat(now.replace("Z", "+00:00")) > retention:
        failures.append("retention expired")
    else:
        checks.append("retention")
    domain = bundle.get("specification", {}).get("domain")
    allowed_domains = policy.get("allowed_domains", [])
    if allowed_domains and domain not in allowed_domains:
        failures.append("bundle domain is not allowed by policy")
    else:
        checks.append("domain_policy")
    if policy.get("require_revocation_check"):
        if package.revocation_snapshot.get("status") != "checked":
            failures.append("revocation snapshot missing or unchecked")
        else:
            checks.append("revocation_snapshot")
    if policy.get("require_bundle_verification"):
        report = verify_bundle(bundle)
        if not report.verified:
            failures.extend(f"bundle verification: {failure}" for failure in report.failures)
        else:
            checks.append("bundle_verification")
    if policy.get("require_audit_events"):
        if audit_log is None or not audit_log.verify() or audit_log.head != package.audit_head:
            failures.append("audit history invalid or head mismatch")
        else:
            checks.append("audit_history")
    if policy.get("sensitive_payloads_prohibited") and "bundle" in package.to_dict():
        failures.append("inline bundle payload prohibited")
    return {"verified": not failures, "checks": checks, "failures": failures, "package_id": package.package_id, "sender_institution_id": package.sender_institution_id, "recipient_institution_id": package.recipient_institution_id}

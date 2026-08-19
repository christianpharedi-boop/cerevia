"""CEREVIA V1.1 Sentinel extensions above the frozen Evidence Core."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import copy
import json
from typing import Any, Callable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from cerevia.core.hashing import hash_object
from cerevia.graph.evidence import EvidenceGraph
from cerevia.verification.bundle import VerificationReport, verify_bundle


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class SentinelEvent:
    sequence: int
    event_type: str
    subject_id: str
    subject_hash: str
    timestamp: str
    details: dict[str, Any]
    previous_event_hash: str | None
    event_hash: str


class TransparencyLog:
    """Append-only hash-linked event log; it deliberately is not a blockchain."""
    def __init__(self, events: tuple[SentinelEvent, ...] = ()) -> None:
        self._events = tuple(events)

    @property
    def events(self) -> tuple[SentinelEvent, ...]:
        return self._events

    def append(self, event_type: str, subject_id: str, subject_hash: str,
               details: dict[str, Any] | None = None, timestamp: str | None = None) -> "TransparencyLog":
        previous = self._events[-1].event_hash if self._events else None
        event = {
            "sequence": len(self._events), "event_type": event_type, "subject_id": subject_id,
            "subject_hash": subject_hash, "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "details": details or {}, "previous_event_hash": previous,
        }
        event_hash = hash_object(event)
        record = SentinelEvent(**event, event_hash=event_hash)
        return TransparencyLog(self._events + (record,))

    def verify(self) -> bool:
        previous = None
        for index, event in enumerate(self._events):
            if event.sequence != index or event.previous_event_hash != previous:
                return False
            unsigned = {"sequence": event.sequence, "event_type": event.event_type,
                        "subject_id": event.subject_id, "subject_hash": event.subject_hash,
                        "timestamp": event.timestamp, "details": event.details,
                        "previous_event_hash": event.previous_event_hash}
            if event.event_hash != hash_object(unsigned):
                return False
            previous = event.event_hash
        return True

    def to_dict(self) -> dict[str, Any]:
        return {"log_type": "CEREVIA SENTINEL TRANSPARENCY LOG", "events": [event.__dict__ for event in self._events],
                "log_hash": hash_object([event.__dict__ for event in self._events])}


@dataclass(frozen=True)
class RevocationRecord:
    subject_id: str
    reason: str
    revoked_at: str
    affected_nodes: tuple[str, ...]
    status: str = "REVOKED"


class RevocationRegistry:
    def __init__(self, records: tuple[RevocationRecord, ...] = ()) -> None:
        self._records = tuple(records)

    @property
    def records(self) -> tuple[RevocationRecord, ...]:
        return self._records

    def revoke(self, subject_id: str, reason: str, graph: EvidenceGraph) -> tuple["RevocationRegistry", RevocationRecord]:
        if not subject_id or not reason.strip():
            raise ValueError("revocation requires subject_id and reason")
        affected = tuple(sorted(graph.invalidate(subject_id))) if subject_id in graph.nodes else (subject_id,)
        record = RevocationRecord(subject_id, reason, datetime.now(timezone.utc).isoformat(), affected)
        return RevocationRegistry(self._records + (record,)), record

    def status_for(self, node_id: str) -> str:
        return "AFFECTED / INVESTIGATE" if any(node_id in record.affected_nodes for record in self._records) else "ACTIVE"

    def to_dict(self) -> dict[str, Any]:
        return {"records": [record.__dict__ for record in self._records]}


@dataclass(frozen=True)
class SignedAttestation:
    attestation_id: str
    subject_bundle_hash: str
    verifier_id: str
    verifier_software: str
    specification_hash: str
    verification_result: str
    timestamp: str
    public_key_b64: str
    signature_b64: str

    def unsigned(self) -> dict[str, Any]:
        return {"attestation_id": self.attestation_id, "subject_bundle_hash": self.subject_bundle_hash,
                "verifier_id": self.verifier_id, "verifier_software": self.verifier_software,
                "specification_hash": self.specification_hash, "verification_result": self.verification_result,
                "timestamp": self.timestamp, "public_key_b64": self.public_key_b64}


def create_attestation(bundle_hash: str, verifier_id: str, specification_hash: str,
                       report: VerificationReport, private_key: Ed25519PrivateKey,
                       verifier_software: str = "cerevia-sentinel-1.1.0",
                       timestamp: str | None = None) -> SignedAttestation:
    public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    attestation_id = hash_object({"bundle_hash": bundle_hash, "verifier_id": verifier_id,
                                  "specification_hash": specification_hash, "result": report.verified})
    record = SignedAttestation(attestation_id, bundle_hash, verifier_id, verifier_software,
                               specification_hash, "VERIFIED" if report.verified else "INVESTIGATE",
                               timestamp or datetime.now(timezone.utc).isoformat(),
                               base64.b64encode(public_key).decode("ascii"), "")
    signature = private_key.sign(_canonical(record.unsigned()))
    return SignedAttestation(**{**record.__dict__, "signature_b64": base64.b64encode(signature).decode("ascii")})


def verify_attestation(attestation: SignedAttestation) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(attestation.public_key_b64))
        public_key.verify(base64.b64decode(attestation.signature_b64), _canonical(attestation.unsigned()))
        expected_id = hash_object({"bundle_hash": attestation.subject_bundle_hash, "verifier_id": attestation.verifier_id,
                                  "specification_hash": attestation.specification_hash,
                                  "result": attestation.verification_result == "VERIFIED"})
        return expected_id == attestation.attestation_id
    except Exception:
        return False


def verify_sentinel_payload(bundle: dict[str, Any], sentinel: dict[str, Any], bundle_report: VerificationReport) -> dict[str, Any]:
    """Return server-derived Sentinel status without trusting client flags.

    Sentinel result files may contain useful client-reported summaries, but the
    API must never present those summaries as independently verified facts.
    This helper verifies the signed attestation, binds it to this bundle and
    specification, and verifies the hash-linked transparency log.
    """
    client_reported = {
        key: copy.deepcopy(sentinel[key])
        for key in ("sentinel_status", "attestation_verified", "transparency_log_verified", "original_verification")
        if key in sentinel
    }
    attestation_verified = False
    attestation_binding_verified = False
    attestation_data = sentinel.get("attestation")
    if isinstance(attestation_data, dict):
        try:
            attestation = SignedAttestation(**copy.deepcopy(attestation_data))
            attestation_verified = verify_attestation(attestation)
            attestation_binding_verified = (
                attestation.subject_bundle_hash == hash_object(bundle)
                and attestation.specification_hash == bundle.get("specification_hash")
                and attestation.verification_result == ("VERIFIED" if bundle_report.verified else "INVESTIGATE")
            )
        except (TypeError, ValueError):
            pass

    transparency_log_verified = False
    log_data = sentinel.get("transparency_log")
    if isinstance(log_data, dict) and isinstance(log_data.get("events"), list):
        try:
            events = tuple(SentinelEvent(**copy.deepcopy(item)) for item in log_data["events"])
            log = TransparencyLog(events)
            transparency_log_verified = log.verify() and log_data.get("log_hash") == hash_object([event.__dict__ for event in events])
        except (TypeError, ValueError):
            pass

    server_verified = {
        "bundle_verified": bundle_report.verified,
        "attestation_verified": attestation_verified and attestation_binding_verified,
        "transparency_log_verified": transparency_log_verified,
    }
    server_verified["sentinel_verified"] = all(server_verified.values())
    return {"client_reported": client_reported, "server_verified": server_verified}


@dataclass(frozen=True)
class AttackResult:
    attack: str
    detected: bool
    failures: tuple[str, ...]


@dataclass(frozen=True)
class SentinelReport:
    status: str
    original: VerificationReport
    attacks: tuple[AttackResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "original": self.original.to_dict(),
                "attacks": [{"attack": item.attack, "detected": item.detected, "failures": list(item.failures)} for item in self.attacks]}


def _attack_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][0]["payload"] = {"tampered": True}
    return target


def _attack_metadata(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][0]["metadata"]["tampered"] = True
    return target


def _attack_parent(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][-1]["provenance"]["parent_artifacts"] = []
    return target


def _attack_substitute(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][1]["artifact_id"] = "substituted-artifact"
    return target


def _attack_remove_ancestor(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"] = target["artifacts"][1:]
    return target


def _attack_parameters(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][1]["provenance"]["parameters"]["tampered"] = True
    return target


def _attack_environment(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["artifacts"][1]["provenance"]["environment"]["os"] = "tampered"
    return target


def _attack_claim(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    claim = next(record for record in target["artifacts"] if record["kind"] == "claim")
    claim["payload"]["statement"] = "forged claim"
    return target


def _attack_uncertainty(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    claim = next(record for record in target["artifacts"] if record["kind"] == "claim")
    claim["payload"]["uncertainty"] = {"type": "fabricated_certainty"}
    return target


def _attack_graph(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["manifest"]["evidence_graph"]["nodes"] = []
    return target


def _attack_stale_execution(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["execution_identity"] = "0" * 64
    return target


def _attack_specification(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target["specification"]["method"] = "forged-method"
    return target


def _attack_partial(bundle: dict[str, Any]) -> dict[str, Any]:
    target = copy.deepcopy(bundle)
    target.pop("artifacts", None)
    return target


_ATTACKS: tuple[tuple[str, Callable[[dict[str, Any]], dict[str, Any]]], ...] = (
    ("modified_source_payload", _attack_payload), ("altered_metadata", _attack_metadata),
    ("altered_parent", _attack_parent), ("substituted_artifact", _attack_substitute),
    ("removed_ancestor", _attack_remove_ancestor), ("altered_analysis_parameters", _attack_parameters),
    ("changed_environment", _attack_environment), ("altered_claim", _attack_claim),
    ("altered_uncertainty", _attack_uncertainty), ("graph_manipulation", _attack_graph),
    ("stale_execution_identity", _attack_stale_execution), ("mismatched_specification", _attack_specification),
    ("partial_bundle", _attack_partial),
)


def run_attack_suite(bundle: dict[str, Any]) -> SentinelReport:
    original = verify_bundle(bundle)
    results: list[AttackResult] = []
    for name, attack in _ATTACKS:
        try:
            report = verify_bundle(attack(bundle))
            results.append(AttackResult(name, not report.verified, report.failures))
        except Exception as exc:
            results.append(AttackResult(name, True, (str(exc),)))
    status = "VERIFIED" if original.verified and all(item.detected for item in results) else "INVESTIGATE"
    return SentinelReport(status, original, tuple(results))

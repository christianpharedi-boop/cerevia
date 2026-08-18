"""V2.2 External Institutional Pilot kit.

This module prepares a blind exchange; it does not claim that an external
institution has participated. The comparison surface is intentionally small,
explicit, and machine-readable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cerevia.core.hashing import hash_object
from cerevia.institutional.exchange import AuditLog, ExchangePackage, InstitutionKeyRing, verify_exchange_package
from cerevia.observatory import ObservatorySnapshot
from cerevia.verification.bundle import verify_bundle


@dataclass(frozen=True)
class PilotScenario:
    scenario_id: str
    description: str
    package: ExchangePackage
    expected_authentic: bool
    expected_failure_class: str | None = None


@dataclass(frozen=True)
class BlindExchangeAnswer:
    scenario_id: str
    package_authentic: bool
    bundle_verified: bool
    lineage_node_ids: tuple[str, ...]
    claim_statement: str | None
    uncertainty: dict[str, Any]
    historical_event_count: int
    revoked_source_ids: tuple[str, ...]
    affected_finding_ids: tuple[str, ...]
    unaffected_finding_ids: tuple[str, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"scenario_id": self.scenario_id, "package_authentic": self.package_authentic, "bundle_verified": self.bundle_verified, "lineage_node_ids": list(self.lineage_node_ids), "claim_statement": self.claim_statement, "uncertainty": self.uncertainty, "historical_event_count": self.historical_event_count, "revoked_source_ids": list(self.revoked_source_ids), "affected_finding_ids": list(self.affected_finding_ids), "unaffected_finding_ids": list(self.unaffected_finding_ids), "failures": list(self.failures)}


@dataclass(frozen=True)
class AgreementReport:
    fields: tuple[str, ...]
    disagreements: dict[str, dict[str, Any]]

    @property
    def agreement(self) -> bool:
        return not self.disagreements

    def to_dict(self) -> dict[str, Any]:
        return {"agreement": self.agreement, "fields": list(self.fields), "disagreements": self.disagreements}


def extract_exchange_answer(scenario_id: str, package: ExchangePackage, bundle: dict[str, Any], key_ring: InstitutionKeyRing, recipient_institution_id: str, audit_log: AuditLog, revoked_source_ids: tuple[str, ...] = (), now: str = "2026-08-18T00:00:00+00:00") -> BlindExchangeAnswer:
    exchange = verify_exchange_package(package, bundle, key_ring, recipient_institution_id, now=now, audit_log=audit_log)
    bundle_report = verify_bundle(bundle)
    snapshot = ObservatorySnapshot.from_bundle(bundle)
    finding_id = bundle.get("manifest", {}).get("final_finding_id")
    finding = snapshot.get_finding(finding_id) if finding_id else None
    lineage = snapshot.get_lineage(finding_id) if finding_id else {"node_ids": []}
    history = snapshot.get_history(as_of=now)
    affected: set[str] = set()
    for source_id in revoked_source_ids:
        affected.update(snapshot.impact_of(source_id).get("affected_finding_ids", []))
    all_findings = {node["node_id"] for node in bundle.get("manifest", {}).get("evidence_graph", {}).get("nodes", []) if node.get("node_type") == "Finding"}
    return BlindExchangeAnswer(scenario_id, exchange["verified"], bundle_report.verified, tuple(lineage.get("node_ids", [])), finding.get("payload", {}).get("statement") if finding else None, finding.get("payload", {}).get("uncertainty", {}) if finding else {}, len(history.get("events", [])), tuple(sorted(revoked_source_ids)), tuple(sorted(affected)), tuple(sorted(all_findings - affected)), tuple(exchange.get("failures", ())))


def mutate_exchange_package(package: ExchangePackage, scenario_id: str) -> PilotScenario:
    data = package.to_dict()
    if scenario_id == "altered_bundle_hash":
        data["bundle_sha256"] = "0" * 64
        return PilotScenario(scenario_id, "Alter the declared bundle hash without resigning the envelope.", ExchangePackage.from_dict(data), False, "bundle_hash_or_signature")
    if scenario_id == "stale_revocation":
        data["revocation_snapshot"] = {"status": "unchecked", "checked_at": "2020-01-01T00:00:00+00:00"}
        return PilotScenario(scenario_id, "Replace the sender revocation snapshot with stale unchecked state.", ExchangePackage.from_dict(data), False, "signature_or_revocation")
    if scenario_id == "wrong_recipient":
        data["recipient_institution_id"] = "institution-c"
        return PilotScenario(scenario_id, "Redirect the signed package to an unlisted recipient.", ExchangePackage.from_dict(data), False, "signature_or_recipient")
    raise ValueError(f"unknown pilot scenario: {scenario_id}")


def compare_answers(left: BlindExchangeAnswer, right: BlindExchangeAnswer) -> AgreementReport:
    fields = ("package_authentic", "bundle_verified", "lineage_node_ids", "claim_statement", "uncertainty", "historical_event_count", "revoked_source_ids", "affected_finding_ids", "unaffected_finding_ids", "failures")
    disagreements: dict[str, dict[str, Any]] = {}
    for field in fields:
        left_value = getattr(left, field)
        right_value = getattr(right, field)
        if left_value != right_value:
            disagreements[field] = {"left": left_value, "right": right_value}
    return AgreementReport(fields, disagreements)

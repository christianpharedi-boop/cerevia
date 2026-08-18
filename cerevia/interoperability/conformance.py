"""Reusable CEREVIA V1.6 interoperability conformance checks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cerevia.core.hashing import hash_object
from cerevia.interoperability.cross_domain import impact_after_revocation
from cerevia.interoperability.profile import EvidenceInteroperabilityProfile
from cerevia.observatory import ObservatorySnapshot
from cerevia.verification.bundle import verify_bundle


@dataclass(frozen=True)
class ConformanceResult:
    profile: str
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    @property
    def conformant(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, Any]:
        return {"profile": self.profile, "conformant": self.conformant, "checks": list(self.checks), "failures": list(self.failures)}


def validate_profile(profile: EvidenceInteroperabilityProfile, bundle: dict[str, Any]) -> ConformanceResult:
    checks: list[str] = []
    failures: list[str] = []
    records = {record.get("artifact_id"): record for record in bundle.get("artifacts", [])}
    if profile.source_artifact_id not in records:
        failures.append("source artifact is absent from bundle")
    else:
        checks.append("evidence_contract:source_identity")
    final = records.get(profile.final_finding_id)
    if final is None or final.get("kind") != "finding":
        failures.append("profile final finding is absent or not a finding")
    else:
        checks.append("claim_contract:finding_role")
    declared_kinds = {record.get("kind") for record in records.values()}
    if not declared_kinds.issubset(set(profile.supported_artifact_types) | {"analysis", "multimodal_inference", "claim", "finding"}):
        failures.append("bundle contains an undeclared artifact type")
    else:
        checks.append("evidence_contract:artifact_types")
    report = verify_bundle(bundle)
    if not report.verified:
        failures.extend(f"serialized_verification:{failure}" for failure in report.failures)
    else:
        checks.append("verification_contract:independent_bundle")
    if final:
        claim = records.get(final.get("payload", {}).get("analysis_id"))
        if claim and claim.get("kind") == "claim":
            payload = claim.get("payload", {})
            required = {"evidence", "inference_id", "hypothesis", "statement", "assumptions", "uncertainty", "method", "experimental_context", "claim_status"}
            missing = sorted(required - set(payload))
            if missing:
                failures.append(f"claim_contract:missing:{','.join(missing)}")
            else:
                checks.append("claim_contract:required_fields")
        else:
            failures.append("claim_contract:claim_reference")
    manifest = bundle.get("manifest", {})
    if manifest.get("evidence_graph_hash") != hash_object(manifest.get("evidence_graph")):
        failures.append("lineage_contract:graph_hash")
    else:
        checks.append("lineage_contract:graph_hash")
    snapshot = ObservatorySnapshot.from_bundle(bundle)
    if profile.final_finding_id not in snapshot.get_lineage().get("node_ids", []):
        failures.append("lineage_contract:final_finding_lineage")
    else:
        checks.append("lineage_contract:observable_lineage")
    impact = impact_after_revocation(bundle, profile.source_artifact_id)
    if profile.final_finding_id not in impact["impact"]["affected_finding_ids"]:
        failures.append("invalidation_contract:final_finding_not_affected")
    else:
        checks.append("invalidation_contract:downstream_impact")
    return ConformanceResult(profile.domain, tuple(checks), tuple(failures))


def validate_cross_domain_composition(bundle: dict[str, Any], profiles: dict[str, EvidenceInteroperabilityProfile]) -> ConformanceResult:
    checks: list[str] = []
    failures: list[str] = []
    report = verify_bundle(bundle)
    if not report.verified:
        failures.extend(f"serialized_verification:{failure}" for failure in report.failures)
    else:
        checks.append("cross_domain:serialized_verification")
    domain_evidence = bundle.get("specification", {}).get("domain_evidence", {})
    if set(domain_evidence) != set(profiles):
        failures.append("cross_domain:domain_evidence_profile_mismatch")
    else:
        checks.append("cross_domain:per_domain_evidence")
    final_id = bundle.get("manifest", {}).get("final_finding_id")
    for domain, profile in profiles.items():
        impact = impact_after_revocation(bundle, profile.source_artifact_id)["impact"]
        if final_id not in impact["affected_finding_ids"]:
            failures.append(f"cross_domain:{domain}:final_finding_not_affected")
        else:
            checks.append(f"invalidation:{domain}:cross_finding")
        for other_domain, other_profile in profiles.items():
            if other_domain != domain and other_profile.final_finding_id in impact["affected_finding_ids"]:
                failures.append(f"invalidation:{domain}:unrelated_{other_domain}_finding_affected")
        if all(other_profile.final_finding_id not in impact["affected_finding_ids"] for other_domain, other_profile in profiles.items() if other_domain != domain):
            checks.append(f"invalidation:{domain}:unrelated_findings_preserved")
    return ConformanceResult("cross-domain", tuple(checks), tuple(failures))


def validate_profiles(profiles: dict[str, EvidenceInteroperabilityProfile], bundles: dict[str, dict[str, Any]]) -> dict[str, ConformanceResult]:
    if set(profiles) != set(bundles):
        raise ValueError("profiles and bundles must cover the same domains")
    return {domain: validate_profile(profiles[domain], bundles[domain]) for domain in sorted(profiles)}

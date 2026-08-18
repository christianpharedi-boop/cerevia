"""CEREVIA V1.0 self-contained evidence-to-claim verification."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import hash_object
from cerevia.core.provenance import Artifact
from cerevia.pipeline import verify_manifest


@dataclass(frozen=True)
class VerificationReport:
    verified: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    final_finding_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"verified": self.verified, "checks": list(self.checks),
                "failures": list(self.failures), "final_finding_id": self.final_finding_id}


def build_bundle(manifest: dict[str, Any], specification: dict[str, Any],
                 specification_hash: str, catalog: ArtifactCatalog) -> dict[str, Any]:
    artifacts = [artifact.to_dict(include_payload=True) for artifact in catalog.all()]
    return {"bundle_type": "CEREVIA INDEPENDENT VERIFICATION BUNDLE",
            "bundle_version": "1.0.0", "manifest": manifest,
            "specification": specification, "specification_hash": specification_hash,
            "artifacts": artifacts}


def write_bundle(bundle: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")


def _verify_artifact_records(records: list[dict[str, Any]]) -> tuple[list[str], list[str], dict[str, dict[str, Any]]]:
    checks: list[str] = []
    failures: list[str] = []
    by_id = {record.get("artifact_id"): record for record in records}
    if len(by_id) != len(records):
        failures.append("artifact IDs are not unique")
    for record in records:
        artifact_id = record.get("artifact_id")
        provenance = record.get("provenance", {})
        parent_refs = []
        for parent_id in provenance.get("parent_artifacts", []):
            parent = by_id.get(parent_id)
            if parent is None:
                failures.append(f"{artifact_id}: missing parent {parent_id}")
            else:
                parent_refs.append({"artifact_id": parent_id, "content_hash": parent.get("provenance", {}).get("content_hash")})
        expected = hash_object({"artifact_id": artifact_id, "kind": record.get("kind"),
                                "payload": record.get("payload"), "metadata": record.get("metadata"),
                                "operation": provenance.get("operation"),
                                "parameters": provenance.get("parameters", {}),
                                "software_version": provenance.get("software_version"),
                                "environment": provenance.get("environment", {}),
                                "parents": parent_refs})
        if expected != provenance.get("content_hash"):
            failures.append(f"{artifact_id}: content identity mismatch")
        else:
            checks.append(f"artifact:{artifact_id}:content_hash")
    return checks, failures, by_id


def verify_bundle(bundle: dict[str, Any]) -> VerificationReport:
    checks: list[str] = []
    failures: list[str] = []
    if bundle.get("bundle_type") != "CEREVIA INDEPENDENT VERIFICATION BUNDLE":
        failures.append("invalid bundle type")
    manifest = bundle.get("manifest", {})
    supplied_manifest_hash = manifest.get("manifest_hash")
    unsigned_manifest = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    if supplied_manifest_hash != hash_object(unsigned_manifest):
        failures.append("manifest hash mismatch")
    else:
        checks.append("manifest_hash")
    specification = bundle.get("specification", {})
    if bundle.get("specification_hash") != hash_object(specification):
        failures.append("specification hash mismatch")
    else:
        checks.append("specification_hash")
    records = bundle.get("artifacts", [])
    artifact_checks, artifact_failures, by_id = _verify_artifact_records(records)
    checks.extend(artifact_checks)
    failures.extend(artifact_failures)
    chain_ids = manifest.get("provenance_chain", [])
    if manifest.get("artifact_count") != len(chain_ids):
        failures.append("manifest artifact count mismatch")
    if any(artifact_id not in by_id for artifact_id in chain_ids):
        failures.append("manifest references an artifact absent from bundle")
    final_id = manifest.get("final_finding_id")
    final = by_id.get(final_id)
    if final is None or final.get("kind") != "finding":
        failures.append("final artifact is not a finding")
    else:
        checks.append("finding_role")
        if final.get("provenance", {}).get("content_hash") != manifest.get("content_hash"):
            failures.append("manifest final content hash mismatch")
        finding_payload = final.get("payload", {})
        claim_id = finding_payload.get("analysis_id")
        claim = by_id.get(claim_id)
        if claim is None or claim.get("kind") != "claim":
            failures.append("finding does not reference a claim artifact")
        else:
            checks.append("claim_role")
            claim_payload = claim.get("payload", {})
            inference_id = claim_payload.get("inference_id")
            inference = by_id.get(inference_id)
            if inference is None or inference.get("kind") != "multimodal_inference":
                failures.append("claim does not reference a multimodal inference")
            else:
                checks.append("inference_role")
            for evidence_id, evidence_hash in zip(claim_payload.get("evidence", []), claim_payload.get("evidence_content_hashes", [])):
                evidence = by_id.get(evidence_id)
                if evidence is None or evidence.get("provenance", {}).get("content_hash") != evidence_hash:
                    failures.append(f"claim evidence mismatch: {evidence_id}")
            uncertainty = claim_payload.get("uncertainty", {})
            if not uncertainty.get("type"):
                failures.append("claim uncertainty declaration missing")
            else:
                checks.append("claim_uncertainty")
            if claim_payload.get("claim_status") not in {"QUALIFIED", "PROVISIONAL"}:
                failures.append("claim status is not qualified or provisional")
    graph = manifest.get("evidence_graph")
    if manifest.get("evidence_graph_hash") != hash_object(graph):
        failures.append("evidence graph hash mismatch")
    else:
        checks.append("evidence_graph_hash")
    return VerificationReport(not failures, tuple(checks), tuple(failures), final_id)


def verify_bundle_file(path: str | Path) -> VerificationReport:
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    return verify_bundle(bundle)

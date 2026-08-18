"""Protocol API: a thin HTTP surface over CEREVIA’s frozen contracts."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from cerevia.observatory import ObservatorySnapshot
from cerevia.verification.bundle import verify_bundle


class VerifyRequest(BaseModel):
    bundle: dict[str, Any]
    sentinel: dict[str, Any] | None = None


class ImpactRequest(BaseModel):
    artifact_id: str = Field(min_length=1)


class ReadOnlyStore:
    """Loads configured artifacts per request; it never writes or mutates evidence."""

    def __init__(self, bundle_path: str | Path | None = None, sentinel_path: str | Path | None = None) -> None:
        self.bundle_path = Path(bundle_path) if bundle_path else None
        self.sentinel_path = Path(sentinel_path) if sentinel_path else None

    def snapshot(self) -> ObservatorySnapshot:
        if self.bundle_path is None:
            raise HTTPException(status_code=503, detail="No configured read-only bundle. Set CEREVIA_BUNDLE_PATH.")
        if not self.bundle_path.exists():
            raise HTTPException(status_code=503, detail="Configured bundle path does not exist.")
        try:
            return ObservatorySnapshot.from_files(self.bundle_path, self.sentinel_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=422, detail=f"Unable to load configured protocol artifacts: {exc}") from exc


def _snapshot_or_404(store: ReadOnlyStore, finding_id: str | None = None) -> ObservatorySnapshot:
    snapshot = store.snapshot()
    if finding_id and finding_id not in snapshot._graph.nodes:  # read-only existence check
        raise HTTPException(status_code=404, detail=f"Unknown artifact or finding: {finding_id}")
    return snapshot


def _query(callable_, *args, **kwargs):
    try:
        return callable_(*args, **kwargs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown protocol object: {exc.args[0] if exc.args else exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def create_app(store: ReadOnlyStore | None = None) -> FastAPI:
    read_store = store or ReadOnlyStore(os.getenv("CEREVIA_BUNDLE_PATH"), os.getenv("CEREVIA_SENTINEL_PATH"))
    api = FastAPI(title="CEREVIA Protocol API", version="2.3.0", description="Read-mostly HTTP interface over Evidence Core, Sentinel, and Observatory. It does not store or rewrite scientific evidence.")

    @api.get("/health")
    def health() -> dict[str, Any]:
        return {"service": "cerevia-protocol-api", "status": "ready", "storage": "read_only_out_of_band", "institutional_exchange_api": "separate_future_boundary"}

    @api.post("/verify")
    @api.post("/verify/bundle")
    def verify(request: VerifyRequest) -> dict[str, Any]:
        report = verify_bundle(request.bundle).to_dict()
        if request.sentinel:
            report["sentinel_status"] = request.sentinel.get("sentinel_status")
            report["attestation_verified"] = request.sentinel.get("attestation_verified")
            report["transparency_log_verified"] = request.sentinel.get("transparency_log_verified")
        return report

    @api.get("/findings/{finding_id}")
    def finding(finding_id: str) -> dict[str, Any]:
        snapshot = _snapshot_or_404(read_store, finding_id)
        return _query(snapshot.get_finding, finding_id)

    @api.get("/findings/{finding_id}/lineage")
    def finding_lineage(finding_id: str) -> dict[str, Any]:
        snapshot = _snapshot_or_404(read_store, finding_id)
        return _query(snapshot.get_lineage, finding_id)

    @api.get("/findings/{finding_id}/evidence")
    def finding_evidence(finding_id: str) -> dict[str, Any]:
        snapshot = _snapshot_or_404(read_store, finding_id)
        return _query(snapshot.get_supporting_evidence, finding_id)

    @api.get("/findings/{finding_id}/verification")
    def finding_verification(finding_id: str) -> dict[str, Any]:
        snapshot = _snapshot_or_404(read_store, finding_id)
        _query(snapshot.get_finding, finding_id)
        return snapshot.get_verification()

    @api.get("/findings/{finding_id}/history")
    def finding_history(finding_id: str, as_of: str | None = Query(default=None)) -> dict[str, Any]:
        snapshot = _snapshot_or_404(read_store, finding_id)
        return _query(snapshot.get_history, finding_id, as_of)

    @api.post("/impact")
    def impact(request: ImpactRequest) -> dict[str, Any]:
        snapshot = read_store.snapshot()
        return _query(snapshot.impact_of, request.artifact_id)

    @api.get("/revocations")
    def revocations(subject_id: str | None = Query(default=None)) -> list[dict[str, Any]]:
        snapshot = read_store.snapshot()
        return snapshot.get_revocations(subject_id)

    @api.get("/attestations")
    def attestations(subject_id: str | None = Query(default=None)) -> list[dict[str, Any]]:
        snapshot = read_store.snapshot()
        return snapshot.get_attestations(subject_id)

    return api


app = create_app()

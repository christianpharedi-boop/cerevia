"""CEREVIA V0.1 end-to-end scientific evidence pipeline."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
from cerevia.acquisition.eeg import EEGObservation, ingest_eeg
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.provenance import Artifact
from cerevia.core.hashing import canonical_json, hash_object


class QualityGateError(ValueError):
    """Raised after a failed QC artifact has been preserved in history."""
    def __init__(self, message: str, catalog: ArtifactCatalog, qc_artifact: Artifact):
        super().__init__(message)
        self.catalog = catalog
        self.qc_artifact = qc_artifact


@dataclass(frozen=True)
class QualityReport:
    passed: bool
    checks: dict[str, Any]
    errors: tuple[str, ...] = ()


def qc_eeg(raw: Artifact, artifact_id: str) -> tuple[Artifact, QualityReport]:
    payload = raw.payload
    data = np.asarray(payload["data"], dtype=float)
    errors: list[str] = []
    checks = {"finite": bool(np.isfinite(data).all()), "channels": int(data.shape[0]), "samples": int(data.shape[1]),
              "sampling_rate_hz": payload["sampling_rate_hz"]}
    if not checks["finite"]:
        errors.append("non-finite EEG sample detected")
    if data.shape[0] < 1 or data.shape[1] < 4:
        errors.append("EEG must contain at least one channel and four samples")
    report = QualityReport(not errors, checks, tuple(errors))
    artifact = Artifact.derive(artifact_id, "qc_report", {"passed": report.passed, "checks": checks, "errors": list(report.errors)},
                               {"quality_gate": True}, "quality_control", (raw,), {"policy": "finite_samples_and_minimum_shape"})
    return artifact, report


def filter_eeg(raw: Artifact, artifact_id: str, low_hz: float = 1.0, high_hz: float = 40.0, qc: Artifact | None = None) -> Artifact:
    data = np.asarray(raw.payload["data"], dtype=float)
    fs = float(raw.payload["sampling_rate_hz"])
    if not 0 < low_hz < high_hz < fs / 2:
        raise ValueError("filter band must satisfy 0 < low < high < Nyquist")
    freqs = np.fft.rfftfreq(data.shape[1], 1.0 / fs)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    filtered = np.fft.irfft(np.fft.rfft(data, axis=1) * mask[None, :], n=data.shape[1], axis=1)
    payload = dict(raw.payload)
    payload["data"] = filtered.tolist()
    return Artifact.derive(artifact_id, "filtered_eeg", payload, {"filter": "ideal_fft_bandpass", "low_hz": low_hz, "high_hz": high_hz},
                           "filter_eeg", (raw,) if qc is None else (raw, qc), {"low_hz": low_hz, "high_hz": high_hz})


def epoch_eeg(filtered: Artifact, artifact_id: str, epoch_seconds: float = 1.0) -> Artifact:
    data = np.asarray(filtered.payload["data"], dtype=float)
    fs = float(filtered.payload["sampling_rate_hz"])
    width = int(round(epoch_seconds * fs))
    if width <= 0 or data.shape[1] < width:
        raise ValueError("epoch width exceeds available samples")
    count = data.shape[1] // width
    epochs = data[:, :count * width].reshape(data.shape[0], count, width).transpose(1, 0, 2)
    return Artifact.derive(artifact_id, "eeg_epochs", epochs.tolist(), {"epoch_seconds": epoch_seconds, "sampling_rate_hz": fs,
                                                                        "epoch_count": count, "channel_names": filtered.payload["channel_names"]},
                           "epoch_eeg", (filtered,), {"epoch_seconds": epoch_seconds})


def spectral_power(epochs: Artifact, artifact_id: str, band: tuple[float, float] = (8.0, 12.0)) -> Artifact:
    values = np.asarray(epochs.payload, dtype=float)
    fs = float(epochs.metadata["sampling_rate_hz"])
    freqs = np.fft.rfftfreq(values.shape[-1], 1.0 / fs)
    psd = np.abs(np.fft.rfft(values, axis=-1)) ** 2 / values.shape[-1]
    selected = (freqs >= band[0]) & (freqs <= band[1])
    power = psd[..., selected].mean(axis=-1)
    return Artifact.derive(artifact_id, "spectral_power", power.tolist(), {"band_hz": list(band), "metric": "mean_fft_power",
                                                                            "channel_names": epochs.metadata["channel_names"], "epoch_count": values.shape[0]},
                           "extract_spectral_power", (epochs,), {"band_hz": list(band)})


def statistical_analysis(feature: Artifact, artifact_id: str, null_value: float = 0.0) -> Artifact:
    values = np.asarray(feature.payload, dtype=float)
    flat = values.ravel()
    mean = float(flat.mean())
    std = float(flat.std(ddof=1)) if flat.size > 1 else 0.0
    se = std / np.sqrt(flat.size) if flat.size else float("nan")
    t = (mean - null_value) / se if se > 0 else float("inf") if mean != null_value else 0.0
    result = {"estimand": "mean_band_power_minus_null", "mean": mean, "null_value": null_value, "std": std,
              "standard_error": float(se), "t_statistic": float(t), "n": int(flat.size)}
    return Artifact.derive(artifact_id, "analysis", result, {"analysis_type": "one_sample_descriptive_t_statistic"},
                           "statistical_analysis", (feature,), {"null_value": null_value})


def finding(analysis: Artifact, evidence: tuple[Artifact, ...], artifact_id: str, statement: str) -> Artifact:
    if not evidence:
        raise ValueError("findings require at least one evidence artifact")
    result = {"finding_id": artifact_id, "statement": statement, "evidence": [a.artifact_id for a in evidence],
              "analysis_id": analysis.artifact_id, "statistical_result": analysis.payload, "status": "PROVISIONAL"}
    return Artifact.derive(artifact_id, "finding", result, {"status": "PROVISIONAL", "evidence_count": len(evidence)},
                           "record_finding", (analysis,) + evidence, {"claim_policy": "computation_does_not_auto_convert_to_truth"})


def evidence_manifest(study_id: str, final: Artifact, catalog: ArtifactCatalog) -> dict[str, Any]:
    chain = catalog.lineage(final.artifact_id)
    manifest = {"manifest_type": "CEREVIA EVIDENCE MANIFEST", "manifest_version": "0.1.1", "study_id": study_id,
                "final_finding_id": final.artifact_id, "artifacts": [a.to_dict(include_payload=False) for a in chain],
                "provenance_chain": [a.artifact_id for a in chain], "content_hash": final.provenance.content_hash}
    manifest["manifest_hash"] = hash_object(manifest)
    return manifest


def verify_manifest(manifest: dict[str, Any]) -> bool:
    supplied = manifest.get("manifest_hash")
    if not supplied:
        return False
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    return supplied == hash_object(unsigned)


def run_pipeline(observation: EEGObservation) -> tuple[ArtifactCatalog, Artifact, dict[str, Any]]:
    catalog = ArtifactCatalog()
    raw = catalog.add(ingest_eeg("raw-eeg-001", observation, "demo-001", "sub-001", "ses-01"))
    qc, report = qc_eeg(raw, "qc-001")
    catalog.add(qc)
    if not report.passed:
        raise QualityGateError(f"quality gate failed: {report.errors}", catalog, qc)
    filtered = catalog.add(filter_eeg(raw, "filter-001", qc=qc))
    epochs = catalog.add(epoch_eeg(filtered, "epoch-001"))
    feature = catalog.add(spectral_power(epochs, "alpha-power-001"))
    analysis = catalog.add(statistical_analysis(feature, "analysis-001"))
    final = catalog.add(finding(analysis, (raw, qc, filtered, epochs, feature), "finding-001",
                                "The synthetic EEG contains measurable 8–12 Hz band power under the stated preprocessing and analysis contract."))
    return catalog, final, evidence_manifest("demo-001", final, catalog)

"""CEREVIA V0.4 executable analysis specifications and rerun verification."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.environment import fingerprint
from cerevia.core.hashing import freeze, hash_object, thaw
from cerevia.core.provenance import Artifact
from cerevia.pipeline import epoch_eeg, filter_eeg, finding, qc_eeg, spectral_power, statistical_analysis


@dataclass(frozen=True)
class AnalysisSpecification:
    input_artifacts: tuple[dict[str, str], ...]
    preprocessing_pipeline: tuple[dict[str, Any], ...]
    feature_definition: dict[str, Any]
    statistical_method: str
    parameters: dict[str, Any]
    software_environment: dict[str, str]
    expected_outputs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.input_artifacts:
            raise ValueError("AnalysisSpecification requires input_artifacts")
        if not self.preprocessing_pipeline:
            raise ValueError("AnalysisSpecification requires preprocessing_pipeline")
        if not self.statistical_method.strip():
            raise ValueError("AnalysisSpecification requires statistical_method")
        if not self.expected_outputs:
            raise ValueError("AnalysisSpecification requires expected_outputs")
        object.__setattr__(self, "input_artifacts", tuple(freeze(item) for item in self.input_artifacts))
        object.__setattr__(self, "preprocessing_pipeline", tuple(freeze(item) for item in self.preprocessing_pipeline))
        object.__setattr__(self, "feature_definition", freeze(self.feature_definition))
        object.__setattr__(self, "parameters", freeze(self.parameters))
        object.__setattr__(self, "software_environment", freeze(self.software_environment))
        object.__setattr__(self, "expected_outputs", tuple(self.expected_outputs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_artifacts": thaw(self.input_artifacts),
            "preprocessing_pipeline": thaw(self.preprocessing_pipeline),
            "feature_definition": thaw(self.feature_definition),
            "statistical_method": self.statistical_method,
            "parameters": thaw(self.parameters),
            "software_environment": thaw(self.software_environment),
            "expected_outputs": list(self.expected_outputs),
        }

    @property
    def specification_hash(self) -> str:
        return hash_object(self.to_dict())

    @classmethod
    def for_eeg(cls, raw: Artifact, project_root: str | None = None) -> "AnalysisSpecification":
        environment = fingerprint(project_root)
        artifact_ids = {
            "qc": "repro-qc-001",
            "filter": "repro-filter-001",
            "epoch": "repro-epoch-001",
            "feature": "repro-alpha-power-001",
            "analysis": "repro-analysis-001",
            "finding": "repro-finding-001",
        }
        return cls(
            input_artifacts=({"artifact_id": raw.artifact_id, "content_hash": raw.provenance.content_hash},),
            preprocessing_pipeline=(
                {"operation": "quality_control", "policy": "finite_samples_and_minimum_shape"},
                {"operation": "filter_eeg", "low_hz": 1.0, "high_hz": 40.0},
                {"operation": "epoch_eeg", "epoch_seconds": 1.0},
            ),
            feature_definition={"operation": "spectral_power", "name": "alpha_power", "band_hz": [8.0, 12.0]},
            statistical_method="one_sample_descriptive_t_statistic",
            parameters={"null_value": 0.0, "artifact_ids": artifact_ids},
            software_environment=environment,
            expected_outputs=tuple(artifact_ids.values()),
        )


@dataclass(frozen=True)
class ReproducibilityResult:
    specification_hash: str
    output_artifact_ids: tuple[str, ...]
    final_artifact_id: str
    final_content_hash: str
    manifest_hash: str
    execution_identity: str


def _check_environment(specification: AnalysisSpecification) -> None:
    current = fingerprint()
    expected = thaw(specification.software_environment)
    mismatches = {key: (expected[key], current.get(key)) for key in expected if current.get(key) != expected[key]}
    if mismatches:
        raise ValueError(f"analysis environment does not match specification: {mismatches}")


def execute_analysis(specification: AnalysisSpecification, catalog: ArtifactCatalog, study_id: str = "reproducibility-study") -> ReproducibilityResult:
    """Execute exactly the operations declared by a specification."""
    _check_environment(specification)
    input_ref = thaw(specification.input_artifacts[0])
    raw = catalog.get(input_ref["artifact_id"])
    if raw.provenance.content_hash != input_ref["content_hash"]:
        raise ValueError("input artifact content hash does not match AnalysisSpecification")
    ids = thaw(specification.parameters)["artifact_ids"]
    qc, report = qc_eeg(raw, ids["qc"])
    catalog.add(qc)
    if not report.passed:
        raise ValueError(f"quality control failed: {report.errors}")
    filter_params = next(step for step in thaw(specification.preprocessing_pipeline) if step["operation"] == "filter_eeg")
    filtered = catalog.add(filter_eeg(raw, ids["filter"], filter_params["low_hz"], filter_params["high_hz"], qc=qc))
    epoch_params = next(step for step in thaw(specification.preprocessing_pipeline) if step["operation"] == "epoch_eeg")
    epochs = catalog.add(epoch_eeg(filtered, ids["epoch"], epoch_params["epoch_seconds"]))
    feature_params = thaw(specification.feature_definition)
    band = tuple(feature_params["band_hz"])
    feature = catalog.add(spectral_power(epochs, ids["feature"], band))
    null_value = thaw(specification.parameters)["null_value"]
    analysis = catalog.add(statistical_analysis(feature, ids["analysis"], null_value))
    final = catalog.add(finding(
        analysis,
        (raw, qc, filtered, epochs, feature),
        ids["finding"],
        "The specified real EEG recording contains measurable alpha-band power under the declared reproducible analysis.",
        catalog=catalog,
    ))
    if catalog.validate_integrity():
        raise RuntimeError("analysis produced an integrity-invalid artifact graph")
    from cerevia.pipeline import evidence_manifest
    manifest = evidence_manifest(study_id, final, catalog)
    if tuple(specification.expected_outputs) != tuple(ids[key] for key in ("qc", "filter", "epoch", "feature", "analysis", "finding")):
        raise ValueError("expected_outputs do not match executable artifact plan")
    execution_identity = hash_object({
        "specification_hash": specification.specification_hash,
        "output_artifact_ids": list(specification.expected_outputs),
        "final_artifact_id": final.artifact_id,
        "final_content_hash": final.provenance.content_hash,
    })
    return ReproducibilityResult(specification.specification_hash, tuple(specification.expected_outputs), final.artifact_id,
                                 final.provenance.content_hash, manifest["manifest_hash"], execution_identity)


def verify_rerun(first: ReproducibilityResult, second: ReproducibilityResult) -> bool:
    return first.execution_identity == second.execution_identity

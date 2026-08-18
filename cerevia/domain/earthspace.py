"""Earth/Space domain adapter for the CEREVIA V1.4 transplant proof."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cerevia.analysis.claims import create_claim_artifact
from cerevia.core.artifacts import ArtifactCatalog
from cerevia.core.hashing import hash_object
from cerevia.core.provenance import Artifact
from cerevia.pipeline import evidence_manifest

SOURCE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01T00:00:00&endtime=2024-01-02T00:00:00&minmagnitude=5&limit=5&orderby=time"
SOURCE_DESCRIPTION = "USGS Earthquake Catalog FDSN Event Web Service GeoJSON"


def load_earth_observations(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list) or not document["features"]:
        raise ValueError("Earth/Space fixture must be a non-empty GeoJSON FeatureCollection")
    for feature in document["features"]:
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        if len(coordinates) < 3:
            raise ValueError("each earthquake feature requires longitude, latitude, and depth")
        if feature.get("id") is None or feature.get("properties", {}).get("time") is None:
            raise ValueError("each earthquake feature requires an id and timestamp")
    return document


def build_earthspace_chain(path: str | Path, study_id: str = "earthspace-usgs-2024-01-01") -> tuple[ArtifactCatalog, Artifact, dict[str, Any], dict[str, Any]]:
    document = load_earth_observations(path)
    raw = Artifact.derive("earthspace-raw-observations-001", "raw_earth_observation", document, {"study_id": study_id, "domain": "earthspace", "source_url": SOURCE_URL, "source_description": SOURCE_DESCRIPTION, "feature_count": len(document["features"])}, "ingest_usgs_geojson", parameters={"format": "geojson", "source": "USGS FDSN Event Web Service"})
    catalog = ArtifactCatalog()
    catalog.add(raw)

    features = document["features"]
    qc_checks = {"feature_count_positive": len(features) > 0, "coordinates_valid": all(-180 <= f["geometry"]["coordinates"][0] <= 180 and -90 <= f["geometry"]["coordinates"][1] <= 90 for f in features), "timestamps_present": all(f["properties"].get("time") is not None for f in features), "magnitudes_present": all(f["properties"].get("mag") is not None for f in features)}
    qc = Artifact.derive("earthspace-qc-001", "earthspace_qc", {"passed": all(qc_checks.values()), "checks": qc_checks}, {"quality_gate": True, "domain": "earthspace"}, "quality_control_earth_observations", (raw,), {"policy": "geojson_spatial_temporal_integrity"})
    catalog.add(qc)
    if not all(qc_checks.values()):
        raise ValueError("Earth/Space quality gate failed")

    normalized = []
    for feature in features:
        longitude, latitude, depth = feature["geometry"]["coordinates"][:3]
        properties = feature["properties"]
        normalized.append({"event_id": feature["id"], "timestamp": datetime.fromtimestamp(properties["time"] / 1000, timezone.utc).isoformat(), "latitude": float(latitude), "longitude": float(longitude), "depth_km": float(depth), "magnitude": float(properties["mag"]), "place": properties.get("place")})
    transformed = Artifact.derive("earthspace-transformation-001", "earthspace_transformed_observations", normalized, {"study_id": study_id, "domain": "earthspace", "operation": "normalize_geojson_event_coordinates_and_time"}, "transform_spatial_temporal_observations", (raw, qc), {"time_unit": "unix_milliseconds_to_iso8601_utc", "coordinate_order": "longitude_latitude_depth"})
    catalog.add(transformed)

    centroid_latitude = sum(item["latitude"] for item in normalized) / len(normalized)
    centroid_longitude = sum(item["longitude"] for item in normalized) / len(normalized)
    mean_magnitude = sum(item["magnitude"] for item in normalized) / len(normalized)
    derived = Artifact.derive("earthspace-derived-product-001", "earthspace_derived_product", {"event_count": len(normalized), "centroid": {"latitude": centroid_latitude, "longitude": centroid_longitude}, "mean_magnitude": mean_magnitude, "maximum_magnitude": max(item["magnitude"] for item in normalized), "mean_depth_km": sum(item["depth_km"] for item in normalized) / len(normalized)}, {"study_id": study_id, "domain": "earthspace", "product": "event_cluster_summary"}, "derive_spatial_temporal_event_product", (transformed,), {"statistics": ["count", "centroid", "mean_magnitude", "maximum_magnitude", "mean_depth_km"]})
    catalog.add(derived)

    analysis = Artifact.derive("earthspace-analysis-001", "analysis", {"analysis_type": "earthquake_event_cluster_description", "estimand": "mean_magnitude_of_fixed_catalog_window", "value": mean_magnitude, "event_count": len(normalized)}, {"study_id": study_id, "domain": "earthspace"}, "analyze_earthspace_derived_product", (derived,), {"window": "2024-01-01 UTC", "threshold": "magnitude >= 5"})
    catalog.add(analysis)

    inference = Artifact.derive("earthspace-inference-001", "multimodal_inference", {"analysis_id": analysis.artifact_id, "result": {"catalog_contains_high_magnitude_events": mean_magnitude >= 5.0, "mean_magnitude": mean_magnitude}}, {"study_id": study_id, "domain": "earthspace"}, "infer_earthspace_catalog_property", (analysis,), {"decision_rule": "mean_magnitude_ge_5"})
    catalog.add(inference)

    uncertainty = {"type": "descriptive_catalog_summary", "not_estimated": True, "reason": "fixture demonstrates spatial-temporal evidence plumbing rather than seismic hazard inference"}
    statement = "The fixed USGS catalog window contains a spatially clustered set of magnitude-threshold earthquake observations with the declared descriptive summary."
    claim = create_claim_artifact("earthspace-claim-001", inference, (raw, derived), "The fixed catalog window contains the declared spatial-temporal earthquake pattern.", statement, ("USGS event records and coordinates are interpreted as supplied by the source API",), uncertainty, {"study_id": study_id, "domain": "earthspace", "source_url": SOURCE_URL}, "descriptive_earthspace_catalog_analysis", catalog=catalog)
    catalog.add(claim)

    finding_payload = {"finding_id": "earthspace-finding-001", "statement": statement, "evidence": [raw.artifact_id, derived.artifact_id], "evidence_content_hashes": [raw.provenance.content_hash, derived.provenance.content_hash], "analysis_id": claim.artifact_id, "statistical_result": analysis.payload, "status": claim.payload["claim_status"], "claim_status": claim.payload["claim_status"]}
    finding = Artifact.derive("earthspace-finding-001", "finding", finding_payload, {"study_id": study_id, "status": claim.payload["claim_status"], "evidence_count": 2}, "record_finding", (claim, raw, derived), {"claim_policy": "computation_does_not_auto_convert_to_truth"})
    catalog.add(finding)

    specification = {"domain": "earthspace", "method": "descriptive_earthspace_catalog_analysis", "study_id": study_id, "source_url": SOURCE_URL, "inputs": [raw.artifact_id], "outputs": ["earthspace_transformed_observations", "earthspace_derived_product", "analysis", "inference", "claim", "finding"], "uncertainty": uncertainty}
    manifest = evidence_manifest(study_id, finding, catalog)
    execution_identity = hash_object({"specification_hash": hash_object(specification), "analysis_id": analysis.artifact_id, "inference_id": inference.artifact_id, "finding_id": finding.artifact_id, "final_content_hash": finding.provenance.content_hash})
    return catalog, finding, {"specification": specification, "specification_hash": hash_object(specification), "execution_identity": execution_identity, "manifest": manifest}, {"raw": raw, "qc": qc, "transformed": transformed, "derived": derived, "analysis": analysis, "inference": inference, "claim": claim, "finding": finding}

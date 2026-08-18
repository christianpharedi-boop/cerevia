"""Reference adapter profiles for the V1.6 conformance suite."""
from __future__ import annotations

from cerevia.interoperability.profile import EvidenceInteroperabilityProfile


COMMON_VERIFICATION = ("serialized_bundle", "content_identity", "lineage_closure", "claim_qualification", "evidence_graph", "sentinel_revocation", "observatory_impact")

REFERENCE_PROFILES = {
    "neuroscience": EvidenceInteroperabilityProfile("neuroscience", "1.0.0", ("raw_eeg", "behavioral_events", "eeg_epochs", "filtered_eeg", "spectral_power", "qc_report", "cross_modal_alignment", "evidence_aware_analysis", "analysis", "multimodal_inference", "claim", "finding"), "domain adapter emits immutable observation and analysis artifacts", ("artifact", "provenance", "manifest", "finding"), "content-addressed artifact identity includes parents and frozen computational context", "parent artifact IDs form the complete computational lineage", COMMON_VERIFICATION, "raw-rec-02-MIvsRest-run-0", "aware-finding-001"),
    "proteomics": EvidenceInteroperabilityProfile("proteomics", "1.0.0", ("raw_proteomics_assay", "proteomics_qc", "proteomics_processed_assay", "protein_quantification", "analysis", "multimodal_inference", "claim", "finding"), "domain adapter emits immutable protein assay and derived artifacts", ("artifact", "provenance", "manifest", "finding"), "content-addressed artifact identity includes parents and frozen computational context", "parent artifact IDs form the complete computational lineage", COMMON_VERIFICATION, "proteomics-raw-assay-001", "proteomics-finding-001"),
    "earthspace": EvidenceInteroperabilityProfile("earthspace", "1.0.0", ("raw_earth_observation", "earthspace_qc", "earthspace_transformed_observations", "earthspace_derived_product", "analysis", "multimodal_inference", "claim", "finding"), "domain adapter emits immutable spatial-temporal observations and derived products", ("artifact", "provenance", "manifest", "finding"), "content-addressed artifact identity includes parents and frozen computational context", "parent artifact IDs form the complete computational lineage", COMMON_VERIFICATION, "earthspace-raw-observations-001", "earthspace-finding-001"),
}

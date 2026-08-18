# CEREVIA V0.4 Experimental Reproducibility

CEREVIA V0.4 adds an executable `AnalysisSpecification`. It describes the computation before execution rather than merely recording the computation afterward.

| Specification field | Meaning |
|---|---|
| `input_artifacts` | Exact input artifact IDs and content hashes. |
| `preprocessing_pipeline` | Ordered operations and parameters for QC, filtering, and epoching. |
| `feature_definition` | Feature operation and band definition. |
| `statistical_method` | Named statistical procedure. |
| `parameters` | Analysis parameters and deterministic output IDs. |
| `software_environment` | Expected computational environment fingerprint. |
| `expected_outputs` | Exact artifact IDs that execution must produce. |

The specification itself has a canonical SHA-256 `specification_hash`. Execution refuses an input artifact whose current content hash differs from the specification, refuses a mismatched software environment, and fails if the declared output plan is not the plan that ran.

## Stable execution identity

Each run still produces a regular manifest hash. Because provenance timestamps are intentionally recorded, two separately executed manifests may have different manifest hashes. V0.4 therefore also emits a timestamp-independent `execution_identity` derived from the specification hash, expected output IDs, final artifact ID, and final content hash.

Two runs are reproducible when their execution identities match. This tests computational equivalence while preserving the auditability of per-run timestamps.

## Real-data proof

The reproducibility example executes the declared analysis twice on the real OpenNeuro ds003810 `sub-02_task-MIvsRest_run-0_eeg.edf` recording. Both executions read the same BIDS source identity, use the same ontology context, create the same output artifact IDs, and produce the same final content hash and execution identity.

```bash
PYTHONPATH=. python3 examples/neuro/reproduce_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The source EEG remains external and is not copied into the CEREVIA repository.

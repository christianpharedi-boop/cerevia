# CEREVIA V0.8 Evidence-Aware Analysis

CEREVIA V0.8 makes the scientific meaning of an analysis explicit. An executable `EvidenceAwareAnalysisSpecification` declares the observations and alignments it consumes, the hypothesis being evaluated, experimental conditions, comparison, method, parameters, assumptions, output definitions, uncertainty, environment, and expected artifact IDs.

## Scientific chain

```text
OBSERVATION → TRANSFORMATION → FEATURE → ALIGNMENT → ANALYSIS → INFERENCE → FINDING
```

The artifact catalog remains authoritative for content identity and parent hashes. The graph projection now distinguishes `Analysis` and `Inference` nodes and represents inference dependencies with `INFERRED_FROM` edges. A finding supports its inference, while the inference preserves exact links to the declared analysis, observations, and alignments.

## Required specification fields

| Field | Purpose |
|---|---|
| `input_artifacts` | Exact content-addressed observation or feature inputs. |
| `alignment_artifacts` | Exact cross-modal relationships required by the analysis. |
| `hypothesis` | The statement being evaluated. |
| `experimental_conditions` | Context in which the hypothesis is interpreted. |
| `comparison` | Declared contrast or baseline. |
| `method` and `parameters` | Computational operation and its configuration. |
| `assumptions` | Explicit conditions required for interpretation. |
| `output_definitions` | Declared outputs and units or interpretation type. |
| `uncertainty` | What is estimated, not estimated, or intentionally left unresolved. |

Execution rejects changed input hashes, disconnected alignments, environment mismatches, incomplete output plans, and unspecified scientific fields. It produces an `evidence_aware_analysis`, `multimodal_inference`, and provisional `finding` artifact with deterministic content identities.

The real V0.8 proof uses OpenNeuro ds003810 EEG and its EDF behavioral events. It declares the alpha-band feature, shared recording-seconds context, descriptive comparison, assumptions, and a deliberate `not_estimated` uncertainty statement rather than presenting an unsupported confidence interval.

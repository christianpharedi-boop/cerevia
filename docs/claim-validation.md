# CEREVIA V0.9 Claim Validation

CEREVIA V0.9 introduces a machine-readable distinction between a **computed result** and a **scientific claim**. A computed result is a value produced by a declared method. A scientific claim is a qualified statement that may be created only after its inference, evidence, assumptions, uncertainty, method, hypothesis, and experimental context have been validated.

## Claim contract

| Component | Validation rule |
|---|---|
| Hypothesis and statement | Both must be explicit and non-empty. |
| Supporting evidence | At least one exact artifact is required, and it must belong to the inference lineage. |
| Inference | Must be a valid analysis or inference artifact. |
| Assumptions | At least one assumption must be declared. |
| Uncertainty | A non-empty uncertainty object with a declared `type` is required. |
| Experimental context | The claim must preserve the context in which the result is interpreted. |
| Method | The computational method must be named. |
| Integrity | Catalog and evidence content hashes must validate before claim creation. |

A claim with `uncertainty.type: not_estimated` is **QUALIFIED**, not silently treated as statistically certain. A claim with a declared uncertainty model is **PROVISIONAL**. Missing prerequisites produce an invalid claim and prevent claim creation.

## Scientific chain

```text
OBSERVATION → TRANSFORMATION → FEATURE → ALIGNMENT → ANALYSIS → INFERENCE → CLAIM → FINDING
```

The claim artifact preserves the computed inference result separately under `computed_result`, alongside the hypothesis, claim statement, evidence IDs and hashes, assumptions, uncertainty, context, method, validation status, and inference identity. The evidence graph represents claims as distinct `Claim` nodes. Findings support the claim rather than allowing a computation to silently become a scientific conclusion.

CEREVIA does not decide that a hypothesis is true. It verifies that a declared claim follows from declared computations under declared assumptions and remains appropriately qualified.

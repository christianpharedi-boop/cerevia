# CEREVIA Documentation

This index is intentionally ordered for a neuroscience researcher approaching CEREVIA for the first time. The EEG/BIDS provenance path is the flagship demonstration; the remaining sections explain the frozen substrate, its implementation-independent contracts, and the tests that show the same trust semantics survive outside neuroscience.

## Architecture contract

Read [Architecture](architecture.md) before adding a new package or adapter. It defines the trust-substrate/application split, establishes `cerevia.neuro` as the flagship namespace, identifies `cerevia.adapters` as the external-domain boundary, documents the lazy BIDS dependency, and describes legacy import paths as compatibility surfaces rather than canonical APIs.

## 1. Neuroscience story

These documents explain the concrete EEG/BIDS problem and the evidence path from acquisition artifacts to independently verifiable claims.

| Document | Purpose |
|---|---|
| [BIDS/EEG](bids-eeg.md) | Ingest and verify BIDS EEG evidence. |
| [Reproducibility](reproducibility.md) | Re-run analysis and inspect serialized provenance. |
| [Claim validation](claim-validation.md) | Validate qualified claims, assumptions, and uncertainty. |
| [30-minute quickstart](pilot/30-minute-quickstart.md) | Follow the first end-to-end repository walkthrough. |

Start from the repository root with `python3 examples/neuro/quickstart.py`.

## 2. Frozen evidence substrate

These documents define the protocol-independent foundation on which all adapters operate.

| Document | Purpose |
|---|---|
| [Evidence Core V1](evidence-core-v1.md) | Immutable artifacts, identities, provenance, claims, and independent verification. |
| [Evidence graph](evidence-graph.md) | Lineage, ancestor closure, and downstream impact traversal. |
| [Independent verification](independent-verification.md) | Fresh-process verification without original in-memory state. |
| [Sentinel](sentinel.md) | Adversarial integrity, attestations, revocation, and transparency history. |
| [Observatory](observatory.md) | Read-only queries over evidence and trust state. |
| [Protocol API V2.3](protocol-api-v2.3.md) | Thin HTTP exposure of the frozen contracts. |

## 3. Generalization and interoperability

These documents describe how an implementation can conform without importing CEREVIA and how the universal contracts compose across independent producers.

| Document | Purpose |
|---|---|
| [Evidence Interoperability V1](evidence-interoperability-v1.md) | The five universal interoperability contracts. |
| [External Conformance V2](external-conformance-v2.md) | Standalone producer/verifier and bidirectional exchange proof. |
| [Cross-domain Evidence V1.5](cross-domain-v1.5.md) | Provenance-only composition of independently verified findings. |

## 4. Transplant tests

Proteomics and Earth/Space are deliberately presented as **substrate transplant tests**, not competing product domains. They test whether identity, lineage, verification, revocation, and impact semantics remain unchanged when observations and derived products change.

| Document | Domain test |
|---|---|
| [Proteomics V1.3](proteomics-v1.3.md) | Protein-expression observations and descriptive comparisons. |
| [Earth/Space V1.4](earthspace-v1.4.md) | Spatial-temporal earthquake observations and derived products. |

The corresponding runnable proofs are under `examples/transplants/`.

## 5. Institutional validation

These documents define the privacy-preserving exchange boundary and prepare external validation. They do not turn CEREVIA into a mutable scientific-data custodian.

| Document | Purpose |
|---|---|
| [Institutional Exchange V2.1](institutional-exchange-v2.1.md) | Signed envelopes, key rotation, audit history, and out-of-band evidence. |
| [External Institutional Pilot V2.2](external-institutional-pilot-v2.2.md) | Blind exchange fixtures and agreement matrices. |
| [Pilot readiness](pilot/readiness.json) | Machine-readable readiness checklist. |

The runnable fixtures are under `examples/institutional_pilot/`.

## Repository layout

| Path | Meaning |
|---|---|
| `cerevia/core/` | Frozen evidence substrate. |
| `cerevia/neuro/` | Flagship neuroscience adapters: EEG, BIDS, and eye tracking. |
| `cerevia/adapters/` | Cross-domain transplant adapters. |
| `cerevia/sentinel/`, `cerevia/observatory/`, `cerevia/interoperability/` | Trust, query, and universal protocol layers. |
| `examples/neuro/` | First-run neuroscience demonstrations. |
| `examples/substrate_stress_tests/` | Cross-domain, conformance, and standalone implementation proofs. |
| `examples/transplants/` | Proteomics and Earth/Space proofs. |
| `examples/institutional_pilot/` | Institutional exchange and external-pilot fixtures. |

The old Python namespaces remain as compatibility wrappers, but new integrations should import from `cerevia.neuro` and `cerevia.adapters`.

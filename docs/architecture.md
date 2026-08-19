# CEREVIA Architecture Contract

This document records the repository organization as an architectural contract. It is a documentation and namespace boundary, not a change to the frozen Evidence Core or interoperability semantics.

> `cerevia.core` and the trust layers are domain-neutral. `cerevia.neuro` is the flagship application namespace. `cerevia.adapters` contains external-domain implementations. Legacy paths are compatibility surfaces, not canonical APIs.

## Trust substrate and applications

CEREVIA has two conceptual layers that share the same evidence semantics:

```text
CEREVIA
    |
    +-- TRUST SUBSTRATE
    |       +-- cerevia.core
    |       +-- cerevia.sentinel
    |       +-- cerevia.observatory
    |       +-- cerevia.interoperability
    |
    +-- APPLICATIONS
            +-- cerevia.neuro
            +-- cerevia.adapters
            +-- cerevia.multimodal
            +-- cerevia.institutional
```

The substrate defines how observations become identifiable, immutable, traceable, independently verifiable evidence. Sentinel, Observatory, and Interoperability operate on those same contracts regardless of whether the source is an EEG recording, a protein assay, or a geophysical observation.

The application namespaces define what observations mean in a domain. They must not create parallel hashing, provenance, verification, revocation, or evidence-graph semantics.

| Namespace | Architectural responsibility | Canonical status |
|---|---|---|
| `cerevia.core` | Artifacts, content identity, provenance, evidence graphs, claims, and verification primitives | Frozen substrate |
| `cerevia.sentinel` | Adversarial integrity, attestations, revocation, and transparency history | Trust layer |
| `cerevia.observatory` | Read-only lineage, support, history, verification, and impact queries | Trust layer |
| `cerevia.interoperability` | Universal evidence contracts and conformance behavior | Protocol layer |
| `cerevia.neuro` | EEG, BIDS, eye tracking, and neuroscience multimodal workflows | Flagship application |
| `cerevia.adapters` | Proteomics and Earth/Space implementations used as transplant tests | External-domain applications |
| `cerevia.multimodal` | Reusable evidence alignment utilities | Shared application support |
| `cerevia.institutional` | Signed institutional exchange and audit workflows | Operational boundary |

## Why neuroscience is the flagship

CEREVIA has its deepest implementation history in the neuroscience path:

```text
EEG -> BIDS -> behavioral events -> eye tracking -> multimodal alignment
    -> analysis -> inference -> claim -> finding
```

The `cerevia.neuro` namespace makes that path visible to a researcher without implying that neuroscience owns the trust model. EEG and BIDS adapters produce CEREVIA artifacts; the Evidence Core determines how those artifacts are identified and connected to claims and findings.

New neuroscience integrations should use imports such as:

```python
from cerevia.neuro.eeg import EEGObservation, ingest_eeg
from cerevia.neuro.bids import ingest_bids_eeg, load_bids_eeg_run
from cerevia.neuro.eye_tracking import ingest_eye_tracking, align_eeg_eye
```

## Lazy dependency boundary

`cerevia.neuro` eagerly exports only lightweight EEG symbols. It does not eagerly import `cerevia.neuro.bids`, because BIDS/EDF loading depends on `pyedflib`. This keeps the following import narrow:

```python
from cerevia.neuro import EEGObservation, ingest_eeg
```

Code that needs EDF/BIDS functionality opts into the heavier dependency explicitly:

```python
from cerevia.neuro.bids import ingest_bids_eeg
```

This is a dependency boundary, not a semantic boundary. Both paths ultimately create the same CEREVIA artifact types and use the same core identity and provenance machinery.

## External-domain adapters

Proteomics and Earth/Space belong under `cerevia.adapters` because they demonstrate portability of the substrate rather than competing with the neuroscience application surface:

```python
from cerevia.adapters.proteomics import build_proteomics_chain
from cerevia.adapters.earthspace import build_earthspace_chain
```

A future satellite, clinical imaging, or materials-science implementation should be evaluated as an adapter or application on top of the same contracts. It should not be added to `cerevia.core` merely because it introduces a new observation type.

## Legacy compatibility surfaces

The reorganization retains forwarding modules for established import paths:

| Legacy path | Canonical path |
|---|---|
| `cerevia.acquisition.eeg` | `cerevia.neuro.eeg` |
| `cerevia.acquisition.bids` | `cerevia.neuro.bids` |
| `cerevia.multimodal.eye_tracking` | `cerevia.neuro.eye_tracking` |
| `cerevia.domain.proteomics` | `cerevia.adapters.proteomics` |
| `cerevia.domain.earthspace` | `cerevia.adapters.earthspace` |

A wrapper re-exports the canonical implementation rather than duplicating it:

```python
# cerevia/acquisition/eeg.py
from cerevia.neuro.eeg import *
```

Therefore old notebooks continue to resolve while new projects use the canonical namespace. The wrappers are migration surfaces and should not receive new implementation logic. Any future behavior change belongs in the canonical module and is then visible through both paths.

## Placement rule for future contributions

When adding a new module, ask two questions. First, does it define domain-neutral evidence identity, lineage, verification, revocation, or interoperability? If so, it belongs in the substrate or trust layers and must preserve their frozen contracts. Second, does it describe a domain observation or workflow? If so, it belongs in `cerevia.neuro` for neuroscience or in `cerevia.adapters` for an external-domain transplant.

This rule keeps domain identity separate from trust identity:

```text
EEG observation       Protein assay        Earth observation
       |                     |                     |
       +---------- domain adapter/application ----+
                             |
                          Artifact
                             |
                       Evidence Core
                             |
                 Sentinel / Observatory /
                   Interoperability
```

The domain knows what the observation is. The Core knows how that observation becomes trustworthy, traceable evidence.

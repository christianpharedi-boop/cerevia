# CEREVIA Invariants

CEREVIA is an evidence infrastructure layer for neuroscience. Its fundamental rule is:

> No finding exists without a traceable computational path back to the observations that produced it.

| ID | Invariant | Enforcement in V0.1 |
|---|---|---|
| I1 | Raw evidence is immutable. | Raw EEG is represented as a frozen artifact; catalog registration rejects replacement. |
| I2 | Every derived artifact has provenance. | `Artifact.derive` creates a complete provenance record and the catalog requires registered parents. |
| I3 | Transformations are deterministic where possible. | FFT filtering, fixed epoching, and fixed spectral-power calculations record parameters and software version. |
| I4 | Analyses reference exact artifact versions. | Analysis parents point to the exact feature artifact and its content hash. |
| I5 | Findings cannot exist without evidence. | `finding()` rejects an empty evidence tuple. |
| I6 | Failed analyses remain in history. | QC is a first-class artifact and is never deleted on failure. |
| I7 | Quality gates precede inference. | The pipeline stops before transformation when QC fails. |
| I8 | Provenance is machine-readable. | Every artifact serializes to JSON-compatible metadata. |
| I9 | Metadata and data are separate concerns. | Artifact metadata carries study and pseudonymous IDs; payload carries signal values. |
| I10 | Reproducibility is a first-class artifact. | Manifest records operation parameters, software version, environment, timestamp, and content hash. |

CEREVIA does not convert an analysis into truth automatically. Findings are recorded as `PROVISIONAL` until an explicit downstream review or reproduction process changes their status.

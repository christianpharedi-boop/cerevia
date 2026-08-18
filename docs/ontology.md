# CEREVIA Neuroscience Ontology v0.2

CEREVIA V0.2 introduces a domain layer above the V0.1.2 evidence engine. The evidence core remains responsible for immutable artifacts, provenance, integrity validation, and manifests. The ontology records what an experiment means: who participated, what session occurred, what task and condition were active, what modality was acquired, and how events, epochs, features, analyses, and findings relate.

## Core entities

| Entity | Meaning | Required relationship |
|---|---|---|
| Study | The scientific investigation. | Root of the ontology hierarchy. |
| Participant | A pseudonymous research subject. | Belongs to a Study. |
| Session | A bounded experimental encounter. | Belongs to a Participant and Study; retains task and condition. |
| Recording | A specific acquisition of physiological or neural data. | Belongs to a Session and declares a Modality. |
| Modality | EEG, MEG, fMRI, ECoG, EMG, ECG, EOG, eye tracking, or behavioral data. | Declared by a Recording. |
| Channel | A measurement stream within a Recording. | Declared by a Recording and uniquely identified. |
| Event | A labeled temporal or experimental occurrence. | Belongs to a Recording. |
| Epoch | A derived temporal segment. | Belongs to a Recording and may reference an Event. |
| Feature | A computationally derived representation. | References exact evidence artifact and Epochs. |
| Analysis | An operation producing quantitative evidence. | References Features and experimental task/condition. |
| Finding | A claim attached to evidence. | References an ontology Analysis and remains PROVISIONAL by default. |

## Experimental context

Neuroscience evidence is not only signal mathematics. CEREVIA preserves the context path:

```text
participant + task + condition + event + recording → signal → analysis → finding
```

When an EEG `Recording` is supplied during ingestion, the resulting raw artifact metadata includes `recording_id`, `modality`, `task`, and `condition`. The artifact still goes through the same V0.1.2 integrity engine; the ontology does not weaken or bypass provenance checks.

## Boundary rule

Ontology entities are immutable and append-only within `NeuroscienceOntology`. Parent entities must be registered before children. Duplicate IDs, non-pseudonymous participants, missing task or condition context, modality mismatches, channel mismatches, and dangling references are rejected.

# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.2 Neuroscience Ontology

CEREVIA now has a domain layer that understands the experimental meaning surrounding a signal. The ontology models Study, pseudonymous Participant, Session, Recording, Modality, Channel, Event, Epoch, Feature, Analysis, and Finding. It preserves the context path:

```text
participant + task + condition + event + recording → signal → analysis → finding
```

The V0.1.2 evidence core remains underneath and continues to enforce immutable artifacts, parent content hashes, environment fingerprints, catalog integrity validation, and independently hashed manifests. Ontology entities are append-only and require registered parents; EEG ingestion can bind a raw artifact to an ontology Recording and carry its task, condition, modality, and recording ID into provenance metadata.

The ontology contract is documented in [`docs/ontology.md`](docs/ontology.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 examples/eeg_pipeline/run.py
python3 -m unittest discover -s tests -v
```

The example writes `examples/eeg_pipeline/evidence_manifest.json`. No database, authentication, cloud service, web interface, or AI model is required.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.

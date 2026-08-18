# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.5 Evidence Graph

CEREVIA now projects its artifact lineage and neuroscience ontology into a pure computational evidence graph. The graph models Study, Participant, Session, Recording, Event, Artifact, Transformation, Feature, Analysis, and Finding nodes connected by `GENERATED_BY`, `DERIVED_FROM`, `RECORDED_DURING`, `ASSOCIATED_WITH`, `ANALYZED_BY`, and `SUPPORTS` edges.

The graph answers questions such as which evidence supports a finding, which findings depend on a recording, and what downstream evidence would be affected if a preprocessing artifact were invalidated. It is an in-memory model with no GUI, database, cloud service, or AI dependency. See [`docs/evidence-graph.md`](docs/evidence-graph.md).

Evidence manifests now include a deterministic graph representation and `evidence_graph_hash` alongside the existing audit manifest hash. The artifact catalog remains authoritative for content identity and integrity validation.

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/reproduce_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The V0.5 example runs the reproducible real-data analysis, projects the result into an evidence graph, and reports support and invalidation coverage. No copied participant data is required in the repository.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.

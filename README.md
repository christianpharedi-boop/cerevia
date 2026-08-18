# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.8 Evidence-Aware Analysis

CEREVIA now makes the scientific meaning of an analysis executable. An `EvidenceAwareAnalysisSpecification` declares exact input observations and alignments, hypothesis, experimental conditions, comparison, method, parameters, assumptions, output definitions, uncertainty, software environment, and expected outputs.

```text
OBSERVATION → TRANSFORMATION → FEATURE → ALIGNMENT → ANALYSIS → INFERENCE → FINDING
```

The graph distinguishes `Analysis` from `Inference`. An inference is connected to its declared parents with `INFERRED_FROM` edges, while a finding supports the inference and preserves the complete evidence chain. Execution rejects changed input hashes, disconnected alignments, environment mismatches, incomplete output plans, and missing scientific semantics.

The real V0.8 proof uses OpenNeuro ds003810 EEG and its 68 EDF behavioral events. It declares an alpha-band feature, shared recording-seconds context, descriptive comparison, assumptions, output definition, and a deliberate `not_estimated` uncertainty statement. See [`docs/evidence-aware.md`](docs/evidence-aware.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/evidence_aware_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

The repository also contains the V0.7 three-observation implementation for EEG, behavioral events, and eye tracking. No participant data is copied into this repository.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.

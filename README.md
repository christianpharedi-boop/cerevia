# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.4 Experimental Reproducibility

CEREVIA now defines analyses before execution through an executable `AnalysisSpecification`. A specification records exact input artifact IDs and content hashes, the preprocessing pipeline, feature definition, statistical method, parameters, software environment, and expected output IDs.

The executor refuses mismatched source content or environment metadata and verifies that the declared artifact plan actually ran. It produces both a per-run manifest hash and a timestamp-independent `execution_identity`. Two executions are computationally reproducible when their execution identities match, even though their audit manifests retain distinct execution timestamps.

The V0.4 proof reruns the declared analysis twice on a real OpenNeuro BIDS EEG recording and obtains the same final content hash and execution identity. See [`docs/reproducibility.md`](docs/reproducibility.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/bids_eeg/reproduce_analysis.py \
  /path/to/ds003810/sub-02/eeg/sub-02_task-MIvsRest_run-0_eeg.edf
```

No copied participant data is required in the CEREVIA repository. The external BIDS dataset remains the source of record.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.

# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.9 Claim Validation

CEREVIA now distinguishes a **computed result** from a **scientific claim**. A result is a value produced by a declared method. A claim is a qualified statement that may be created only after its inference, exact supporting evidence, assumptions, uncertainty, method, hypothesis, and experimental context have been validated.

```text
OBSERVATION → TRANSFORMATION → FEATURE → ALIGNMENT → ANALYSIS → INFERENCE → CLAIM → FINDING
```

Claim validation rejects missing evidence, invalid or disconnected inference, broken evidence content hashes, missing assumptions, missing uncertainty, missing context, and missing method. An explicit `not_estimated` uncertainty declaration yields a `QUALIFIED` claim rather than a false appearance of certainty. CEREVIA does not decide that a hypothesis is true; it verifies that a declared claim follows from declared computations under declared assumptions. See [`docs/claim-validation.md`](docs/claim-validation.md).

The real V0.9 proof uses OpenNeuro ds003810 EEG and its 68 EDF behavioral events. It produces separate analysis, inference, claim, and finding artifacts and preserves the computed result independently inside the claim artifact.

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

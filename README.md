# CEREVIA

**Evidence infrastructure for neuroscience.** CEREVIA records a computational path from immutable observations to provisional findings. It is not a replacement for EEG, MRI, behavioral, or physiological analysis libraries; it is the provenance and evidence layer those tools can build upon.

## V0.7 Multimodal Observation

CEREVIA now models three independent observational streams: **EEG**, **behavioral events**, and **eye tracking**. Each observation remains independently content-addressed and auditable. Explicit alignment artifacts relate observations only when participant, session, task, and declared timebase context are compatible. Inference artifacts then combine observations and alignments without collapsing them into one opaque dataset.

```text
STUDY → PARTICIPANT → SESSION → TASK
              ┌──────────┼──────────┐
             EEG      BEHAVIOR   EYE TRACKING
              └──────────┼──────────┘
                 ALIGNMENTS / TIMEBASE
                           ↓
                   MULTIMODAL INFERENCE
                           ↓
                        FINDING
```

The V0.7 eye-tracking adapter consumes BIDS `_physio.tsv` or `_physio.tsv.gz` plus JSON sidecars and requires `PhysioType=eyetrack`, declared columns, monotonic timestamps, finite samples, and sampling-frequency-consistent duration. The real proof uses OpenNeuro EEGEyeNet `ds005872` and preserves the eye stream independently. A deliberately incompatible EEG-eye relationship is rejected rather than silently combined. See [`docs/eye-tracking.md`](docs/eye-tracking.md).

## Run

```bash
cd /home/ubuntu/cerevia
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 examples/eye_tracking/ingest_openneuro.py \
  /path/to/eye_physio.tsv \
  /path/to/eye_physio.json
```

The real EEGEyeNet proof ingested 161,733 eye-tracking samples at 500 Hz, preserved the source SHA-256, and rejected an incompatible EEG context. Three-stream inference is covered by tests with explicit EEG-behavior and EEG-eye alignment parents.

## Inherited Earth foundation

The repository was cloned from [`christianpharedi-boop/coresignal`](https://github.com/christianpharedi-boop/coresignal), an Earth-rotation and geomagnetic research framework. The extracted, licensed modules are under `third_party/coresignal_earth/`, including strict IERS C04 parsing, LOD records, and the machine-readable provenance schema. CEREVIA adapts those provenance and admission principles to neuroscience artifacts.

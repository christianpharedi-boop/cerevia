from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from cerevia.neuro.eeg import EEGObservation
from cerevia.pipeline import run_pipeline


def main() -> None:
    fs = 128.0
    seconds = 8
    t = np.arange(int(fs * seconds)) / fs
    rng = np.random.default_rng(7)
    signal = np.sin(2 * np.pi * 10 * t) + 0.2 * np.sin(2 * np.pi * 20 * t) + 0.05 * rng.standard_normal(t.size)
    data = np.vstack([signal, 0.8 * signal + 0.05 * rng.standard_normal(t.size)])
    observation = EEGObservation.from_array(data, fs, ("C3", "C4"), ((0, "start"),))
    _, _, manifest = run_pipeline(observation)
    destination = Path(__file__).with_name("evidence_manifest.json")
    destination.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(destination), "provenance_chain": manifest["provenance_chain"], "content_hash": manifest["content_hash"]}, indent=2))


if __name__ == "__main__":
    main()

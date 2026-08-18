from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest

from cerevia.neuro.bids import load_bids_eeg_run


class BidsTests(unittest.TestCase):
    def test_bids_metadata_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            eeg = root / "sub-01" / "eeg"
            eeg.mkdir(parents=True)
            (root / "dataset_description.json").write_text(json.dumps({"Name": "fixture", "BIDSVersion": "1.9.0", "License": "CC0"}))
            stem = "sub-01_task-rest_run-01"
            data = eeg / f"{stem}_eeg.edf"
            data.write_bytes(b"fixture")
            (eeg / f"{stem}_eeg.json").write_text(json.dumps({"EEGReference": "Cz", "SamplingFrequency": 125, "EEGChannelCount": 1, "RecordingType": "continuous"}))
            (eeg / f"{stem}_channels.tsv").write_text("name\ttype\tunits\nCz\tEEG\tMicrov\n")
            run = load_bids_eeg_run(data)
            self.assertEqual(run.participant_id, "sub-01")
            self.assertEqual(run.task, "rest")
            self.assertEqual(run.run, "01")
            self.assertEqual(run.sidecar["SamplingFrequency"], 125)

    @unittest.skipUnless(os.environ.get("CEREVIA_BIDS_EDF"), "set CEREVIA_BIDS_EDF to run the real OpenNeuro signal test")
    def test_real_openneuro_file_is_bids_compatible(self):
        run = load_bids_eeg_run(os.environ["CEREVIA_BIDS_EDF"])
        observation = run.to_observation()
        self.assertEqual(observation.sampling_rate_hz, float(run.sidecar["SamplingFrequency"]))
        self.assertEqual(len(observation.channel_names), int(run.sidecar["EEGChannelCount"]))
        self.assertGreater(len(observation.data[0]), 0)


if __name__ == "__main__":
    unittest.main()

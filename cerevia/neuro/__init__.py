"""Neuroscience-facing CEREVIA adapters for EEG/BIDS and multimodal evidence."""

from .eeg import EEGObservation, ingest_eeg

__all__ = ["EEGObservation", "ingest_eeg"]

__version__ = "2.4.1"


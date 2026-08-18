"""Compatibility wrapper for :mod:`cerevia.neuro.eeg`.

The neuroscience namespace is canonical as of CEREVIA 2.4.0. This module
remains importable so existing analyses do not break during the reorganization.
"""

from cerevia.neuro.eeg import *  # noqa: F401,F403

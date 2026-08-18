"""Computational environment fingerprinting for reproducibility manifests."""
from __future__ import annotations
import platform
import sys
from pathlib import Path
from .hashing import sha256_file


def fingerprint(project_root: str | Path | None = None) -> dict[str, str]:
    result = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "numpy_version": "unavailable",
        "os": platform.platform(),
        "architecture": platform.machine(),
        "cerevia_version": "1.2.0",
    }
    try:
        import numpy
        result["numpy_version"] = numpy.__version__
    except ImportError:
        pass
    if project_root is not None:
        pyproject = Path(project_root) / "pyproject.toml"
        if pyproject.is_file():
            result["dependency_manifest_sha256"] = sha256_file(pyproject)
    result["python_executable"] = sys.executable
    return result

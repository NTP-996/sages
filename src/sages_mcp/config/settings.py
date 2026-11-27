"""Where the content lives."""

from __future__ import annotations

import os
from pathlib import Path

ENV_DATA_DIR = "SAGES_DATA_DIR"
_PACKAGE = Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """The folder holding skills/ and sources/.

    In order: the SAGES_DATA_DIR environment variable, the copy bundled inside the installed
    package, then the repository root when running from a checkout.
    """
    candidates = [_PACKAGE / "_data", _PACKAGE.parents[1]]
    override = os.environ.get(ENV_DATA_DIR)
    if override:
        candidates.insert(0, Path(override).expanduser())
    for candidate in candidates:
        if (candidate / "skills" / "sages" / "roster.json").is_file():
            return candidate
    looked = ", ".join(str(candidate) for candidate in candidates)
    raise RuntimeError(f"Sages content not found (looked in: {looked}). Set {ENV_DATA_DIR}.")

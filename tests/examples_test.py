"""Ensure canonical examples/ scripts stay runnable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def test_whenever_typeid_and_sqlite_example(tmp_path):
    """Run the documented whenever + TypeID + SQLite example in a clean process."""
    # Subprocess avoids the SessionManager singleton already configured by conftest.
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "whenever_typeid_and_sqlite.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert (tmp_path / "database.db").exists()

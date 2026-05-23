"""CLI smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STL_ROOT = REPO_ROOT / "vendor" / "flip-jump" / "flipjump" / "stl"


def test_cli_dump_json_round_trips(tmp_path):
    if not (STL_ROOT / "conf.json").is_file():
        pytest.skip("flip-jump submodule not initialised")
    output = tmp_path / "index.json"
    env = {"PYTHONPATH": str(REPO_ROOT / "docs" / "_ext")}
    result = subprocess.run(
        [sys.executable, "-m", "fj_stl_extract",
         "--dump-json",
         "--stl-root", str(STL_ROOT),
         "--output", str(output),
         "--pretty"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result.returncode == 0, (
        f"CLI failed: stdout={result.stdout!r}, stderr={result.stderr!r}"
    )
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "files" in data
    assert any(f["rel_path"] == "runlib" for f in data["files"])


def test_cli_requires_dump_json_flag():
    env = {"PYTHONPATH": str(REPO_ROOT / "docs" / "_ext")}
    result = subprocess.run(
        [sys.executable, "-m", "fj_stl_extract"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result.returncode != 0
    assert "--dump-json" in result.stderr


def test_cli_missing_stl_root_returns_friendly_error(tmp_path):
    env = {"PYTHONPATH": str(REPO_ROOT / "docs" / "_ext")}
    result = subprocess.run(
        [sys.executable, "-m", "fj_stl_extract",
         "--dump-json",
         "--stl-root", str(tmp_path / "nonexistent")],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result.returncode == 1
    assert "submodule" in result.stderr.lower() or "missing" in result.stderr.lower()

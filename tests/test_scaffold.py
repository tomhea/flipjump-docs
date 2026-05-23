"""M1 scaffold smoke tests: submodule present, Sphinx build succeeds.

These tests are the load-bearing contract for milestone 1. They MUST stay
green from M1 onward — every later milestone inherits the contract that
`make html` cleanly produces a Sphinx site from the current `docs/source/`
tree, and that the upstream `flip-jump` submodule is initialised so its
STL source is reachable for later milestones' extractor.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_SOURCE = REPO_ROOT / "docs" / "source"
DOCS_BUILD = REPO_ROOT / "docs" / "_build" / "html"
VENDOR_FJ = REPO_ROOT / "vendor" / "flip-jump"


def test_flip_jump_submodule_initialised():
    """The flip-jump submodule must be checked out (not just configured)."""
    conf = VENDOR_FJ / "flipjump" / "stl" / "conf.json"
    assert conf.is_file(), (
        f"Expected {conf} to exist. Run `git submodule update --init --recursive` "
        f"to initialise the flip-jump submodule."
    )


def test_sphinx_conf_exists():
    """conf.py must exist at the planned location."""
    conf = DOCS_SOURCE / "conf.py"
    assert conf.is_file(), f"Sphinx config missing at {conf}"


def test_sphinx_build_succeeds(tmp_path):
    """`sphinx-build -W` must exit 0 against the current docs/source/ tree.

    Builds into a tmp_path to avoid clobbering the developer's local
    docs/_build/. The -W flag promotes warnings to errors, matching the
    plan's "no warnings" contract.
    """
    if shutil.which("sphinx-build") is None:
        pytest.skip("sphinx-build not on PATH (install docs/requirements.txt)")

    out_dir = tmp_path / "html"
    result = subprocess.run(
        ["sphinx-build", "-W", "-b", "html", str(DOCS_SOURCE), str(out_dir)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, (
        f"sphinx-build failed with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert (out_dir / "index.html").is_file(), "index.html missing from build output"

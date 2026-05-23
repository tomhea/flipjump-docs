"""Shared pytest setup.

Puts `docs/_ext/` on sys.path so the `fj_stl_extract` package is
importable from tests without requiring a separate `pip install -e .`
step. This makes the test suite work on Python versions that don't
satisfy the project's `requires-python` (e.g. local dev on 3.11 while
CI runs 3.12).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = REPO_ROOT / "docs" / "_ext"

if str(EXT_DIR) not in sys.path:
    sys.path.insert(0, str(EXT_DIR))

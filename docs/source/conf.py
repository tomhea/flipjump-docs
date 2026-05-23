"""Sphinx configuration for fjdocs.tomhe.app.

M4: adds the `fj_stl_extract` extension which parses every .fj file
under vendor/flip-jump/flipjump/stl/ and renders per-file + per-macro
Markdown pages into stl/_generated/ on every build.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Put our extension package on sys.path so `extensions = ["fj_stl_extract"]`
# can find it. The package lives outside source/ to keep the Sphinx
# source tree clean.
_EXT_DIR = (Path(__file__).resolve().parent.parent / "_ext")
if str(_EXT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXT_DIR))

project = "FlipJump"
author = "Tom Herman"
copyright = "2026, Tom Herman"  # noqa: A001 — shadows Sphinx config slot
release = "0.4"

extensions = [
    "myst_parser",
    "fj_stl_extract",
]

# Path resolution: from docs/source/conf.py, the flip-jump submodule
# sits at ../../vendor/flip-jump/flipjump/stl. This is the default in
# the extension; declared here for visibility.
fj_stl_root = "../../vendor/flip-jump/flipjump/stl"
fj_stl_output = "stl/_generated"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "attrs_inline",
    "attrs_block",
    "fieldlist",
]
myst_heading_anchors = 3

source_suffix = {
    ".md": "markdown",
    ".rst": "restructuredtext",
}

exclude_patterns: list[str] = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

html_theme = "furo"
html_title = "FlipJump"

# Custom Pygments style matching the FlipJump IDE's `fj-dark` theme so
# code blocks here look identical to code in the editor at fj.tomhe.app.
# The module-path string lets Sphinx import it as a custom style class.
pygments_style = "fj_stl_extract.pygments_style.FlipJumpDarkStyle"
pygments_dark_style = "fj_stl_extract.pygments_style.FlipJumpDarkStyle"

# Permanent "Try the IDE" link will move into html_theme_options in M8;
# left out at M1 so empty-scaffold Furo defaults render cleanly.

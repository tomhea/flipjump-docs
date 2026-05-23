"""Sphinx configuration for fjdocs.tomhe.app.

Minimal at M1: Furo theme + MyST Markdown parser only.
Extensions for the STL extractor, custom Pygments lexer, sitemap, and
not-found page land in later milestones (see plan v0.4, v0.5, v0.9).
"""

from __future__ import annotations

project = "FlipJump"
author = "Tom Herman"
copyright = "2026, Tom Herman"  # noqa: A001 — shadows Sphinx config slot
release = "0.1"

extensions = [
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "attrs_inline",
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

# Permanent "Try the IDE" link will move into html_theme_options in M8;
# left out at M1 so empty-scaffold Furo defaults render cleanly.

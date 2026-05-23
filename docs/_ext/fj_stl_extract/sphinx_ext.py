"""Sphinx extension hook.

Wires the extractor + renderer into the Sphinx build via the
`builder-inited` event so the generated Markdown pages exist before
Sphinx reads the source tree.

Configuration values (set in `conf.py`):

    fj_stl_root      Path to the flipjump/stl/ directory inside a
                     flip-jump checkout. Defaults to ../../vendor/flip-jump/flipjump/stl
                     relative to confdir (which matches the layout
                     this repo's submodule sits at).

    fj_stl_output    Sphinx-source-relative path where the generated
                     pages should land. Defaults to "stl/_generated".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .pipeline import extract_stl
from .renderer import render_stl

__all__ = ["setup"]


def setup(app: Any) -> dict[str, Any]:  # `Any` to avoid hard sphinx dep at import time
    app.add_config_value("fj_stl_root", "../../vendor/flip-jump/flipjump/stl", "env")
    app.add_config_value("fj_stl_output", "stl/_generated", "env")
    app.connect("builder-inited", _on_builder_inited)
    return {
        "version": "0.4",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _on_builder_inited(app: Any) -> None:
    # Resolve paths relative to the Sphinx conf directory.
    confdir = Path(app.confdir)
    stl_root = (confdir / app.config.fj_stl_root).resolve()
    out_dir = (app.srcdir / app.config.fj_stl_output).resolve()

    try:
        index = extract_stl(stl_root)
    except FileNotFoundError as e:
        from sphinx.errors import ExtensionError
        raise ExtensionError(
            f"fj_stl_extract: cannot find STL source at {stl_root}.\n"
            f"Run `git submodule update --init --recursive` and try again.\n"
            f"(Underlying error: {e})"
        )

    render_stl(index, out_dir)

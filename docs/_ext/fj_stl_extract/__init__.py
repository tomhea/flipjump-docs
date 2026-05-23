"""FlipJump STL extractor.

Parses every .fj file under a flip-jump checkout's `flipjump/stl/`
directory (driven by `conf.json`), extracts macros + namespaces +
doc comments + complexity tags, and builds a dependency graph.

The renderer (per-macro and per-file Markdown pages) lives in M4 — this
package, at M3, produces only a structured Python object graph and a
JSON dump exposed via `python -m fj_stl_extract`.

Sphinx extension entry point will be wired in M4 when the renderer
exists. At M3 importing this module is the only public API.
"""

from __future__ import annotations

from .sphinx_ext import setup

__all__ = ["setup"]

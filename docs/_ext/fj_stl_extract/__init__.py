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

# Public re-exports populated as modules are built across the milestones.
# At M3 only the tokenizer + parser + pipeline live here; the Sphinx
# extension hook (`def setup(app):`) lands in M4 with the renderer.
__all__: list[str] = []

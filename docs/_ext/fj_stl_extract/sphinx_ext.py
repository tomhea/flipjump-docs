"""Sphinx extension hook.

Wires the extractor + renderer + Pygments lexer/style into the Sphinx
build via the `builder-inited` event so the generated Markdown pages
exist before Sphinx reads the source tree.

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
from .pygments_lexer import FlipJumpLexer
from .pygments_style import FlipJumpDarkStyle
from .renderer import render_stl

__all__ = ["setup"]


def setup(app: Any) -> dict[str, Any]:  # `Any` to avoid hard sphinx dep at import time
    app.add_config_value("fj_stl_root", "../../vendor/flip-jump/flipjump/stl", "env")
    app.add_config_value("fj_stl_output", "stl", "env")
    app.add_lexer("fj", FlipJumpLexer)
    # Sphinx's add_lexer only registers the alias passed to it. Other
    # aliases on the lexer class (`flipjump`, `FlipJump`) work because
    # Pygments' own get_lexer_by_name picks them up from the class's
    # aliases attribute when the lexer is importable.
    app.connect("builder-inited", _on_builder_inited)
    app.connect("html-page-context", _add_extra_favicon_links)
    return {
        "version": "0.5",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _on_builder_inited(app: Any) -> None:
    from sphinx.errors import ExtensionError

    # Resolve paths relative to the Sphinx conf directory.
    confdir = Path(app.confdir)
    stl_root = (confdir / app.config.fj_stl_root).resolve()
    out_dir = (app.srcdir / app.config.fj_stl_output).resolve()

    try:
        index = extract_stl(stl_root)
    except FileNotFoundError as e:
        raise ExtensionError(
            f"fj_stl_extract: cannot find STL source at {stl_root}.\n"
            f"Run `git submodule update --init --recursive` and try again.\n"
            f"(Underlying error: {e})"
        )

    try:
        render_stl(index, out_dir)
    except (OSError, PermissionError) as e:
        raise ExtensionError(
            f"fj_stl_extract: failed to write generated pages to {out_dir}.\n"
            f"Check filesystem permissions and that the path is writable.\n"
            f"(Underlying error: {type(e).__name__}: {e})"
        )
    except Exception as e:  # noqa: BLE001 — friendly Sphinx error surface
        # Jinja2 template errors, key errors, anything else — surface as
        # an ExtensionError so Sphinx prints something readable instead
        # of a raw traceback during the build.
        raise ExtensionError(
            f"fj_stl_extract: render failed.\n"
            f"(Underlying error: {type(e).__name__}: {e})"
        )


# Extra <link> tags injected into every page's <head>. Furo refuses to
# be extended via layout.html, and Sphinx's html_favicon config covers
# only the .ico. We append to `metatags` (which Furo / Sphinx render
# inside <head>) so the apple-touch-icon and high-DPI PNG favicon are
# picked up by browsers on every page.
_EXTRA_HEAD_LINKS = (
    '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">\n'
    '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">'
)


def _add_extra_favicon_links(app: Any, pagename: str, templatename: str,
                             context: dict, doctree: Any) -> None:
    existing = context.get("metatags", "")
    context["metatags"] = (existing + "\n" + _EXTRA_HEAD_LINKS) if existing else _EXTRA_HEAD_LINKS

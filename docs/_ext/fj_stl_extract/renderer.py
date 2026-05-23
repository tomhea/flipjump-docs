"""Render the parsed StlIndex into Markdown pages.

Output layout under `output_dir/`:

    _root.md                          — master toctree of all file pages
    file--<flattened-rel-path>.md     — one per .fj source file
    macro--<fq-name>--<arity>.md      — one per macro (orphan; linked from file pages)

The hand-written `docs/source/stl/index.md` toctrees `_root` and any
sibling intro pages.

Slug rules (must be stable across regenerations so URLs don't churn):

    file slug:  "file--" + rel_path.replace("/", "-")
                e.g. "bit/math" → "file--bit-math"
    macro slug: "macro--" + fq_name + "--" + arity
                e.g. "stl.startup" arity 0 → "macro--stl.startup--0"

Slugs use `--` as a delimiter that won't collide with `.` namespace
separators or `/` directory separators.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import jinja2

from .dep_graph import macro_key
from .pipeline import ExtractedFile, StlIndex
from .parser import MacroNode

__all__ = ["render_stl", "file_slug", "macro_slug"]


TEMPLATES_DIR = Path(__file__).parent / "templates"


def file_slug(rel_path: str) -> str:
    return "file--" + rel_path.replace("/", "-")


def macro_slug(macro: MacroNode) -> str:
    return f"macro--{macro.fq_name}--{macro.arity}"


def _short_desc(text: str) -> str:
    """First non-empty line of a description, truncated for compact lists."""
    if not text:
        return ""
    for line in text.split("\n"):
        line = line.strip()
        if line:
            return line[:140]
    return ""


@dataclass
class _MacroLink:
    fq_name: str
    arity: int
    link: str
    has_overloads: bool = False


def render_stl(index: StlIndex, output_dir: str | Path) -> list[Path]:
    """Render `index` to Markdown files under `output_dir`.

    Returns the list of written paths so the Sphinx extension can pass
    them to the build's mtime cache. Existing stale files (not in the
    returned list) are removed so a deleted upstream macro's page
    disappears from the next build.
    """
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,                # rendering Markdown, not HTML
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    macro_tpl = env.get_template("macro.md.j2")
    file_tpl = env.get_template("file.md.j2")
    root_tpl = env.get_template("stl_root.md.j2")

    # Pre-compute overload sets so the page header can include the arity
    # only when ambiguity exists.
    overload_keys: set[str] = set()
    by_fq: dict[str, int] = defaultdict(int)
    for f in index.files:
        for m in f.file_node.macros:
            by_fq[m.fq_name] += 1
    overload_keys = {fq for fq, n in by_fq.items() if n > 1}

    # Reverse macro_key → MacroNode + file index so we can resolve dep
    # graph edges to actual files (for the link path).
    macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]] = {}
    for f in index.files:
        for m in f.file_node.macros:
            macro_by_key[macro_key(m)] = (m, f)

    written: list[Path] = []

    # ---------- per-macro pages ----------
    for f in index.files:
        for m in f.file_node.macros:
            ctx = _macro_context(
                macro=m,
                file=f,
                index=index,
                has_overloads=m.fq_name in overload_keys,
                macro_by_key=macro_by_key,
            )
            text = macro_tpl.render(**ctx)
            path = out / (macro_slug(m) + ".md")
            path.write_text(text, encoding="utf-8")
            written.append(path)

    # ---------- per-file pages ----------
    for f in index.files:
        ctx = _file_context(
            file=f,
            has_overloads_fn=lambda fq: fq in overload_keys,
        )
        text = file_tpl.render(**ctx)
        path = out / (file_slug(f.rel_path) + ".md")
        path.write_text(text, encoding="utf-8")
        written.append(path)

    # ---------- root toctree ----------
    text = root_tpl.render(
        files=[{"slug": file_slug(f.rel_path)} for f in index.files],
    )
    root_path = out / "_root.md"
    root_path.write_text(text, encoding="utf-8")
    written.append(root_path)

    # ---------- prune stale ----------
    keep = {p.name for p in written}
    for existing in out.glob("*.md"):
        if existing.name not in keep:
            existing.unlink()

    return written


def _macro_context(*, macro: MacroNode, file: ExtractedFile, index: StlIndex,
                   has_overloads: bool,
                   macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]]
                   ) -> dict:
    doc = file.docs.get(id(macro))
    deps = sorted(index.dep_graph.depends_on.get(macro_key(macro), set())) \
        if index.dep_graph else []
    users = sorted(index.dep_graph.used_by.get(macro_key(macro), set())) \
        if index.dep_graph else []

    return {
        "macro": _ProxyMacro(macro, doc),
        "file_rel": file.rel_path,
        "file_link": file_slug(file.rel_path) + ".md",
        "has_overloads": has_overloads,
        "depends_on": [_resolve_link(k, macro_by_key) for k in deps
                       if k in macro_by_key],
        "used_by": [_resolve_link(k, macro_by_key) for k in users
                    if k in macro_by_key],
    }


def _file_context(*, file: ExtractedFile, has_overloads_fn) -> dict:
    macros_by_ns: dict[str, list[MacroNode]] = defaultdict(list)
    for m in file.file_node.macros:
        ns = ".".join(m.namespace_path)
        macros_by_ns[ns].append(m)

    proxied = {
        ns: [_FileLinkMacro(m, file.docs.get(id(m)),
                             has_overloads_fn(m.fq_name))
             for m in ms]
        for ns, ms in macros_by_ns.items()
    }
    constants = [_FileLinkConst(c, file.docs.get(id(c)))
                 for c in file.file_node.constants]

    # File-level description: first non-empty contiguous comment at the
    # very top of the source (before any code), if any.
    file_description = _extract_file_intro(file.source)

    return {
        "file_rel": file.rel_path,
        "file_description": file_description,
        "constants": constants,
        "macros": file.file_node.macros,  # presence flag for the template
        "macros_by_namespace": proxied,
    }


def _extract_file_intro(source: str) -> str:
    """First contiguous `//` comment block at the top of source, with the
    `// ` prefix stripped. Useful for a file-level intro blurb."""
    lines: list[str] = []
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped and not lines:
            continue  # skip leading blanks
        if not stripped:
            break  # blank after a comment block → boundary
        if not stripped.startswith("//"):
            break
        body = stripped[2:]
        if body.startswith(" "):
            body = body[1:]
        lines.append(body)
    return "\n".join(lines).strip()


# ---------- small proxy classes that adapt parser dataclasses to the templates ----------

class _ProxyMacro:
    """Adapter around a MacroNode that also exposes its DocInfo."""
    def __init__(self, macro: MacroNode, doc):
        self._macro = macro
        self.doc = doc or _EmptyDoc()

    def __getattr__(self, name):
        return getattr(self._macro, name)


class _FileLinkMacro:
    """Macro adapter for the per-file page (adds `link` and `short_desc`)."""
    def __init__(self, macro: MacroNode, doc, has_overloads: bool):
        self.fq_name = macro.fq_name
        self.arity = macro.arity
        self.params = macro.params
        self.has_overloads = has_overloads
        self.link = macro_slug(macro) + ".md"
        self.doc = doc
        self.short_desc = _short_desc(doc.description) if doc else ""


class _FileLinkConst:
    def __init__(self, const, doc):
        self.fq_name = const.fq_name
        self.expr = " ".join(t.text for t in const.expr_tokens)
        self.doc = doc


class _EmptyDoc:
    description = ""
    time_complexity = None
    space_complexity = None
    requires: list[str] = []
    output_params: dict[str, str] = {}


def _resolve_link(key: str,
                  macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]]
                  ) -> _MacroLink:
    macro, _file = macro_by_key[key]
    return _MacroLink(
        fq_name=macro.fq_name,
        arity=macro.arity,
        link=macro_slug(macro) + ".md",
        has_overloads=False,
    )

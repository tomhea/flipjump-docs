"""Render the parsed StlIndex into Markdown pages.

Output layout under `output_dir/` (typically `docs/source/stl/`):

    <rel_path>.md                       — one per .fj source file
    <rel_path>/<name>--<arity>.md       — one per macro
    .render_manifest.json               — what we wrote last time (for pruning)

Examples:

    runlib.fj                           → runlib.md
    runlib's stl.startup arity 1        → runlib/startup--1.md
    bit/math.fj                         → bit/math.md
    bit/math's add arity 3              → bit/math/add--3.md
    hex/pointers/stack.fj               → hex/pointers/stack.md
    that file's push--1                 → hex/pointers/stack/push--1.md

Page URLs match these paths verbatim (`/stl/bit/math.html`,
`/stl/bit/math/add--3.html`).

Slug rules:

    macro slug:  "<name>--<arity>" inside the file's directory
    file slug:   "<rel_path>" verbatim, mirroring conf.json's "all" list

These slugs are stable across regenerations: same upstream macro
always lands at the same URL.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import jinja2

from .dep_graph import macro_key
from .pipeline import ExtractedFile, StlIndex
from .parser import MacroNode

__all__ = ["render_stl", "file_doc_path", "macro_doc_path"]


TEMPLATES_DIR = Path(__file__).parent / "templates"
_MANIFEST_NAME = ".render_manifest.json"


# ---------- path helpers ----------

def file_doc_path(rel_path: str) -> str:
    """Doc path within the STL output dir (POSIX-style, without `.md`)
    for a file page.

    `rel_path` is the path from conf.json (e.g. `runlib`, `bit/math`,
    `hex/pointers/stack`). The doc path is identical — the file page
    lives at `<output_dir>/<rel_path>.md`."""
    return rel_path


def macro_doc_path(macro: MacroNode, file_rel: str) -> str:
    """Doc path within the STL output dir (POSIX-style, without `.md`)
    for a macro page."""
    return f"{file_rel}/{macro.name}--{macro.arity}"


def _link_md(from_doc: str, to_doc: str) -> str:
    """Compute the relative `.md` link from `from_doc` to `to_doc`.
    Both are doc paths (no `.md` extension) under the SAME root."""
    from_dir = os.path.dirname(from_doc)
    target = to_doc + ".md"
    if not from_dir:
        return target
    return os.path.relpath(target, start=from_dir).replace(os.sep, "/")


def _link_to_source_root(from_stl_doc: str, to_source_doc: str,
                         stl_output_prefix: str) -> str:
    """Compute a link from an STL doc page to a page elsewhere in the
    Sphinx source tree (e.g. `language/complexity`).

    `from_stl_doc` is the STL-relative doc path (e.g. `bit/casting/ascii2bin--3`).
    `to_source_doc` is the SOURCE-relative doc path (e.g. `language/complexity`).
    `stl_output_prefix` is where in the source tree the STL output lives
    (typically `stl`).
    """
    full_from = f"{stl_output_prefix}/{from_stl_doc}" if stl_output_prefix else from_stl_doc
    return _link_md(full_from, to_source_doc)


def _short_desc(text: str) -> str:
    """First content line of a description, suitable as the inline
    summary in a list bullet.

    Prefers PROSE lines over indented pseudocode (e.g. for `bit.swap`
    whose first source line is `//   a, b = b, a` and second is
    `// a,b are bits.`, the pseudocode is bad summary material — the
    prose is much more informative).

    Truncates long lines on word boundaries and never cuts inside an
    inline-code backtick pair (which would leave a stray ``` ` ```
    in the output).
    """
    if not text:
        return ""

    lines = [line.rstrip() for line in text.split("\n")]

    for line in lines:
        stripped = line.strip()
        if stripped and not line.startswith("  "):
            return _truncate(stripped, 140)

    for line in lines:
        stripped = line.strip()
        if stripped:
            return _truncate(stripped, 140)

    return ""


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    if cut.count("`") % 2 == 1:
        cut = cut.rsplit("`", 1)[0].rstrip()
    return cut + " …"


@dataclass
class _MacroLink:
    fq_name: str
    arity: int
    link: str
    has_overloads: bool = False


def render_stl(index: StlIndex, output_dir: str | Path,
               stl_output_prefix: str = "stl") -> list[Path]:
    """Render `index` to Markdown files under `output_dir`.

    Pruning is manifest-based: we write `.render_manifest.json` after
    every successful render and compare against it on the next run.
    Stale files are removed; empty directories left behind get cleaned
    up too. The hand-written `index.md` (and any other file we never
    write) is therefore safe to live in the same `output_dir`.

    `stl_output_prefix` is where in the Sphinx source tree this
    `output_dir` lives. Used to compute correct relative links from
    macro pages to pages OUTSIDE the STL tree (e.g. the complexity
    glossary at `language/complexity.md`).
    """
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    macro_tpl = env.get_template("macro.md.j2")
    file_tpl = env.get_template("file.md.j2")

    # Pre-compute overload sets (arity ambiguity per fq-name).
    by_fq: dict[str, int] = defaultdict(int)
    for f in index.files:
        for m in f.file_node.macros:
            by_fq[m.fq_name] += 1
    overload_keys = {fq for fq, n in by_fq.items() if n > 1}

    # Reverse macro_key → (MacroNode, file). Needed to resolve dep
    # graph edges into actual file/macro paths for link computation.
    macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]] = {}
    for f in index.files:
        for m in f.file_node.macros:
            macro_by_key[macro_key(m)] = (m, f)

    written: list[Path] = []

    # ---------- per-macro pages ----------
    for f in index.files:
        for m in f.file_node.macros:
            macro_doc = macro_doc_path(m, f.rel_path)
            ctx = _macro_context(
                macro=m,
                file=f,
                index=index,
                has_overloads=m.fq_name in overload_keys,
                macro_by_key=macro_by_key,
                overload_keys=overload_keys,
                macro_doc=macro_doc,
                stl_output_prefix=stl_output_prefix,
            )
            text = macro_tpl.render(**ctx)
            path = out / (macro_doc + ".md")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written.append(path)

    # ---------- per-file pages ----------
    for f in index.files:
        file_doc = file_doc_path(f.rel_path)
        ctx = _file_context(
            file=f,
            has_overloads_fn=lambda fq: fq in overload_keys,
            file_doc=file_doc,
        )
        text = file_tpl.render(**ctx)
        path = out / (file_doc + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)

    # ---------- prune stale files via manifest ----------
    _prune_via_manifest(out, written)

    return written


def _prune_via_manifest(out: Path, written: list[Path]) -> None:
    """Delete any file we wrote on a previous render that we did NOT
    write this time. The manifest lives at `<out>/.render_manifest.json`."""
    manifest_path = out / _MANIFEST_NAME
    new_rel = {p.relative_to(out).as_posix() for p in written}

    if manifest_path.exists():
        try:
            old_rel = set(
                json.loads(manifest_path.read_text(encoding="utf-8")).get("files", [])
            )
        except (json.JSONDecodeError, OSError):
            old_rel = set()
        for stale in old_rel - new_rel:
            stale_path = out / stale
            if stale_path.exists():
                stale_path.unlink()
        # Best-effort: prune empty directories left behind.
        for stale in sorted(old_rel - new_rel, key=lambda p: -p.count("/")):
            parent = (out / stale).parent
            while parent != out and parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

    manifest_path.write_text(
        json.dumps({"files": sorted(new_rel)}, indent=2),
        encoding="utf-8",
    )


def _macro_context(*, macro: MacroNode, file: ExtractedFile, index: StlIndex,
                   has_overloads: bool,
                   macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]],
                   overload_keys: set[str],
                   macro_doc: str,
                   stl_output_prefix: str,
                   ) -> dict:
    doc = file.docs.get(id(macro))
    deps = sorted(index.dep_graph.depends_on.get(macro_key(macro), set())) \
        if index.dep_graph else []
    users = sorted(index.dep_graph.used_by.get(macro_key(macro), set())) \
        if index.dep_graph else []

    file_doc = file_doc_path(file.rel_path)

    return {
        "macro": _ProxyMacro(macro, doc),
        "file_rel": file.rel_path,
        "file_link": _link_md(macro_doc, file_doc),
        "glossary_link": _link_to_source_root(
            macro_doc, "language/complexity", stl_output_prefix
        ),
        "has_overloads": has_overloads,
        "depends_on": [
            _resolve_link(k, macro_by_key, overload_keys, from_doc=macro_doc)
            for k in deps if k in macro_by_key
        ],
        "used_by": [
            _resolve_link(k, macro_by_key, overload_keys, from_doc=macro_doc)
            for k in users if k in macro_by_key
        ],
    }


def _file_context(*, file: ExtractedFile, has_overloads_fn, file_doc: str) -> dict:
    macros_by_ns: dict[str, list[MacroNode]] = defaultdict(list)
    for m in file.file_node.macros:
        ns = ".".join(m.namespace_path)
        macros_by_ns[ns].append(m)

    proxied = {
        ns: [_FileLinkMacro(m, file.docs.get(id(m)),
                             has_overloads_fn(m.fq_name),
                             from_doc=file_doc, file_rel=file.rel_path)
             for m in ms]
        for ns, ms in macros_by_ns.items()
    }
    constants = [_FileLinkConst(c, file.docs.get(id(c)))
                 for c in file.file_node.constants]

    file_description = _extract_file_intro(file.source)

    return {
        "file_rel": file.rel_path,
        "file_description": file_description,
        "constants": constants,
        "macros": file.file_node.macros,
        "macros_by_namespace": proxied,
    }


def _extract_file_intro(source: str) -> str:
    """First contiguous `//` comment block at the top of source, with the
    `// ` prefix stripped. Useful for a file-level intro blurb."""
    lines: list[str] = []
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped and not lines:
            continue
        if not stripped:
            break
        if not stripped.startswith("//"):
            break
        body = stripped[2:]
        if body.startswith(" "):
            body = body[1:]
        lines.append(body)
    return "\n".join(lines).strip()


# ---------- proxy classes for templates ----------

class _ProxyMacro:
    def __init__(self, macro: MacroNode, doc):
        self._macro = macro
        self.doc = doc or _EmptyDoc()

    def __getattr__(self, name):
        return getattr(self._macro, name)


class _FileLinkMacro:
    """Macro adapter for the per-file page (adds `link` and `short_desc`)."""
    def __init__(self, macro: MacroNode, doc, has_overloads: bool,
                 from_doc: str, file_rel: str):
        self.fq_name = macro.fq_name
        self.arity = macro.arity
        self.params = macro.params
        self.has_overloads = has_overloads
        self.link = _link_md(from_doc, macro_doc_path(macro, file_rel))
        self.doc = doc
        self.short_desc = _short_desc(doc.description) if doc else ""


class _FileLinkConst:
    def __init__(self, const, doc):
        self.fq_name = const.fq_name
        self.expr = " ".join(t.text for t in const.expr_tokens)
        self.doc = doc


@dataclass
class _EmptyDoc:
    description: str = ""
    time_complexity: str | None = None
    space_complexity: str | None = None
    requires: list[str] = field(default_factory=list)
    output_params: dict[str, str] = field(default_factory=dict)


def _resolve_link(key: str,
                  macro_by_key: dict[str, tuple[MacroNode, ExtractedFile]],
                  overload_keys: set[str],
                  *,
                  from_doc: str,
                  ) -> _MacroLink:
    macro, file = macro_by_key[key]
    target = macro_doc_path(macro, file.rel_path)
    return _MacroLink(
        fq_name=macro.fq_name,
        arity=macro.arity,
        link=_link_md(from_doc, target),
        has_overloads=macro.fq_name in overload_keys,
    )

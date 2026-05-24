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
import re
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

    The STL convention is:

        // Time/Space complexity lines           ← stripped by doc_attach
        // optional note/warning prose
        //   indented intent summary             ← THIS is the natural summary
        // longer prose explanation

    So: prefer the FIRST INDENTED LINE (the conventional "intent
    summary"), falling back to the first non-blank line if there is
    no indented line. This fixes cases like `bit.inc1` and
    `bit.exact_xor` where the first non-indented line is a warning
    or a note about implementation details — those should not be
    surfaced as the macro's one-line summary.

    Truncates long lines on word boundaries and never cuts inside an
    inline-code backtick pair.
    """
    if not text:
        return ""

    lines = [line.rstrip() for line in text.split("\n")]

    # Pass 1: prefer indented (2+ space) lines.
    for line in lines:
        if line.startswith("  ") and line.strip():
            return _truncate(line.strip(), 140)

    # Pass 2: fall back to the first non-blank line.
    for line in lines:
        if line.strip():
            return _truncate(line.strip(), 140)

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
    ns_index_tpl = env.get_template("namespace_index.md.j2")
    all_macros_tpl = env.get_template("all_macros.md.j2")

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

    # ---------- per-namespace index pages ----------
    # For each STL subdirectory (`bit/`, `hex/`, `hex/pointers/`) we
    # emit an `index.md` listing the files under it. Sphinx + Furo
    # then automatically include this in the sidebar tree under the
    # corresponding directory node.
    ns_dirs = _collect_namespace_dirs(index)
    for ns_path, ns_files in ns_dirs.items():
        ctx = _namespace_index_context(
            ns_path=ns_path,
            files=ns_files,
            all_files=index.files,
        )
        text = ns_index_tpl.render(**ctx)
        path = out / ns_path / "index.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written.append(path)

    # ---------- alphabetical macro index ----------
    all_macros_rows = []
    for f in index.files:
        for m in f.file_node.macros:
            doc = f.docs.get(id(m))
            short = _short_desc(
                _resolve_directive_markers(doc.description, "")
                if doc and doc.description else ""
            )
            all_macros_rows.append({
                "fq_name": m.fq_name,
                "arity": m.arity,
                "file_rel": f.rel_path,
                "link": _link_md("all_macros", macro_doc_path(m, f.rel_path)),
                "time": doc.time_complexity if doc else None,
                "space": doc.space_complexity if doc else None,
                "short": short,
            })
    all_macros_rows.sort(key=lambda r: (r["fq_name"], r["arity"]))
    all_macros_text = all_macros_tpl.render(rows=all_macros_rows)
    all_macros_path = out / "all_macros.md"
    all_macros_path.write_text(all_macros_text, encoding="utf-8")
    written.append(all_macros_path)

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
    source_body = _extract_macro_source(file.source, macro.start_line, macro.end_line)
    callsites = _find_callsites(macro, index, limit=3)
    sibling_macros = [m for m in file.file_node.macros]
    prev_macro, next_macro = _prev_next(macro, sibling_macros)

    directives_link = _link_to_source_root(
        macro_doc, "language/directives", stl_output_prefix
    )
    return {
        "macro": _ProxyMacro(macro, doc, directives_link),
        "file_rel": file.rel_path,
        "file_link": _link_md(macro_doc, file_doc),
        "glossary_link": _link_to_source_root(
            macro_doc, "language/complexity", stl_output_prefix
        ),
        "directives_link": directives_link,
        "has_overloads": has_overloads,
        "depends_on": [
            _resolve_link(k, macro_by_key, overload_keys, from_doc=macro_doc)
            for k in deps if k in macro_by_key
        ],
        "used_by": [
            _resolve_link(k, macro_by_key, overload_keys, from_doc=macro_doc)
            for k in users if k in macro_by_key
        ],
        "source_body": source_body,
        "callsites": callsites,
        "prev_macro": (_prev_next_link(prev_macro, file.rel_path, overload_keys,
                                       from_doc=macro_doc)
                       if prev_macro is not None else None),
        "next_macro": (_prev_next_link(next_macro, file.rel_path, overload_keys,
                                       from_doc=macro_doc)
                       if next_macro is not None else None),
        # JSON-LD structured data (Polish #D3) — TechArticle markup so
        # search engines understand this is API docs for a specific
        # macro with a fixed identifier.
        "json_ld": json.dumps({
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": f"{macro.fq_name} (arity {macro.arity})",
            "description": (
                # Resolve directive markers AND drop the trailing
                # backticks/spaces from the first description line so
                # nothing zero-width-space-wrapped leaks into the
                # JSON-LD <script> block. The empty directives_link
                # arg makes the resolver strip markers to bare names.
                _resolve_directive_markers(
                    doc.description.split("\n")[0], ""
                ).strip().strip("`")
                if doc and doc.description
                else f"FlipJump STL macro {macro.fq_name}"
            ),
            "url": f"https://fjdocs.tomhe.app/{stl_output_prefix}/{macro_doc}.html",
            "isPartOf": {
                "@type": "TechArticle",
                "name": "FlipJump Standard Library",
                "url": "https://fjdocs.tomhe.app/stl/",
            },
            "proficiencyLevel": "Expert",
        }),
    }


def _extract_macro_source(source: str, start_line: int, end_line: int) -> str:
    """Return the lines of `source` from start_line..end_line inclusive
    (1-indexed). The renderer puts this in a collapsible code block on
    each macro page so readers can see the actual implementation."""
    lines = source.splitlines()
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        return ""
    return "\n".join(lines[start_line - 1 : end_line])


def _find_callsites(target: MacroNode, index: StlIndex,
                    limit: int) -> list[dict]:
    """Find up to `limit` macros that call `target`. Returns dicts with
    `caller_name`, `file_rel`, `line` so the template can show short
    "Example uses" snippets."""
    if not index.dep_graph:
        return []
    target_key = macro_key(target)
    callsites: list[dict] = []
    for f in index.files:
        for caller in f.file_node.macros:
            if caller is target:
                continue
            caller_key = macro_key(caller)
            if target_key in index.dep_graph.depends_on.get(caller_key, set()):
                callsites.append({
                    "caller_fq": caller.fq_name,
                    "caller_arity": caller.arity,
                    "file_rel": f.rel_path,
                    "start_line": caller.start_line,
                    "end_line": caller.end_line,
                })
                if len(callsites) >= limit:
                    return callsites
    return callsites


def _prev_next(macro: MacroNode, siblings: list[MacroNode]
               ) -> tuple[MacroNode | None, MacroNode | None]:
    """Find the macro before and after `macro` in its file's source-order
    macro list. None if `macro` is at an edge."""
    try:
        idx = siblings.index(macro)
    except ValueError:
        return None, None
    prev = siblings[idx - 1] if idx > 0 else None
    nxt = siblings[idx + 1] if idx + 1 < len(siblings) else None
    return prev, nxt


def _prev_next_link(target: MacroNode, file_rel: str,
                    overload_keys: set[str], from_doc: str) -> dict:
    return {
        "fq_name": target.fq_name,
        "arity": target.arity,
        "has_overloads": target.fq_name in overload_keys,
        "link": _link_md(from_doc, macro_doc_path(target, file_rel)),
    }


def _file_context(*, file: ExtractedFile, has_overloads_fn, file_doc: str) -> dict:
    macros_by_ns: dict[str, list[MacroNode]] = defaultdict(list)
    for m in file.file_node.macros:
        ns = ".".join(m.namespace_path)
        macros_by_ns[ns].append(m)

    # File pages compute their own directives link (different depth
    # than macro pages — file pages are one level shallower).
    directives_link = _link_to_source_root(
        file_doc, "language/directives", "stl"
    )

    proxied = {
        ns: [_FileLinkMacro(m, file.docs.get(id(m)),
                             has_overloads_fn(m.fq_name),
                             from_doc=file_doc, file_rel=file.rel_path,
                             directives_link=directives_link)
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


def _collect_namespace_dirs(index: StlIndex) -> dict[str, list[ExtractedFile]]:
    """Return a mapping of namespace dir path → files under it.

    For an STL with `runlib`, `bit/memory`, `bit/math`,
    `hex/pointers/stack`, this returns:
        {"bit": [bit/memory, bit/math, ...],
         "hex": [hex/memory, ...],
         "hex/pointers": [hex/pointers/basic_pointers, ...]}

    Top-level files (no `/`) get no namespace entry — they appear in
    the stl/index.md root toctree.
    """
    by_dir: dict[str, list[ExtractedFile]] = defaultdict(list)
    for f in index.files:
        if "/" not in f.rel_path:
            continue
        # For each containing directory, add the file.
        parts = f.rel_path.split("/")
        for depth in range(1, len(parts)):
            ns_dir = "/".join(parts[:depth])
            by_dir[ns_dir].append(f)
    return by_dir


# Hand-authored prose for the three known namespace directories. The
# user pointed at the README in https://github.com/tomhea/flip-jump/
# tree/main/flipjump/stl as the source for these blurbs.
_NAMESPACE_INTROS: dict[str, str] = {
    "bit": (
        "The `bit` namespace holds the bit-level standard library: "
        "every operation works on one bit at a time, or on a vector "
        "of `n` bits packed in memory. Use it when you need precise "
        "single-bit control — boolean logic, bit-shift loops, "
        "individual flag manipulation.\n\n"
        "Bit-level operations are simpler and easier to reason about "
        "than the hex equivalents, but they are slower per useful "
        "value computed: a single decimal digit takes roughly four "
        "bit operations vs one hex operation. For arithmetic-heavy "
        "code prefer the [`hex` namespace](../hex/index.md)."
    ),
    "hex": (
        "The `hex` namespace holds the hex-level standard library: "
        "every variable is a 4-bit nibble, and arithmetic is driven "
        "by precomputed lookup tables initialised by `hex.init`. "
        "Use it when you need fast arithmetic on multi-digit values — "
        "addition, multiplication, division, comparison, and so on.\n\n"
        "Hex operations are 4× denser than the bit equivalents (1 nibble "
        "= 4 bits) and the table-driven ops run in roughly constant "
        "operations per nibble instead of growing with the bit width. "
        "Pointer and stack support is layered on top in the "
        "[`hex.pointers` namespace](pointers/index.md)."
    ),
    "hex/pointers": (
        "The `hex.pointers` namespace adds pointer arithmetic, "
        "indirect read/write, and a stack to the hex variable model. "
        "Pointers are nibble-vectors holding an absolute bit address; "
        "the macros emit the self-modifying jump-target sequences "
        "needed to follow a pointer at run time.\n\n"
        "Before using any `hex.pointers.*` macro the program must "
        "call `hex.pointers.ptr_init` (or the bundled "
        "`stl.startup_and_init_all`) to build the dispatcher tables."
    ),
}


def _namespace_index_context(*, ns_path: str,
                             files: list[ExtractedFile],
                             all_files: list[ExtractedFile]) -> dict:
    intro = _NAMESPACE_INTROS.get(ns_path, "")
    # Children: files that live DIRECTLY in this dir (one level down).
    depth = ns_path.count("/") + 1
    direct_children = [
        f for f in files
        if f.rel_path.count("/") == depth
    ]
    # Sub-namespaces: dirs one level deeper than ns_path.
    sub_ns: list[str] = sorted({
        f.rel_path.rsplit("/", 1)[0]
        for f in files
        if f.rel_path.count("/") > depth and f.rel_path.startswith(ns_path + "/")
    })
    sub_ns = [s for s in sub_ns if s != ns_path]

    return {
        "ns_path": ns_path,
        "ns_short": ns_path.replace("/", "."),
        "ns_intro": intro,
        "direct_files": [
            {"rel": f.rel_path, "slug": f.rel_path.rsplit("/", 1)[-1]}
            for f in direct_children
        ],
        "sub_namespaces": [
            {"rel": s, "slug": s.rsplit("/", 1)[-1]}
            for s in sub_ns
        ],
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

# Zero-width-space-wrapped sentinel `​{DIRECTIVE:name}​` from
# doc_attach. The renderer rewrites these to real Markdown links
# pointing at language/directives.md from the page's correct depth.
_DIRECTIVE_MARKER_RE = re.compile(r"​\{DIRECTIVE:(\w+)\}​")


def _resolve_directive_markers(text: str, directives_link: str) -> str:
    """Replace `{DIRECTIVE:name}` sentinels from doc_attach with real
    Markdown links to the directives reference page."""
    if not directives_link:
        # Caller doesn't care about the link target — strip the markers
        # back to the bare directive name (used by the all-macros
        # alphabetical index where we don't have a per-page directives
        # link).
        return _DIRECTIVE_MARKER_RE.sub(lambda m: f"`{m.group(1)}`", text)
    return _DIRECTIVE_MARKER_RE.sub(
        lambda m: f"[`{m.group(1)}`]({directives_link})", text
    )


class _ProxyMacro:
    def __init__(self, macro: MacroNode, doc, directives_link: str):
        self._macro = macro
        # Resolve directive sentinels in the description to real links
        # pointing at language/directives.md from this macro's depth.
        if doc and doc.description:
            resolved = doc.__class__(
                description=_resolve_directive_markers(doc.description, directives_link),
                time_complexity=doc.time_complexity,
                space_complexity=doc.space_complexity,
                requires=doc.requires,
                output_params=doc.output_params,
                raw_doc_lines=doc.raw_doc_lines,
            )
            self.doc = resolved
        else:
            self.doc = doc or _EmptyDoc()

    def __getattr__(self, name):
        return getattr(self._macro, name)


class _FileLinkMacro:
    """Macro adapter for the per-file page (adds `link` and `short_desc`)."""
    def __init__(self, macro: MacroNode, doc, has_overloads: bool,
                 from_doc: str, file_rel: str, directives_link: str):
        self.fq_name = macro.fq_name
        self.arity = macro.arity
        self.params = macro.params
        self.has_overloads = has_overloads
        self.link = _link_md(from_doc, macro_doc_path(macro, file_rel))
        self.doc = doc
        raw_desc = doc.description if doc else ""
        # Resolve the directive sentinels before truncation so they
        # render as real links in the bullet, not as marker text.
        resolved = _resolve_directive_markers(raw_desc, directives_link)
        self.short_desc = _short_desc(resolved)


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

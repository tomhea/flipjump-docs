"""Renderer contract tests + golden snapshot tests.

The "golden" tests are smoke-level — assert the rendered output
contains the expected key elements rather than byte-for-byte matching
(which would explode on every template tweak).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fj_stl_extract.parser import parse
from fj_stl_extract.dep_graph import build_dep_graph
from fj_stl_extract.doc_attach import attach_docs
from fj_stl_extract.pipeline import ExtractedFile, StlIndex, extract_stl
from fj_stl_extract.renderer import (
    _json_ld,
    file_doc_path,
    macro_doc_path,
    render_stl,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STL_ROOT = REPO_ROOT / "vendor" / "flip-jump" / "flipjump" / "stl"


def _mini_index(source: str, rel_path: str = "fixture") -> StlIndex:
    """Build an in-memory StlIndex from a single source snippet."""
    fn = parse(source)
    docs = attach_docs(source, fn)
    f = ExtractedFile(
        rel_path=rel_path,
        abs_path=f"/fake/{rel_path}.fj",
        source=source,
        file_node=fn,
        docs=docs,
    )
    idx = StlIndex(files=[f])
    idx.dep_graph = build_dep_graph(idx.all_macros)
    return idx


# ---------- path helpers ----------

def test_file_doc_path_preserves_directory_structure():
    assert file_doc_path("hex/pointers/stack") == "hex/pointers/stack"
    assert file_doc_path("runlib") == "runlib"


def test_macro_doc_path_nests_under_file():
    src = "ns stl { def loop {} }"
    [m] = parse(src).macros
    assert macro_doc_path(m, "runlib") == "runlib/loop--0"


# ---------- in-memory render ----------

def test_render_produces_one_file_per_macro_and_one_per_file(tmp_path):
    src = """\
ns stl {
    // first macro
    def loop {}
    // second macro
    def fj f, j { f;j }
}
"""
    idx = _mini_index(src, rel_path="runlib")
    written = render_stl(idx, tmp_path)
    rel_paths = {p.relative_to(tmp_path).as_posix() for p in written}
    assert "runlib.md" in rel_paths
    assert "runlib/loop--0.md" in rel_paths
    assert "runlib/fj--2.md" in rel_paths


def test_macro_page_contains_signature_and_description(tmp_path):
    src = """\
ns stl {
    // Time Complexity: 4@+12
    // adds two values
    def add a, b { x }
}
"""
    idx = _mini_index(src, rel_path="runlib")
    render_stl(idx, tmp_path)
    page = (tmp_path / "runlib" / "add--2.md").read_text(encoding="utf-8")
    assert "stl.add" in page
    assert "def add a, b" in page
    assert "4@+12" in page
    assert "adds two values" in page


def test_arity_overload_pages_are_distinct(tmp_path):
    src = """\
ns stl {
    def wflip_macro dst, val { wflip dst, val }
    def wflip_macro dst, val, jmp { wflip dst, val, jmp }
}
"""
    idx = _mini_index(src, rel_path="runlib")
    render_stl(idx, tmp_path)
    a2 = (tmp_path / "runlib" / "wflip_macro--2.md").read_text(encoding="utf-8")
    a3 = (tmp_path / "runlib" / "wflip_macro--3.md").read_text(encoding="utf-8")
    assert "arity 2" in a2
    assert "arity 3" in a3


def test_file_page_lists_macros_grouped_by_namespace(tmp_path):
    src = """\
ns stl { def loop {} }
ns bit { def helper {} }
"""
    idx = _mini_index(src, rel_path="runlib")
    render_stl(idx, tmp_path)
    page = (tmp_path / "runlib.md").read_text(encoding="utf-8")
    assert "### `stl`" in page
    assert "### `bit`" in page
    assert "stl.loop" in page and "bit.helper" in page


def test_file_page_renders_each_macro_on_its_own_bullet_line(tmp_path):
    """Regression: an earlier template used inline `{% if %}...{% endif %}`
    at end-of-line. With Jinja's `trim_blocks=True`, the newline after
    `{% endif %}` got stripped, so EVERY macro bullet concatenated into
    one physical line. Markdown then rendered the whole list as a
    single bullet with the rest as inline run-on text."""
    src = """\
ns bit {
    // first macro
    def inc1 dst, carry {}
    // second macro
    def add1 dst, src, carry {}
    // third macro
    def sub dst, src {}
}
"""
    render_stl(_mini_index(src, rel_path="bit/math"), tmp_path)
    page = (tmp_path / "bit" / "math.md").read_text(encoding="utf-8")
    bullet_lines = [
        line for line in page.splitlines()
        if line.lstrip().startswith("- [`")
    ]
    assert len(bullet_lines) == 3, (
        f"Expected 3 bullet lines for 3 macros, got {len(bullet_lines)}.\n"
        f"Rendered page:\n{page}"
    )


def test_constants_appear_in_file_page(tmp_path):
    src = """\
// the word size doubled
dw = 2 * w
"""
    idx = _mini_index(src, rel_path="runlib")
    render_stl(idx, tmp_path)
    page = (tmp_path / "runlib.md").read_text(encoding="utf-8")
    assert "dw" in page
    assert "2 * w" in page
    assert "the word size doubled" in page


def test_depends_on_section_renders_links(tmp_path):
    src = """\
ns stl {
    def target {}
    def caller { stl.target }
}
"""
    idx = _mini_index(src, rel_path="runlib")
    render_stl(idx, tmp_path)
    caller_page = (tmp_path / "runlib" / "caller--0.md").read_text(encoding="utf-8")
    target_page = (tmp_path / "runlib" / "target--0.md").read_text(encoding="utf-8")
    assert "## Depends on" in caller_page
    # Both macros live in the same file dir so the relative link is
    # just `target--0.md` (sibling, no ../).
    assert "target--0.md" in caller_page
    assert "## Used by" in target_page
    assert "caller--0.md" in target_page


def test_cross_file_macro_link_uses_relative_path(tmp_path):
    """A macro that calls a macro in a different file should have a
    `../<other_dir>/<other_name>--<arity>.md` link, not the bare slug."""
    src = """\
ns runlib { def target {} }
ns bit { ns math { def caller { runlib.target } } }
"""
    # Two files: runlib.fj and bit/math.fj. The cross-file dep link
    # from bit/math/caller--0 → runlib/target--0 needs `../../runlib/...`
    fn = parse(src)
    docs = attach_docs(src, fn)
    files = []
    for rel, macro_names in [("runlib", {"target"}), ("bit/math", {"caller"})]:
        sub_fn = type(fn)()
        sub_fn.macros = [m for m in fn.macros if m.name in macro_names]
        files.append(ExtractedFile(
            rel_path=rel, abs_path=f"/fake/{rel}.fj",
            source=src, file_node=sub_fn, docs=docs,
        ))
    idx = StlIndex(files=files)
    idx.dep_graph = build_dep_graph(idx.all_macros)
    render_stl(idx, tmp_path)
    caller_page = (tmp_path / "bit" / "math" / "caller--0.md").read_text(encoding="utf-8")
    # From bit/math/caller--0.md to runlib/target--0.md = `../../runlib/target--0.md`
    assert "../../runlib/target--0.md" in caller_page


def test_nullary_macro_in_used_by_has_closed_inline_code(tmp_path):
    """Regression: nullary macros in used_by/depends_on lists must
    have a closed inline-code span. Previously the closing backtick
    lived inside `{% if arity %}`, which omitted it for arity=0."""
    src = """\
ns stl {
    def target {}
    def caller { stl.target }
}
"""
    render_stl(_mini_index(src, rel_path="runlib"), tmp_path)
    target_page = (tmp_path / "runlib" / "target--0.md").read_text(encoding="utf-8")
    # The list item must be: - [`stl.caller`](caller--0.md), NOT
    # - [`stl.caller](caller--0.md) (unclosed inline code).
    assert "[`stl.caller`](caller--0.md)" in target_page
    caller_page = (tmp_path / "runlib" / "caller--0.md").read_text(encoding="utf-8")
    assert "[`stl.target`](target--0.md)" in caller_page


def test_overloaded_macro_link_shows_arity_in_text(tmp_path):
    """When a macro has overloads, the link DISPLAY text includes the
    /arity disambiguator so readers can tell which overload they're
    being directed to."""
    src = """\
ns stl {
    def m { x }
    def m a, b { x }
    def caller { stl.m 1, 2 }
}
"""
    render_stl(_mini_index(src, rel_path="runlib"), tmp_path)
    caller_page = (tmp_path / "runlib" / "caller--0.md").read_text(encoding="utf-8")
    assert "[`stl.m/2`](m--2.md)" in caller_page


def test_stale_files_pruned_on_regenerate(tmp_path):
    src1 = "ns stl { def a {} def b {} }"
    render_stl(_mini_index(src1, rel_path="runlib"), tmp_path)
    assert (tmp_path / "runlib" / "a--0.md").exists()
    assert (tmp_path / "runlib" / "b--0.md").exists()

    src2 = "ns stl { def a {} }"
    render_stl(_mini_index(src2, rel_path="runlib"), tmp_path)
    assert (tmp_path / "runlib" / "a--0.md").exists()
    assert not (tmp_path / "runlib" / "b--0.md").exists()


def test_no_root_md_emitted(tmp_path):
    """An earlier draft wrote `_root.md` as a second toctree, but it
    was orphan + unreachable. Removed in M4 follow-up. This test
    locks in that we don't accidentally regenerate it."""
    src = "ns stl { def a {} }"
    render_stl(_mini_index(src, rel_path="bit/math"), tmp_path)
    assert not (tmp_path / "_root.md").exists()


def test_macro_page_has_orphan_frontmatter(tmp_path):
    src = "ns stl { def loop {} }"
    render_stl(_mini_index(src, rel_path="runlib"), tmp_path)
    page = (tmp_path / "runlib" / "loop--0.md").read_text(encoding="utf-8")
    # Orphan flag still leads the frontmatter; additional html_meta
    # entries (page description for SEO) may follow before the closing
    # delimiter.
    assert page.startswith("---\norphan: true\n")
    # And the frontmatter is closed somewhere in the file.
    assert "\n---\n" in page


def test_complexity_links_to_glossary(tmp_path):
    """Macro pages link to the hand-written complexity glossary at
    language/complexity.md. Anchor on the link TARGET so future
    template wording tweaks don't break the test silently."""
    src = """\
ns stl {
    // Time Complexity: 4@
    def add {}
}
"""
    render_stl(_mini_index(src, rel_path="runlib"), tmp_path)
    page = (tmp_path / "runlib" / "add--0.md").read_text(encoding="utf-8")
    assert "language/complexity.md" in page


# ---------- JSON-LD <script> safety ----------

def test_json_ld_escapes_html_for_script_context():
    """Security unit test for the `</script>`-safe JSON-LD serialiser.

    Macro descriptions come from doc comments in the (untrusted) upstream
    flip-jump submodule and are embedded verbatim in an inline
    `<script type="application/ld+json">` block. `json.dumps` escapes for
    JSON but NOT for HTML, and the HTML parser terminates a `<script>`
    element at the first literal `</script>` regardless of JSON context. A
    description like `</script><img onerror=...>` would otherwise break out
    of the block and inject live markup (stored XSS) on every visitor.

    `_json_ld` must `\\uXXXX`-escape `<`, `>`, and `&` so the output stays
    valid JSON while remaining inert inside a `<script>` element."""
    out = _json_ld({"description": "</script><img src=x onerror=alert(1)>&"})

    # No HTML-significant character may survive literally.
    assert "<" not in out
    assert ">" not in out
    assert "&" not in out
    # The payload is preserved in escaped form, and the result is still
    # valid JSON that round-trips to the original value.
    assert "\\u003c/script\\u003e\\u003cimg" in out
    import json as _json
    assert _json.loads(out)["description"] == "</script><img src=x onerror=alert(1)>&"


def test_macro_page_jsonld_block_has_no_script_breakout(tmp_path):
    """End-to-end: a malicious first-line description must not break out
    of the rendered macro page's JSON-LD `<script>` block."""
    src = """\
ns stl {
    // </script><img src=x onerror=alert(document.cookie)>
    def evil {}
}
"""
    render_stl(_mini_index(src, rel_path="runlib"), tmp_path)
    page = (tmp_path / "runlib" / "evil--0.md").read_text(encoding="utf-8")

    # Isolate the JSON-LD payload (the {raw} html passthrough that lands
    # verbatim in the served HTML) and assert it contains no premature
    # `</script>` — the breakout — but does carry the escaped payload.
    open_tag = '<script type="application/ld+json">'
    body = page[page.index(open_tag) + len(open_tag):]
    json_ld = body[: body.index("</script>")]
    # No HTML-significant character may survive literally inside the
    # JSON-LD — any `<`/`>` here is a potential breakout from the block.
    assert "<" not in json_ld
    assert ">" not in json_ld
    # The payload's angle brackets are present, but only escaped.
    assert "\\u003c" in json_ld and "\\u003e" in json_ld


# ---------- end-to-end against real STL ----------

@pytest.fixture(scope="module")
def stl_render_dir(tmp_path_factory):
    if not (STL_ROOT / "conf.json").is_file():
        pytest.skip("flip-jump submodule not initialised")
    out = tmp_path_factory.mktemp("rendered")
    index = extract_stl(STL_ROOT)
    render_stl(index, out)
    return out


def test_known_files_have_rendered_pages(stl_render_dir):
    """Every .fj file in conf.json should yield a page at the
    corresponding nested path."""
    for rel in ("runlib", "bit/math", "hex/math", "hex/pointers/stack"):
        page = stl_render_dir / (rel + ".md")
        assert page.is_file(), f"No file page at {page}"


def test_known_macros_have_rendered_pages(stl_render_dir):
    """Macro pages live under their parent file's directory."""
    samples = [
        ("runlib", "startup", 1),     # stl.startup arity 1
        ("runlib", "fj", 2),          # stl.fj arity 2
        ("bit/math", "add", 3),       # bit.add arity 3
        ("hex/math", "add", 2),       # hex.add arity 2
    ]
    for file_rel, name, arity in samples:
        page = stl_render_dir / file_rel / f"{name}--{arity}.md"
        assert page.is_file(), f"Missing {page}"


def test_runlib_file_page_exists_and_mentions_dw(stl_render_dir):
    page = (stl_render_dir / "runlib.md").read_text(encoding="utf-8")
    assert "runlib" in page
    assert "dw" in page  # the dw constant should be listed


def test_hex_pointers_pages_use_nested_directory(stl_render_dir):
    """hex/pointers/* macros land under their parent file's directory."""
    # E.g. hex/pointers/stack.fj's macros live under
    # stl/hex/pointers/stack/<name>--<arity>.md
    stack_dir = stl_render_dir / "hex" / "pointers" / "stack"
    assert stack_dir.is_dir(), f"no directory at {stack_dir}"
    macro_pages = list(stack_dir.glob("*--*.md"))
    assert macro_pages, "no macro pages generated under hex/pointers/stack/"


def test_arity_overloads_render_separate_pages(stl_render_dir):
    """stl.startup has /0 and /1; both must be present in runlib/."""
    a0 = stl_render_dir / "runlib" / "startup--0.md"
    a1 = stl_render_dir / "runlib" / "startup--1.md"
    assert a0.exists() and a1.exists()
    # The arity-0 wrapper calls the arity-1 base. Since they live in
    # the same directory, the link is a sibling: `startup--1.md`.
    a0_text = a0.read_text(encoding="utf-8")
    assert "startup--1.md" in a0_text

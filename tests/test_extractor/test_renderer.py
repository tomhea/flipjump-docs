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
from fj_stl_extract.renderer import file_slug, macro_slug, render_stl


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


# ---------- slugs ----------

def test_file_slug_replaces_slashes_with_dashes():
    assert file_slug("hex/pointers/stack") == "file--hex-pointers-stack"
    assert file_slug("runlib") == "file--runlib"


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
    idx = _mini_index(src)
    written = render_stl(idx, tmp_path)
    names = {p.name for p in written}
    assert "file--fixture.md" in names
    assert "macro--stl.loop--0.md" in names
    assert "macro--stl.fj--2.md" in names


def test_macro_page_contains_signature_and_description(tmp_path):
    src = """\
ns stl {
    // Time Complexity: 4@+12
    // adds two values
    def add a, b { x }
}
"""
    idx = _mini_index(src)
    render_stl(idx, tmp_path)
    page = (tmp_path / "macro--stl.add--2.md").read_text(encoding="utf-8")
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
    idx = _mini_index(src)
    render_stl(idx, tmp_path)
    a2 = (tmp_path / "macro--stl.wflip_macro--2.md").read_text(encoding="utf-8")
    a3 = (tmp_path / "macro--stl.wflip_macro--3.md").read_text(encoding="utf-8")
    # Page heading should include arity when overloads exist.
    assert "arity 2" in a2
    assert "arity 3" in a3


def test_file_page_lists_macros_grouped_by_namespace(tmp_path):
    src = """\
ns stl { def loop {} }
ns bit { def helper {} }
"""
    idx = _mini_index(src)
    render_stl(idx, tmp_path)
    page = (tmp_path / "file--fixture.md").read_text(encoding="utf-8")
    assert "### `stl`" in page
    assert "### `bit`" in page
    assert "stl.loop" in page and "bit.helper" in page


def test_constants_appear_in_file_page(tmp_path):
    src = """\
// the word size doubled
dw = 2 * w
"""
    idx = _mini_index(src)
    render_stl(idx, tmp_path)
    page = (tmp_path / "file--fixture.md").read_text(encoding="utf-8")
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
    idx = _mini_index(src)
    render_stl(idx, tmp_path)
    caller_page = (tmp_path / "macro--stl.caller--0.md").read_text(encoding="utf-8")
    target_page = (tmp_path / "macro--stl.target--0.md").read_text(encoding="utf-8")
    assert "## Depends on" in caller_page
    assert "macro--stl.target--0.md" in caller_page
    assert "## Used by" in target_page
    assert "macro--stl.caller--0.md" in target_page


def test_nullary_macro_in_used_by_has_closed_inline_code(tmp_path):
    """Regression: when a nullary (arity-0) macro appears in another
    macro's `used_by` list, its Markdown link must have a closed
    inline-code span. The previous template put the closing backtick
    inside an `{% if dep.arity %}` block, so for arity=0 (falsy in
    Jinja) the backtick was omitted, producing broken Markdown like
    `` - [`stl.loop](macro--stl.loop--0.md) `` that MyST would not
    parse as a link.
    """
    src = """\
ns stl {
    def target {}
    def caller { stl.target }
}
"""
    render_stl(_mini_index(src), tmp_path)
    target_page = (tmp_path / "macro--stl.target--0.md").read_text(encoding="utf-8")
    # The list item must look like: - [`stl.caller`](macro--stl.caller--0.md)
    # NOT:                          - [`stl.caller](macro--stl.caller--0.md)
    assert "[`stl.caller`](macro--stl.caller--0.md)" in target_page
    # And similarly the caller's depends_on:
    caller_page = (tmp_path / "macro--stl.caller--0.md").read_text(encoding="utf-8")
    assert "[`stl.target`](macro--stl.target--0.md)" in caller_page


def test_overloaded_macro_link_shows_arity_in_text(tmp_path):
    """When a macro has overloads, the link DISPLAY text should include
    the /arity disambiguator so readers can tell which overload they're
    being directed to."""
    src = """\
ns stl {
    def m { x }
    def m a, b { x }
    def caller { stl.m 1, 2 }
}
"""
    render_stl(_mini_index(src), tmp_path)
    caller_page = (tmp_path / "macro--stl.caller--0.md").read_text(encoding="utf-8")
    # Caller calls m/2; the link text should include the /2.
    assert "[`stl.m/2`](macro--stl.m--2.md)" in caller_page


def test_stale_files_pruned_on_regenerate(tmp_path):
    # First render with two macros.
    src1 = "ns stl { def a {} def b {} }"
    render_stl(_mini_index(src1), tmp_path)
    assert (tmp_path / "macro--stl.a--0.md").exists()
    assert (tmp_path / "macro--stl.b--0.md").exists()

    # Second render with only one — the other should be pruned.
    src2 = "ns stl { def a {} }"
    render_stl(_mini_index(src2), tmp_path)
    assert (tmp_path / "macro--stl.a--0.md").exists()
    assert not (tmp_path / "macro--stl.b--0.md").exists()


def test_no_root_md_emitted(tmp_path):
    """An earlier draft wrote `_root.md` as a second toctree, but it
    was orphan + unreachable. Removed in M4 follow-up. This test
    locks in that we don't accidentally regenerate it."""
    src = "ns stl { def a {} }"
    render_stl(_mini_index(src, rel_path="bit/math"), tmp_path)
    assert not (tmp_path / "_root.md").exists()


def test_macro_page_has_orphan_frontmatter(tmp_path):
    src = "ns stl { def loop {} }"
    render_stl(_mini_index(src), tmp_path)
    page = (tmp_path / "macro--stl.loop--0.md").read_text(encoding="utf-8")
    # Pages should be marked :orphan: so they don't need to be in any
    # toctree but can still be linked from file pages.
    assert page.startswith("---\norphan: true\n---")


def test_complexity_links_to_glossary(tmp_path):
    """M6: macro pages link to the hand-written complexity glossary at
    language/complexity.md so readers can find what @, w, dw, dbit, n
    mean without having to leave the page they're reading.
    Anchor the assertion on the LINK TARGET path (not the visible text)
    so future template-wording tweaks don't silently break the link.
    """
    src = """\
ns stl {
    // Time Complexity: 4@
    def add {}
}
"""
    render_stl(_mini_index(src), tmp_path)
    page = (tmp_path / "macro--stl.add--0.md").read_text(encoding="utf-8")
    assert "language/complexity.md" in page


# ---------- end-to-end against real STL ----------

@pytest.fixture(scope="module")
def stl_render_dir(tmp_path_factory):
    if not (STL_ROOT / "conf.json").is_file():
        pytest.skip("flip-jump submodule not initialised")
    out = tmp_path_factory.mktemp("rendered")
    index = extract_stl(STL_ROOT)
    render_stl(index, out)
    return out


def test_known_macros_have_rendered_pages(stl_render_dir):
    for fq in ("stl.startup", "stl.fj", "bit.add", "hex.add", "hex.div"):
        # At least one arity-suffixed page must exist for each name.
        matches = list(stl_render_dir.glob(f"macro--{fq}--*.md"))
        assert matches, f"No macro page found for {fq}"


def test_runlib_file_page_exists_and_mentions_dw(stl_render_dir):
    page = (stl_render_dir / "file--runlib.md").read_text(encoding="utf-8")
    assert "runlib" in page
    assert "dw" in page  # the dw constant should be listed


def test_hex_pointers_pages_use_dotted_namespace(stl_render_dir):
    # hex.pointers.* macros must produce pages with the full dotted
    # namespace in the filename.
    matches = list(stl_render_dir.glob("macro--hex.pointers.*--*.md"))
    assert matches, "no hex.pointers macro pages generated"


def test_arity_overloads_render_separate_pages(stl_render_dir):
    """stl.startup has /0 and /1; both must be present."""
    a0 = stl_render_dir / "macro--stl.startup--0.md"
    a1 = stl_render_dir / "macro--stl.startup--1.md"
    assert a0.exists() and a1.exists()
    # Pages should reference each other in the dep graph.
    a0_text = a0.read_text(encoding="utf-8")
    assert "macro--stl.startup--1.md" in a0_text

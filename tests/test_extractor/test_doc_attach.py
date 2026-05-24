"""Doc-attachment + field-extraction tests."""

from __future__ import annotations

from fj_stl_extract.doc_attach import attach_docs
from fj_stl_extract.parser import parse


def _doc(src: str, macro_name: str):
    file = parse(src)
    [macro] = [m for m in file.macros if m.name == macro_name]
    docs = attach_docs(src, file)
    return docs[id(macro)]


# ---------- attachment rules ----------

def test_doc_block_immediately_above_def_is_attached():
    src = """\
ns stl {
    // doc line 1
    // doc line 2
    def loop {}
}
"""
    info = _doc(src, "loop")
    # Each non-blank line gets a "  " trailing hard break so MyST
    # renders source line breaks as visual line breaks (Markdown
    # otherwise collapses single \n into a space within a paragraph).
    assert info.description == "doc line 1  \ndoc line 2  "
    assert len(info.raw_doc_lines) == 2


def test_blank_line_between_doc_and_def_breaks_attachment():
    src = """\
ns stl {
    // file-level banner that should NOT attach
    // because there is a blank line below it

    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.description == ""
    assert info.raw_doc_lines == []


def test_banner_dashes_terminate_attachment():
    src = """\
ns stl {
    // ---------- Section banner
    // doc that DOES attach to the next def
    def loop {}
}
"""
    info = _doc(src, "loop")
    # The banner line stops the walk. Only the real doc attaches.
    assert "doc that DOES attach" in info.description
    assert "Section banner" not in info.description


def test_doc_attached_in_nested_namespace():
    src = """\
ns hex {
    ns add {
        // adds two hexes
        def foo {}
    }
}
"""
    info = _doc(src, "foo")
    assert info.description == "adds two hexes  "


# ---------- structured fields ----------

def test_time_complexity_extracted():
    src = """\
ns stl {
    // Time Complexity: 4@+12
    def add {}
}
"""
    info = _doc(src, "add")
    assert info.time_complexity == "4@+12"
    assert info.space_complexity is None


def test_time_and_space_complexity_extracted_separately():
    src = """\
ns hex {
    //  Time Complexity: 4@+12
    // Space Complexity: 4@+52
    def add dst, src {}
}
"""
    info = _doc(src, "add")
    assert info.time_complexity == "4@+12"
    assert info.space_complexity == "4@+52"


def test_combined_complexity_fills_both_fields():
    src = """\
ns stl {
    // Complexity: 2
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "2"
    assert info.space_complexity == "2"


def test_ambiguous_complexity_after_time_becomes_space():
    """`Time Complexity: A` then `Complexity: B` — the B becomes Space
    (since the surrounding context already pinned Time)."""
    src = """\
ns stl {
    // Time Complexity: A
    // Complexity: B
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "A"
    assert info.space_complexity == "B"


def test_ambiguous_complexity_after_space_becomes_time():
    """Mirror: `Space Complexity: S` then `Complexity: B` → B is Time."""
    src = """\
ns stl {
    // Space Complexity: S
    // Complexity: B
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.space_complexity == "S"
    assert info.time_complexity == "B"


def test_short_time_form_extracts_correctly():
    """`Time: X` (without "Complexity") is a real convention used in
    the STL — bit/memory.fj uses it as a follow-up to a leading
    `Complexity:` line."""
    src = """\
ns stl {
    // Time: 4@+1
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "4@+1"
    assert info.space_complexity is None


def test_short_space_form_extracts_correctly():
    src = """\
ns stl {
    // Space: 3@+8
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.space_complexity == "3@+8"


def test_complexity_then_space_short_form_realistic():
    """The bit.swap pattern from bit/memory.fj:
    `// Complexity: 2@+5`  ← ambiguous, becomes Time
    `// Space: 3@+8`       ← short Space form, real Space"""
    src = """\
ns stl {
    // Complexity: 2@+5
    // Space: 3@+8
    //   a, b = b, a
    // a,b are bits.
    def swap a, b {}
}
"""
    info = _doc(src, "swap")
    assert info.time_complexity == "2@+5"
    assert info.space_complexity == "3@+8"
    # The pseudocode line is backticked (indented → code line); the
    # prose explanation appears in description.
    assert "`a, b = b, a`" in info.description
    assert "a,b are bits." in info.description


def test_inline_operator_token_is_backticked():
    """Polish #1: tokens like `dst==carry` that contain identifier+op
    are wrapped in backticks so they render as code in prose."""
    src = """\
ns bit {
    // Unsafe for dst==carry (but there is no reason in calling it that way)
    def inc1 dst, carry {}
}
"""
    info = _doc(src, "inc1")
    assert "`dst==carry`" in info.description


def test_indented_pseudocode_wrapped_in_backticks():
    """Polish #1: indented pseudocode lines (e.g. `//   x[:n]++`)
    are wrapped entirely in inline backticks."""
    src = """\
ns bit {
    //   x[:n]++
    def inc n, x {}
}
"""
    info = _doc(src, "inc")
    assert "`x[:n]++`" in info.description


def test_plain_dotted_name_not_backticked_inline():
    """Polish #1: a token like `bit.add` (no operators, just dots)
    should NOT be backticked — it would conflict with cross-page
    links that the renderer adds separately."""
    src = """\
ns stl {
    // see bit.add for the addition pattern
    def f {}
}
"""
    info = _doc(src, "f")
    # No backticks around `bit.add`.
    assert "`bit.add`" not in info.description
    assert "bit.add" in info.description


def test_requires_collected_as_list():
    src = """\
ns hex {
    // @requires hex.add.init (or hex.init)
    // @requires hex.tables_init
    def add {}
}
"""
    info = _doc(src, "add")
    assert info.requires == [
        "hex.add.init (or hex.init)",
        "hex.tables_init",
    ]


def test_output_param_collected_as_dict():
    src = """\
ns stl {
    // @output-param IO: the address of the I/O opcode
    // @output-param CODE_END: where execution should jump after init
    def startup {}
}
"""
    info = _doc(src, "startup")
    assert info.output_params == {
        "IO": "the address of the I/O opcode",
        "CODE_END": "where execution should jump after init",
    }


def test_description_with_pseudocode_indentation_preserved():
    src = """\
ns hex {
    // Time Complexity: 4@
    //   dst += src
    //
    // both dst, src are hexes.
    def add dst, src {}
}
"""
    info = _doc(src, "add")
    assert info.time_complexity == "4@"
    # An indented pseudocode line (`//   dst += src`) gets wrapped in
    # backticks so the operators are visually distinguished from prose.
    # The original indent is preserved before the opening backtick.
    assert "  `dst += src`" in info.description
    assert "both dst, src are hexes." in info.description


def test_description_lines_get_markdown_hard_breaks():
    """Two non-blank source lines should produce two separate visual
    lines in rendered Markdown. We emit a `  ` (two-space) hard break
    at the end of each non-blank line so MyST preserves the break."""
    src = """\
ns stl {
    // first line of doc
    // second line of doc
    def f {}
}
"""
    info = _doc(src, "f")
    assert info.description == "first line of doc  \nsecond line of doc  "


def test_blank_line_in_doc_becomes_paragraph_break():
    """A bare `//` in source = blank doc line = paragraph break in
    output. Should NOT become a hard break."""
    src = """\
ns stl {
    // first paragraph
    //
    // second paragraph
    def f {}
}
"""
    info = _doc(src, "f")
    # Non-blank lines get the `  ` trailing hard break. The blank
    # line stays as an empty line, producing `\n\n` between paras.
    assert info.description == "first paragraph  \n\nsecond paragraph  "


# ---------- top-level constants get doc too ----------

def test_constant_gets_doc_attached():
    src = """\
// double word size
dw = 2 * w
"""
    file = parse(src)
    [const] = file.constants
    docs = attach_docs(src, file)
    assert docs[id(const)].description == "double word size  "


# ---------- empty doc ----------

def test_def_with_no_doc_yields_empty_docinfo():
    src = "ns stl { def loop {} }"
    info = _doc(src, "loop")
    assert info.is_empty
    assert info.description == ""
    assert info.time_complexity is None
    assert info.raw_doc_lines == []

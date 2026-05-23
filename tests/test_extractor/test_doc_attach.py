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
    assert info.description == "doc line 1\ndoc line 2"
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
    assert info.description == "adds two hexes"


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


def test_combined_complexity_does_not_override_explicit_fields():
    # If both Time/Space and Complexity appear, the explicit ones win.
    src = """\
ns stl {
    // Time Complexity: A
    // Complexity: B
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "A"
    # Space stays None because Time was set explicitly — the catch-all
    # only fires when BOTH explicit fields are missing.
    assert info.space_complexity is None


def test_combined_complexity_after_explicit_space_only():
    # Reversed order vs the test above — pin the same precedence rule.
    src = """\
ns stl {
    // Space Complexity: S
    // Complexity: B
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.space_complexity == "S"
    # Time stays None — catch-all only fires when BOTH fields are missing.
    assert info.time_complexity is None


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
    # The "  dst += src" line preserves its indent (note: leading 2-space
    # indent after the `// ` prefix); blank `//` line and the trailing
    # paragraph both appear in description.
    assert "  dst += src" in info.description
    assert "both dst, src are hexes." in info.description


# ---------- top-level constants get doc too ----------

def test_constant_gets_doc_attached():
    src = """\
// double word size
dw = 2 * w
"""
    file = parse(src)
    [const] = file.constants
    docs = attach_docs(src, file)
    assert docs[id(const)].description == "double word size"


# ---------- empty doc ----------

def test_def_with_no_doc_yields_empty_docinfo():
    src = "ns stl { def loop {} }"
    info = _doc(src, "loop")
    assert info.is_empty
    assert info.description == ""
    assert info.time_complexity is None
    assert info.raw_doc_lines == []

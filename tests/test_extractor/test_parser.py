"""Parser contract tests.

Covers the eight TDD-focus scenarios from the M3 plan:
  - simple def
  - ns nesting (with re-opened same-name blocks)
  - arity overload
  - < requires / > exports clauses
  - top-level constants
  - multi-line via \\
  - file-banner separation
  - parsing real STL fragments verbatim
"""

from __future__ import annotations

from fj_stl_extract.parser import (
    ConstantNode,
    FileNode,
    MacroNode,
    ParseError,
    parse,
)


# ---------- top-level shape ----------

def test_empty_source_parses_to_empty_file():
    f = parse("")
    assert isinstance(f, FileNode)
    assert f.macros == []
    assert f.constants == []


def test_top_level_constants():
    src = """\
dw   = 2 * w
dbit = w + #w
"""
    f = parse(src)
    assert len(f.constants) == 2
    assert [c.name for c in f.constants] == ["dw", "dbit"]
    assert all(c.namespace_path == () for c in f.constants)


# ---------- simple def ----------

def test_simple_def():
    src = "ns stl { def loop { ;$ - dw } }"
    f = parse(src)
    assert len(f.macros) == 1
    m = f.macros[0]
    assert m.name == "loop"
    assert m.namespace_path == ("stl",)
    assert m.params == []
    assert m.arity == 0
    assert m.locals_ == []
    assert m.requires_labels == []
    assert m.exports_labels == []
    assert m.fq_name == "stl.loop"


def test_def_with_params():
    src = "ns stl { def fj f, j { f;j } }"
    [m] = parse(src).macros
    assert m.params == ["f", "j"]
    assert m.arity == 2


# ---------- @ locals / < requires / > exports ----------

def test_locals_clause():
    src = "ns stl { def startup @ code_start { stl.startup code_start } }"
    [m] = parse(src).macros
    assert m.params == []
    assert m.locals_ == ["code_start"]


def test_exports_clause():
    src = "ns stl { def startup code_start > IO { ;code_start IO: ;0 } }"
    [m] = parse(src).macros
    assert m.params == ["code_start"]
    assert m.exports_labels == ["IO"]


def test_requires_clause_with_dotted_labels():
    src = """ns hex { ns add { def clear_carry @ ret < ..tables.ret, .dst { wflip x } } }"""
    [m] = parse(src).macros
    assert m.locals_ == ["ret"]
    assert m.requires_labels == ["..tables.ret", ".dst"]


# ---------- arity overloading ----------

def test_two_defs_same_name_different_arity():
    src = """\
ns stl {
    def wflip_macro dst, val { wflip dst, val }
    def wflip_macro dst, val, jmp_addr { wflip dst, val, jmp_addr }
}
"""
    macros = [m for m in parse(src).macros if m.name == "wflip_macro"]
    assert len(macros) == 2
    arities = sorted(m.arity for m in macros)
    assert arities == [2, 3]


# ---------- namespace nesting ----------

def test_nested_namespaces():
    src = """\
ns hex {
    ns pointers {
        def ptr_init { x }
    }
}
"""
    [m] = parse(src).macros
    assert m.namespace_path == ("hex", "pointers")
    assert m.fq_name == "hex.pointers.ptr_init"


def test_same_namespace_reopened_in_one_file():
    """`ns add { def foo ... }` then later `ns add { def bar ... }`
    inside the SAME outer namespace must yield both macros with the same
    namespace_path. The parser does not need to physically merge the
    NamespaceNodes — the flat-list output naturally collapses them."""
    src = """\
ns hex {
    ns add { def foo { x } }
    ns add { def bar { y } }
}
"""
    f = parse(src)
    assert len(f.macros) == 2
    assert all(m.namespace_path == ("hex", "add") for m in f.macros)
    assert {m.name for m in f.macros} == {"foo", "bar"}


# ---------- multi-line continuation (handled by tokenizer; verify it round-trips) ----------

def test_def_with_backslash_continuation_in_signature():
    src = """\
ns hex { def cmp a, b, lt, eq, gt \\
    < .ret, .dst { stl.fj a, b } }
"""
    [m] = parse(src).macros
    assert m.params == ["a", "b", "lt", "eq", "gt"]
    assert m.requires_labels == [".ret", ".dst"]


# ---------- body is opaque ----------

def test_body_captured_as_token_list_without_braces():
    src = "ns stl { def fj f, j { f;j } }"
    [m] = parse(src).macros
    # Body should NOT contain the outer braces.
    body_text = " ".join(t.text for t in m.body_tokens if t.kind.name != "NEWLINE")
    assert "f" in body_text and "j" in body_text
    assert "{" not in body_text
    assert "}" not in body_text


def test_body_brace_balancing_with_nested_repblock():
    # `rep(...) { ... }` inside a body must not break the matcher.
    src = """\
ns hex { def add n, dst, src {
    .add.clear_carry
    { rep(n, i) .add dst+i*dw, src+i*dw }
    .add.clear_carry
} }
"""
    macros = parse(src).macros
    assert len(macros) == 1


# ---------- mixed constants + macros at same level ----------

def test_constants_and_macros_interleave():
    src = """\
dw = 2 * w
ns stl {
    def loop { ;$ - dw }
}
dbit = w + #w
"""
    f = parse(src)
    assert {c.name for c in f.constants} == {"dw", "dbit"}
    assert [m.fq_name for m in f.macros] == ["stl.loop"]


# ---------- robustness: unknown constructs do not crash ----------

def test_label_at_top_level_does_not_crash():
    # Labels with `:` are valid in source but not at top level in STL;
    # the parser must skip them silently rather than raising.
    src = "weird_label:\nns stl { def loop {} }"
    [m] = parse(src).macros
    assert m.fq_name == "stl.loop"


def test_comments_between_defs_dont_swallow_next_def():
    src = """\
ns stl {
    // some doc
    def a {}

    // another doc
    def b {}
}
"""
    macros = parse(src).macros
    assert [m.name for m in macros] == ["a", "b"]


# ---------- start/end line tracking ----------

def test_line_numbers_track_source_position():
    src = """\
ns stl {
    def loop {
        ;$ - dw
    }
}
"""
    [m] = parse(src).macros
    assert m.start_line == 2
    assert m.end_line == 4


# ---------- parse against real STL snippets ----------

def test_parse_runlib_header_block():
    """Parse the first ~70 lines of runlib.fj verbatim — checks the
    overloaded `def startup` cases and the top-level constants."""
    src = """\
// w = ??       // memory and operands width.
dw   = 2 * w
dbit = w + #w


ns stl {
    // Complexity: 2
    def startup @ code_start {
        stl.startup code_start
      code_start:
    }

    // @output-param IO: ...
    def startup code_start > IO {
        ;code_start
      IO:
        ;0
    }

    def startup_and_init_all {
        .startup_and_init_all 100
    }

    def startup_and_init_all stack_bit_size @ code_start {
        .startup_and_init_all code_start, stack_bit_size
      code_start:
    }

    def startup_and_init_all code_start, stack_bit_size {
        stl.startup_and_init_pointers code_start
        hex.init
        stl.stack_init stack_bit_size
    }
}
"""
    f = parse(src)
    assert {c.name for c in f.constants} == {"dw", "dbit"}
    # Two `startup` overloads + three `startup_and_init_all` overloads = 5
    startup = [m for m in f.macros if m.name == "startup"]
    init_all = [m for m in f.macros if m.name == "startup_and_init_all"]
    assert sorted(m.arity for m in startup) == [0, 1]
    assert sorted(m.arity for m in init_all) == [0, 1, 2]
    # `>` clause captured
    [exporter] = [m for m in startup if m.exports_labels]
    assert exporter.exports_labels == ["IO"]

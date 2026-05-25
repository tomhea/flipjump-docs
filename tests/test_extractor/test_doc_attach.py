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
    """`Time Complexity: 4@+12` then `Complexity: 2@+8` — the 2@+8 becomes Space
    (since the surrounding context already pinned Time). Real complexity
    values used because the parser validates value shape."""
    src = """\
ns stl {
    // Time Complexity: 4@+12
    // Complexity: 2@+8
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "4@+12"
    assert info.space_complexity == "2@+8"


def test_ambiguous_complexity_after_space_becomes_time():
    """Mirror: `Space Complexity: 2@+8` then `Complexity: 4@+12` → time."""
    src = """\
ns stl {
    // Space Complexity: 2@+8
    // Complexity: 4@+12
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.space_complexity == "2@+8"
    assert info.time_complexity == "4@+12"


def test_short_time_form_extracts_correctly():
    """`Time: X` (without "Complexity") is a real convention used in
    the STL — bit/memory.fj uses it as a follow-up to a leading
    `Complexity:` line."""
    src = """\
ns testns {
    // Time: 4@+1
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "4@+1"
    assert info.space_complexity is None


def test_short_space_form_extracts_correctly():
    src = """\
ns testns {
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


def test_indented_prose_line_not_wrapped_as_code():
    """Polish batch 2 #2: an indented line that LOOKS like prose
    (e.g. `//   prints x[:n] as an unsigned decimal number`) should
    NOT be wrapped entirely in backticks. The bit.print_dec_uint
    convention uses 2-space indent for intent summaries even though
    they're prose, not code."""
    src = """\
ns bit {
    //   prints x[:n] as an unsigned decimal number (without leading zeros).
    def print_dec_uint n, x {}
}
"""
    info = _doc(src, "print_dec_uint")
    # The whole line should NOT be a code block.
    assert "`prints x[:n] as an unsigned decimal number" not in info.description
    # But `x[:n]` should still be backticked inline.
    assert "`x[:n]`" in info.description
    # The natural English ("unsigned decimal number") survives unchanged.
    assert "unsigned decimal number" in info.description


def test_short_desc_prefers_indented_line_over_warning():
    """Polish batch 3: the heuristic now prefers an indented intent
    line (the STL's convention for "this is what the macro does")
    over earlier non-indented warning/note text.

    For e.g. `bit.inc1` whose doc is:
        // Unsafe for dst==carry ...
        // Complexity: 2@+6
        //   {carry:dst}++
        // carry,dst are bits.
    the summary should be `{carry:dst}++`, not the "Unsafe" warning.
    """
    from fj_stl_extract.renderer import _short_desc

    src = """\
ns bit {
    // Unsafe for dst==carry (but there is no reason in calling it that way)
    // Complexity: 2@+6
    //   {carry:dst}++
    // carry,dst are bits.
    def inc1 dst, carry {}
}
"""
    info = _doc(src, "inc1")
    # The indented `{carry:dst}++` line should win as summary.
    summary = _short_desc(info.description)
    assert "{carry:dst}++" in summary
    # The warning prefix should NOT be the summary.
    assert "Unsafe" not in summary


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


def test_url_not_backticked():
    """Regression (CR-ist polish): a URL like `https://example.com/foo`
    would have matched the inline-code regex (identifier prefix, has
    operator chars like `/` and `=`) and gotten backticked, which
    breaks any surrounding `[label](url)` Markdown link."""
    src = """\
ns stl {
    // see https://esolangs.org/wiki/FlipJump for context
    def f {}
}
"""
    info = _doc(src, "f")
    # URL stays bare — no backticks.
    assert "`https" not in info.description
    assert "https://esolangs.org/wiki/FlipJump" in info.description


def test_markdown_link_url_not_backticked():
    """A `[label](url)` Markdown link in a doc comment must survive
    the inline-code transform with the URL intact."""
    src = """\
ns stl {
    // see [esolangs](https://esolangs.org/wiki/FlipJump) for context
    def f {}
}
"""
    info = _doc(src, "f")
    assert "(https://esolangs.org/wiki/FlipJump)" in info.description
    # The URL must NOT be backticked.
    assert "(`https" not in info.description


def test_triple_complexity_block_explicit_space_wins():
    """Regression (CR-ist polish): if a doc block has both an ambiguous
    `Complexity:` AND a later explicit `Space:`, the explicit Space
    must win — the previous ambiguous resolution was silently dropping
    the explicit value into the still-empty space slot."""
    src = """\
ns stl {
    // Time Complexity: 4@
    // Complexity: 2@+1
    // Space Complexity: 8@+4
    def loop {}
}
"""
    info = _doc(src, "loop")
    assert info.time_complexity == "4@"
    assert info.space_complexity == "8@+4"


def test_complexity_without_colon_is_captured():
    """Polish batch 2 #1: the upstream STL uses BOTH `Complexity: X`
    and bare `Complexity X` (no colon) — e.g. bit/pointers.fj uses
    `// Complexity 2w@ + 2@`. Both forms must be captured."""
    src = """\
ns stl {
    // Complexity 9@-7
    def f {}
}
"""
    info = _doc(src, "f")
    assert info.time_complexity == "9@-7"
    assert info.space_complexity == "9@-7"


def test_complexity_without_colon_followed_by_space_short_form():
    """Real bit/pointers.fj pattern: bare `Complexity 2w@ + 2@` (the
    ambiguous form) with no later explicit Time/Space → both fields
    filled."""
    src = """\
ns bit {
    // Complexity 2w@ + 2@
    def ptr_inc {}
}
"""
    info = _doc(src, "ptr_inc")
    assert info.time_complexity == "2w@ + 2@"
    assert info.space_complexity == "2w@ + 2@"


def test_complexity_prose_not_captured():
    """The colonless `Complexity` matcher must NOT consume English
    prose like `// Complexity is the runtime cost`. The value-shape
    validator (digit/@/operator required) blocks this."""
    src = """\
ns stl {
    // Complexity is the runtime cost of this macro.
    def f {}
}
"""
    info = _doc(src, "f")
    # Should NOT be treated as a complexity entry — falls through to
    # description.
    assert info.time_complexity is None
    assert info.space_complexity is None
    assert "Complexity is the runtime cost" in info.description


def test_size_complexity_maps_to_space():
    """Polish batch 3: `// Size Complexity: N` is the upstream STL's
    label for what we call space complexity. Used by bit.bit, hex.hex,
    hex.tables_init.* macros."""
    src = """\
ns stl {
    // Size Complexity: 1
    //
    // a basic memory cell.
    def cell { x }
}
"""
    info = _doc(src, "cell")
    assert info.space_complexity == "1"
    assert info.time_complexity is None


def test_typo_time_complexity_case_insensitive():
    """Polish batch 3: bit/cond_jumps.fj has `// TIme Complexity: ...`
    (capital I typo). Case-insensitive match captures it."""
    src = """\
ns stl {
    // TIme Complexity: n(2@+4)
    // Space Complexity: n(3@+6)
    def cmp n {}
}
"""
    info = _doc(src, "cmp")
    assert info.time_complexity == "n(2@+4)"
    assert info.space_complexity == "n(3@+6)"


def test_description_override_replaces_extracted_description():
    """Polish batch 3: when an override exists for (fq_name, arity),
    it replaces the auto-extracted description but leaves complexity
    and other fields untouched."""
    src = """\
ns bit {
    // Size Complexity: 1
    //
    // some auto-extracted text we want to override
    def bit value {}
}
"""
    info = _doc(src, "bit")
    # Override fires: arity-1 form has the "with initial value" summary.
    assert "Binary variable with initial value" in info.description
    assert "won't ever be executed" in info.description
    # Complexity still comes from the source.
    assert info.space_complexity == "1"


def test_description_override_carries_through_short_desc():
    """The file-page bullet summary derives from the override, not
    from the original source comment."""
    from fj_stl_extract.renderer import _short_desc
    from fj_stl_extract.doc_attach import _DESCRIPTION_OVERRIDES

    summary = _short_desc(_DESCRIPTION_OVERRIDES[("bit.ptr_inc", 1)])
    assert "ptr += 2w" in summary


def test_memory_primitive_overrides_split_by_arity():
    """Polish batch 4: each of the 8 memory primitives has its own
    one-line summary (no shared paragraph). Covers bit.bit, bit.vec,
    hex.hex, hex.vec at both their declared arities.
    """
    from fj_stl_extract.renderer import _short_desc
    from fj_stl_extract.doc_attach import _DESCRIPTION_OVERRIDES

    assert _short_desc(_DESCRIPTION_OVERRIDES[("bit.bit", 0)]) == "Binary variable."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("bit.bit", 1)]) == \
        "Binary variable with initial value."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("bit.vec", 1)]) == "Binary vector."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("bit.vec", 2)]) == \
        "Binary vector with initial value."

    assert _short_desc(_DESCRIPTION_OVERRIDES[("hex.hex", 0)]) == \
        "Hexadecimal variable."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("hex.hex", 1)]) == \
        "Hexadecimal variable with initial value."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("hex.vec", 1)]) == \
        "Hexadecimal vector."
    assert _short_desc(_DESCRIPTION_OVERRIDES[("hex.vec", 2)]) == \
        "Hexadecimal vector with initial value."


def test_like_prefix_normalized_to_effectively():
    """Polish batch 4: upstream `// Like: sp++` / `// like: *ptr;`
    intent-prefix is normalized to `Effectively:` for readability."""
    src = """\
ns hex {
    //   Like:  sp++
    def sp_inc {}
}
"""
    info = _doc(src, "sp_inc")
    assert "Effectively:" in info.description
    assert "Like:" not in info.description


def test_validator_accepts_single_letter_complexity():
    """Polish batch 5: `// Complexity: n` for bit.not/2 was silently
    dropped because the old validator required at least one
    `0-9@()+-*^~/#` character. Single-letter values like n, w, nb are
    now accepted; obvious prose like 'is the runtime cost' is still
    rejected via the 3+letter-pair prose-detector."""
    from fj_stl_extract.doc_attach import _looks_like_complexity_value
    assert _looks_like_complexity_value("n") is True
    assert _looks_like_complexity_value("w") is True
    assert _looks_like_complexity_value("nb") is True
    assert _looks_like_complexity_value("2@+4") is True
    assert _looks_like_complexity_value("n(3@+30)") is True
    # Prose still rejected.
    assert _looks_like_complexity_value("is the runtime cost") is False
    assert _looks_like_complexity_value("depends on the input") is False


def test_bare_complexity_n_parses_end_to_end():
    """Regression for bit.not/2: source `// Complexity: n` should now
    populate BOTH time and space complexity via the ambiguous-resolution
    logic (no other complexity entries → ambiguous fills both fields)."""
    src = """\
ns bit {
    // Complexity: n
    //   dst[:n] ^= (1<<n)-1
    def not n, dst {}
}
"""
    info = _doc(src, "not")
    assert info.time_complexity == "n"
    assert info.space_complexity == "n"


def test_complexity_overrides_fill_when_missing():
    """Polish batch 5: time/space complexity overrides fill empty
    fields without replacing source-supplied values."""
    src = """\
ns hex {
    //   if hex==0 goto l0, else continue.
    def if0 hex, l0 @ l1 {}
}
"""
    info = _doc(src, "if0")
    # Source has no Complexity line → override fills both.
    assert info.time_complexity == "@-1"
    assert info.space_complexity == "@+15"


def test_complexity_overrides_do_not_overwrite_source():
    """Overrides only fill empty fields. If source has an explicit
    Complexity comment, it wins."""
    src = """\
ns hex {
    // Time Complexity: 999
    // Space Complexity: 888
    def if0 hex, l0 @ l1 {}
}
"""
    info = _doc(src, "if0")
    # Source values win over the (@-1, @+15) override.
    assert info.time_complexity == "999"
    assert info.space_complexity == "888"


def test_assumes_override_appends_to_existing_description():
    """Polish batch 6: an `@Assumes:` line is appended to the description
    on a new paragraph, leaving prose and complexity untouched."""
    src = """\
ns bit {
    //  Time Complexity: n(2@-1)
    //   x[:n] <<= times
    def shl n, times, x {}
}
"""
    info = _doc(src, "shl")
    # Original prose still there.
    assert "x[:n] <<= times" in info.description
    # Plus the appended @Assumes.
    assert "@Assumes: times <= n" in info.description


def test_assumes_override_works_without_existing_description():
    """If a macro has no description prose, the @Assumes line stands
    alone (no leading blank lines)."""
    from fj_stl_extract.doc_attach import _apply_assumes_override
    from fj_stl_extract.doc_attach import DocInfo
    info = DocInfo()
    _apply_assumes_override("bit.shl", 3, info)
    assert info.description == "@Assumes: times <= n"


def test_no_assumes_for_unregistered_macro():
    """Macros not in the override dict get no @Assumes added."""
    src = """\
ns bit {
    //   no-op test
    def foobar {}
}
"""
    info = _doc(src, "foobar")
    assert "@Assumes:" not in info.description


def test_data_declaration_complexity_override():
    """Memory-primitive overrides use the literal string
    '0 (data declaration)' for Time, communicating that the macro
    is data, not executable code."""
    from fj_stl_extract.doc_attach import _TIME_COMPLEXITY_OVERRIDES
    assert _TIME_COMPLEXITY_OVERRIDES[("bit.bit", 0)] == "0 (data declaration)"
    assert _TIME_COMPLEXITY_OVERRIDES[("hex.vec", 2)] == "0 (data declaration)"


def test_like_prefix_normalization_preserves_prose():
    """The `Like:` substitution is line-anchored, so mid-sentence
    usages (with OR without a colon) are left alone. Regression for
    the CR-finding on bit.str/1: source has `// used to initialize a
    string, like:   bit.str "Hello, World!"` — the inline `like:` must
    not be rewritten to `Effectively:`."""
    from fj_stl_extract.doc_attach import _normalize_like_prefix
    # No colon → no substitution.
    assert _normalize_like_prefix("I would like to test this") == \
        "I would like to test this"
    # Mid-sentence colon → no substitution (regression: this used to rewrite).
    assert _normalize_like_prefix("used to initialize a string, like: bit.str") == \
        "used to initialize a string, like: bit.str"
    # Line-leading colon form → substituted.
    assert _normalize_like_prefix("like: x++") == "Effectively: x++"
    assert _normalize_like_prefix("Like: y--") == "Effectively: y--"
    # Indented + backticked (post-_extract_fields form) → substituted, leading
    # whitespace and backtick preserved.
    assert _normalize_like_prefix("  `Like:  sp++`") == "  `Effectively:  sp++`"
    # Multiline: substitutes per-line, not just at offset 0.
    assert _normalize_like_prefix("first line\n  Like: second") == \
        "first line\n  Effectively: second"


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
    # `testns` (not `stl`) to avoid triggering any real-macro overrides.
    src = "ns testns { def someop {} }"
    info = _doc(src, "someop")
    assert info.is_empty
    assert info.description == ""
    assert info.time_complexity is None
    assert info.raw_doc_lines == []

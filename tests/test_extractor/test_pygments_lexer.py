"""Pygments lexer + style contract tests.

The lexer must recognise the token categories from CodeEditor.tsx's
Monaco tokenizer so code blocks on the docs site colour identically
to the IDE at fj.tomhe.app.
"""

from __future__ import annotations

from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Whitespace,
)

from fj_stl_extract.pygments_lexer import FlipJumpLexer
from fj_stl_extract.pygments_style import FlipJumpDarkStyle


def _kinds_with_text(src: str) -> list[tuple[type, str]]:
    lex = FlipJumpLexer()
    return [(tt, txt) for tt, txt in lex.get_tokens(src) if not _is_whitespace(tt)]


def _is_whitespace(tt) -> bool:
    return tt in (Whitespace,) or "Whitespace" in str(tt)


# ---------- token kinds ----------

def test_def_macro_classifies_keyword_and_function_name():
    out = _kinds_with_text("def startup")
    assert out == [(Keyword.Declaration, "def"), (Name.Function, "startup")]


def test_ns_classifies_keyword_and_namespace_name():
    out = _kinds_with_text("ns stl")
    assert out == [(Keyword, "ns"), (Name.Namespace, "stl")]


def test_directives_are_name_builtin():
    for word in ("pad", "reserve", "segment", "wflip"):
        [(tt, txt)] = _kinds_with_text(word)
        assert tt is Name.Builtin
        assert txt == word


def test_well_known_types_are_keyword_type():
    # Matches the IDE's `types` list — NOT including `bit`, which the
    # IDE colours as a plain identifier.
    for word in ("dbit", "dw", "w"):
        [(tt, txt)] = _kinds_with_text(word)
        assert tt is Keyword.Type
        assert txt == word


def test_bit_is_not_classified_as_a_type():
    # `bit` is not in the IDE's `types` list (CodeEditor.tsx line 157).
    # It's used as both a namespace name (`ns bit`) and a value type
    # at runtime. The lexer must NOT colour it as Keyword.Type.
    # We use `ns bit` here so the `ns NAME` rule wins and `bit` is
    # classified as Name.Namespace (matching the IDE behaviour where
    # `bit` falls into the identifier branch, not the types branch).
    out = _kinds_with_text("ns bit")
    assert out == [(Keyword, "ns"), (Name.Namespace, "bit")]


def test_label_classification():
    # `code_start:` — identifier followed by colon
    out = _kinds_with_text("code_start:")
    assert out[0] == (Name.Label, "code_start")
    assert out[-1] == (Punctuation, ":")


def test_constant_classification():
    out = _kinds_with_text("dw = 2 * w")
    # First token should be Name.Constant for `dw`
    assert out[0] == (Name.Constant, "dw")


def test_equality_op_does_not_trigger_constant_rule():
    """Regression: previously the constant rule used a bare `=` literal,
    so `a == b` mis-classified `a` as Name.Constant. (CR-ist M5 finding.)

    We use `; a == b` so the macro-call rule (line-start identifier)
    doesn't get involved — this test is about the constant-rule's
    lookahead, not the macro-call rule.
    """
    out = _kinds_with_text("; a == b")
    # No Name.Constant anywhere in the output.
    kinds = [tt for tt, _ in out]
    assert Name.Constant not in kinds
    # `a` and `b` should both be plain Name.
    name_texts = [txt for tt, txt in out if tt is Name]
    assert "a" in name_texts and "b" in name_texts


def test_def_inside_string_is_not_keyword():
    """Regression: previously strings were matched LAST in the rules
    list, so a string literal containing `def` had its outer quote
    consumed by the Text catchall and `def` mis-classified as
    Keyword.Declaration. (CR-ist M5 finding.)
    """
    out = _kinds_with_text('"def foo"')
    # The whole quoted token should be a single String.Double — no
    # Keyword anywhere in the output.
    kinds = [tt for tt, _ in out]
    assert all(tt is not Keyword.Declaration for tt in kinds)
    assert any(tt is String.Double and txt == '"def foo"'
               for tt, txt in out)


def test_macro_call_at_line_start_is_function_magic():
    """A line that starts with an identifier (not a language word) and
    has args / a comment / EOL after it is the IDE's `macro.call`
    pattern. Pygments emits Name.Function.Magic so the IDE palette
    colours it `#e8c47a`.
    """
    out = _kinds_with_text("stl.output_char 'H'")
    assert out[0] == (Name.Function.Magic, "stl.output_char")


def test_numbers_classified():
    assert _kinds_with_text("0xCAFE") == [(Number.Hex, "0xCAFE")]
    assert _kinds_with_text("0b1010") == [(Number.Bin, "0b1010")]
    assert _kinds_with_text("12345") == [(Number.Integer, "12345")]


def test_strings_classified():
    out = _kinds_with_text('"hello"')
    assert out == [(String.Double, '"hello"')]
    out = _kinds_with_text("'H'")
    assert out == [(String.Single, "'H'")]


def test_line_comment():
    [(tt, txt)] = _kinds_with_text("// this is a comment")
    assert tt is Comment.Single
    assert txt == "// this is a comment"


def test_semicolon_is_punctuation():
    out = _kinds_with_text("f;j")
    # f, ;, j
    kinds = [tt for tt, _ in out]
    assert Punctuation in kinds


def test_operator_chars_are_operator():
    out = _kinds_with_text("a + b")
    assert any(tt is Operator and txt == "+" for tt, txt in out)


# ---------- real-world snippets ----------

def test_full_def_line_tokenizes():
    src = "def startup code_start > IO {"
    out = _kinds_with_text(src)
    # First 3: def keyword, function name, identifier param
    assert out[0] == (Keyword.Declaration, "def")
    assert out[1] == (Name.Function, "startup")
    # `>` should be an Operator (not GT — Pygments doesn't distinguish)
    assert any(tt is Operator and txt == ">" for tt, txt in out)


def test_dotted_identifier_classified_when_not_at_line_start():
    # `stl.startup` mid-line (after `;`) appears as a plain Name.
    # At line start it would be Name.Function.Magic — see
    # test_macro_call_at_line_start_is_function_magic.
    out = _kinds_with_text("; stl.startup")
    assert any(tt is Name and txt == "stl.startup" for tt, txt in out)


def test_leading_dot_identifier_classified_when_not_at_line_start():
    # `.tables.x` mid-line is Name.Other (namespace-relative ref).
    out = _kinds_with_text("; .tables.x")
    assert any(tt is Name.Other and txt == ".tables.x" for tt, txt in out)


def test_dotted_identifier_at_line_start_is_macro_call():
    # `stl.startup args...` at line start is a macro call.
    out = _kinds_with_text("stl.startup arg1, arg2")
    assert out[0] == (Name.Function.Magic, "stl.startup")


def test_line_continuation_is_consumed():
    # `def foo a, \<newline>b` should yield no NEWLINE / no backslash text;
    # the `\<newline>` is whitespace.
    out = _kinds_with_text("def foo a, \\\nb")
    # Tokens should be: def keyword, foo function-name, a ident, comma, b ident
    kinds = [tt for tt, _ in out]
    assert all(tt is not Operator or txt != "\\" for tt, txt in out)
    # `def` and the two arg idents `a`/`b` should all be present:
    texts = [txt for _, txt in out]
    assert "a" in texts and "b" in texts


# ---------- style ----------

def test_style_defines_all_pygments_tokens_used_by_lexer():
    """Sanity check: every token type the lexer can emit has a colour
    in the style. Missing entries would render as unstyled text on the
    site — not a crash but visually inconsistent."""
    style = FlipJumpDarkStyle
    used_token_types = {
        Keyword, Keyword.Declaration, Keyword.Type,
        Name, Name.Function, Name.Namespace,
        Name.Label, Name.Constant, Name.Other, Name.Builtin,
        Number.Hex, Number.Bin, Number.Integer,
        String.Single, String.Double,
        Comment.Single, Operator, Punctuation,
    }
    for tt in used_token_types:
        style_for = style.style_for_token(tt)
        # `style_for_token` returns a dict with at least `color` or `bgcolor`.
        # An unmapped token returns {'color': None, 'bgcolor': None, ...}.
        assert style_for["color"] is not None, (
            f"Token type {tt} has no colour in FlipJumpDarkStyle"
        )


def test_style_keyword_color_matches_ide():
    """The IDE's Monaco theme uses #569cd6 for keywords. Pin it."""
    style = FlipJumpDarkStyle
    assert style.style_for_token(Keyword)["color"].lower().lstrip("#") == "569cd6"


def test_style_comment_color_matches_ide():
    style = FlipJumpDarkStyle
    assert style.style_for_token(Comment.Single)["color"].lower().lstrip("#") == "6a9955"


def test_style_string_color_matches_ide():
    style = FlipJumpDarkStyle
    assert style.style_for_token(String.Double)["color"].lower().lstrip("#") == "ce9178"

"""Tokenizer contract tests.

The tokenizer is the bottom layer — every other module reads its output.
These tests pin down: line/col tracking, comment / string / number /
identifier classification, keyword vs ident, dotted identifiers, line
continuation, and the file-banner comment shape.
"""

from __future__ import annotations

import pytest

from fj_stl_extract.tokenizer import KEYWORDS, Token, TokenKind, tokenize


def toks(src: str) -> list[Token]:
    return [t for t in tokenize(src) if t.kind != TokenKind.EOF]


# ---------- basics ----------

def test_empty_source_yields_only_eof():
    assert list(tokenize("")) == [Token(TokenKind.EOF, "", 1, 1)]


def test_whitespace_only_dropped_but_newlines_kept():
    out = toks(" \t  \n\t\n")
    assert [t.kind for t in out] == [TokenKind.NEWLINE, TokenKind.NEWLINE]


def test_simple_line_comment():
    out = toks("// hello world\n")
    assert out[0].kind == TokenKind.COMMENT
    assert out[0].text == "// hello world"
    assert out[1].kind == TokenKind.NEWLINE


def test_comment_at_eof_without_trailing_newline():
    out = toks("// trailing")
    assert len(out) == 1
    assert out[0].kind == TokenKind.COMMENT
    assert out[0].text == "// trailing"


# ---------- identifiers vs keywords vs types ----------

@pytest.mark.parametrize("word", sorted(KEYWORDS))
def test_each_keyword_is_classified(word: str):
    [t] = toks(word)
    assert t.kind == TokenKind.KEYWORD
    assert t.text == word


def test_well_known_type_words_are_just_idents():
    # `dbit`, `dw`, `w`, `bit` are constant/parameter names defined in
    # runlib.fj — the tokenizer treats them as plain identifiers. The
    # Pygments lexer in M5 does its own visual classification.
    out = toks("dbit dw w bit")
    assert [t.kind for t in out] == [TokenKind.IDENT] * 4
    assert [t.text for t in out] == ["dbit", "dw", "w", "bit"]


def test_dotted_identifier_is_ident_not_keyword():
    # `def.foo` is not a keyword even though `def` appears
    [t] = toks("def.foo")
    assert t.kind == TokenKind.IDENT
    assert t.text == "def.foo"


def test_leading_dot_identifier():
    [t] = toks(".add")
    assert t.kind == TokenKind.IDENT
    assert t.text == ".add"


def test_double_dot_identifier():
    [t] = toks("..tables.ret")
    assert t.kind == TokenKind.IDENT
    assert t.text == "..tables.ret"


def test_bare_dot_falls_through_to_op():
    # `.` followed by space is not a valid ident start; should not crash
    out = toks(". x")
    assert out[0].kind == TokenKind.OP
    assert out[0].text == "."
    assert out[-1].kind == TokenKind.IDENT
    assert out[-1].text == "x"


# ---------- numbers ----------

def test_decimal():
    [t] = toks("12345")
    assert t.kind == TokenKind.NUMBER and t.text == "12345"


def test_hex_number():
    [t] = toks("0xCAFE")
    assert t.kind == TokenKind.NUMBER and t.text == "0xCAFE"


def test_binary_number():
    [t] = toks("0b1010")
    assert t.kind == TokenKind.NUMBER and t.text == "0b1010"


# ---------- strings ----------

def test_double_quoted_string():
    [t] = toks('"hello\\n"')
    assert t.kind == TokenKind.STRING and t.text == '"hello\\n"'


def test_single_quoted_string():
    [t] = toks("'H'")
    assert t.kind == TokenKind.STRING and t.text == "'H'"


# ---------- punctuation and operators ----------

def test_punctuation_each_mapped():
    out = toks("{}();,=@<>:")
    expected = [
        TokenKind.LBRACE, TokenKind.RBRACE,
        TokenKind.LPAREN, TokenKind.RPAREN,
        TokenKind.SEMI, TokenKind.COMMA,
        TokenKind.EQUALS, TokenKind.AT,
        TokenKind.LT, TokenKind.GT, TokenKind.COLON,
    ]
    assert [t.kind for t in out] == expected


def test_operator_chunking():
    [t] = toks("?")
    assert t.kind == TokenKind.OP and t.text == "?"


# ---------- line continuation ----------

def test_backslash_newline_consumed_as_nothing():
    # `def foo a, \
    #  b, c` becomes a single logical line of tokens
    out = toks("def foo a, \\\nb, c")
    # We expect: KEYWORD def, IDENT foo, IDENT a, COMMA, IDENT b, COMMA, IDENT c
    kinds = [t.kind for t in out]
    assert TokenKind.NEWLINE not in kinds
    assert kinds == [
        TokenKind.KEYWORD, TokenKind.IDENT, TokenKind.IDENT, TokenKind.COMMA,
        TokenKind.IDENT, TokenKind.COMMA, TokenKind.IDENT,
    ]


def test_backslash_newline_advances_line_counter():
    # After the backslash continuation, subsequent tokens report the
    # NEW physical line so the doc-comment attachment pass picks the
    # right anchor.
    out = toks("a \\\nb")
    assert out[0].line == 1
    assert out[1].line == 2


# ---------- real-world snippet from runlib.fj ----------

def test_real_macro_header_tokenizes():
    src = "def startup code_start > IO {"
    out = toks(src)
    assert [t.kind for t in out] == [
        TokenKind.KEYWORD,    # def
        TokenKind.IDENT,      # startup
        TokenKind.IDENT,      # code_start
        TokenKind.GT,         # >
        TokenKind.IDENT,      # IO
        TokenKind.LBRACE,     # {
    ]


def test_complexity_doc_comment_preserves_full_text():
    src = "// Complexity: ~7000  (7026 for w=64, 6894 for w=16)"
    [t] = toks(src)
    assert t.kind == TokenKind.COMMENT
    assert t.text == src


def test_line_and_col_tracked():
    out = toks("ab\ncd")
    assert out[0].line == 1 and out[0].col == 1
    assert out[1].kind == TokenKind.NEWLINE
    assert out[2].line == 2 and out[2].col == 1


def test_string_with_escaped_newline_advances_line_counter():
    # `"abc\<newline>def"` — the backslash-newline inside the string is
    # an escape sequence, not a token boundary. The line counter MUST
    # advance through it so downstream doc-attachment finds the correct
    # source row for the next def. (CR-ist finding on M3.)
    src = '"abc\\\ndef"\n\nns stl { def loop {} }'
    out = list(tokenize(src))
    # Find the def keyword and check its line.
    def_tok = next(t for t in out if t.kind == TokenKind.KEYWORD and t.text == "def")
    assert def_tok.line == 4, (
        f"def should be on line 4 (string line 1, esc newline → line 2, "
        f"newline line 3, blank line 4), got line {def_tok.line}"
    )

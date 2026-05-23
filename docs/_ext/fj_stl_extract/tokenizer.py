"""Token stream for FlipJump source.

Token taxonomy is intentionally fine-grained so the parser doesn't have
to re-classify substrings. Whitespace is dropped EXCEPT newlines, which
the doc-comment attachment pass and the dep-graph walker both rely on as
statement separators.

`//` is the only comment form (verified against the upstream flip-jump
STL — there is no `/* */`). Backslash-newline (`\\\n`) is a soft line
continuation and is consumed as nothing; the parser sees the next
physical line as a continuation of the previous logical line.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterator

__all__ = ["Token", "TokenKind", "tokenize"]


class TokenKind(str, Enum):
    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    SEMI = "SEMI"
    COMMA = "COMMA"
    EQUALS = "EQUALS"
    AT = "AT"
    LT = "LT"
    GT = "GT"
    COLON = "COLON"
    IDENT = "IDENT"
    KEYWORD = "KEYWORD"
    NUMBER = "NUMBER"
    STRING = "STRING"
    OP = "OP"
    EOF = "EOF"


KEYWORDS = frozenset({"def", "ns", "rep", "pad", "reserve", "segment", "wflip"})

# The Monaco tokenizer for the IDE classifies `dbit`, `dw`, `w`, `bit` as
# "types" for syntax highlighting. They are NOT language keywords —
# `dw` and `dbit` are defined as named constants in runlib.fj and `w`
# is set at compile time. The parser treats them as plain IDENTs.
#
# Reserved for the M5 Pygments lexer, which will mirror the Monaco
# tokenizer's visual classification for code blocks in the docs.
WELL_KNOWN_TYPE_NAMES = frozenset({"dbit", "dw", "w", "bit"})

# Single-char punctuation that maps 1:1 to a token kind.
_PUNCT: dict[str, TokenKind] = {
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "[": TokenKind.LBRACKET,
    "]": TokenKind.RBRACKET,
    ";": TokenKind.SEMI,
    ",": TokenKind.COMMA,
    "=": TokenKind.EQUALS,
    "@": TokenKind.AT,
    "<": TokenKind.LT,
    ">": TokenKind.GT,
    ":": TokenKind.COLON,
}

# Characters that may appear in an OP token. Match the Monarch tokenizer's
# operator character class minus the ones already covered as their own
# single-char tokens above (`=`, `<`, `>`, `@`, `:`).
_OP_CHARS = frozenset("!?^|%&*+-/#$")


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    text: str
    line: int   # 1-based
    col: int    # 1-based


def tokenize(source: str) -> Iterator[Token]:
    """Yield tokens from `source`. Drops whitespace except newlines."""
    line = 1
    col = 1
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        # ---- whitespace + line continuation ----
        if ch == "\\" and i + 1 < n and source[i + 1] == "\n":
            i += 2
            line += 1
            col = 1
            continue

        if ch == " " or ch == "\t" or ch == "\r":
            i += 1
            col += 1
            continue

        if ch == "\n":
            yield Token(TokenKind.NEWLINE, "\n", line, col)
            i += 1
            line += 1
            col = 1
            continue

        # ---- line comment ----
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            start = i
            while i < n and source[i] != "\n":
                i += 1
            text = source[start:i]
            yield Token(TokenKind.COMMENT, text, line, col)
            col += i - start
            continue

        # ---- strings ----
        if ch == '"' or ch == "'":
            quote = ch
            start = i
            start_col = col
            string_start_line = line
            i += 1
            col += 1
            while i < n:
                if source[i] == "\\" and i + 1 < n:
                    # An escaped newline inside a string still advances
                    # the line counter — otherwise every token after the
                    # string would report a wrong line number, and the
                    # doc-attachment pass would walk to the wrong source
                    # row. (See CR-ist finding on PR #5.)
                    if source[i + 1] == "\n":
                        line += 1
                        col = 1
                    else:
                        col += 2
                    i += 2
                    continue
                if source[i] == quote:
                    i += 1
                    col += 1
                    break
                if source[i] == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
            yield Token(TokenKind.STRING, source[start:i], string_start_line, start_col)
            continue

        # ---- numbers ----
        if ch.isdigit():
            start = i
            start_col = col
            if ch == "0" and i + 1 < n and source[i + 1] in ("x", "X", "b", "B"):
                i += 2
                col += 2
                while i < n and (source[i].isalnum() or source[i] == "_"):
                    i += 1
                    col += 1
            else:
                while i < n and source[i].isdigit():
                    i += 1
                    col += 1
            yield Token(TokenKind.NUMBER, source[start:i], line, start_col)
            continue

        # ---- identifiers (with optional leading `.` / `..` and embedded dots) ----
        if ch.isalpha() or ch == "_" or ch == ".":
            start = i
            start_col = col
            # Allow up to two leading dots (current-ns / parent-ns refs).
            # A standalone `.` followed by no name is NOT an identifier; bail to OP.
            if ch == ".":
                # peek past 1 or 2 dots
                j = i
                while j < n and source[j] == ".":
                    j += 1
                # need at least one [A-Za-z_] after
                if j < n and (source[j].isalpha() or source[j] == "_"):
                    i = j
                    col += j - start
                else:
                    # bare `.` or `..` not followed by name — treat as OP
                    yield Token(TokenKind.OP, source[start:j or start + 1], line, start_col)
                    if j == start:
                        i += 1
                        col += 1
                    else:
                        i = j
                        col += j - start
                    continue
            while i < n and (source[i].isalnum() or source[i] == "_" or source[i] == "."):
                i += 1
                col += 1
            text = source[start:i]
            # KEYWORD only for bare words (no dots, no leading dots).
            # `dw`/`dbit`/`w`/`bit` are IDENTs even though the IDE
            # highlights them as types — they're just names defined in
            # runlib.fj.
            if "." not in text and text in KEYWORDS:
                yield Token(TokenKind.KEYWORD, text, line, start_col)
            else:
                yield Token(TokenKind.IDENT, text, line, start_col)
            continue

        # ---- single-char punctuation ----
        if ch in _PUNCT:
            yield Token(_PUNCT[ch], ch, line, col)
            i += 1
            col += 1
            continue

        # ---- operators (chunked) ----
        if ch in _OP_CHARS:
            start = i
            start_col = col
            while i < n and source[i] in _OP_CHARS:
                i += 1
                col += 1
            yield Token(TokenKind.OP, source[start:i], line, start_col)
            continue

        # Unknown character — yield as OP so we don't drop information.
        # Parser will skip OP tokens it doesn't care about.
        yield Token(TokenKind.OP, ch, line, col)
        i += 1
        col += 1

    yield Token(TokenKind.EOF, "", line, col)

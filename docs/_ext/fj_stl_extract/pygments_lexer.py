"""Pygments lexer for FlipJump source.

Mirrors the Monaco/Monarch tokenizer that ships with the FlipJump IDE
at https://fj.tomhe.app — token kinds match exactly so this docs site
and the IDE colour `.fj` code blocks identically.

Reference: `components/CodeEditor.tsx` in the fj.tomhe.app repo,
`monaco.languages.setMonarchTokensProvider('flipjump', { ... })` call.

Token mapping (Monarch → Pygments):

    keywords ['ns', 'rep']        → Keyword
    'def'                          → Keyword.Declaration
    types ['dbit','dw','w','bit'] → Keyword.Type
    directives ['pad','reserve','segment','wflip'] → Name.Builtin
    labels (ident before ':')     → Name.Label
    constants (ident before '=')  → Name.Constant
    macro names (after `def`)     → Name.Function
    macro calls (ident at line start, no `:`/`=`)
                                  → Name.Function.Magic
    `//` line comments            → Comment.Single
    numbers (0x, 0b, decimal)     → Number.Hex / Number.Bin / Number.Integer
    strings ("..." or '...')      → String.Double / String.Single
    `;` `,`                       → Punctuation
    operator chars                → Operator
    everything else                → Text / Name
"""

from __future__ import annotations

from pygments.lexer import RegexLexer, bygroups, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)

__all__ = ["FlipJumpLexer"]


# Bare-word identifiers that should NEVER be classified as a macro
# call, even when they appear at line-start. Mirrors the negative
# lookahead in the IDE's macro-call regex.
_NON_MACRO_LEAD_WORDS = (
    "def", "ns", "rep", "pad", "reserve", "segment", "wflip",
    "dbit", "dw", "w",
    # NOTE: `bit` is NOT in the IDE's `types` list, so it must NOT be
    # excluded here either. The IDE colours `bit` as a plain identifier.
)


class FlipJumpLexer(RegexLexer):
    name = "FlipJump"
    aliases = ["fj", "flipjump", "FlipJump"]
    filenames = ["*.fj"]
    mimetypes = ["text/x-flipjump"]

    tokens = {
        "root": [
            # ---- Strings FIRST so quoted content isn't reinterpreted ----
            # (CR-ist M5 finding: previously a string like "def" had the
            # outer quote eaten by the catchall and `def` mis-classified
            # as Keyword.Declaration.)
            (r'"([^"\\]|\\.)*"', String.Double),
            (r"'([^'\\]|\\.)*'", String.Single),

            # ---- Whitespace & comments ----
            (r"\\\n", Whitespace),  # line continuation
            (r"//[^\n]*", Comment.Single),

            # ---- Macro call detection (parity with the IDE) ----
            # An identifier at the START of a logical line, not one of
            # the language keywords/types, followed by either an args
            # list, a comment, or EOL, is coloured as a macro call.
            # Mirrors the regex in CodeEditor.tsx exactly.
            (r"(^[ \t]*)"
             r"((?!(?:" + "|".join(_NON_MACRO_LEAD_WORDS) + r")\b)"
             r"[A-Za-z_.][\w.]*)"
             r"(?=[ \t]+[^;\s/]|[ \t]*(?://|$))",
             bygroups(Whitespace, Name.Function.Magic)),

            (r"[ \t]+", Whitespace),
            (r"\n", Whitespace),

            # ---- def NAME / ns NAME with the introduced-name coloured ----
            (r"(\bdef\b)([ \t]+)([A-Za-z_]\w*)",
             bygroups(Keyword.Declaration, Whitespace, Name.Function)),
            (r"(\bns\b)([ \t]+)([A-Za-z_]\w*)",
             bygroups(Keyword, Whitespace, Name.Namespace)),

            # ---- Other simple keywords ----
            (r"\brep\b", Keyword),

            # ---- Labels and constants BEFORE type/directive rules ----
            # so `dw = ...` is constant LHS, not a type word, and
            # `foo:` is a label, not an ident.

            # Constants: `IDENT = expr`. The `(?!=)` after `=` is critical
            # so the rule does NOT fire on `a == b` (CR-ist M5 finding).
            (r"([A-Za-z_]\w*)([ \t]*)(=)(?!=)",
             bygroups(Name.Constant, Whitespace, Operator)),

            # Labels: `IDENT:`. The `(?!:)` after `:` avoids matching
            # the `::` digraph if FlipJump ever introduces one.
            (r"([A-Za-z_]\w*)([ \t]*)(:)(?!:)",
             bygroups(Name.Label, Whitespace, Punctuation)),

            # ---- Directives ----
            (words(("pad", "reserve", "segment", "wflip"), suffix=r"\b"),
             Name.Builtin),

            # ---- Well-known type-like names ----
            # Matches the IDE's `types` list — NOT including `bit`,
            # which the IDE classifies as a plain identifier.
            (words(("dbit", "dw", "w"), suffix=r"\b"),
             Keyword.Type),

            # ---- Identifiers ----
            # Dotted prefixes (namespace navigation): `.foo`, `..tables.x`.
            (r"\.{1,2}[A-Za-z_][\w.]*", Name.Other),
            # Bare or dotted identifiers (`stl.startup`, `bit`, `_local`).
            (r"[A-Za-z_][\w.]*", Name),

            # ---- Literals ----
            (r"0[xX][0-9a-fA-F]+", Number.Hex),
            (r"0[bB][01]+", Number.Bin),
            (r"\d+", Number.Integer),

            # ---- Punctuation & operators ----
            (r"[;,{}()\[\]]", Punctuation),
            (r"[!=<>?@^|%&*+\-/:#$]", Operator),

            # ---- Fallback ----
            (r".", Text),
        ],
    }

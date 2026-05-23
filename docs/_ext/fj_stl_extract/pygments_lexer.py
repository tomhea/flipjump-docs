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

from pygments.lexer import RegexLexer, bygroups, include, words
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


class FlipJumpLexer(RegexLexer):
    name = "FlipJump"
    aliases = ["fj", "flipjump", "FlipJump"]
    filenames = ["*.fj"]
    mimetypes = ["text/x-flipjump"]

    tokens = {
        "root": [
            # Whitespace & comments
            (r"[ \t]+", Whitespace),
            (r"\\\n", Whitespace),  # line continuation
            (r"\n", Whitespace),
            (r"//[^\n]*", Comment.Single),

            # `def NAME` — colour NAME as Name.Function
            (r"(\bdef\b)([ \t]+)([A-Za-z_]\w*)",
             bygroups(Keyword.Declaration, Whitespace, Name.Function)),

            # `ns NAME` — colour NAME as Name.Namespace
            (r"(\bns\b)([ \t]+)([A-Za-z_]\w*)",
             bygroups(Keyword, Whitespace, Name.Namespace)),

            # Other declaration keywords
            (r"\brep\b", Keyword),

            # Labels and constants come BEFORE the type/directive rules
            # so that `dw =` (the constant definition in runlib.fj) is
            # coloured as a constant LHS, not as a type word. Mirrors
            # the rule ordering in CodeEditor.tsx's Monaco tokenizer.

            # Labels: identifier followed by `:`
            (r"([A-Za-z_]\w*)(\s*)(:)",
             bygroups(Name.Label, Whitespace, Punctuation)),

            # Constants: identifier followed by `=`
            (r"([A-Za-z_]\w*)(\s*)(=)",
             bygroups(Name.Constant, Whitespace, Operator)),

            # Directives
            (words(("pad", "reserve", "segment", "wflip"), suffix=r"\b"),
             Name.Builtin),

            # Well-known type-like names (compile-time constants defined
            # in runlib.fj but classified visually as types to match the
            # IDE).
            (words(("dbit", "dw", "w", "bit"), suffix=r"\b"),
             Keyword.Type),

            # Dotted identifiers (namespace refs like `stl.startup`,
            # `.foo`, `..tables.x`). Matched after labels/constants so
            # those win when followed by `:`/`=`.
            (r"\.{1,2}[A-Za-z_][\w.]*", Name.Other),
            (r"[A-Za-z_][\w.]*", Name),

            # Numbers
            (r"0[xX][0-9a-fA-F]+", Number.Hex),
            (r"0[bB][01]+", Number.Bin),
            (r"\d+", Number.Integer),

            # Strings
            (r'"([^"\\]|\\.)*"', String.Double),
            (r"'([^'\\]|\\.)*'", String.Single),

            # Punctuation: `;` is the flip/jump separator, `,` separates args
            (r"[;,{}()\[\]]", Punctuation),

            # Operators — see CodeEditor.tsx's operator character class
            (r"[!=<>?@^|%&*+\-/:#$]", Operator),

            # Anything else
            (r".", Text),
        ],
    }

"""Pygments style matching the FlipJump IDE's `fj-dark` theme.

Source of truth: the theme block in `components/CodeEditor.tsx`
(`monaco.editor.defineTheme('fj-dark', {...})`). The hex colours
below are copied verbatim so code blocks here look identical to
code in the editor at https://fj.tomhe.app.
"""

from __future__ import annotations

from pygments.style import Style
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

__all__ = ["FlipJumpDarkStyle"]


class FlipJumpDarkStyle(Style):
    name = "fj-dark"
    background_color = "#1e1e1e"
    highlight_color = "#264f78"
    line_number_color = "#858585"

    styles = {
        Text:               "#d4d4d4",
        Whitespace:         "#d4d4d4",

        Comment:            "italic #6a9955",
        Comment.Single:     "italic #6a9955",

        # 'def', 'ns', 'rep'
        Keyword:                  "bold #569cd6",
        Keyword.Declaration:      "bold #569cd6",
        # 'pad', 'reserve', 'segment', 'wflip'
        Name.Builtin:             "#e07b39",
        # 'dbit', 'dw', 'w', 'bit'
        Keyword.Type:             "#4ec9b0",

        # Identifiers
        Name:                     "#9cdcfe",
        # Labels (`foo:` LHS)
        Name.Label:               "#4ec9b0",
        # Constants (`foo = ...` LHS)
        Name.Constant:            "#c792ea",
        # `def NAME` — the macro being defined
        Name.Function:            "#56c8c8",
        # Macro invocation at statement start
        Name.Function.Magic:      "#e8c47a",
        # Namespace names after `ns`
        Name.Namespace:           "#56c8c8",
        # Dotted identifiers (namespace refs)
        Name.Other:               "#9cdcfe",

        Number:                   "#b5cea8",
        Number.Hex:               "#b5cea8",
        Number.Bin:               "#b5cea8",
        Number.Integer:           "#b5cea8",

        String:                   "#ce9178",
        String.Single:            "#ce9178",
        String.Double:            "#ce9178",

        Operator:                 "#d4d4d4",
        Punctuation:              "#d4d4d4",
    }

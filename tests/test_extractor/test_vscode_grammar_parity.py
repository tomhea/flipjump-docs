"""Parity guard: the shared TextMate grammar must stay in lock-step with the
Pygments lexer.

The VS Code extension and the JetBrains bundle both consume
``editors/grammars/flipjump.tmLanguage.json``. That grammar is a hand-written
port of ``docs/_ext/fj_stl_extract/pygments_lexer.py`` (which mirrors the IDE's
Monaco tokenizer). These tests fail loudly if the lexer's word-lists change
without the grammar following, if the editor packages' colours drift from the
``fj-dark`` Pygments style, and if the per-editor synced copies drift from the
canonical grammar.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fj_stl_extract.pygments_lexer import _NON_MACRO_LEAD_WORDS
from fj_stl_extract.pygments_style import FlipJumpDarkStyle

# Repo root = three levels up from tests/test_extractor/.
_ROOT = Path(__file__).resolve().parents[2]
_EDITORS = _ROOT / "editors"
_CANONICAL_GRAMMAR = _EDITORS / "grammars" / "flipjump.tmLanguage.json"
_CANONICAL_THEME = _EDITORS / "flipjump-dark.tmTheme"
_VSCODE_PKG = _EDITORS / "vscode" / "package.json"

_HEX = re.compile(r"#[0-9a-fA-F]{6}")


def _hexes(text: str) -> set[str]:
    return {h.lower() for h in _HEX.findall(text)}

# Keywords that introduce a name (def/ns) plus the bare keyword (rep). These
# are the non-directive, non-type words excluded from macro-call detection.
_KEYWORDS = {"def", "ns", "rep"}


def _grammar() -> dict:
    return json.loads(_CANONICAL_GRAMMAR.read_text(encoding="utf-8"))


def _pattern_match_by_scope(grammar: dict, scope: str) -> str:
    for rule in grammar["patterns"]:
        if rule.get("name") == scope:
            return rule["match"]
    raise AssertionError(f"no top-level pattern with name {scope!r}")


def _alternation_words(regex: str) -> set[str]:
    """Pull the words out of a ``\\b(a|b|c)\\b`` style match."""
    m = re.search(r"\(([A-Za-z_|]+)\)", regex)
    assert m, f"no alternation group found in {regex!r}"
    return set(m.group(1).split("|"))


def test_macro_call_exclusion_matches_lexer():
    """The negative-lookahead word-list in the macro-call rule must equal the
    lexer's ``_NON_MACRO_LEAD_WORDS`` exactly."""
    grammar = _grammar()
    macro_rule = next(
        r["match"]
        for r in grammar["patterns"]
        if "(?!(?:" in r.get("match", "")
    )
    inner = re.search(r"\(\?!\(\?:([^)]*)\)", macro_rule)
    assert inner, "could not find the (?!(?:...)) exclusion group"
    grammar_words = set(inner.group(1).split("|"))
    assert grammar_words == set(_NON_MACRO_LEAD_WORDS)


def test_directive_and_type_words_partition_the_exclusion_list():
    """Directives + types + {def,ns,rep} must reconstruct the exclusion list,
    and directives must not overlap types — ties both rules back to the single
    exported constant."""
    grammar = _grammar()
    directives = _alternation_words(
        _pattern_match_by_scope(grammar, "keyword.other.directive.flipjump")
    )
    types = _alternation_words(
        _pattern_match_by_scope(grammar, "support.type.flipjump")
    )
    assert directives.isdisjoint(types)
    assert directives | types | _KEYWORDS == set(_NON_MACRO_LEAD_WORDS)


def test_bit_is_not_a_type():
    """`bit` is deliberately NOT a type (the IDE colours it as an identifier)."""
    grammar = _grammar()
    types = _alternation_words(
        _pattern_match_by_scope(grammar, "support.type.flipjump")
    )
    assert "bit" not in types


def test_synced_copies_are_byte_identical_to_canonical():
    """`npm run sync` copies the canonical grammar/theme into the per-editor
    packages; the committed copies must match byte-for-byte."""
    canonical_grammar = _CANONICAL_GRAMMAR.read_bytes()
    for copy in (
        _EDITORS / "vscode" / "syntaxes" / "flipjump.tmLanguage.json",
        _EDITORS / "jetbrains" / "flipjump.tmLanguage.json",
    ):
        assert copy.read_bytes() == canonical_grammar, f"{copy} drifted; run `npm run sync`"

    canonical_theme = _CANONICAL_THEME.read_bytes()
    assert (_EDITORS / "jetbrains" / "flipjump-dark.tmTheme").read_bytes() == canonical_theme


# ---- colour parity with the fj-dark Pygments style ----

def _style_foreground_hexes() -> set[str]:
    """The distinct token foreground colours in the fj-dark Pygments style."""
    out: set[str] = set()
    for value in FlipJumpDarkStyle.styles.values():
        out |= _hexes(value)
    return out


def _vscode_tokencolor_hexes() -> set[str]:
    pkg = json.loads(_VSCODE_PKG.read_text(encoding="utf-8"))
    rules = pkg["contributes"]["configurationDefaults"][
        "editor.tokenColorCustomizations"
    ]["textMateRules"]
    out: set[str] = set()
    for rule in rules:
        fg = rule["settings"].get("foreground")
        if fg:
            out.add(fg.lower())
    return out


def test_vscode_colours_match_the_fj_dark_style():
    """The VS Code extension's token colours must be exactly the foreground
    palette of the docs-site fj-dark style — no more, no fewer."""
    assert _vscode_tokencolor_hexes() == _style_foreground_hexes()


def test_jetbrains_theme_covers_the_fj_dark_palette():
    """Every fj-dark token colour must appear in the JetBrains .tmTheme (which
    additionally carries editor-chrome colours, hence subset not equality)."""
    theme_hexes = _hexes(_CANONICAL_THEME.read_text(encoding="utf-8"))
    assert _style_foreground_hexes() <= theme_hexes

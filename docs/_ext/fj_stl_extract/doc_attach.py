"""Attach doc comments to macros and extract structured fields.

The attachment rule (verified against the upstream STL):

    A `def` macro's doc comment is the CONTIGUOUS run of `//` lines
    immediately above its `def` keyword. "Contiguous" means no blank
    line between the doc block and the `def`. A blank line means the
    comment block is a file-level banner / separator, not a macro doc.

Structured fields recognised inside the doc block:

    // Time Complexity: ...      →  time_complexity
    // Space Complexity: ...     →  space_complexity
    // Complexity: ...           →  both fields (if Time/Space not given)
    // @requires X (or Y)        →  requires.append("X (or Y)")
    // @output-param NAME: ...   →  output_params[NAME] = ...

Every other `//` line is concatenated into the free-form description.
The doc-comment prefix `// ` is stripped from description lines so the
output renders as clean Markdown.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parser import FileNode

__all__ = ["DocInfo", "attach_docs"]


_TIME_RE = re.compile(r"^\s*Time\s+Complexity\s*:\s*(.+?)\s*$")
_SPACE_RE = re.compile(r"^\s*Space\s+Complexity\s*:\s*(.+?)\s*$")
# Bare `Complexity` line: the colon is OPTIONAL because the upstream
# STL uses both `Complexity: 9@-7` and `Complexity 9@-7` (see e.g.
# bit/pointers.fj, bit/output.fj). The captured value is then validated
# downstream to ensure it actually looks like a complexity expression
# (so plain prose starting with the word "Complexity" doesn't match).
_BOTH_RE = re.compile(r"^\s*Complexity\s*:?\s+(.+?)\s*$")
# Short forms `Time: X` / `Space: X` appear in many STL files as
# follow-ups to a leading `Complexity:` line — see e.g. bit/memory.fj
# where `// Complexity: 2@+5` is followed by `// Space: 3@+8`,
# meaning the first was Time and the second is Space.
_TIME_SHORT_RE = re.compile(r"^\s*Time\s*:\s*(.+?)\s*$")
_SPACE_SHORT_RE = re.compile(r"^\s*Space\s*:\s*(.+?)\s*$")
_REQUIRES_RE = re.compile(r"^\s*@requires\s+(.+?)\s*$")
_OUTPUT_PARAM_RE = re.compile(r"^\s*@output-param\s+(\w+)\s*:\s*(.+?)\s*$")
_BANNER_RE = re.compile(r"^\s*[-=*~]{3,}")

# Validator: a complexity value should contain at least one
# "complexity-y" character (digit, @, operator, paren). This blocks
# false-positive matches like `Complexity is the runtime cost` from
# being captured as an ambiguous complexity entry.
_COMPLEXITY_CHARS = set("0123456789@()+-*^~/#")


def _looks_like_complexity_value(value: str) -> bool:
    return any(c in _COMPLEXITY_CHARS for c in value)


# A line is "prose" if it contains at least one pair of adjacent
# 3+-letter lowercase English words joined by whitespace only.
# Pseudocode like `dst += src` or `a, b = b, a` won't match (no
# adjacent multi-letter word pairs); English like "prints x[:n] as
# an unsigned decimal number" matches readily ("as an", "an unsigned",
# "unsigned decimal", "decimal number"). Used to keep indented prose
# lines like the `//   prints x[:n] as ...` summary in bit.print_dec_uint
# from being wrapped entirely in inline-code backticks.
_PROSE_LINE_RE = re.compile(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b")

# An "inline code" token in prose: identifier-prefixed run containing at
# least one operator-only char (`= + - * / % & | ^ < > ! [`). Identifier
# prefix prevents matching bare `/`, `*` etc.; the operator gate
# prevents false-positives on plain dotted names like `bit.add` (which
# get linked elsewhere). Negative lookbehind/lookahead avoids
# re-wrapping already-backticked content.
_INLINE_CODE_RE = re.compile(
    r"(?<![`\w])"
    r"([A-Za-z_][\w.\[\]:]*[\[=+\-*/%&|^<>!][\w.\[\]:=+\-*/%&|^<>!]*)"
    r"(?![`\w])"
)


def _backtick_inline_code(text: str) -> str:
    """Wrap inline code-like tokens (`dst==carry`, `x[:n]++`, …) in
    Markdown inline-code backticks. Leaves natural prose alone.

    URLs (anything containing `://`) are skipped via a callback so a
    raw `https://...` or a `[label](url)` Markdown link doesn't get
    its scheme/path backticked into garbage.
    """
    def repl(m: re.Match) -> str:
        token = m.group(1)
        if "://" in token:
            return token
        return f"`{token}`"
    return _INLINE_CODE_RE.sub(repl, text)


# Known assembler directive words. When a description mentions one of
# these as a bare word it gets turned into a placeholder marker; the
# renderer's per-page context provides the relative link target and
# replaces the markers with real Markdown links. We can't write absolute
# `[wflip](/language/directives.md)` here because relative links from a
# nested macro page differ in depth.
_DIRECTIVE_WORDS = frozenset({"wflip", "pad", "reserve", "segment"})
_DIRECTIVE_RE = re.compile(
    r"(?<![`\w./])(" + "|".join(sorted(_DIRECTIVE_WORDS)) + r")\b(?![`\w.])"
)


def _mark_directives(text: str) -> str:
    """Mark `wflip` / `pad` / `reserve` / `segment` mentions for
    later replacement by the renderer with a cross-page link.

    Uses a zero-width-space-wrapped sentinel
    `​{DIRECTIVE:name}​` so the later replacement step
    is unambiguous even if the same name appears inside backticks
    or URLs.
    """
    return _DIRECTIVE_RE.sub(
        lambda m: f"​{{DIRECTIVE:{m.group(1)}}}​", text
    )


@dataclass
class DocInfo:
    description: str = ""
    time_complexity: str | None = None
    space_complexity: str | None = None
    requires: list[str] = field(default_factory=list)
    output_params: dict[str, str] = field(default_factory=dict)
    raw_doc_lines: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return (
            not self.description
            and self.time_complexity is None
            and self.space_complexity is None
            and not self.requires
            and not self.output_params
        )


def attach_docs(source: str, file: FileNode) -> dict[int, DocInfo]:
    """Return a map from `id(node)` → DocInfo for every macro/constant
    in `file`.

    Why `id(node)`: dataclasses aren't hashable by default and we don't
    want to mutate the parser's output. The caller looks up by identity.
    """
    lines = source.splitlines()
    result: dict[int, DocInfo] = {}

    for macro in file.macros:
        doc_lines = _collect_doc_block(lines, macro.start_line)
        result[id(macro)] = _extract_fields(doc_lines)

    for const in file.constants:
        doc_lines = _collect_doc_block(lines, const.start_line)
        result[id(const)] = _extract_fields(doc_lines)

    return result


def _collect_doc_block(lines: list[str], anchor_line: int) -> list[str]:
    """Walk backward from `anchor_line - 1` (1-based) collecting
    contiguous `//` lines. Stop on blank, non-comment, or banner.
    """
    out: list[str] = []
    # anchor_line is 1-based; lines[anchor_line - 1] IS the def line.
    # Start one line above it.
    i = anchor_line - 2
    while i >= 0:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            break  # blank line — boundary
        if not stripped.startswith("//"):
            break  # non-comment line — boundary
        # Skip banner lines (e.g., `// ---------- Section`).
        if _BANNER_RE.match(stripped[2:]):
            break
        out.append(raw)
        i -= 1
    out.reverse()
    return out


def _extract_fields(doc_lines: list[str]) -> DocInfo:
    info = DocInfo(raw_doc_lines=list(doc_lines))
    description_parts: list[str] = []

    # Pass 1: classify each line. Complexity-like lines go into
    # `complexity_entries`; @-tags update info directly; everything
    # else becomes description.
    #
    # Each complexity entry: (kind, value) where kind is one of
    # 'time', 'space', or 'ambiguous'. Ambiguous means it was a bare
    # `Complexity:` line whose target field depends on what other
    # complexity lines surround it.
    complexity_entries: list[tuple[str, str]] = []

    for line in doc_lines:
        body = _strip_comment_prefix(line)

        # Doc tags first (most specific).
        m = _REQUIRES_RE.match(body)
        if m:
            info.requires.append(m.group(1))
            continue
        m = _OUTPUT_PARAM_RE.match(body)
        if m:
            info.output_params[m.group(1)] = m.group(2)
            continue

        # Longest complexity forms before short ones.
        m = _TIME_RE.match(body)
        if m:
            complexity_entries.append(("time", m.group(1)))
            continue
        m = _SPACE_RE.match(body)
        if m:
            complexity_entries.append(("space", m.group(1)))
            continue
        m = _BOTH_RE.match(body)
        if m and _looks_like_complexity_value(m.group(1)):
            complexity_entries.append(("ambiguous", m.group(1)))
            continue
        m = _TIME_SHORT_RE.match(body)
        if m:
            complexity_entries.append(("time", m.group(1)))
            continue
        m = _SPACE_SHORT_RE.match(body)
        if m:
            complexity_entries.append(("space", m.group(1)))
            continue

        description_parts.append(body)

    # Pass 2: resolve ambiguous Complexity: entries against their
    # neighbours. A bare `Complexity:` followed by a later `Space:`
    # (or `Space Complexity:`) line, with no earlier Time spec,
    # becomes Time. Mirror for the opposite layout.
    for i, (kind, val) in enumerate(complexity_entries):
        if kind != "ambiguous":
            continue
        later_kinds = [k for k, _ in complexity_entries[i + 1:]]
        earlier_kinds = [k for k, _ in complexity_entries[:i]]
        if (
            "space" in later_kinds and "time" not in later_kinds
            and "time" not in earlier_kinds
        ):
            complexity_entries[i] = ("time", val)
        elif (
            "time" in earlier_kinds and "space" not in earlier_kinds
            and "space" not in later_kinds
        ):
            complexity_entries[i] = ("space", val)

    # Pass 3a: assign all EXPLICIT entries first. This ensures that
    # in a pathological [Time:A, Complexity:B, Space:C] block, the
    # explicit `Space:C` populates space before any ambiguous entry
    # could grab the slot. (CR-ist finding on the polish batch.)
    for kind, val in complexity_entries:
        if kind == "time" and info.time_complexity is None:
            info.time_complexity = val
        elif kind == "space" and info.space_complexity is None:
            info.space_complexity = val

    # Pass 3b: ambiguous entries fill any remaining empty slots. If
    # both time and space are still unset, an ambiguous entry fills
    # BOTH (the canonical `Complexity: X` → both case).
    for kind, val in complexity_entries:
        if kind != "ambiguous":
            continue
        if info.time_complexity is None:
            info.time_complexity = val
        if info.space_complexity is None:
            info.space_complexity = val

    # Description: trim leading/trailing blank lines but preserve
    # indentation on non-blank lines. Each non-blank line gets a
    # two-space trailing hard break so that single `//` lines in
    # source render as visually separate lines in HTML (Markdown
    # collapses bare `\n` into a single space within a paragraph).
    # Blank source lines stay as paragraph breaks (`\n\n`).
    while description_parts and not description_parts[0].strip():
        description_parts.pop(0)
    while description_parts and not description_parts[-1].strip():
        description_parts.pop()
    out_lines: list[str] = []
    for part in description_parts:
        if not part.strip():
            out_lines.append("")
            continue
        # Pseudocode convention: a `//   x++` line (i.e. two or more
        # leading spaces inside the comment) is USUALLY wrapped
        # entirely in inline code so the operators don't get treated
        # as prose. BUT some macros use indentation for prose intent
        # summaries (e.g. `//   prints x[:n] as an unsigned decimal
        # number` in bit.print_dec_uint). Detect prose via the
        # adjacent-multi-letter-words heuristic and treat those as
        # prose with per-token inline-code instead.
        stripped_left = part.lstrip(" ")
        leading = part[: len(part) - len(stripped_left)]
        content = stripped_left.rstrip()
        if len(leading) >= 2 and not _PROSE_LINE_RE.search(content):
            transformed = leading + "`" + content + "`"
        else:
            transformed = leading + _mark_directives(_backtick_inline_code(content))
        out_lines.append(transformed + "  ")
    info.description = "\n".join(out_lines)
    return info


def _strip_comment_prefix(line: str) -> str:
    """Strip the leading whitespace + `//` (+ optional single space)
    from a comment line.

    `//foo` → `foo`
    `// foo` → `foo`
    `//   foo` → `  foo`   (extra indent preserved — useful for
                             pseudocode blocks like `//   x++`)
    """
    s = line.lstrip()
    assert s.startswith("//"), f"not a comment line: {line!r}"
    s = s[2:]
    if s.startswith(" "):
        s = s[1:]
    return s

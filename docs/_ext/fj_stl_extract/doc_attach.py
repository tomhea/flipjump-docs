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

from .parser import ConstantNode, FileNode, MacroNode

__all__ = ["DocInfo", "attach_docs"]


_TIME_RE = re.compile(r"^\s*Time\s+Complexity:\s*(.+?)\s*$")
_SPACE_RE = re.compile(r"^\s*Space\s+Complexity:\s*(.+?)\s*$")
_BOTH_RE = re.compile(r"^\s*Complexity:\s*(.+?)\s*$")
_REQUIRES_RE = re.compile(r"^\s*@requires\s+(.+?)\s*$")
_OUTPUT_PARAM_RE = re.compile(r"^\s*@output-param\s+(\w+)\s*:\s*(.+?)\s*$")
_BANNER_RE = re.compile(r"^\s*[-=*~]{3,}")


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

    for line in doc_lines:
        body = _strip_comment_prefix(line)

        m = _TIME_RE.match(body)
        if m:
            info.time_complexity = m.group(1)
            continue
        m = _SPACE_RE.match(body)
        if m:
            info.space_complexity = m.group(1)
            continue
        m = _BOTH_RE.match(body)
        if m and info.time_complexity is None and info.space_complexity is None:
            info.time_complexity = m.group(1)
            info.space_complexity = m.group(1)
            continue
        m = _REQUIRES_RE.match(body)
        if m:
            info.requires.append(m.group(1))
            continue
        m = _OUTPUT_PARAM_RE.match(body)
        if m:
            info.output_params[m.group(1)] = m.group(2)
            continue

        description_parts.append(body)

    # Trim leading and trailing BLANK lines, but preserve indentation
    # on non-blank lines (matters for `//   pseudocode` blocks). A
    # plain `.strip()` would erode the leading two-space indent.
    while description_parts and not description_parts[0].strip():
        description_parts.pop(0)
    while description_parts and not description_parts[-1].strip():
        description_parts.pop()
    info.description = "\n".join(description_parts)
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

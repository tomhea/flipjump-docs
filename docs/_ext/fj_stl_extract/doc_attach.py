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


# -----------------------------------------------------------------------
# Per-macro description overrides.
#
# When the upstream `.fj` doc comment is missing, focused on warnings
# / notes rather than what the macro does, or just unclear, we replace
# its extracted description with a hand-authored summary.
#
# Each override is keyed by `(fq_name, arity)`. Applied AFTER auto-
# extraction so complexity, @requires, @output-param, etc. are still
# pulled from source — only the prose description changes.
#
# Overrides are written in Markdown and may use inline backticks.
# Multi-line summaries should use two-trailing-space hard breaks
# (handled by the renderer) to preserve line breaks in HTML.
# -----------------------------------------------------------------------

_BIT_DESCRIPTION = (
    "This is the basic variable in the FlipJump standard library — a bit "
    "(can contain only 0 or 1).\n\n"
    "You can't place it as you would any other standard library macro, "
    "because \"running\" this line is undefined behavior. The `bit` (and "
    "`bit.vec`) should be placed in a region of memory that won't ever be "
    "executed — typically below `stl.loop`."
)

_HEX_DESCRIPTION = (
    "This is another basic variable in the FlipJump standard library — "
    "a hex nibble (can contain only 0 through 15).\n\n"
    "You can't place it as you would any other standard library macro, "
    "because \"running\" this line is undefined behavior. The `hex` (and "
    "`hex.vec`) should be placed in a region of memory that won't ever be "
    "executed — typically below `stl.loop`."
)


_DESCRIPTION_OVERRIDES: dict[tuple[str, int], str] = {
    # ---------- bit memory primitives ----------
    ("bit.bit", 0): _BIT_DESCRIPTION,
    ("bit.bit", 1): _BIT_DESCRIPTION,
    ("bit.vec", 1): _BIT_DESCRIPTION,
    ("bit.vec", 2): _BIT_DESCRIPTION,

    # ---------- hex memory primitives ----------
    ("hex.hex", 0): _HEX_DESCRIPTION,
    ("hex.hex", 1): _HEX_DESCRIPTION,
    ("hex.vec", 1): _HEX_DESCRIPTION,
    ("hex.vec", 2): _HEX_DESCRIPTION,

    # ---------- bit specific intent (source had no useful summary) ----------
    ("bit.ptr_inc", 1):
        "`ptr += 2w` — advance a w-wide bit-pointer by one dw-aligned word.",

    ("bit.mul.mul_add_if", 4):
        "`if flag: dst[:n] += src[:n]` — conditional in-place add. `flag` is a bit.",

    # ---------- bit.cmp (auto-extracted summary "jump to:" is unhelpful) ----------
    ("bit.cmp", 5):
        "Three-way compare on bits: jumps to `lt` if `a<b`, `eq` if `a==b`, "
        "`gt` if `a>b`. `a`, `b` are bits; `lt`, `eq`, `gt` are addresses.",
    ("bit.cmp", 6):
        "Three-way compare on n-bit vectors: jumps to `lt` if `a[:n]<b[:n]`, "
        "`eq` if equal, `gt` if `a[:n]>b[:n]`.",

    # ---------- bit/div (user requested major update) ----------
    ("bit.idiv", 5):
        "Signed integer division: `q = a/b`, `r = a%b` with "
        "`sign(r)==sign(a)`. Jumps to `end` if `b==0`. `q`, `a`, `b`, `r` "
        "are bit[:n]. Wasteful in space — prefer `hex.idiv` for serious work.",
    ("bit.div", 5):
        "Unsigned integer division: `q = a/b`, `r = a%b`. Jumps to `end` "
        "if `b==0`. `q`, `a`, `b`, `r` are bit[:n]. Wasteful in space — "
        "prefer `hex.div` for serious work.",
    ("bit.div.div_step", 5):
        "One step of bit-level long division: `R[0] ^= N`; then if "
        "`R[:n] >= D[:n]`, do `R -= D` and toggle `Q[0]`. The inner loop "
        "of `bit.div` / `bit.idiv`.",
    ("bit.idiv_loop", 5):
        "Compact signed integer division (slower than `bit.idiv`, but uses "
        "much less program space): `q = a/b`, `r = a%b` with "
        "`sign(r)==sign(a)`. Jumps to `end` if `b==0`.",
    ("bit.div_loop", 5):
        "Compact unsigned integer division (slower than `bit.div`, but uses "
        "much less program space): `q = a/b`, `r = a%b`. Jumps to `end` "
        "if `b==0`.",

    # ---------- hex/math wrappers without source docs ----------
    ("hex.add.add_constant_with_leading_zeros", 4):
        "Internal helper for `hex.add_constant`: strips `const`'s trailing "
        "zero nibbles, then adds the result back into `dst[:n]` at the "
        "matching nibble offset (so the trailing zeros are skipped instead "
        "of materialised as wasted-work additions).",
    ("hex.add.add_hex_shifted_constant", 4):
        "Wrapper around the 5-arity `add_hex_shifted_constant`: derives "
        "`n_const = (#const + 3) / 4` automatically so the caller doesn't "
        "have to compute the constant's nibble length.",
    ("hex.sub.sub_constant_with_leading_zeros", 4):
        "Internal helper for `hex.sub_constant`: strips `const`'s trailing "
        "zero nibbles, then subtracts the result from `dst[:n]` at the "
        "matching nibble offset (so the trailing zeros are skipped instead "
        "of materialised as wasted-work subtractions).",
    ("hex.sub.sub_hex_shifted_constant", 4):
        "Wrapper around the 5-arity `sub_hex_shifted_constant`: derives "
        "`n_const = (#const + 3) / 4` automatically so the caller doesn't "
        "have to compute the constant's nibble length.",

    # ---------- hex/math_basic ----------
    # add_count_bits — get the bare-parens "(n=2 ...)" out of the summary.
    # The natural summary IS the indented intent line in source; the
    # prefer-indented heuristic picks it up after this fix.

    # ---------- hex/tables_init (better summaries) ----------
    # NOTE: the user said the /1 form's auto-extracted summary is fine
    # ("A table. When jumping to entry d - it xors d into dst, and jumps
    # to hex.tables.ret"). The /3 form is the generic n-entry helper.
    ("hex.init", 0):
        "Initialise every truth table that the `hex.*` macros depend on. "
        "Call this exactly once at program start; bundled into "
        "`stl.startup_and_init_all`. Don't mix with any `hex.*.init` "
        "calls — those would redeclare the same tables.",
    ("hex.tables.init_shared", 0):
        "Allocate the shared `ret` and `res` symbols used by every "
        "table-driven hex operation. Called once by `hex.init`.",
    ("hex.tables.init_all", 0):
        "Inner macro of `hex.init` — emits every per-operation "
        "`hex.*.init` block (or, and, mul, cmp, add, sub) in sequence. "
        "Don't call this directly; use `hex.init`.",
    ("hex.tables.clean_table_entry__table", 3):
        "Generic n-entry XOR-dispatch table: when jumped to at entry `d`, "
        "XORs `d` into `dst` and jumps to `ret`. `n` must be a power of "
        "two and the table must be `(1<<n)`-padded. The 1-arity form "
        "specialises this to `n=256, ret=hex.tables.ret`.",
    ("hex.tables.jump_to_table_entry", 3):
        "Dispatch into a 256-padded table at entry `(src<<4 | dst)`, "
        "then XOR `hex.tables.res` into `dst` on return. The hot path of "
        "every table-driven hex operation.",

    # ---------- hex/mul ----------
    ("hex.mul.clear_carry", 0):
        "Reset the per-multiplication carry-tracking variable to zero. "
        "Called by `hex.add_mul` at the start and end of each addition "
        "step (and transitively by `hex.mul` through `hex.add_mul`).",

    # ---------- hex/div (user requested) ----------
    ("hex.div", 7):
        "Unsigned integer division: `q = a/b`, `r = a%b`. Jumps to `div0` "
        "if `b==0`. `q`, `a` are hex[:n]; `r`, `b` are hex[:nb].",
    ("hex.idiv", 8):
        "Signed integer division with configurable remainder convention "
        "(`rem_opt`: 0 = `sign(r)==sign(b)`, Python-style floor division; "
        "1 = `sign(r)==sign(a)`, C-style truncation; 2 = remainder always "
        "positive). Jumps to `div0` if `b==0`. `q`, `a` are hex[:n]; "
        "`r`, `b` are hex[:nb].",

    # ---------- ptrlib ----------
    # stl.get_sp source has `//   dst[:w/4] = sp` (indented) — the
    # prefer-indented heuristic picks it after this fix. No override needed.

    # ---------- hex/pointers ----------
    ("hex.pointers.ptr_init", 0):
        "One-time initialisation of the pointer dispatch infrastructure: "
        "global opcodes, pointer-copies, and the read-byte handling "
        "table. Must be called once at program start, immediately after "
        "`stl.startup` so the read-byte table lands at address 256. "
        "Bundled into `stl.startup_and_init_all`.",
    ("hex.pointers.read_byte_from_inners_ptrs", 0):
        "`hex.pointers.read_byte[:2] = *ptr` — read one byte through the "
        "currently-set flip/jump pointers. Use after "
        "`hex.pointers.set_flip_and_jump_pointers`.",
}


def _apply_override(macro_fq: str, macro_arity: int, info: "DocInfo") -> None:
    """Replace `info.description` with the hand-authored override if one
    exists for this macro. Non-destructive on all other DocInfo fields
    (complexity, @requires, etc. still come from the auto-extracted
    source).

    Note: override strings BYPASS the auto-backticking / directive-marking
    pipeline that `_extract_fields` runs on regular description lines.
    Authors of new overrides must hand-backtick code tokens (`bit.add`,
    `dst[:n]`, …) themselves. Paragraph breaks use `\\n\\n` as usual.
    """
    override = _DESCRIPTION_OVERRIDES.get((macro_fq, macro_arity))
    if override is not None:
        info.description = override


# IGNORECASE for the "Time" / "Space" prefix words because the upstream
# STL has typos like `// TIme Complexity: ...` in bit/cond_jumps.fj.
_TIME_RE = re.compile(r"^\s*Time\s+Complexity\s*:\s*(.+?)\s*$", re.IGNORECASE)
_SPACE_RE = re.compile(r"^\s*Space\s+Complexity\s*:\s*(.+?)\s*$", re.IGNORECASE)
# `Size Complexity: N` is the upstream STL's convention for "this
# macro's expansion takes N bits/ops of program space" — semantically
# equivalent to Space Complexity. Used by `bit.bit`, `hex.hex`,
# `hex.tables_init.clean_table_entry__table`, `hex.pointers.ptr_init`,
# `hex.add_count_bits`'s carry table macros, etc.
_SIZE_RE = re.compile(r"^\s*Size\s+Complexity\s*:\s*(.+?)\s*$", re.IGNORECASE)
# Bare `Complexity` line: the colon is OPTIONAL because the upstream
# STL uses both `Complexity: 9@-7` and `Complexity 9@-7` (see e.g.
# bit/pointers.fj, bit/output.fj). The captured value is then validated
# downstream to ensure it actually looks like a complexity expression
# (so plain prose starting with the word "Complexity" doesn't match).
_BOTH_RE = re.compile(r"^\s*Complexity\s*:?\s+(.+?)\s*$", re.IGNORECASE)
# Short forms `Time: X` / `Space: X` appear in many STL files as
# follow-ups to a leading `Complexity:` line — see e.g. bit/memory.fj
# where `// Complexity: 2@+5` is followed by `// Space: 3@+8`,
# meaning the first was Time and the second is Space.
_TIME_SHORT_RE = re.compile(r"^\s*Time\s*:\s*(.+?)\s*$", re.IGNORECASE)
_SPACE_SHORT_RE = re.compile(r"^\s*Space\s*:\s*(.+?)\s*$", re.IGNORECASE)
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
        info = _extract_fields(doc_lines)
        _apply_override(macro.fq_name, macro.arity, info)
        result[id(macro)] = info

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
        # `Size Complexity:` is the upstream STL's term for what we
        # call space complexity. Same kind, different label.
        m = _SIZE_RE.match(body)
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

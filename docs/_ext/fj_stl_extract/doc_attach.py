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

_PLACEMENT_WARNING = (
    "You can't place it as you would any other standard library macro, "
    "because \"running\" this line is undefined behavior. All `bit`, "
    "`bit.vec`, `hex`, and `hex.vec` declarations should be placed in a "
    "region of memory that won't ever be executed — typically below "
    "`stl.loop`."
)


def _with_warning(summary: str) -> str:
    """Per-arity memory-primitive summary + the shared placement warning.

    The renderer's `_short_desc` picks the first non-blank line for the
    file-page bullet, so the leading summary is what shows up there; the
    warning paragraph below shows on the macro page only.
    """
    return f"{summary}\n\n{_PLACEMENT_WARNING}"


_DESCRIPTION_OVERRIDES: dict[tuple[str, int], str] = {
    # ---------- bit memory primitives (arity-specific summaries) ----------
    ("bit.bit", 0): _with_warning("Binary variable."),
    ("bit.bit", 1): _with_warning("Binary variable with initial value."),
    ("bit.vec", 1): _with_warning("Binary vector."),
    ("bit.vec", 2): _with_warning("Binary vector with initial value."),

    # ---------- hex memory primitives (arity-specific summaries) ----------
    ("hex.hex", 0): _with_warning("Hexadecimal variable."),
    ("hex.hex", 1): _with_warning("Hexadecimal variable with initial value."),
    ("hex.vec", 1): _with_warning("Hexadecimal vector."),
    ("hex.vec", 2): _with_warning("Hexadecimal vector with initial value."),

    # ---------- bit specific intent (source had no useful summary) ----------
    ("bit.ptr_inc", 1):
        "`ptr += 2w` — advance a w-wide bit-pointer by one dw-aligned word.",

    ("bit.mul.mul_add_if", 4):
        "`if flag: dst[:n] += src[:n]` — conditional in-place add. `flag` is a bit.",

    ("bit.neg", 2):
        "`x[:n] = -x[:n]`",

    # ---------- bit/hex ptr_flip / ptr_jump (source intent line is just `like: ...`) ----------
    ("bit.ptr_flip", 1):
        "Flip the bit whose address is stored in `ptr`. Effectively `*ptr;`.",
    ("bit.ptr_jump", 1):
        "Jump to the address stored in `ptr`. Effectively `;*ptr`.",
    ("hex.ptr_flip", 1):
        "Flip the bit whose address is stored in `ptr`. Effectively `*ptr;`.",
    ("hex.ptr_jump", 1):
        "Jump to the address stored in `ptr`. Effectively `;*ptr`.",

    # ---------- bit.cmp + cmp_next_eq (auto "jump to:" is just a header) ----------
    ("bit.cmp", 5):
        "Three-way compare on bits: jumps to `lt` if `a<b`, `eq` if `a==b`, "
        "`gt` if `a>b`. `a`, `b` are bits; `lt`, `eq`, `gt` are addresses.",
    ("bit.cmp", 6):
        "Three-way compare on n-bit vectors: jumps to `lt` if `a[:n]<b[:n]`, "
        "`eq` if equal, `gt` if `a[:n]>b[:n]`.",
    ("bit._.cmp_next_eq", 4):
        "1 step of multi-bit `bit.cmp`.",

    # ---------- hex.cmp family (mirrors the bit.cmp overrides above) ----------
    ("hex.cmp", 5):
        "Three-way compare on hex nibbles: jumps to `lt` if `a<b`, `eq` if "
        "`a==b`, `gt` if `a>b`. `a`, `b` are hexes; `lt`, `eq`, `gt` are addresses.",
    ("hex.cmp", 6):
        "Three-way compare on n-nibble hex vectors: jumps to `lt` if "
        "`a[:n]<b[:n]`, `eq` if equal, `gt` if `a[:n]>b[:n]`.",
    ("hex.cmp.cmp_eq_next", 4):
        "1 step of multi-nibble `hex.cmp`.",

    # ---------- empty-source macros (zero doc lines above the `def`) ----------
    ("bit._.print_str_one_char", 2):
        "Print one byte from a null-terminated string; jumps to `end` when "
        "it hits `\\0`. Inner loop of `bit.print_str`.",
    ("bit.print_hex_uint.print_digit", 2):
        "Print one hex digit, but only after the first non-zero digit has "
        "been seen (suppresses leading zeros). Inner loop of `bit.print_hex_uint`.",
    ("hex.dec.step", 2):
        "One nibble of a propagating decrement: decrement `hex` by 1; on "
        "underflow continue to the next nibble, else jump to `end`.",
    ("hex.inc.step", 2):
        "One nibble of a propagating increment: increment `hex` by 1; on "
        "overflow continue to the next nibble, else jump to `end`.",

    # ---------- other fragment / metadata-leak summaries ----------
    ("hex.if_flags", 4):
        "Jumps to `l1` if bit `hex` of the 16-bit `flags` constant is "
        "set, else `l0`.",
    ("hex.add_mul", 2):
        "`res += x * dst + carry_dst` — one shift-and-add (multiply-"
        "accumulate) step used by `hex.mul`. Reads/writes the global "
        "multiplication carry.",
    ("bit.print_dec_uint.div10_step", 8):
        "One step inside `bit.print_dec_uint`: divides `src` by 10, "
        "stashes the remainder as an ASCII digit, and trips `char_flag` "
        "to make this digit printable.",

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
    # `n_const` (in the complexity expressions for these four) is the
    # minimal `hex.vec` size needed to store `const` — i.e. the number
    # of hex nibbles required to represent its value.
    ("hex.add.add_constant_with_leading_zeros", 4):
        "Internal helper for `hex.add_constant`: strips `const`'s trailing "
        "zero nibbles, then adds the result back into `dst[:n]` at the "
        "matching nibble offset (so the trailing zeros are skipped instead "
        "of materialised as wasted-work additions).\n\n"
        "`n_const` is the minimal `hex.vec` size needed to store `const`.",
    ("hex.add.add_hex_shifted_constant", 4):
        "Wrapper around the 5-arity `add_hex_shifted_constant`: derives "
        "`n_const = (#const + 3) / 4` automatically so the caller doesn't "
        "have to compute the constant's nibble length.\n\n"
        "`n_const` is the minimal `hex.vec` size needed to store `const`.",
    ("hex.sub.sub_constant_with_leading_zeros", 4):
        "Internal helper for `hex.sub_constant`: strips `const`'s trailing "
        "zero nibbles, then subtracts the result from `dst[:n]` at the "
        "matching nibble offset (so the trailing zeros are skipped instead "
        "of materialised as wasted-work subtractions).\n\n"
        "`n_const` is the minimal `hex.vec` size needed to store `const`.",
    ("hex.sub.sub_hex_shifted_constant", 4):
        "Wrapper around the 5-arity `sub_hex_shifted_constant`: derives "
        "`n_const = (#const + 3) / 4` automatically so the caller doesn't "
        "have to compute the constant's nibble length.\n\n"
        "`n_const` is the minimal `hex.vec` size needed to store `const`.",

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

    # ---------- ptrlib ----------
    ("stl.ptr_init", 0):
        "One-time initialisation of the pointer dispatch infrastructure. "
        "Use `stl.startup_and_init_pointers`, which calls this for you.",

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

    # ---------- batch 6: accepted doc rewrites ----------

    # bit.input/2 source doc said "(lsb first)" but the body reads bytes
    # in REVERSE memory order (byte 0 lands at offset 8*(n-1)*dw). The
    # net effect is that dst[:8n] is a single 8n-bit little-endian
    # number — author-provided wording captures that intent.
    ("bit.input", 2):
        "Effectively inputs an `8*n` bits little endian number into "
        "`dst[:8n]`.\n\n"
        "`dst` is an output parameter.",

    # bit.print_str/2 — clarify that the macro prints UP TO n chars,
    # stopping early on the first `\0`. The original wording missed
    # the "first n-chars" part.
    ("bit.print_str", 2):
        "Prints the first n-chars of the string at `x[:8n]`, or until "
        "reaches the first `'\\0'` (the earlier).",

    # stl.startup_and_init_all/1 — source doc says "bits" but the
    # underlying stl.stack_init allocates `hex.vec n` (hex slots, not
    # bits). The 2-arity form already says "hexes"; align /1.
    ("stl.startup_and_init_all", 1):
        "Startup macro — should be the first piece of code in your "
        "program. Initialises everything needed for the standard library.\n\n"
        "`stack_bit_size` is the size of the global-stack (will hold "
        "this number of hexes / return-addresses).",

    # ---------- flipjump 1.4.0 additions ----------

    # hex.scmp/6 — the source doc's `a<b` / `a>b` get HTML-escaped
    # before auto-backticking, which splits the entities into broken
    # code spans (same issue the bit.cmp / hex.cmp overrides fix).
    ("hex.scmp", 6):
        "Three-way SIGNED compare (two's complement) on n-nibble hex "
        "vectors: jumps to `lt` if `a[:n]<b[:n]`, `eq` if equal, `gt` "
        "if `a[:n]>b[:n]`. `a`, `b` are not modified.\n\n"
        "Method: flips the sign bit (MSB) of copies of `a`, `b`, then "
        "unsigned-compares — this maps the signed range monotonically "
        "onto the unsigned range, so it is correct over the whole "
        "range with no subtraction (hence no overflow).",

    # hex/input.fj `_until` primitives — the auto-backticker wraps
    # hyphenated prose ("non-digit") and swallows trailing periods
    # into code spans ("stop_byte[:2].").
    ("hex.input_dec_uint_until", 3):
        "`dst[:n]` = the unsigned decimal number read from input "
        "(mod 16^n).\n\n"
        "Reads ASCII `'0'`..`'9'` and STOPS at the first non-digit "
        "byte, which is stored in `stop_byte[:2]`. The primitive "
        "behind `hex.input_dec_uint`.",
    ("hex.input_dec_int_until", 3):
        "`dst[:n]` = the signed decimal number read from input (two's "
        "complement, mod 16^n).\n\n"
        "Reads an optional leading `'-'`, then ASCII `'0'`..`'9'`, and "
        "STOPS at the first non-digit byte, which gets stored in "
        "`stop_byte[:2]` (note that a leading `'+'` stops with "
        "`dst=0`). The primitive behind `hex.input_dec_int`.",

    # Indexed (nth) pointers — "index-th" / "dw-aligned" get wrongly
    # backticked by the hyphen-token rule, and `*ptr` is left bare.
    # The ptr_index override keeps the source's @Assumes line (it
    # lives in the description, so an override would otherwise drop it).
    ("hex.ptr_index", 3):
        "`dst[:w/4] = ptr + index*2w` — the address of the index-th "
        "dw-aligned op past `*ptr`.\n\n"
        "`dst`, `ptr` are `hex[:w/4]`; `index` is a signed "
        "`hex[:w/4]`. Works for negative `index` too.\n\n"
        "@Assumes: `w` in {16, 32, 64, 128}.",
    ("hex.read_nth_hex", 3):
        "`dst = *(ptr + index*2w)` — read the index-th hex past "
        "`*ptr`.\n\n"
        "`dst` is a hex; `ptr` is a `hex[:w/4]`; `index` is a signed "
        "`hex[:w/4]` (may be negative). `ptr`, `index` are preserved.",
    ("hex.read_nth_byte", 3):
        "`dst[:2] = *(ptr + index*2w)` — read the index-th byte past "
        "`*ptr`.\n\n"
        "`dst` is a `hex[:2]`; `ptr` is a `hex[:w/4]`; `index` is a "
        "signed `hex[:w/4]` (may be negative). `ptr`, `index` are "
        "preserved.",
    ("hex.write_nth_hex", 3):
        "`*(ptr + index*2w) = src` — write `src` into the index-th "
        "hex past `*ptr`.\n\n"
        "`src` is a hex; `ptr` is a `hex[:w/4]`; `index` is a signed "
        "`hex[:w/4]` (may be negative). `ptr`, `index`, `src` are "
        "preserved.",
    ("hex.write_nth_byte", 3):
        "`*(ptr + index*2w)[:2] = src[:2]` — write the index-th byte "
        "past `*ptr`.\n\n"
        "`src` is a `hex[:2]`; `ptr` is a `hex[:w/4]`; `index` is a "
        "signed `hex[:w/4]` (may be negative). `ptr`, `index`, `src` "
        "are preserved.",

    # hex/strings.fj line / byte-buffer helpers — trailing-period
    # swallow ("len[:w/4].") in the auto-backticked descriptions.
    ("hex.input_ptr_line", 2):
        "Reads bytes from input into the pointed buffer, until a "
        "`'\\n'` or a 0-byte (EOF); writes the byte count into "
        "`len[:w/4]`.",
    ("hex.print_ptr_text", 2):
        "Prints `len[:w/4]` bytes from the pointed buffer.",
    ("hex.print_ptr_line", 2):
        "Prints bytes from the pointed buffer, until a `'\\n'` or a "
        "0-byte (EOF); writes the byte count into `len[:w/4]`.\n\n"
        "A terminating `'\\n'` is printed too (a terminating 0-byte "
        "is not); either way `len` excludes it.",
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


# -----------------------------------------------------------------------
# Time / space complexity overrides.
#
# Keyed by (fq_name, arity). Fills the corresponding DocInfo field ONLY
# when it's still None — overrides supplement source, they don't replace
# upstream complexity comments. So if upstream later adds a Complexity:
# line to one of these macros, we'll silently start picking it up
# without needing to delete the override entry first.
#
# Use cases:
#   - Wrappers that delegate to a documented macro (copy from callee).
#   - Memory declarations where time isn't meaningful (use the literal
#     string "0 (data declaration)").
#   - 1-time init macros (use the literal string "O(1)").
#   - Inner helpers whose complexity is implicit in the caller.
# -----------------------------------------------------------------------

_TIME_COMPLEXITY_OVERRIDES: dict[tuple[str, int], str] = {
    # ---------- data declarations (time is N/A by design) ----------
    ("bit.bit", 0): "0 (data declaration)",
    ("bit.bit", 1): "0 (data declaration)",
    ("bit.vec", 1): "0 (data declaration)",
    ("bit.vec", 2): "0 (data declaration)",
    ("bit.str", 1): "0 (data declaration)",
    ("hex.hex", 0): "0 (data declaration)",
    ("hex.hex", 1): "0 (data declaration)",
    ("hex.vec", 1): "0 (data declaration)",
    ("hex.vec", 2): "0 (data declaration)",

    # ---------- one-time init macros (called once at startup) ----------
    ("bit.pointers.ptr_init", 0): "O(1)",
    ("hex.init", 0): "O(1)",
    ("hex.pointers.ptr_init", 0): "O(1)",
    ("hex.pointers.stack_init", 1): "O(1)",
    ("stl.stack_init", 1): "O(1)",

    # ---------- compile-time conditional emitters ----------
    # Upstream `runlib.fj:106` has a banner `// Complexity: 1` above
    # this group, but blank lines separate it from each `def` so the
    # doc-attach rule doesn't carry it through.
    ("stl.comp_if", 3): "1",
    ("stl.comp_if0", 2): "1",
    ("stl.comp_if1", 2): "1",
    ("stl.comp_flip_if", 2): "1",
    ("stl.skip", 0): "1",

    # ---------- misc ----------
    # stl.loop's body is `;$ - dw` — an unconditional self-jump that
    # never terminates. "Halt" is the conventional FJ word for this
    # pattern (programs commonly end with stl.loop), but the literal
    # behaviour is an infinite self-loop.
    ("stl.loop", 0): "∞ (infinite self-loop)",
    ("hex.tables.init_shared", 0): "0",
    ("hex.tables.init_all", 0): "1",

    # Helpers / inner-loop pieces (manually derived).
    # NOTE: `bit.print_hex_uint.print_digit/2` time is the
    # author-verified value 29@+34. The upstream file has a non-
    # standard banner `//Comp: 29@+44` above `ns print_hex_uint`
    # (bit/output.fj:90) which would give a different number — the
    # banner is not picked up by the extractor (typo for `Complexity`
    # and not adjacent to the def), and the 29@+34 value here was
    # provided by the author after re-deriving from the body.
    ("bit._.print_str_one_char", 2): "16@+32",
    ("bit.print_hex_uint.print_digit", 2): "29@+34",
    ("bit.pointers.advance_by_one_and_flip__ptr_wflip", 2): "@+n+1",
    ("hex.pointers.advance_by_one_and_flip__ptr_wflip", 2): "@+n+1",

    # ---------- wrappers that delegate to a documented macro ----------
    # Copy the wrapped macro's complexity (the wrapper adds only labels,
    # no extra FJ ops).
    ("hex.if0", 2): "@-1",          # wraps hex.if/3
    ("hex.if1", 2): "@-1",          # wraps hex.if/3
    ("hex.if0", 3): "n(@-1)",       # wraps hex.if/4
    ("hex.if1", 3): "n(@-1)",       # wraps hex.if/4
    ("hex.dec.step", 2): "@",       # wraps hex.dec1/3
    ("hex.inc.step", 2): "@",       # wraps hex.inc1/3
    ("hex.cmp.cmp_eq_next", 4): "3@+8",  # wraps hex.cmp/5
    ("hex.add.add_constant_with_leading_zeros", 4): "n_const(4@+12) + 5@+2",
    ("hex.add.add_hex_shifted_constant", 4): "n_const(4@+12) + 5@+2",
    ("hex.sub.sub_constant_with_leading_zeros", 4): "n_const(4@+12) + 5@+2",
    ("hex.sub.sub_hex_shifted_constant", 4): "n_const(4@+12) + 5@+2",
}


_SPACE_COMPLEXITY_OVERRIDES: dict[tuple[str, int], str] = {
    # ---------- data declarations ----------
    # /1 and /2 entries also listed defensively: their source files have
    # `// Size Complexity:` comments that the extractor currently picks
    # up, so these overrides are no-ops today (the "fill only when None"
    # rule skips them). They keep us covered if the upstream doc comment
    # ever drops or moves.
    ("bit.bit", 0): "1",
    ("bit.bit", 1): "1",
    ("bit.vec", 1): "n",
    ("bit.vec", 2): "n",
    ("bit.str", 1): "(#str+15)&(~7)  // which is (strlen(str)+1)*8",
    ("hex.hex", 0): "1",
    ("hex.hex", 1): "1",
    ("hex.vec", 1): "n",
    ("hex.vec", 2): "n",

    # ---------- compile-time emitters ----------
    ("stl.comp_if", 3): "1",
    ("stl.comp_if0", 2): "1",
    ("stl.comp_if1", 2): "1",
    ("stl.comp_flip_if", 2): "1",
    ("stl.skip", 0): "1",

    # ---------- misc ----------
    ("stl.loop", 0): "1",
    ("hex.tables.init_shared", 0): "2",
    ("hex.tables.init_all", 0): "6464+@",

    # Helpers / inner-loop pieces.
    ("bit._.print_str_one_char", 2): "16@+32",
    ("bit.print_hex_uint.print_digit", 2): "35@+57",
    ("bit.pointers.advance_by_one_and_flip__ptr_wflip", 2): "@+n+1",
    ("hex.pointers.advance_by_one_and_flip__ptr_wflip", 2): "@+n+1",

    # ---------- wrappers ----------
    ("hex.if0", 2): "@+15",
    ("hex.if1", 2): "@+15",
    ("hex.if0", 3): "n(@+15)",
    ("hex.if1", 3): "n(@+15)",
    ("hex.dec.step", 2): "1.5@+13",
    ("hex.inc.step", 2): "1.5@+13",
    ("hex.cmp.cmp_eq_next", 4): "3@+30",
    ("hex.add.add_constant_with_leading_zeros", 4):
        "n_const(2.5@+39) + (dst_n - hex_shift)(1.5@+13) + 4@+29",
    ("hex.add.add_hex_shifted_constant", 4):
        "n_const(2.5@+39) + (dst_n - hex_shift)(1.5@+13) + 4@+29",
    ("hex.sub.sub_constant_with_leading_zeros", 4):
        "n_const(2.5@+39) + (dst_n - hex_shift)(1.5@+13) + 4@+29",
    ("hex.sub.sub_hex_shifted_constant", 4):
        "n_const(2.5@+39) + (dst_n - hex_shift)(1.5@+13) + 4@+29",
}


def _apply_complexity_overrides(
    macro_fq: str, macro_arity: int, info: "DocInfo",
) -> None:
    """Fill `info.time_complexity` and `info.space_complexity` from the
    override dicts, but ONLY when the field is still None. This means
    overrides supplement source rather than replacing it — if upstream
    later adds a Complexity: line, the override silently steps aside.

    Note: override values BYPASS `_looks_like_complexity_value` — they
    go straight to the field. So override strings can include narrative
    annotations like `"0 (data declaration)"` or `"∞ (infinite self-
    loop)"` that the validator would reject as prose.
    """
    key = (macro_fq, macro_arity)
    if info.time_complexity is None:
        t = _TIME_COMPLEXITY_OVERRIDES.get(key)
        if t is not None:
            info.time_complexity = t
    if info.space_complexity is None:
        s = _SPACE_COMPLEXITY_OVERRIDES.get(key)
        if s is not None:
            info.space_complexity = s


# -----------------------------------------------------------------------
# @Assumes overrides.
#
# When a macro silently depends on a precondition (e.g. `times <= n` for
# a shift macro, or `stack non-empty` for stl.return), upstream STL
# already uses the `// @Assumes: ...` convention (see e.g.
# hex.tables.clean_table_entry__table/3). For the macros listed here
# the assumption is real but not yet stated in source; the override
# appends an `@Assumes: ...` line to the rendered description.
#
# Keyed by (fq_name, arity). The values are quoted verbatim after the
# `@Assumes: ` prefix. These mirror the lines that will be added to
# upstream source in the next flipjump PR.
# -----------------------------------------------------------------------

_ASSUMES_OVERRIDES: dict[tuple[str, int], str] = {
    # ---------- shift bounds ----------
    ("bit.shl", 3): "times <= n",
    ("bit.shr", 3): "times <= n",
    ("bit.shra", 3): "times <= n",
    ("hex.shl_hex", 3): "times <= n",
    ("hex.shr_hex", 3): "times <= n",

    # ---------- stack / pointer lifecycle ----------
    ("stl.return", 0): "matched by a prior `stl.call` (stack non-empty)",
    ("stl.call", 1): "stack has room (caller-side responsibility)",
    ("stl.call", 2): "stack has room (caller-side responsibility)",
    ("stl.fret", 1):
        "`ret_reg` contains a valid return address from a prior `stl.fcall`",

    # ---------- aliasing ----------
    ("hex.add_count_bits", 3): "`dst` and `src` do not alias",

    # ---------- pointer / shift constraints ----------
    # /2 form takes `hex, bit_shift`; the 1-arity form has no bit_shift.
    ("hex.pointers.xor_hex_to_flip_ptr", 2): "`bit_shift` is divisible by 4",
}


def _apply_assumes_override(
    macro_fq: str, macro_arity: int, info: "DocInfo",
) -> None:
    """Append an `@Assumes: ...` line to `info.description` if one is
    registered for this macro. Mirrors what upstream `// @Assumes: ...`
    lines would produce once they land in source.
    """
    text = _ASSUMES_OVERRIDES.get((macro_fq, macro_arity))
    if text is None:
        return
    line = f"@Assumes: {text}"
    info.description = (
        f"{info.description}\n\n{line}" if info.description else line
    )


# Upstream STL convention: `// like: *ptr;` / `// Like: sp++` introduces
# a pseudocode intent line. "Effectively:" reads as English in our docs.
#
# Anchored at start-of-line (multiline mode) with optional leading
# whitespace + optional backtick, so we only catch the prefix form. Mid-
# sentence colon usages like `// used to initialize a string, like:
# bit.str "Hello, World!"` in bit/casting.fj are NOT rewritten.
# The optional `?` backtick lets us match the post-`_extract_fields`
# wrapped form `  `Like:  sp++`` as well as the raw source form.
_LIKE_PREFIX_RE = re.compile(r"(?m)^([ \t]*`?)[Ll]ike:")


def _normalize_like_prefix(text: str) -> str:
    """Replace upstream `Like:` / `like:` intent-prefix with `Effectively:`.
    Applied to every macro description (auto-extracted AND override).
    Only matches at line-start (after optional whitespace and one
    optional backtick) — see `_LIKE_PREFIX_RE` for why."""
    return _LIKE_PREFIX_RE.sub(r"\1Effectively:", text)


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

# Validator: reject obvious prose; accept everything else.
#
# Earlier this required at least one of `0-9@()+-*^~/#` to be present,
# but that wrongly rejected legitimate single-letter values like `n`
# and `w` — e.g. `bit.not/2`'s `// Complexity: n` was silently dropped.
# The 3+-letter prose-pair regex catches the false-positive cases we
# actually care about, like `Complexity is the runtime cost`.
_COMPLEXITY_PROSE_RE = re.compile(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b")


def _looks_like_complexity_value(value: str) -> bool:
    return not _COMPLEXITY_PROSE_RE.search(value)


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


def _esc(text: str) -> str:
    """Escape HTML-significant characters in upstream-sourced text.

    MyST-Parser passes raw HTML through to the rendered output by default.
    Escaping < > & at the extraction boundary prevents doc comments in
    untrusted upstream .fj source files from injecting live HTML tags
    (stored XSS) into the generated documentation pages.

    This is safe to apply to all extracted text: the pipeline's own
    markup uses only backticks and `[](…)` Markdown syntax — never raw
    angle brackets — so escaping them in source content doesn't break
    any existing rendering.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
        _apply_complexity_overrides(macro.fq_name, macro.arity, info)
        info.description = _normalize_like_prefix(info.description)
        _apply_assumes_override(macro.fq_name, macro.arity, info)
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
            info.requires.append(_esc(m.group(1)))
            continue
        m = _OUTPUT_PARAM_RE.match(body)
        if m:
            info.output_params[m.group(1)] = _esc(m.group(2))
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
        # Escape HTML-significant characters BEFORE any Markdown transformation.
        # MyST passes raw HTML through; upstream source is untrusted.
        content = _esc(stripped_left.rstrip())
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

# Glossary

FlipJump-specific terms, in alphabetical order. Each entry links to the deeper treatment elsewhere in the docs.

```{glossary}
:sorted:

@ (at-unit)
   The unit of complexity in STL annotations. `@` = log₂(total number of FlipJump ops in the assembled program), typically 15–25. See [the complexity glossary](../language/complexity.md) for why this is the natural unit (short version: `wflip`'s cost is proportional to the number of set bits in its address, and address widths are log₂(N) bits).

bit address
   Every FlipJump address is a BIT address, not a byte address. `dw` worth of bits is one instruction; `8` worth is one byte; `1` worth is a single flippable bit.

bit variable
   An STL convention for a single-bit storage cell, declared with `bit.bit` (one bit) or `bit.vec n` (n-bit vector). Reads happen via self-modifying jumps; writes happen via `wflip`. See [bit/memory.fj](../stl/bit/memory.md).

dbit
   `w + #w` — the bit offset from a packed variable's start to the bit that holds its value. Used pervasively in STL pointer arithmetic. See [Types](../language/types.md).

dw
   `2 * w` — the size of one FlipJump instruction in bits. Two consecutive bit-addresses differing by `dw` are two consecutive instructions. See [Types](../language/types.md).

flip
   To toggle a single bit. The first half of every FlipJump instruction.

flip-jump (or `fj` op)
   One execution of the `a;b` instruction: flip bit `a`, jump to `b`. The atomic unit of execution.

halt
   The runtime stops when it executes an instruction whose jump-address is its own location AND whose flip-address sits OUTSIDE the instruction body (i.e. flipping a bit that isn't in this instruction's two-word region). The canonical halt is `stl.loop`.

hex variable
   An STL convention for a 4-bit nibble cell, declared with `hex.hex` or `hex.vec n`. Arithmetic on hex variables uses precomputed lookup tables (initialised by `hex.init`) and is generally faster than bit-level arithmetic for multi-digit values. See [hex/memory.fj](../stl/hex/memory.md).

IO (I/O opcode)
   The bit-address at `2*w` where input/output happens. After `stl.startup`, this address is also exposed as the label `IO`. Flipping bits at `IO` emits output; the runtime auto-populates input bits at `3*w + #w`. See [I/O](../language/io.md).

macro
   A reusable code template, defined with `def NAME ARGS { ... }`. Macros expand at assembly time. See [Macros](../language/macros.md).

namespace
   A grouping construct, defined with `ns NAME { ... }`. Nests freely; same-name blocks merge. See [Namespaces](../language/namespaces.md).

OISC
   One-Instruction-Set Computer. FlipJump is one — it has exactly one instruction. Other OISCs include Subleq, BitBitJump, TOGA.

pointer
   A nibble-vector holding an absolute bit address. Dereferencing a pointer requires the `hex.pointers.*` macros, which generate the self-modifying jump-target sequences to follow the pointer at run time. See [hex/pointers/index](../stl/hex/pointers/index.md).

pseudocode (in macro docs)
   The convention of writing an indented `//   expr` line as a one-line summary of what a macro does. E.g. `//   dst += src` for `bit.add`. The docs site renders these in inline code style.

rep
   Compile-time loop: `rep(N, var) body` expands `body` N times with `var` bound to 0..N-1. N must be a constant.

self-modifying jump
   The core trick of FlipJump variable implementation: by `wflip`ping bits in an instruction's jump-address, an earlier flip can change where a later jump goes. This is how the STL implements `if`, `mov`, and every other read/write operation.

stack
   A region of memory used by `stl.fcall`/`stl.fret`/`hex.pointers.push_*`/`hex.pointers.pop_*` to save return addresses and local values. Initialised by `stl.stack_init` (called automatically inside `stl.startup_and_init_all`).

STL
   "Standard Template Library" — the suite of macros under `flipjump/stl/` that this site auto-documents. Provides variables, arithmetic, I/O, control flow, pointers, and a stack on top of FlipJump's single instruction.

w (word width)
   The machine word width in bits, set at assembly time via `fj --width N` (default 64). NOT declared in source. Every size constant derives from `w`. See [Types](../language/types.md).

wflip
   The assembler directive `wflip DST, VAL [, JMP]` that XORs VAL into the word at DST. Used as the building block for almost every "write" operation in the STL. See [Directives](../language/directives.md).

word
   `w` bits. The size of a single FlipJump address (and therefore the size of either half of an `a;b` instruction).
```

## See also

- [Cheat sheet](cheat-sheet.md) — one-page quick reference.
- [Language Reference](../language/index.md) — full prose.
- [Complexity glossary](../language/complexity.md) — `@`, `w`, `n`, etc. in complexity annotations.

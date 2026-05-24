# How the STL works

The FlipJump standard library is a 300-macro stack of self-modifying-code patterns. This page explains the meta-pattern — once you see it, every individual macro becomes obvious.

## The whole language, again

```fj
a;b
```

flips the bit at `a`, then jumps to `b`. Notice what's NOT in the language:

- No load / store instruction.
- No compare instruction.
- No add / subtract / multiply.
- No call / return.

Everything you'd expect from a CPU is missing. Yet the STL implements all of it. How?

## The core trick: jump-address as variable

FlipJump's read primitive is **read by jumping**. Suppose you want to read a one-bit variable `x`. You don't load `x` into a register (there is no register and no load). Instead, you write your code so that the JUMP-address of an upcoming instruction depends on `x`. After execution flows through that instruction, control ends up in different places depending on what `x` was.

In other words: **the program counter is the only register**, and **rewriting jump-addresses is the only kind of state change**.

## The STL's standard layout for a one-bit variable

Inside `stl/bit/memory.fj`, the macro `bit.bit` declares:

```fj
def bit value { ... }     // a one-bit storage cell
```

What gets generated is a tiny instruction whose jump-address is pre-loaded with the variable's value (or its complement). When the code "reads" the variable, it does so by JUMPING through that instruction — the destination depends on the stored value.

To **write** to the variable, the STL uses `wflip` to XOR the right bits in the jump-address. After the write, future reads (jumps through the same instruction) land in the new place.

That's it. That's the whole library, recursively applied.

## Why there's a `bit` namespace AND a `hex` namespace

Bit-level variables are conceptually clean but expensive in instructions per useful value. The `hex` namespace packs four bits into one variable and uses precomputed lookup tables for arithmetic.

Concretely:

| | bit | hex |
|---|---|---|
| Storage per nibble | 4 separate bit-cells | 1 nibble-cell |
| Add two nibbles | ~16 ops (per-bit ripple) | ~4 ops + lookup |
| Cost of `mul` | quadratic in bits | quadratic in nibbles (≈ 16× faster) |

For most non-trivial programs you'll want `hex.*`. The `bit.*` set is there when you need fine-grained control or when nibble-alignment is awkward.

## Why pointers need init

A pointer is a variable holding a bit-address. To "dereference" it, the STL needs to flip the right bits in some other instruction's jump-address — but at run time, it doesn't know which bits to flip until the pointer's value is determined.

The trick: `hex.pointers.ptr_init` (and the bundled `stl.startup_and_init_all`) precomputes a giant lookup table. At dereference time, the macro indexes into the table using the pointer's nibbles and emits the corresponding flips. This is why pointer macros are an order of magnitude more expensive than direct-address ones.

## Why `wflip` complexity is `@` (log of program size)

`wflip DST, VAL` emits a sequence of single-bit flips — one per set bit of `DST`. Addresses are `log₂(program_size)` bits wide, so an average `wflip` costs `log₂(N)` flips. Since `wflip` is underneath virtually every STL write operation, the per-op cost of the STL is naturally measured in `log₂(N)` units. The complexity glossary uses `@` as the shorthand for this unit.

For a typical FlipJump program with ~1M ops, `@` ≈ 20. A macro annotated `4@+12` runs ~92 ops per call.

## Why startup is mandatory

`stl.startup` initialises the I/O opcode at address `2*w`. Without it, your program can't emit output (because the runtime watches `2*w` for output events).

The heavier variants add:
- `stl.startup_and_init_pointers` — pointer dispatch tables (~5KB → 100KB depending on word width)
- `stl.startup_and_init_all` — pointer tables + hex truth tables + a stack

Each level of initialisation is ~thousand to tens-of-thousands of ops. Worth it for what you get, but the lightest startup that suffices is always the right choice.

## How to read a typical STL macro

Take `bit.add` from `stl/bit/math.fj`. The macro body is short — ten lines or so — but the magic is in the chain of `wflip`s. Walk through with this mental model:

1. The macro declares some local labels.
2. It emits some `wflip` calls to pre-load jump-addresses based on the inputs.
3. It then `;`s through those instructions, with the jumps landing in different places depending on the inputs.
4. The final `;` lands at the macro's exit label.

Once you see this pattern in three or four macros, the whole library becomes legible. The complexity table at the top of each macro tells you how many `wflip`s and jumps to expect.

## See also

- [The FlipJump instruction](../language/instruction.md) — the one operation, explained.
- [Macros](../language/macros.md) — `def`, `ns`, `rep`, signature clauses.
- [Directives](../language/directives.md) — `wflip`, `pad`, `reserve`, `segment`.
- [Complexity notation](../language/complexity.md) — what `@`, `w`, `dw`, `n` mean.
- [Standard Library](../stl/index.md) — every macro, auto-documented.

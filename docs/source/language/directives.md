# Directives

Four directives operate on the program's memory layout. They are not macros — they're built into the assembler.

## `pad N`

Insert padding so the current address is a multiple of `N` words.

```fj
pad 8                  // align to 8-word boundary
```

Used heavily in the hex module's macros that rely on a 256-byte-aligned lookup table base address.

## `reserve N`

Reserve `N` bits at the current address without emitting any instructions. Effectively `pad`s past the requested range — used to allocate uninitialised storage for variables that the macro will later flip into shape.

```fj
reserve 8 * dw         // allocate 8 words of zeroed-out storage
```

## `segment ADDR`

Set the assembler's "current bit-address" to `ADDR`. Subsequent code is emitted starting at the new address, with the old position abandoned. Used to place code in a specific memory region — e.g. the STL puts its lookup tables at a fixed address to keep relative offsets short.

```fj
segment 0x100          // jump the assembler cursor to bit-address 0x100
```

## `wflip DST, VAL [, JMP]`

The fundamental "word-flip" operation: flip the `w`-bit word at `DST` so it XORs with `VAL`. Optionally, with the third argument, also generate a flip-jump that goes to `JMP` after the flip.

```fj
wflip 0x80, 0x42       // XOR the word at 0x80 with 0x42
wflip 0x80, 0x42, end  // and then jump to label `end`
```

`wflip` is the building block that lets a macro modify another instruction's jump-address at assembly time. It generates a sequence of single-bit `a;b` instructions that, when executed, XOR `VAL` into the word at `DST`. The `stl.wflip_macro` macro family wraps this directive — see [`stl.wflip_macro`](../stl/_generated/macro--stl.wflip_macro--2.md).

## When to reach for these

You almost never need `pad`, `reserve`, `segment`, or bare `wflip` in user code — the STL macros wrap every common pattern. They appear in user code only when:

- You're building a custom layout that the STL doesn't anticipate.
- You're optimising a hot path and need explicit alignment.
- You're writing a new STL macro.

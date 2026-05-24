# Swap two variables

## Problem

Exchange the contents of two variables without using extra storage. The classic "triple-XOR" trick written in FlipJump.

## Code

```fj
stl.startup_and_init_all

bit.print_dec_uint 8, a
stl.output ' '
bit.print_dec_uint 8, b
stl.output " ->\n"

bit.swap 8, a, b

bit.print_dec_uint 8, a
stl.output ' '
bit.print_dec_uint 8, b
stl.output '\n'

stl.loop

a: bit.vec 8, 7
b: bit.vec 8, 42
```

Output:
```
7 42 ->
42 7
```

## Walkthrough

- `bit.swap n, a, b` — exchanges `a[:n]` and `b[:n]` in place via three XORs per bit. No temp variable needed; the STL implementation is the standard `a ^= b; b ^= a; a ^= b` pattern.

## Variations

**Hex** — use `hex.swap` instead:

```fj
hex.swap 2, h1, h2
h1: hex.vec 2, 0xAB
h2: hex.vec 2, 0xCD
```

**Single-bit swap** without specifying length:

```fj
bit.swap a, b
a: bit.bit 1
b: bit.bit 0
```

## See also

- [`bit.swap`](../stl/bit/memory/swap--2.md), [`bit.swap`](../stl/bit/memory/swap--3.md) (the `n`-arity overload)
- [`hex.swap`](../stl/hex/memory/swap--2.md)

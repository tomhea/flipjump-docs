# Print a number in decimal

## Problem

Convert a binary value to its decimal ASCII representation and print it.

## Code

```fj
stl.startup
bit.print_dec_uint 32, n
stl.output '\n'
stl.loop

n: bit.vec 32, 12345
```

## Walkthrough

- `n: bit.vec 32, 12345` — allocate a 32-bit variable initialised to `12345`. The initial value is encoded at assembly time as bit-flips into the variable's region.
- `bit.print_dec_uint 32, n` — divides `n` by 10 repeatedly, printing each remainder as the corresponding `'0'`–`'9'` ASCII byte. The macro runs in `n²·(2@+4)` time; the comment in the source notes the 28/93 ratio used to size the print buffer.

## Variations

**Signed integers** (handles negative numbers + leading `-`):

```fj
stl.startup
bit.print_dec_int 32, signed_val
stl.output '\n'
stl.loop

signed_val: bit.vec 32, 0 - 12345     // -12345
```

**Hex** instead of decimal — much cheaper, no division loop:

```fj
stl.startup
bit.print_hex_int 32, n, 1   // last arg = "uppercase digits"
stl.output '\n'
stl.loop

n: bit.vec 32, 0xCAFE
```

**Decimal from a `hex.vec` value** — the same decimal output for the (faster-arithmetic) hex family. Needs `hex.init`, so use `stl.startup_and_init_all`; here `n` counts nibbles, so 8 nibbles = 32 bits:

```fj
stl.startup_and_init_all
hex.print_dec_uint 8, n
stl.output '\n'
stl.loop

n: hex.vec 8, 12345
```

`hex.print_dec_int` is the signed form.

## See also

- [`bit.print_dec_uint`](../stl/bit/output/print_dec_uint--2.md)
- [`bit.print_dec_int`](../stl/bit/output/print_dec_int--2.md)
- [`bit.print_hex_int`](../stl/bit/output/print_hex_int--3.md)
- [`hex.print_dec_uint`](../stl/hex/output/print_dec_uint--2.md), [`hex.print_dec_int`](../stl/hex/output/print_dec_int--2.md)
- The [Complexity glossary](../language/complexity.md) — to understand `n²·(2@+4)`.

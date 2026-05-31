# Read, transform, print

## Problem

Read a hex digit from stdin, double it, print the result. A minimal "compute and print" program.

## Code

```fj
stl.startup_and_init_all

hex.input_as_hex input_buf, hex_err

// double
hex.add input_buf, input_buf

// print and exit
hex.print 1, input_buf
stl.output '\n'
stl.loop

hex_err:
    stl.output "not a hex digit\n"
    stl.loop

input_buf: hex.hex
```

## Walkthrough

- `stl.startup_and_init_all` — needed because we use the `hex.*` family, which depends on lookup tables initialised by `hex.init`.
- `hex.input_as_hex dst, err_label` — read one ASCII character from stdin, parse it as a hex digit (`0`-`9`, `a`-`f`, `A`-`F`), store the 4-bit value in `dst`. Branches to `err_label` on bad input.
- `hex.add input_buf, input_buf` — adds `input_buf` to itself, in place. Doubles it.
- `hex.print 1, input_buf` — print as ASCII hex (one nibble = one digit).

## Variations

**Wider value** (use a 4-nibble buffer):

```fj
input_buf: hex.vec 4      // 4 nibbles instead of 1
hex.print 4, input_buf
```

**Decimal input** instead of a single hex digit — read a whole decimal number until newline/EOF:

```fj
hex.input_dec_uint 4, value, hex_err     // value: hex.vec 4
```

`hex.input_dec_uint n, dst, error` parses ASCII `'0'`–`'9'` into the `n`-nibble `dst` and jumps to `error` on any non-digit byte; `hex.input_dec_int` additionally accepts a leading `-`.

## See also

- [`hex.input_as_hex`](../stl/hex/input/input_as_hex--2.md)
- [`hex.input_dec_uint`](../stl/hex/input/input_dec_uint--3.md), [`hex.input_dec_int`](../stl/hex/input/input_dec_int--3.md)
- [`hex.add`](../stl/hex/math/add--2.md), [`hex.print`](../stl/hex/output/print--1.md)

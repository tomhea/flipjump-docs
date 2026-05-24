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
hex.vec input_buf, 4
hex.print 4, input_buf
```

**Decimal input** instead of hex:

```fj
hex.input_as_dec input_buf, hex_err
```

## See also

- [`hex.input_as_hex`](../stl/hex/input/input_as_hex--2.md)
- [`hex.add`](../stl/hex/math/add--2.md), [`hex.print`](../stl/hex/output/print--1.md)

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
hex.input_dec_uint 4, value, hex_err     // read into a 4-nibble value
// ...
value: hex.vec 4                          // declared below stl.loop
```

`hex.input_dec_uint n, dst, error` reads ASCII `'0'`–`'9'` into the `n`-nibble `dst`, stopping at `'\n'` or `'\0'` (EOF); it jumps to `error` only on a byte that is neither a digit nor a terminator. `hex.input_dec_int` additionally accepts a leading `-`. Unlike `hex.print_dec_uint`, these readers use the hex lookup tables, so the program must run `stl.startup_and_init_all` (as the main example above does), not just `stl.startup`.

**Several numbers on one line** — since flipjump 1.4.0 the readers above are thin wrappers around `hex.input_dec_uint_until` / `hex.input_dec_int_until`, which stop at the *first non-digit byte* and hand it back to you instead of treating it as an error:

```fj
hex.input_dec_uint_until 4, a, stop_byte  // reads "12 34" up to the space
hex.input_dec_uint_until 4, b, stop_byte  // reads the second number
// ...
stop_byte: hex.vec 2                      // declared below stl.loop
```

`stop_byte[:2]` receives the byte that ended the number (the space, comma, `'\n'`, …), so you decide what separators mean — ideal for parsing space-separated input.

## See also

- [`hex.input_as_hex`](../stl/hex/input/input_as_hex--2.md)
- [`hex.input_dec_uint`](../stl/hex/input/input_dec_uint--3.md), [`hex.input_dec_int`](../stl/hex/input/input_dec_int--3.md)
- [`hex.input_dec_uint_until`](../stl/hex/input/input_dec_uint_until--3.md), [`hex.input_dec_int_until`](../stl/hex/input/input_dec_int_until--3.md)
- [`hex.add`](../stl/hex/math/add--2.md), [`hex.print`](../stl/hex/output/print--1.md)

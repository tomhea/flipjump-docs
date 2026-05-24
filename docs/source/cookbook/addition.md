# Add two numbers

## Problem

Read two decimal numbers from stdin, print their sum.

## Code

```fj
stl.startup_and_init_all

bit.print_str 9, prompt_a
bit.input_dec a, err
bit.print_str 9, prompt_b
bit.input_dec b, err

bit.add 32, a, b

bit.print_str 7, eq_str
bit.print_dec_uint 32, a
stl.output '\n'
stl.loop

err:
    stl.output "bad input\n"
    stl.loop

prompt_a: bit.str "first:  "
prompt_b: bit.str "second: "
eq_str:   bit.str "sum = "
a: bit.vec 32
b: bit.vec 32
```

## Walkthrough

- `bit.input_dec dst, err` — reads decimal digits from stdin until a non-digit is hit (typically newline); parses to a binary integer.
- `bit.add n, dst, src` — adds `src[:n]` into `dst[:n]` in place. Result lives in `dst`. The macro propagates the carry naturally.
- `bit.print_dec_uint 32, a` — print `a` (now holding `a+b`).

## Variations

**Hex** for less-expensive arithmetic:

```fj
hex.add 8, dst, src
```

**Subtraction**:

```fj
bit.sub 32, a, b      // a -= b
```

**Multiplication**:

```fj
bit.mul 16, dst, x       // dst *= x (both 16-bit)
```

## See also

- [`bit.add`](../stl/bit/math/add--3.md), [`bit.sub`](../stl/bit/math/sub--3.md), [`bit.mul`](../stl/bit/mul/mul--3.md)
- [`hex.add`](../stl/hex/math/add--2.md), [`hex.add`](../stl/hex/math/add--3.md) (vector form)
- The [decimal print](print-decimal.md) and [conditional branch](conditional-branch.md) recipes.

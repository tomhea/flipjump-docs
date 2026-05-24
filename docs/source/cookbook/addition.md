# Add two numbers

## Problem

Add two values stored in data labels and print the sum. (Reading decimal numbers from stdin is more involved — there is no `bit.input_dec` in the STL; you'd hand-roll one using `bit.input` + per-digit parsing. This recipe sticks to compile-time values for clarity.)

## Code

```fj
stl.startup_and_init_all

bit.print_str 7, label_a
bit.print_dec_uint 32, a
stl.output '\n'

bit.print_str 7, label_b
bit.print_dec_uint 32, b
stl.output '\n'

bit.add 32, a, b      // a += b

bit.print_str 7, label_sum
bit.print_dec_uint 32, a
stl.output '\n'
stl.loop

label_a:   bit.str "a   = "
label_b:   bit.str "b   = "
label_sum: bit.str "a+b = "
a: bit.vec 32, 123
b: bit.vec 32, 456
```

Output:
```
a   = 123
b   = 456
a+b = 579
```

## Walkthrough

- `bit.vec 32, val` allocates a 32-bit variable initialised to `val`. The initial value is baked into the macro expansion at assembly time.
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

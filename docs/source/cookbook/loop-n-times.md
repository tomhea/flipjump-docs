# Loop N times

## Problem

Run a block of code N times where N is known at assembly time (a compile-time constant).

## Code

```fj
stl.startup
rep(5, i) stl.output_char 'A' + i
stl.output '\n'
stl.loop
```

Output: `ABCDE\n`

## Walkthrough

- `rep(N, var) body` is FlipJump's compile-time loop. It expands its body N times with `var` bound to `0, 1, 2, …, N-1`. `N` must be a constant expression — there is no runtime `for` loop at the language level (you build one yourself using conditional branches).
- `'A' + i` is an assembly-time expression: at expansion #0 it's `'A'`, at #1 it's `'B'`, etc.

## Variations

**Runtime loop** (N known only at runtime): use a counter variable + conditional branch.

```fj
stl.startup_and_init_all

bit.bit done_flag
counter_loop:
    bit.print_dec_uint 8, n
    stl.output '\n'
    bit.dec 8, n
    bit.if 8, n, end, counter_loop
end:
    stl.loop

n: bit.vec 8, 5
```

**Loop with index in body** — `rep` supports complex expressions referencing `i`:

```fj
rep(16, i) bit.zero 8, table + i*8*dw
```

## See also

- [Macros — rep](../language/macros.md)
- [`bit.dec`](../stl/bit/math/dec--2.md), [`bit.if`](../stl/bit/cond_jumps/if--4.md)

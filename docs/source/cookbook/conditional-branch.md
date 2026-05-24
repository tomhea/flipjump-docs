# Conditional branches

## Problem

Run different code paths based on a value.

## Code

```fj
stl.startup_and_init_all

bit.if 8, x, x_is_zero, x_is_nonzero

x_is_zero:
    stl.output "x is zero\n"
    ;done

x_is_nonzero:
    stl.output "x is nonzero\n"
    ;done

done:
    stl.loop

x: bit.vec 8, 42
```

## Walkthrough

- `bit.if 8, x, l0, l1` — check the 8-bit value `x`: jump to `l0` if all bits are `0`, otherwise jump to `l1`. Three-way variants exist (`bit.cmp lt, eq, gt`); a one-armed variant `bit.if0` jumps only when zero and falls through otherwise.
- The labels `x_is_zero`, `x_is_nonzero`, `done` are local to the file; the `;done` bare-jump (no flip) is the FlipJump idiom for "fall through".

## Variations

**Three-way comparison** (`<`, `==`, `>`):

```fj
bit.cmp 8, a, b, lt, eq, gt
lt: stl.output "a<b\n";  ;done
eq: stl.output "a==b\n"; ;done
gt: stl.output "a>b\n";  ;done
done: stl.loop
```

**Hex-level branches** when you're already using `hex.*`:

```fj
hex.if 8, x, x_is_zero, x_is_nonzero
```

## See also

- [`bit.if`](../stl/bit/cond_jumps/if--4.md), [`bit.if0`](../stl/bit/cond_jumps/if0--3.md), [`bit.if1`](../stl/bit/cond_jumps/if1--3.md), [`bit.cmp`](../stl/bit/cond_jumps/cmp--6.md)
- [`hex.if`](../stl/hex/cond_jumps/if--4.md), [`hex.cmp`](../stl/hex/cond_jumps/cmp--6.md)

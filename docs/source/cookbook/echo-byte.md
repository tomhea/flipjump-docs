# Echo a byte

## Problem

Read one byte from stdin, write it back to stdout. The "cat -n 1" of FlipJump.

## Code

```fj
stl.startup
bit.input b
bit.output b
stl.loop

b: bit.vec 8
```

## Walkthrough

- `stl.startup` — minimal startup; nothing fancy needed.
- `b: bit.vec 8` — allocate an 8-bit variable in data memory **after** `stl.loop`. Variables live outside the executable code path because they're read via self-modifying jumps; if they were inline they'd execute as instructions.
- `bit.input b` — read 8 bits from stdin in LSB-first order, populating `b`.
- `bit.output b` — write the byte back out the same way.

## Variations

**Echo until EOF (loop forever, exit on null input)**:

```fj
stl.startup_and_init_all      // need stack for `fcall`/`fret`
loop_top:
    bit.input b
    bit.if0 8, b, end          // jump to `end` if all 8 bits are 0
    bit.output b
    ;loop_top
end:
    stl.loop

b: bit.vec 8
```

## See also

- [hello-world](hello-world.md) — output-only.
- [`bit.input`](../stl/bit/input/input--1.md), [`bit.output`](../stl/bit/output/output--1.md), [`bit.if0`](../stl/bit/cond_jumps/if0--3.md)

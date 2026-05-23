# The FlipJump Instruction

The whole language is one operation:

```fj
a;b
```

Semantically equivalent to:

```text
*a = NOT *a      // flip the bit at address a
goto b           // then jump to address b
```

`a` and `b` are bit addresses — full assembly-time expressions, not just literals. Both may use labels, constants, and arithmetic.

## Shorthand forms

Two abbreviations are common:

```fj
a;        // flip bit a, fall through to the next instruction
;b        // jump to b without flipping anything (formally: flip bit 0, which is harmless if 0 is never observed)
;         // self-loop placeholder — both halves are 0
```

The third form (a bare `;`) appears mostly inside macros as a syntactic skeleton; `stl.loop` is essentially `;$ - dw` — jump to the current instruction's predecessor, forming an infinite loop.

## Execution model

- The CPU starts with the instruction pointer at address `0`.
- Each instruction is two consecutive words: the flip address `a` and the jump address `b`. The instruction occupies bits `[ip, ip + dw)` where `dw` is the [double-word size](types.md).
- After executing `a;b`, the instruction pointer is set to `b`. There is no implicit increment — execution flow is always explicit.
- The machine halts when it executes an instruction that jumps to itself (i.e. `b == ip`) AND the flip address `a` is NOT within the instruction's own `[ip, ip + dw)` body. The canonical halt is `stl.loop`, which expands to `;$ - dw` — a self-loop whose flip address (bit `0`) sits outside the instruction body.

Inside `stl.loop`, `$` evaluates to the current write-head position, which after emitting the two-word instruction equals `ip + dw`. So `$ - dw` equals `ip` — a genuine self-loop on the current instruction's first word, not a jump to a predecessor.

## What gives the language power

Traditional programming languages have separate read, write, and compare instructions. FlipJump has none of these directly. Variables and conditionals are built by **modifying the program at runtime**: the trick is that a single jump address in a `flip;jump` instruction can be conditionally rewritten by an earlier flip, so the next time control flow reaches that instruction it goes somewhere different.

This is why the standard library is so large despite the language being so small — the STL is essentially a library of established self-modifying patterns.

## See also

- [Lexical Structure](lexical.md) — what counts as a valid `a` or `b` expression.
- [Expressions](expressions.md) — operators and precedence for address arithmetic.
- [Input / Output](io.md) — how the address `IO` (set up by `stl.startup`) makes I/O happen.
- [esolangs.org/FlipJump](https://esolangs.org/wiki/FlipJump) — extended commentary on the language design.

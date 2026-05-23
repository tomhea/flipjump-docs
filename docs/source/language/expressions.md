# Expressions

Address expressions in FlipJump are evaluated at **assembly time**, not at runtime. The result is always a non-negative integer bit-address.

## Available operators

All operators are taken from the Monaco tokenizer's character class. The list below mirrors typical C-family precedence; consult the [upstream compiler](https://github.com/tomhea/flip-jump/blob/main/flipjump/assembler/) for the authoritative parser if you need a corner case settled.

| Operator | Meaning | Example |
|----------|---------|---------|
| `+`, `-`, `*`, `/`, `%` | Arithmetic | `dst + i * dw` |
| `<<`, `>>` | Shifts | `n << 3` |
| `&`, `|`, `^` | Bitwise AND / OR / XOR | `(d & 0xf)` |
| `~` | Bitwise NOT (unary) | `~mask` |
| `==`, `!=`, `<`, `>`, `<=`, `>=` | Compare (yields 0 or 1) | `a > b` |
| `?:` | Ternary | `(a > b) ? a : b` |
| `#x` | Bit-length operator | `#w` = number of bits required to represent `w` |
| `$` | Current bit-address | `;$ - dw` |
| `@x` | "Operation cost" / one FlipJump op cost | Used in complexity annotations; see [Complexity notation](complexity.md) |

## Bit-length: `#`

The `#` prefix returns the bit length of its operand:

```fj
#0         // 0
#1         // 1
#0xff      // 8
#w         // floor(log2(w)) + 1 — typically 7 for w=64
```

`#w` is used pervasively in the STL to allocate just-enough bits for an address.

## Current-address: `$`

Inside a `def` body, `$` refers to the bit-address of the current instruction. `stl.loop` is `;$ - dw` — flip bit 0 (harmless), then jump back one word, which puts the IP at this instruction's own first word — a tight self-loop that halts the machine per the rules in [The FlipJump Instruction](instruction.md#execution-model).

## Operator precedence (informal)

From highest to lowest:

1. Unary `-`, `~`, `#`, `$`
2. `*`, `/`, `%`
3. `+`, `-`
4. `<<`, `>>`
5. `<`, `<=`, `>`, `>=`
6. `==`, `!=`
7. `&`
8. `^`
9. `|`
10. `?:` (ternary)

Parentheses override precedence wherever it matters.

## Examples from the STL

```fj
dst + i * dw                          // pointer arithmetic — STL.bit.add
((d & 0xf) > (d >> 4)) ? x : 0        // a conditional flip address — hex.cond_jumps
(#const) + 3) / 4                     // ceil-divide a constant's bit length by 4 — hex.math
$ - dw                                // a self-loop jump address — stl.loop
```

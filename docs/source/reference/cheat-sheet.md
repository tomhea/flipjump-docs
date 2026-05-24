# FlipJump in 5 minutes

A single-page cheat sheet covering everything you need to start reading and writing FlipJump.

## The instruction

```fj
a;b              // flip the bit at address a, then jump to address b
```

That's the whole language. Variables, conditionals, arithmetic — all built from this.

**Shorthands:**

| Form | Meaning |
|---|---|
| `a;b` | flip a, jump to b |
| `a;`  | flip a, fall through |
| `;b`  | jump to b, no flip (formally: flip bit 0) |
| `;`   | bare self-loop / placeholder |

**Halt**: jump-to-self with flip-address OUTSIDE the instruction's own body. Canonical: `stl.loop` → `;$ - dw`.

## Lexical

| | |
|---|---|
| Comments | `// to end of line` (only form) |
| Numbers | `42`, `0xCAFE`, `0b1010` |
| Strings | `"text"` or `'text'` |
| Identifiers | `[A-Za-z_]\w*` (bare) or `name.sub.leaf` (dotted) |
| Line continuation | `\` at end of line |

## Operators (highest → lowest precedence)

```
#  (prefix bit-length)
*  /  %
+  -
<<  >>
<  <=  >  >=
==  !=
&
^
|
?:   (ternary)
```

Special: `$` is the current bit-address.

## Keywords

| Keyword | Use |
|---|---|
| `def NAME ARGS [@ LOCALS] [< REQS] [> EXPORTS] { ... }` | define a macro |
| `ns NAME { ... }` | open a namespace block |
| `rep(N, var) body` | repeat body N times with `var` bound 0..N-1 |

## Directives (built-in, not macros)

| Directive | Use |
|---|---|
| `pad N` | align current address to a multiple of N words |
| `reserve N` | reserve N bits of empty storage |
| `segment ADDR` | move the assembler cursor to bit-address ADDR |
| `wflip DST, VAL [, JMP]` | XOR VAL into word at DST, then optionally jump to JMP |

## Built-in names

| Name | Meaning |
|---|---|
| `w` | machine word width (bits) — set at compile time |
| `dw` | 2 * w — size of one instruction in bits |
| `dbit` | w + #w — offset to value bit inside a packed variable |
| `bit` | the namespace name (not a type keyword) |

## The 10 macros every program uses

| Macro | What it does |
|---|---|
| `stl.startup` | minimal init (I/O opcode only) |
| `stl.startup_and_init_all` | full init (I/O + pointers + hex tables + stack) |
| `stl.output "..."` | print a literal string |
| `stl.output_char c` | print one ASCII byte |
| `stl.loop` | halt (self-loop) |
| `bit.vec n[, val]` | declare an n-bit variable |
| `bit.if n, x, l0, l1` | branch on n-bit value (zero → l0 else l1) |
| `bit.add n, dst, src` | dst += src |
| `bit.print_dec_uint n, x` | print x as decimal |
| `hex.vec n[, val]` | declare an n-nibble hex variable (faster arithmetic) |

## Program skeleton

```fj
stl.startup_and_init_all       // initialise

// your code

stl.loop                       // halt

// data variables go below the halt
my_var: bit.vec 32, 0
```

## I/O addresses

| Address | Meaning |
|---|---|
| `2*w`   | the I/O opcode (after `stl.startup` this is exposed as the label `IO`) |
| `3*w + #w` | the next input bit (runtime auto-loads here on each read) |

## Where to go next

- [Hello World walkthrough](../getting-started/hello-world.md)
- [Cookbook recipes](../cookbook/index.md)
- [Standard Library](../stl/index.md) — all ~300 macros documented
- [Language Reference](../language/index.md) — full prose explanations
- [Glossary](glossary.md) — definitions of FJ-specific terms
- [How the STL works](how-the-stl-works.md) — the meta-pattern that makes the library possible

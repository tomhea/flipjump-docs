# Language Reference

FlipJump is a one-instruction esoteric language. The whole machine has exactly one operation: `a;b` flips the bit at address `a`, then jumps to address `b`. Everything else — variables, conditionals, arithmetic, I/O — is built out of that single instruction via self-modifying code.

The reference below covers the bare language and its assembly-time machinery. For the standard library that builds practical abstractions on top of it, see [Standard Library](../stl/index.md).

```{toctree}
:maxdepth: 1

instruction
lexical
expressions
macros
namespaces
directives
types
io
complexity
```

## Quick recap of the layers

- **Core instruction** — one operation: `a;b`. See [The FlipJump Instruction](instruction.md).
- **Assembly syntax** — comments, identifiers, numbers, expressions. See [Lexical Structure](lexical.md) and [Expressions](expressions.md).
- **Reusable code** — `def`, `ns`, `rep`. See [Macros](macros.md) and [Namespaces](namespaces.md).
- **Memory layout** — `pad`, `reserve`, `segment`, `wflip`. See [Directives](directives.md).
- **Built-in names** — `w`, `dw`, `dbit`, `bit`. See [Types and built-in names](types.md).
- **I/O** — the special IO opcode addresses. See [Input / Output](io.md).
- **Complexity notation** — what the `@` symbol means in the STL's annotations. See [Complexity notation](complexity.md).

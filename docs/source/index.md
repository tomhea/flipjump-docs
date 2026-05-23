# FlipJump Documentation

Welcome to the documentation for [FlipJump](https://github.com/tomhea/flip-jump) — a one-instruction esoteric programming language.

This site is under construction.

## What is FlipJump?

FlipJump's only instruction is `a;b`: flip the bit at address `a`, then jump to address `b`. Despite this minimalism, a substantial standard library implements variables, arithmetic, I/O, pointers, and a stack on top of self-modifying code.

While these docs are being built, see:

- The [GitHub repository](https://github.com/tomhea/flip-jump) for the language implementation, examples, and tests
- The [esolangs wiki entry](https://esolangs.org/wiki/FlipJump) for an overview
- The [FlipJump IDE](https://fj.tomhe.app) for an in-browser editor + compiler + runtime

```{toctree}
:maxdepth: 2
:hidden:

stl/index
```

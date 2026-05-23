# Installation

The FlipJump toolchain — the assembler `fj`, the interpreter, and the standard library — is distributed as a single Python package.

## Prerequisites

- Python 3.10 or newer.
- Any modern OS (Linux, macOS, Windows).

## Install

```sh
pip install flipjump
```

That puts a `fj` script on your `PATH`. Sanity check:

```sh
fj --version
```

You should see a version string like `1.3.0`.

## Optional: clone the repo for examples and tests

The PyPI package gives you everything you need to assemble and run programs, but the upstream [`tomhea/flip-jump`](https://github.com/tomhea/flip-jump) repo also ships example programs, tests, and the source of the standard library that this documentation auto-generates.

```sh
git clone https://github.com/tomhea/flip-jump.git
```

## Don't want to install anything?

The [FlipJump IDE at fj.tomhe.app](https://fj.tomhe.app) is the full toolchain compiled to WebAssembly — it runs the same assembler and interpreter as the CLI, entirely in your browser. Pre-loaded examples include Hello World, a prime sieve, and a calculator.

## Editor support

- **VS Code** — the [Monaco-based syntax highlighting](https://github.com/tomhea/fj.tomhe.app/blob/main/components/CodeEditor.tsx) that powers the IDE could be wrapped into a VS Code extension; one isn't published yet.
- **Vim / Emacs / other** — `.fj` files don't have an established syntax mode upstream. The [Lexical Structure](../language/lexical.md) reference is short enough to bootstrap one quickly.

## What's next

Continue with the [Hello World walkthrough](hello-world.md) to write and run your first FlipJump program.

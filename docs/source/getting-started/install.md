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

You should see a version string like `1.4.0`.

## Optional: clone the repo for examples and tests

The PyPI package gives you everything you need to assemble and run programs, but the upstream [`tomhea/flip-jump`](https://github.com/tomhea/flipjump) repo also ships example programs, tests, and the source of the standard library that this documentation auto-generates.

```sh
git clone https://github.com/tomhea/flipjump.git
```

## Don't want to install anything?

The [FlipJump IDE at fj.tomhe.app](https://fj.tomhe.app) runs the same assembler and interpreter as the CLI for you — you write code in the browser and it runs on the server, with output streamed back live. Pre-loaded examples include Hello World, a prime sieve, and a calculator.

## Editor support

`.fj` syntax highlighting is available as published plugins, both applying the same `fj-dark` colours as the IDE and these docs:

- **VS Code** — [FlipJump on the VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump).
- **JetBrains IDEs** (IntelliJ IDEA, PyCharm, CLion, …) — [FlipJump on the JetBrains Marketplace](https://plugins.jetbrains.com/plugin/32134-flipjump).

See [Editor syntax highlighting](../tools/editor-highlighting.md) for details. **Vim / Emacs / other** editors don't have an established `.fj` mode yet — the [Lexical Structure](../language/lexical.md) reference is short enough to bootstrap one quickly.

## What's next

Continue with the [Hello World walkthrough](hello-world.md) to write and run your first FlipJump program.

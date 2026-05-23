# FlipJump IDE — fj.tomhe.app

```{button-link} https://fj.tomhe.app
:color: primary
:expand:
:tooltip: Open the IDE in a new tab

🚀 Open the FlipJump IDE
```

## What it is

An in-browser FlipJump development environment: editor with syntax highlighting, the assembler, and the interpreter — all compiled to WebAssembly and running locally in your browser tab. No server round-trip, no install.

The editor is Monaco (the same engine VS Code uses). The tokenizer that powers its syntax highlighting is the source of truth for [this site's Pygments lexer](../language/lexical.md) too, so code blocks look identical across both.

## What you can do

- **Try every getting-started example** without installing anything.
- **Load pre-baked sample programs** from the file menu — Hello World, a calculator, the prime sieve, a function-call demo, and more.
- **Step through execution** one FlipJump op at a time.
- **Watch memory** as it changes — the self-modifying-code patterns from the [Standard Library](../stl/index.md) become visible.
- **Save and share** programs via the URL.

## When to use it vs the local `fj` toolchain

| Use case | Use this |
|---|---|
| First touch — try without committing | IDE |
| Building a small demo | IDE |
| Reading STL macro source while experimenting | IDE (side-by-side panels) |
| Long-running simulations | Local `fj` (no browser-tab overhead) |
| Custom toolchain integration (Makefiles, CI) | Local `fj` |
| Multi-file projects | Local `fj` (the IDE is single-file for now) |

## Related

- [Getting Started — Install](../getting-started/install.md) for the local `fj` toolchain.
- [Hello World](../getting-started/hello-world.md) — the three-line program you can paste straight into the IDE.
- [`c2fj`](c2fj.md) and [`bf2fj`](bf2fj.md) — companion compilers that target FlipJump from higher-level languages.

## Source

The IDE is open source. The repo lives alongside this docs site under [`tomhea`](https://github.com/tomhea/) — see [`fj.tomhe.app`](https://github.com/tomhea/fj.tomhe.app).

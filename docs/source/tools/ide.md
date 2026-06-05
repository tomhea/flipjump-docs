# FlipJump IDE — fj.tomhe.app

```{button-link} https://fj.tomhe.app
:color: primary
:expand:
:tooltip: Open the IDE in a new tab

🚀 Open the FlipJump IDE
```

## What it is

A browser-based FlipJump development environment — nothing to install, just open the link. The editor runs in your browser; the **assembler and interpreter run on the server** (the real `fj` toolchain), and your program's output streams back live over a WebSocket as it runs.

The editor is Monaco (the same engine VS Code uses). The tokenizer that powers its syntax highlighting is the source of truth for [this site's Pygments lexer](../language/lexical.md) too, so code blocks look identical across both.

## What you can do

- **Write and run FlipJump** straight from the browser — `fj` assembles and runs your code on the server and streams `stdout`/`stderr` into the terminal in real time.
- **Feed it input** — the terminal is interactive, so programs that read `stdin` work too.
- **Compile to `.fjm`** and download the assembled binary, or re-run an already-compiled image without recompiling.
- **Load pre-baked sample programs** — Hello World, a calculator, the prime sieve, a function-call demo, and more.
- **Import from other languages** — convert Brainfuck with [`bf2fj`](bf2fj.md) or C with [`c2fj`](c2fj.md) and run the result.
- **Browse the language reference and STL** in a side panel while you work.
- **Work across multiple files** in a file tree; your open project persists in the browser between visits.

## When to use it vs the local `fj` toolchain

| Use case | Use this |
|---|---|
| First touch — try without installing anything | IDE |
| Building a small demo | IDE |
| Reading STL macro source while experimenting | IDE (side-by-side panels) |
| Long-running simulations | Local `fj` (the hosted runner has time limits) |
| Custom toolchain integration (Makefiles, CI) | Local `fj` |
| Keeping large projects under version control | Local `fj` |

## Related

- [Getting Started — Install](../getting-started/install.md) for the local `fj` toolchain.
- [Hello World](../getting-started/hello-world.md) — the three-line program you can paste straight into the IDE.
- [`c2fj`](c2fj.md) and [`bf2fj`](bf2fj.md) — companion compilers that target FlipJump from higher-level languages.

## Source

The IDE is open source. The repo lives alongside this docs site under [`tomhea`](https://github.com/tomhea/) — see [`fj.tomhe.app`](https://github.com/tomhea/fj.tomhe.app).

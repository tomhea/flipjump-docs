# FlipJump

**The official FlipJump documentation.** FlipJump is a one-instruction esoteric programming language — the only instruction is `a;b`: flip the bit at address `a`, then jump to address `b`. Despite the minimalism, a substantial [standard library](stl/index.md) implements variables, arithmetic, I/O, pointers, and a stack on top of self-modifying code.

```{button-link} https://fj.tomhe.app
:color: primary
:expand:

🚀 Try FlipJump in your browser — fj.tomhe.app
```

## Where to start

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 🌱 New to FlipJump?
:link: getting-started/index
:link-type: doc

Install, run "Hello World", and learn the program skeleton.
:::

:::{grid-item-card} 📖 Language reference
:link: language/index
:link-type: doc

The single instruction, expression syntax, macros, namespaces, I/O.
:::

:::{grid-item-card} 📚 Standard library
:link: stl/index
:link-type: doc

Auto-generated reference for every macro in `flipjump/stl/`.
:::

:::{grid-item-card} 🍳 Cookbook
:link: cookbook/index
:link-type: doc

Ten short recipes: hello world, echo, decimal print, branches, loops, swap, add, function call.
:::

:::{grid-item-card} 📝 Examples
:link: examples/index
:link-type: doc

Hello World, prime sieve, calculator, quine — annotated.
:::

:::{grid-item-card} 🛠️ Companion tools
:link: tools/index
:link-type: doc

The browser IDE, c2fj (C compiler), bf2fj (Brainfuck compiler).
:::

::::

## External links

- The [upstream `flip-jump` repository](https://github.com/tomhea/flip-jump) for the language implementation, examples, and tests.
- The [esolangs.org wiki entry](https://esolangs.org/wiki/FlipJump) for background and design commentary.

```{toctree}
:maxdepth: 2
:hidden:

getting-started/index
cookbook/index
language/index
stl/index
reference/index
examples/index
tools/index
```

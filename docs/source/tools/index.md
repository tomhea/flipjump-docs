# Companion tools

Three projects sit in the FlipJump ecosystem alongside the language itself:

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 🌐 FlipJump IDE
:link: ide
:link-type: doc

Browser-based editor, compiler, and runtime. Write FlipJump, hit Run, see output — no install required.

**[fj.tomhe.app →](https://fj.tomhe.app)**
:::

:::{grid-item-card} 🅒 c2fj
:link: c2fj
:link-type: doc

C-to-FlipJump compiler. Pipeline: C → RISC-V → FlipJump.

`pip install c2fj`
:::

:::{grid-item-card} 🧠 bf2fj
:link: bf2fj
:link-type: doc

Brainfuck-to-FlipJump compiler with four optimisation passes.

`pip install bf2fj`
:::

::::

```{toctree}
:hidden:

ide
c2fj
bf2fj
```

The IDE is the easiest entry point — it works without any local install. The compilers (c2fj, bf2fj) let you target FlipJump from higher-level languages, which is the most practical way to write non-trivial programs.

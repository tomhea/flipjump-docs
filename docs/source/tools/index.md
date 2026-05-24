# Companion tools and resources

Five places to go beyond this docs site:

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

:::{grid-item-card} 🐙 flip-jump on GitHub
:link: flip-jump
:link-type: doc

The upstream repo: language implementation, standard library, example programs, tests, the GitHub wiki.
:::

:::{grid-item-card} 📜 esolangs.org/FlipJump
:link: esolangs
:link-type: doc

Background commentary on the language design, computational classification, and links to related single-instruction languages.
:::

::::

```{toctree}
:hidden:

ide
c2fj
bf2fj
flip-jump
esolangs
```

The IDE is the easiest entry point — no local install. The compilers (c2fj, bf2fj) let you target FlipJump from higher-level languages. The upstream repo is where issues, contributions, and the language implementation live. The esolangs page is the canonical external reference.

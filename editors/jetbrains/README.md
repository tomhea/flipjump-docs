# FlipJump for JetBrains IDEs (TextMate bundle)

Syntax highlighting for the [FlipJump](https://github.com/tomhea/flip-jump)
assembly language in any JetBrains IDE — IntelliJ IDEA, PyCharm, CLion, WebStorm,
GoLand, Rider, etc. It reuses the **same TextMate grammar** as the FlipJump VS
Code extension, so highlighting matches the [IDE](https://fj.tomhe.app) and the
[docs site](https://fjdocs.tomhe.app).

This folder is a TextMate bundle (in VS Code-extension format — a `package.json`
manifest plus the grammar):

- `package.json` — the manifest JetBrains reads to find the grammar + `.fj` association
- `flipjump.tmLanguage.json` — the grammar (classifies tokens)
- `flipjump-dark.tmTheme` — optional colour theme reproducing the exact `fj-dark` palette

## Install

> **This is a TextMate bundle, not a plugin.** Do **not** use *Settings → Plugins
> → Install Plugin from Disk* (that will fail with "Failed to load plugin
> descriptor"). Use the TextMate Bundles importer below.

JetBrains IDEs ship the **TextMate Bundles** support (bundled by default; if a
search for "TextMate" in *Settings → Plugins* shows it disabled, enable it).

1. Download and unzip `flipjump-jetbrains-textmate.zip` from the
   [docs site](https://fjdocs.tomhe.app/tools/editor-highlighting.html). You get a
   folder `flipjump-jetbrains-textmate/`.
2. *Settings → Editor → TextMate Bundles → `+`* and select that **folder** (the
   one containing `package.json`).
3. Open any `.fj` file — it's now highlighted.

Out of the box the grammar's standard scopes (`keyword`, `string`, `comment`,
`entity.name.function`, …) are coloured by your active IDE colour scheme (looks
reasonable in Darcula).

### Want the exact fj-dark colours?

JetBrains' TextMate support colours tokens from your **IDE colour scheme** via a
fixed, built-in scope→colour map, and it [does not support custom TextMate
themes](https://youtrack.jetbrains.com/issue/IJPL-34298), so the bundled
`flipjump-dark.tmTheme` cannot be applied and this bundle can't reproduce the
website colours exactly (e.g. macro calls and macro definitions collapse to one
colour, and labels are left plain).

For pixel-exact `fj-dark` parity in JetBrains, install the **native plugin**
instead — see [`editors/jetbrains-plugin`](../jetbrains-plugin/) /
the [docs site](https://fjdocs.tomhe.app/tools/editor-highlighting.html). The
`.tmTheme` is kept here only as a reference for the palette.

## Source

Developed in the docs repo: <https://github.com/tomhea/flipjump-docs> under
`editors/jetbrains`. The grammar is synced from the canonical
`editors/grammars/flipjump.tmLanguage.json`.

## License

BSD 2-Clause.

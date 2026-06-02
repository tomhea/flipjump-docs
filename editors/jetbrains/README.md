# FlipJump for JetBrains IDEs (TextMate bundle)

Syntax highlighting for the [FlipJump](https://github.com/tomhea/flip-jump)
assembly language in any JetBrains IDE — IntelliJ IDEA, PyCharm, CLion, WebStorm,
GoLand, Rider, etc. It reuses the **same TextMate grammar** as the FlipJump VS
Code extension, so highlighting matches the [IDE](https://fj.tomhe.app) and the
[docs site](https://fjdocs.tomhe.app).

This folder is a TextMate bundle:

- `flipjump.tmLanguage.json` — the grammar (associates `.fj` files, classifies tokens)
- `flipjump-dark.tmTheme` — optional colour theme reproducing the exact `fj-dark` palette

## Install

JetBrains IDEs ship the **TextMate Bundles** plugin (bundled by default; if not,
enable it in *Settings → Plugins*).

1. Download and unzip `flipjump-jetbrains-textmate.zip` from the
   [docs site](https://fjdocs.tomhe.app/tools/editor-highlighting.html).
2. *Settings → Editor → TextMate Bundles → `+`* and select the unzipped folder.
3. Open any `.fj` file — it's now highlighted.

Out of the box the grammar's standard scopes (`keyword`, `string`, `comment`,
`entity.name.function`, …) are coloured by your active IDE colour scheme (looks
good in Darcula).

### Exact `fj-dark` colours (optional)

To match the website/IDE palette precisely, load the bundled TextMate theme:

*Settings → Editor → Color Scheme → TextMate* — pick **FlipJump Dark**, or import
`flipjump-dark.tmTheme` if it isn't listed.

## Source

Developed in the docs repo: <https://github.com/tomhea/flipjump-docs> under
`editors/jetbrains`. The grammar is synced from the canonical
`editors/grammars/flipjump.tmLanguage.json`.

## License

BSD 2-Clause.

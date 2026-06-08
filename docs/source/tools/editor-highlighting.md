# Editor syntax highlighting — VS Code & JetBrains

```{button-link} https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump
:color: primary
:expand:
:tooltip: Open the FlipJump extension on the VS Code Marketplace

🧩 Get the VS Code extension
```

```{button-link} https://plugins.jetbrains.com/plugin/32134-flipjump
:color: primary
:expand:
:tooltip: Open the FlipJump plugin on the JetBrains Marketplace

🧩 Get the JetBrains plugin
```

## What it is

Syntax highlighting for `.fj` files in [VS Code](https://code.visualstudio.com)
and [JetBrains IDEs](https://www.jetbrains.com) (IntelliJ IDEA, PyCharm, CLion,
WebStorm, …).

The classification is ported from the [FlipJump IDE](ide.md)'s Monaco tokenizer
and kept in lock-step with [this site's Pygments lexer](../language/lexical.md)
by automated parity tests. So a `.fj` file gets the same `fj-dark` palette as the
IDE and the code blocks here — `def`/`ns`/`rep` in blue, macro calls in gold,
macro definitions in cyan, labels in teal, constants in purple, directives in
orange, plus strings, numbers, and comments.

For exact colours, **VS Code** uses a TextMate grammar + scoped colour rules, and
**JetBrains** uses a native plugin with its own lexer (its built-in TextMate
engine can't reproduce the per-token colours).

## VS Code

**Install** from the
[VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump):

- **In the editor:** open the Extensions view, search **FlipJump**, click *Install*.
- **Command line:**

  ```bash
  code --install-extension flipjump.flipjump
  ```

**Colours.** The extension applies the exact `fj-dark` colours to FlipJump tokens
**only** — every scope ends in `.flipjump`, so your own editor theme is untouched
for every other language. Nothing to switch.

Want to tweak them? Add this to your `settings.json` and edit the hexes:

```json
"editor.tokenColorCustomizations": {
  "textMateRules": [
    { "scope": "keyword.control.flipjump", "settings": { "foreground": "#569cd6", "fontStyle": "bold" } },
    { "scope": "entity.name.function.call.flipjump", "settings": { "foreground": "#e8c47a" } },
    { "scope": "comment.line.double-slash.flipjump", "settings": { "foreground": "#6a9955", "fontStyle": "italic" } }
  ]
}
```

## JetBrains IDEs

A native IntelliJ Platform plugin with its own lexer, so it reproduces the VS
Code colours **exactly**, including macro-call (gold) vs macro-definition (cyan),
labels, constants, and the rest — things JetBrains' built-in TextMate engine
[can't do](https://youtrack.jetbrains.com/issue/IJPL-34298).

**Install** from the
[JetBrains Marketplace](https://plugins.jetbrains.com/plugin/32134-flipjump):

1. *Settings → **Plugins** → Marketplace*, search **FlipJump**, click *Install* → restart.
2. Open any `.fj` file. Tweak colours under *Settings → Editor → Color Scheme → FlipJump*.

Prefer to build it yourself? `cd editors/jetbrains-plugin && ./gradlew buildPlugin`
produces `build/distributions/flipjump-jetbrains-*.zip`, which you can load via
*Settings → **Plugins** → ⚙ → Install Plugin from Disk…* (the first build downloads
the IntelliJ Platform).

## Source

Everything lives in the docs repo at
[`tomhea/flipjump-docs`](https://github.com/tomhea/flipjump-docs) under `editors/`
— the VS Code extension in `editors/vscode`, the native JetBrains plugin in
`editors/jetbrains-plugin`, and the shared grammar in
`editors/grammars/flipjump.tmLanguage.json`. Bug reports
and improvements welcome there.

## Related

- [FlipJump IDE](ide.md) — the in-browser editor whose tokenizer this mirrors.
- [Lexical structure](../language/lexical.md) — what the tokens mean.
- [Hello World](../getting-started/hello-world.md) — paste it into a `.fj` file and watch it light up.

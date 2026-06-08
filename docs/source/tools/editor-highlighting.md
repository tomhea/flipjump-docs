# Editor syntax highlighting — VS Code & JetBrains

```{button-link} ../_static/flipjump-vscode.vsix
:color: primary
:expand:
:tooltip: Download the VS Code extension

⬇ Download VS Code extension (`.vsix`)
```

```{button-link} ../_static/flipjump-jetbrains.zip
:color: primary
:expand:
:tooltip: Download the native JetBrains plugin (exact fj-dark colours)

⬇ Download JetBrains plugin (`.zip`)
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

**Install**

- **Marketplace:** search **FlipJump** in the Extensions view, or
- **From VSIX:** download the `.vsix` above, then

  ```bash
  code --install-extension flipjump-vscode.vsix
  ```

  or *Extensions → ··· → Install from VSIX…*

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

It's distributed as a normal plugin (it uses the Plugins page):

1. Download the `.zip` above. (Or build it yourself:
   `cd editors/jetbrains-plugin && ./gradlew buildPlugin` →
   `build/distributions/flipjump-jetbrains-*.zip`; the first build downloads the
   IntelliJ Platform.)
2. *Settings → **Plugins** → ⚙ → Install Plugin from Disk…* → select the zip → restart.
3. Open any `.fj` file. Tweak colours under *Settings → Editor → Color Scheme → FlipJump*.

A JetBrains Marketplace listing is planned so this becomes a one-click install.

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

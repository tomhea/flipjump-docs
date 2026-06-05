# Editor syntax highlighting — VS Code & JetBrains

```{button-link} ../_static/flipjump-vscode.vsix
:color: primary
:expand:
:tooltip: Download the VS Code extension

⬇ Download VS Code extension (`.vsix`)
```

```{button-link} ../_static/flipjump-jetbrains-textmate.zip
:color: primary
:expand:
:tooltip: Download the JetBrains TextMate bundle

⬇ Download JetBrains bundle (`.zip`)
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
**JetBrains** uses a native plugin with its own lexer (its TextMate engine can't
reproduce the per-token colours — see below). A lighter, *approximate* JetBrains
TextMate bundle is also available.

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

Two options, depending on whether you want exact colours.

### Native plugin — exact `fj-dark` (recommended)

A real IntelliJ Platform plugin with its own lexer, so it reproduces the VS Code
colours **exactly**, including macro-call (gold) vs macro-definition (cyan),
labels, constants, and the rest — things the TextMate route can't do in JetBrains.

It's distributed as a normal plugin (this one *does* use the Plugins page):

1. Build the zip: `cd editors/jetbrains-plugin && gradle buildPlugin` →
   `build/distributions/flipjump-jetbrains-*.zip`. (First build downloads the
   IntelliJ Platform.)
2. *Settings → **Plugins** → ⚙ → Install Plugin from Disk…* → select the zip → restart.
3. Open any `.fj` file. Tweak colours under *Settings → Editor → Color Scheme → FlipJump*.

A JetBrains Marketplace listing is planned so this becomes a one-click install.

### TextMate bundle — lightweight, approximate

The `.zip` above is a TextMate bundle (**not** a plugin — don't use *Install
Plugin from Disk* for it). It needs no build:

1. Unzip it → a `flipjump-jetbrains-textmate/` folder.
2. *Settings → Editor → **TextMate Bundles** → `+`* and select that folder.
3. Open any `.fj` file.

JetBrains colours TextMate tokens from your active IDE scheme via a fixed,
built-in scope map and [can't load custom TextMate
themes](https://youtrack.jetbrains.com/issue/IJPL-34298), so this route is
approximate — macro calls and definitions share a colour and labels stay plain.
Use the native plugin above for exact parity.

## Source

Everything lives in the docs repo at
[`tomhea/flipjump-docs`](https://github.com/tomhea/flipjump-docs) under `editors/`
— the VS Code extension in `editors/vscode`, the JetBrains native plugin in
`editors/jetbrains-plugin`, the JetBrains TextMate bundle in `editors/jetbrains`,
and the shared grammar in `editors/grammars/flipjump.tmLanguage.json`. Bug reports
and improvements welcome there.

## Related

- [FlipJump IDE](ide.md) — the in-browser editor whose tokenizer this mirrors.
- [Lexical structure](../language/lexical.md) — what the tokens mean.
- [Hello World](../getting-started/hello-world.md) — paste it into a `.fj` file and watch it light up.

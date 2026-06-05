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

Both editors are driven by **one shared TextMate grammar**, ported from the
[FlipJump IDE](ide.md)'s Monaco tokenizer and kept in lock-step with [this site's
Pygments lexer](../language/lexical.md) by an automated parity test. So a `.fj`
file looks the same in your editor, in the IDE, and in the code blocks here —
same `fj-dark` palette: `def`/`ns`/`rep` in blue, macro calls in gold, labels in
teal, constants in purple, directives in orange, strings, numbers, and comments
all coloured to match.

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

This is a **TextMate bundle**, not a plugin — don't use *Settings → Plugins →
Install Plugin from Disk* (it will fail). Import it through the built-in TextMate
Bundles support instead:

1. Download and unzip the bundle above → you get a `flipjump-jetbrains-textmate/` folder.
2. *Settings → Editor → TextMate Bundles → `+`* and select that **folder** (the one containing `package.json`).
3. Open any `.fj` file.

For the exact `fj-dark` palette, the bundle includes a `flipjump-dark.tmTheme`:
*Settings → Editor → Color Scheme → TextMate → **FlipJump Dark***. Otherwise the
grammar's standard scopes are coloured by your active scheme (looks good in
Darcula out of the box).

## Source

Both packages live in the docs repo at
[`tomhea/flipjump-docs`](https://github.com/tomhea/flipjump-docs) under
`editors/` — the VS Code extension in `editors/vscode`, the JetBrains bundle in
`editors/jetbrains`, and the shared grammar in
`editors/grammars/flipjump.tmLanguage.json`. Bug reports and improvements welcome
there.

## Related

- [FlipJump IDE](ide.md) — the in-browser editor whose tokenizer this mirrors.
- [Lexical structure](../language/lexical.md) — what the tokens mean.
- [Hello World](../getting-started/hello-world.md) — paste it into a `.fj` file and watch it light up.

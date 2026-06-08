# FlipJump for VS Code

[![VS Code Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/flipjump.flipjump?label=Marketplace&logo=visualstudiocode)](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/flipjump.flipjump?label=installs)](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump)
[![Rating](https://img.shields.io/visual-studio-marketplace/r/flipjump.flipjump?label=rating)](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump&ssr=false#review-details)

Syntax highlighting for the [FlipJump](https://github.com/tomhea/flip-jump)
assembly language — the one-instruction esoteric language. Opens `.fj` files
with the exact token colours used by the [FlipJump IDE](https://fj.tomhe.app)
and the [docs site](https://fjdocs.tomhe.app).

## What it highlights

- `def` / `ns` / `rep` keywords, and the macro / namespace names they introduce
- Macro calls at the start of a line (e.g. `stl.output "Hi"`)
- Directives: `pad`, `reserve`, `segment`, `wflip`
- Types `dbit` / `dw` / `w`, labels (`loop:`), and constants (`X = ...`)
- `//` comments, `"…"` / `'…'` strings, and `0x` / `0b` / decimal numbers
- Operators and punctuation

The grammar is a TextMate port of the FlipJump IDE's Monaco tokenizer, kept in
lock-step with the docs site's Pygments lexer by an automated parity test, so
code looks identical across the IDE, the docs, and your editor.

## Colours

The extension ships the exact `fj-dark` colours and applies them **only to
FlipJump tokens** (every scope ends in `.flipjump`), so your own editor theme is
left untouched for every other language. No theme switch required.

Prefer to tune them yourself? Add an `editor.tokenColorCustomizations` block to
your `settings.json` with `textMateRules` targeting the `*.flipjump` scopes.

## Install

From the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=flipjump.flipjump):

- **In the editor:** search for **FlipJump** in the Extensions view, click *Install*.
- **Command line:**

  ```
  code --install-extension flipjump.flipjump
  ```

## Source & issues

Developed in the docs repo: <https://github.com/tomhea/flipjump-docs> under
`editors/vscode`. The shared grammar lives at `editors/grammars/flipjump.tmLanguage.json`.

## License

BSD 2-Clause — see [LICENSE](LICENSE).

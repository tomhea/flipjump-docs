# FlipJump editor tooling

Syntax highlighting for `.fj` files in VS Code and JetBrains IDEs.

- **VS Code** is driven by a TextMate grammar ported from the docs-site Pygments
  lexer (the IDE's Monaco tokenizer).
- **JetBrains** uses a native plugin with its own lexer (JetBrains can't apply
  custom TextMate themes). It lives in [`jetbrains-plugin/`](jetbrains-plugin/)
  and has its own README.

This directory holds the canonical grammar/theme and the VS Code extension.
Layout:

```
editors/
├── grammars/flipjump.tmLanguage.json   # CANONICAL grammar (single source of truth)
├── flipjump-dark.tmTheme               # CANONICAL fj-dark theme (palette mirror)
├── colors.mjs                          # fj-dark palette for the preview renderer
├── sync.mjs                            # copies the canonical grammar into vscode/
├── grammar.mjs                         # loads the grammar via vscode-textmate + oniguruma
├── test/                               # verifier + preview renderer
├── vscode/                             # VS Code extension (declarative)
└── jetbrains-plugin/                   # native JetBrains plugin (own lexer; see its README)
```

## Develop

```sh
cd editors
npm install          # vscode-textmate + oniguruma (+ optional resvg for the preview)
npm run sync         # refresh the VS Code grammar copy from the canonical grammar
npm run verify       # tokenize the golden cases (from test_pygments_lexer.py) and assert scopes
npm run render       # write test/preview.svg + preview.png (needs optional @resvg/resvg-js)
```

The colour palette lives in three hand-mirrored places — `vscode/package.json`
(`configurationDefaults`), `flipjump-dark.tmTheme`, and `colors.mjs`. They are
all guarded against drifting from the canonical Pygments style by
`tests/test_extractor/test_vscode_grammar_parity.py`, which also checks the
grammar's word-lists and that the synced copy is byte-identical.

## Rebuild the shipped artifact

`docs/source/_static/flipjump-vscode.vsix` is a committed binary that ships from
the docs site. **If you change the grammar, colours, or language configuration,
repackage it** (CI fails otherwise — it diffs the embedded files against these
sources):

```sh
cd editors
npm run sync
( cd vscode && npx --yes @vscode/vsce package --out ../../docs/source/_static/flipjump-vscode.vsix )
```

Then commit the updated artifact. (The native JetBrains plugin zip is rebuilt
separately — see [`jetbrains-plugin/README.md`](jetbrains-plugin/README.md).)

## Publish

- **VS Code Marketplace:** `cd vscode && npx --yes @vscode/vsce publish` (needs an Azure DevOps PAT for the `flipjump` publisher).
- **Open VSX (optional):** `npx --yes ovsx publish`.
- **JetBrains plugin:** see [`jetbrains-plugin/README.md`](jetbrains-plugin/README.md).

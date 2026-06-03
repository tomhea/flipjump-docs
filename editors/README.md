# FlipJump editor tooling

Syntax highlighting for `.fj` files in VS Code and JetBrains IDEs, both driven by
one TextMate grammar ported from the docs-site Pygments lexer (the IDE's Monaco
tokenizer). Layout:

```
editors/
├── grammars/flipjump.tmLanguage.json   # CANONICAL grammar (single source of truth)
├── flipjump-dark.tmTheme               # CANONICAL fj-dark theme (JetBrains)
├── colors.mjs                          # fj-dark palette for the preview renderer
├── sync.mjs                            # copies canonical grammar/theme into vscode/ + jetbrains/
├── grammar.mjs                         # loads the grammar via vscode-textmate + oniguruma
├── test/                               # verifier + preview renderer
├── vscode/                             # VS Code extension (declarative)
└── jetbrains/                          # JetBrains TextMate bundle
```

## Develop

```sh
cd editors
npm install          # vscode-textmate + oniguruma (+ optional resvg for the preview)
npm run sync         # refresh the per-editor copies from the canonical grammar/theme
npm run verify       # tokenize the golden cases (from test_pygments_lexer.py) and assert scopes
npm run render       # write test/preview.svg + preview.png (needs optional @resvg/resvg-js)
```

The colour palette lives in three hand-mirrored places — `vscode/package.json`
(`configurationDefaults`), `flipjump-dark.tmTheme`, and `colors.mjs`. They are
all guarded against drifting from the canonical Pygments style by
`tests/test_extractor/test_vscode_grammar_parity.py`, which also checks the
grammar's word-lists and that the synced copies are byte-identical.

## Rebuild the shipped artifacts

`docs/source/_static/flipjump-vscode.vsix` and
`docs/source/_static/flipjump-jetbrains-textmate.zip` are committed binaries that
ship from the docs site. **If you change the grammar, colours, or language
configuration, repackage them** (CI fails otherwise — it diffs the embedded
files against these sources):

```sh
cd editors
npm run sync

# VS Code extension -> .vsix
( cd vscode && npx --yes @vscode/vsce package --out ../../docs/source/_static/flipjump-vscode.vsix )

# JetBrains bundle -> .zip (a folder named flipjump-jetbrains-textmate/)
stage=$(mktemp -d)
mkdir "$stage/flipjump-jetbrains-textmate"
cp jetbrains/flipjump.tmLanguage.json jetbrains/flipjump-dark.tmTheme jetbrains/README.md "$stage/flipjump-jetbrains-textmate/"
( cd "$stage" && zip -r -X - flipjump-jetbrains-textmate ) > ../docs/source/_static/flipjump-jetbrains-textmate.zip
```

Then commit the updated artifacts.

## Publish

- **VS Code Marketplace:** `cd vscode && npx --yes @vscode/vsce publish` (needs an Azure DevOps PAT for the `tomhea` publisher).
- **Open VSX (optional):** `npx --yes ovsx publish`.

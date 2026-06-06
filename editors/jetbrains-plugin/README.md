# FlipJump — native JetBrains plugin

Exact `fj-dark` syntax highlighting for `.fj` files in any JetBrains IDE
(IntelliJ IDEA, PyCharm, CLion, WebStorm, GoLand, Rider, …).

This is a real IntelliJ Platform plugin with its own lexer and
`SyntaxHighlighter`, so it reproduces the VS Code colours **exactly** —
including the macro-call (gold) vs macro-definition (cyan) distinction that
JetBrains' built-in TextMate engine collapses, and per-token colours for labels,
constants, directives, types, numbers, strings, comments.

The lexer is a hand-written port of the same ordered, line-aware rules as the
shared TextMate grammar / docs-site Pygments lexer, and is verified against the
identical golden cases in `src/test/java/.../FlipJumpLexerTest.java`.

## Install (from disk)

> Settings → **Plugins** → ⚙ → **Install Plugin from Disk…**

1. Download `flipjump-jetbrains-plugin.zip` from the
   [docs site](https://fjdocs.tomhe.app/tools/editor-highlighting.html).
2. *Settings → Plugins → ⚙ → Install Plugin from Disk…* → select the zip.
3. Restart the IDE when prompted. Open any `.fj` file.

Colours are applied out of the box; tweak them under *Settings → Editor →
Color Scheme → FlipJump*.

## Build from source

Requires JDK 17+. The first build downloads the IntelliJ Platform.

```sh
cd editors/jetbrains-plugin
./gradlew test          # run the lexer parity tests
./gradlew buildPlugin   # -> build/distributions/flipjump-jetbrains-<version>.zip
```

To try it in a sandbox IDE: `./gradlew runIde`.

## Publish

`./gradlew publishPlugin` to the [JetBrains Marketplace](https://plugins.jetbrains.com)
(needs a `PUBLISH_TOKEN`); or upload the built zip manually to the Marketplace.

## License

BSD 2-Clause.

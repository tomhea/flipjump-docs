# FlipJump — native JetBrains plugin

[![JetBrains Plugin Version](https://img.shields.io/jetbrains/plugin/v/32134?label=Marketplace&logo=jetbrains)](https://plugins.jetbrains.com/plugin/32134-flipjump)
[![Downloads](https://img.shields.io/jetbrains/plugin/d/32134?label=downloads)](https://plugins.jetbrains.com/plugin/32134-flipjump)
[![Rating](https://img.shields.io/jetbrains/plugin/r/rating/32134?label=rating)](https://plugins.jetbrains.com/plugin/32134-flipjump/reviews)

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

## Go to definition

**Ctrl/Cmd+click** (or *Go to Declaration*, `Ctrl/Cmd+B`) on a macro name jumps
to where it's declared. Clicking `xor` in `hex.xor a b c` finds the matching
`def xor` across every `.fj` file in the project — one match jumps straight
there, several open the usual navigation popup. The clicked segment is used on
its own, so the `hex.` namespace prefix is ignored (a macro is declared
`def xor` inside `ns hex`).

## Install

From the [JetBrains Marketplace](https://plugins.jetbrains.com/plugin/32134-flipjump):

1. *Settings → **Plugins** → Marketplace*, search **FlipJump**, click *Install*.
2. Restart the IDE when prompted. Open any `.fj` file.

Colours are applied out of the box; tweak them under *Settings → Editor →
Color Scheme → FlipJump*.

To install a locally built `.zip` instead, use *Settings → **Plugins** → ⚙ →
**Install Plugin from Disk…*** (see [Build from source](#build-from-source)).

## Build from source

Requires JDK 17+. The first build downloads the IntelliJ Platform.

```sh
cd editors/jetbrains-plugin
./gradlew test          # run the lexer parity tests
./gradlew buildPlugin   # -> build/distributions/flipjump-jetbrains-<version>.zip
```

To try it in a sandbox IDE: `./gradlew runIde`.

## Publish

CI builds and uploads the plugin `.zip` on every PR that touches the plugin (see
[`jetbrains-plugin.yml`](../../.github/workflows/jetbrains-plugin.yml)), but
**publishing a new version to the Marketplace is always manual.** Bump `version`
in `build.gradle.kts` and add a `## [x.y.z]` CHANGELOG entry first, then:

`./gradlew publishPlugin` to the [JetBrains Marketplace](https://plugins.jetbrains.com)
(needs a `PUBLISH_TOKEN`); or upload the built zip manually to the Marketplace.

## License

BSD 2-Clause.

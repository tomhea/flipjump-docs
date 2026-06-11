# Changelog

## [0.2.0]

### Added

- **Go to definition:** Ctrl/Cmd+click (or *Go to Declaration*) on a macro name
  jumps to its `def` declaration, searching every `.fj` file in the project. The
  clicked dotted segment is used alone, so `xor` in `hex.xor` finds `def xor`;
  multiple matches open the usual navigation popup.

### Fixed

- Namespace-relative macro calls that start with leading dots — `.zero`,
  `..foo`, `.a.b` — are now highlighted as macro calls (previously a leading dot
  fell back to a plain identifier colour), as are calls inside a `rep(...)`
  clause (e.g. `rep(n, i) bit.exact_xor …`). A lone `.` and names with
  consecutive dots after a segment are no longer mis-coloured as calls.

## [0.1.0]

### Added

- Initial release of the native FlipJump plugin for JetBrains IDEs (IntelliJ
  IDEA, PyCharm, CLion, WebStorm, …).
- Hand-written lexer for `.fj` files reproducing the exact `fj-dark` colours of
  the FlipJump IDE and docs site, verified for parity with the docs-site
  Pygments lexer.
- Distinct colours for macro definitions (cyan) vs. macro calls (gold), plus
  `def`/`ns`/`rep` keywords, namespaces, directives, types, labels, constants,
  numbers, strings, and `//` comments.
- Colour customisation under *Settings → Editor → Color Scheme → FlipJump*.

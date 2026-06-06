# Changelog

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

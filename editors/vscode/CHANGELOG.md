# Changelog

## 0.2.0

- **Go to definition:** Ctrl/Cmd+click (or F12) on a macro name jumps to its
  `def` declaration, searching every `.fj` file in the workspace. The clicked
  dotted segment is used alone, so `xor` in `hex.xor` finds `def xor`; multiple
  matches open a peek list.
- **Highlighting:** namespace-relative macro calls that start with leading dots
  — `.zero`, `..foo`, `.a.b` — are now coloured as macro calls, as are calls
  inside a `rep(...)` clause (e.g. `rep(n, i) bit.exact_xor …`). A lone `.` and
  names with consecutive dots after a segment are no longer mis-coloured as
  calls.

## 0.1.0

- Initial release.
- TextMate grammar for `.fj` files, ported from the FlipJump IDE's Monaco
  tokenizer and verified for parity with the docs-site Pygments lexer.
- Ships the `fj-dark` colours scoped to FlipJump tokens only, so other
  languages and your chosen theme are unaffected.
- Language configuration: `//` line comments, bracket matching, auto-closing
  pairs.

# Lexical Structure

## Comments

FlipJump has **one** comment form: `//` to end of line.

```fj
// a comment, all of this line is ignored
a;b   // also fine after code
```

There is no `/* ... */` block-comment syntax. (The Monaco tokenizer that ships with the IDE explicitly rejects it.)

## Identifiers

An identifier matches `[A-Za-z_][A-Za-z0-9_.]*` — letters, digits, underscores, and dots. The dot enables namespace navigation:

```fj
my_macro            // a bare identifier
stl.startup         // a namespace-qualified reference
hex.pointers.write_hex
```

Identifiers can also lead with one or two dots, denoting current-namespace or parent-namespace lookup respectively:

```fj
ns hex {
    def add { .clear_carry }     // .clear_carry  ≡ hex.clear_carry (current ns)
    ns pointers {
        def f { ..add }          // ..add  ≡ hex.add (parent ns)
    }
}
```

## Numbers

Three forms, the same as most modern languages:

```fj
42          // decimal
0xCAFE      // hex (case-insensitive prefix; nibbles are case-insensitive too)
0b1010      // binary
```

All number tokens are unsigned integers at lex time. Negative values are produced by the unary `-` operator at expression time.

## Strings

Either single or double quotes; identical semantics. Backslash escapes work as in C:

```fj
"hello\n"
'H'
```

Strings appear as arguments to macros that emit characters (e.g. `stl.output "Hello"` in the STL).

## Line continuation

A backslash at end of line consumes the newline so a logical line can span multiple physical lines:

```fj
def really_long_macro a, b, c, d, \
    e, f, g, h, \
    i { ... }
```

This is common in STL `def` lines with many parameters and in `wflip` calls with large embedded constants.

## Operators

The operator character class is:

```
! = < > ? @ ^ | % & * + - / : # $
```

See [Expressions](expressions.md) for precedence and individual operator meanings.

Separators:

- `;` — flip / jump separator inside an instruction.
- `,` — argument separator inside macro calls and `def` signatures.

Brackets: `( )`, `[ ]`, `{ }` are all distinct. Braces delimit macro bodies and namespace bodies; parens group expressions and `rep(...)` calls; brackets group `dw`-sized address arithmetic in the STL convention.

## File extension

FlipJump source files use `.fj`. The Sphinx Pygments lexer here is registered for that extension (and for the `fj`, `flipjump`, `FlipJump` MyST language tags).

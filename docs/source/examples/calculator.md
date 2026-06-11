# Calculator

[`programs/calc.fj`](https://github.com/tomhea/flipjump/blob/main/programs/calc.fj) — an interactive REPL that parses two numbers and one operator from stdin, evaluates, and prints the result. Supports `+`, `-`, `*`, `/`, `%`, decimal or hexadecimal input.

```text
> 12345 + 67890
80235
> 0xff * 0xff
0xfe01
```

The full program is ~600 lines — too long to inline. The shape:

```fj
stl.startup

loop:
    bit.zero hex_used
    bit.print 3, prompt_string
    getch
    remove_spaces
    check_quit should_quit, before_start
  // ... lots of parsing helpers ...

    insert_number a
    bit.mov 8, op, ascii
    insert_number b
    calc a, op, b
    bit.print_dec_int 64, result
    ;loop                  // back to the top
```

[View on GitHub](https://github.com/tomhea/flipjump/blob/main/programs/calc.fj).

## What it demonstrates

- **Stateful input parsing.** A `getch` helper, character-by-character whitespace skipping, hex/decimal mode detection.
- **Conditional dispatch.** `bit.cmp` chains for `+`/`-`/`*`/`/`/`%` opcode routing.
- **Error handling.** A dedicated `err_loop` label that prints an error message and restarts the prompt without aborting.
- **Multi-pass output.** The result is printed in decimal or hex depending on whether either operand was hex-input.

## Why it's useful to read

The calculator is the smallest non-trivial program in the upstream repo that exercises macros from every STL submodule. Reading it end to end is the fastest way to internalise how `bit.*`, `hex.*`, `stl.fcall`/`stl.fret`, and the I/O wrappers compose into a real program.

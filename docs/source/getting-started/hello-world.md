# Hello, World!

The smallest useful FlipJump program is three lines.

## The program

Save this as `hello.fj`:

```fj
stl.startup
stl.output "Hello, World!\n"
stl.loop
```

Run it:

```sh
fj hello.fj
```

Output:

```
Hello, World!
```

That's it. No headers, no `main`, no imports — the standard library is implicitly available because the `fj` tool includes it.

```{note}
`fj hello.fj` both **assembles** and **runs** the program. To assemble only (writing a `.fjm` binary), use `fj -a hello.fj`. To run an already-assembled binary, use `fj -r hello.fjm`.
```

## What just happened

Three macro calls, each from the standard library:

```fj
stl.startup
```

Initialises the `IO` opcode address (see [Input / Output](../language/io.md)). This is the lightest startup variant — enough for output-only programs. Heavier variants (`stl.startup_and_init_pointers`, `stl.startup_and_init_all`) also set up pointer tables, hex truth tables, and the stack — needed when you use the `bit.pointers.*` / `hex.*` / stack-based macros. See [Anatomy](anatomy.md#startup-variants).

```fj
stl.output "Hello, World!\n"
```

A loop that converts each character of the string to its 8-bit ASCII code, then flips the IO opcode 8 times (LSB first) to emit one byte to stdout. It expands to roughly `13 chars * 8 bits/char * ~3 ops/bit = ~300` FlipJump operations.

```fj
stl.loop
```

The halt. Expands to `;$ - dw` — a self-loop on the current instruction whose flip address is `0` (outside the instruction body), which is the FlipJump runtime's halt condition.

```{tip}
Want to skip the local install? Paste the same three lines into the [FlipJump IDE](https://fj.tomhe.app) and click Run. The IDE runs the exact same assembler + interpreter (the real `fj` toolchain) for you.
```

## Variations

**Print a number in decimal**: notice that the variable `x` is declared as a DATA LABEL *after* `stl.loop`, not inline with the code. FlipJump variables are regions of program memory the code reads via self-modifying jumps — they have to sit outside the executable path.

```fj
stl.startup
bit.print_dec_uint 32, x
stl.loop

x: bit.vec 32, 12345
```

**Echo a hex digit from stdin**: same pattern — variable below the halt.

```fj
stl.startup
hex.input_hex input_buf
hex.output input_buf
stl.loop

input_buf: hex.hex
```

(The exact STL macro signatures may change between releases; the auto-generated per-macro pages under [Standard Library](../stl/index.md) always reflect the pinned upstream version.)

## What's next

Read [Anatomy of a FlipJump program](anatomy.md) to understand the broader structure — when to call which `startup_*` macro, how memory gets laid out, and the conventions you'll see across STL macros.

Or jump straight into the [Standard Library](../stl/index.md) to browse what's available.

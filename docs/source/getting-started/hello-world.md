# Hello, World!

The smallest useful FlipJump program is three lines.

## The program

Save this as `hello.fj`:

```fj
stl.startup_and_init_all
stl.output "Hello, World!\n"
stl.loop
```

Run it:

```sh
fj hello.fj --run
```

Output:

```
Hello, World!
```

That's it. No headers, no `main`, no imports — the standard library is implicitly available because the `fj` tool includes it.

## What just happened

Three macro calls, each from the standard library:

```fj
stl.startup_and_init_all
```

Initialises everything the STL needs: the `IO` opcode address (see [Input / Output](../language/io.md)), the pointer tables that `bit.pointers.*` uses, the hex lookup tables that `hex.*` uses, and the stack. Every program starts with this (or with a lighter `stl.startup`-family call if you only need a subset).

```fj
stl.output "Hello, World!\n"
```

A loop that converts each character of the string to its 8-bit ASCII code, then flips the IO opcode 8 times (LSB first) to emit one byte to stdout. It expands to roughly `13 chars * 8 bits/char * ~3 ops/bit = ~300` FlipJump operations.

```fj
stl.loop
```

The halt. Expands to `;$ - dw` — a self-loop on the current instruction whose flip address is `0` (outside the instruction body), which is the FlipJump runtime's halt condition.

```{tip}
Want to skip the local install? Paste the same three lines into the [FlipJump IDE](https://fj.tomhe.app) and click Run. The IDE runs the exact same assembler + interpreter compiled to WebAssembly.
```

## Variations

**Echo input back as output:**

```fj
stl.startup_and_init_all

hex.hex input_buf
hex.input_hex input_buf
hex.output input_buf

stl.loop
```

**Print a number in decimal:**

```fj
stl.startup_and_init_all

bit.bit_vec 32, x, 12345
bit.print_dec_uint 32, x

stl.loop
```

(The exact STL macro signatures may change between releases; the auto-generated per-macro pages under [Standard Library](../stl/index.md) always reflect the pinned upstream version.)

## What's next

Read [Anatomy of a FlipJump program](anatomy.md) to understand the broader structure — when to call which `startup_*` macro, how memory gets laid out, and the conventions you'll see across STL macros.

Or jump straight into the [Standard Library](../stl/index.md) to browse what's available.

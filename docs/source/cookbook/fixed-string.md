# Define and print a string variable

## Problem

Store a string in data memory and print it from multiple call sites (or modify it at runtime).

## Code

```fj
stl.startup

bit.print_str 20, greeting
bit.print_str 20, greeting

stl.loop

greeting: bit.str "Hello, World!\n"
```

## Walkthrough

- `bit.str "..."` is the assembly-time form for building a string variable. It allocates enough memory for the string's bytes plus a trailing null and initialises the bits accordingly.
- `bit.print_str n, addr` reads bytes from `addr` and prints them, stopping at either `n` bytes or the first null byte (whichever comes first). The `n` is a safety cap — set it to "maximum string length you'll ever store here".

The same `greeting` data is read twice in the program above; FlipJump's "variable" is just a region of bits the code knows how to read via self-modifying jumps.

## Variations

**Strings of different lengths in the same program**: each `bit.str` declaration is independent, with its own size:

```fj
short: bit.str "ok\n"
long:  bit.str "this is a longer message with more bytes\n"
```

**Modify the string at runtime**: use `bit.mov` to copy a character into the buffer, OR use the higher-level `bit.bin2ascii` / `bit.dec2ascii` macros to fill positions from numeric values.

## See also

- [`bit.str`](../stl/bit/casting/str--1.md), [`bit.print_str`](../stl/bit/output/print_str--2.md)
- [`bit.mov`](../stl/bit/memory/mov--3.md)

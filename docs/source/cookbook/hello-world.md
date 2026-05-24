# Hello, World!

## Problem

Print a literal string to stdout.

## Code

```fj
stl.startup
stl.output "Hello, World!\n"
stl.loop
```

## Walkthrough

- `stl.startup` initialises just the I/O opcode — the cheapest startup. Output-only programs don't need pointer tables or the hex truth tables, so the heavier `stl.startup_and_init_pointers` / `stl.startup_and_init_all` would be overkill.
- `stl.output "..."` expands the string at assembly time into a sequence of bit-flips at the I/O opcode address. One byte = 8 ops; this 14-character string is roughly 112 ops.
- `stl.loop` halts the machine by jumping to itself with a flip-address of `0` (outside the instruction's body), which is the runtime's halt condition.

## Variations

**Print a string variable** — useful when the string is built dynamically:

```fj
stl.startup
bit.print_str 20, msg
stl.loop

msg: bit.str "Hello, World!\n"
```

The `20` is the maximum bytes to scan; `bit.print_str` stops at the first null byte.

**Add a smiley** (the canonical upstream Hello World):

```fj
stl.startup
stl.output "Hello, World!\n(:"
stl.loop
```

## See also

- [echo-byte](echo-byte.md) — minimal input + output round-trip
- [`stl.output`](../stl/runlib/output--1.md), [`bit.print_str`](../stl/bit/output/print_str--2.md)

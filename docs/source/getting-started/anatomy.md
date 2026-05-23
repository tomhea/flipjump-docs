# Anatomy of a FlipJump program

Every non-trivial FlipJump program has the same skeleton:

```fj
stl.startup_and_init_all       // 1. initialise the runtime + STL globals

// 2. your code

stl.loop                       // 3. halt
```

The startup line is mandatory. The halt is conventional but not enforced — your code can also branch into a trap loop of its own design.

## Startup variants

The STL ships three startup macros, each progressively heavier:

| Macro | Initialises | When to use |
|---|---|---|
| [`stl.startup`](../stl/_generated/file--runlib.md) | only the `IO` opcode | output only; no pointers, no hex |
| [`stl.startup_and_init_pointers`](../stl/_generated/file--runlib.md) | IO + bit/hex pointer tables | when you use `bit.pointers.*` or `hex.pointers.*` |
| [`stl.startup_and_init_all`](../stl/_generated/file--runlib.md) | IO + pointers + hex truth tables + stack | the safe default; what tutorials use |

`stl.startup_and_init_all` is ~7000 operations on a default-width build but only runs once. Use it unless you have a specific reason not to.

## Memory layout (informal)

```
0                          IP starts here
2*w                        IO opcode (set up by stl.startup → label `IO`)
3*w + #w                   input bit slot (runtime auto-loads here)
…
your code + STL expansions
…
hex lookup tables          if startup_and_init_all was called
stack                      if startup_and_init_all was called
```

Most user code doesn't manipulate absolute addresses directly — the STL's macros encapsulate the layout. You'll only see explicit addresses if you write a new STL macro or tune a hot path.

## Variable conventions

A FlipJump "variable" is a region of program memory that the code reads via self-modifying jumps. The STL has two competing systems:

- **Bit variables** — defined via `def bit_var @ x { x: .bit }`. One bit per variable; ops are simple but each takes O(1) FlipJump operations.
- **Hex variables** — defined via `def hex_var @ x { x: .hex }`. Four bits per variable; arithmetic is table-driven and runs in fewer operations per nibble.

Vector forms (`bit.vec n, value`, `hex.vec n, value`) allocate `n` consecutive variables for arrays. Both are defined inside their respective namespaces in [`bit/memory.fj`](../stl/_generated/file--bit-memory.md) and [`hex/memory.fj`](../stl/_generated/file--hex-memory.md), so the call site reads `bit.vec` / `hex.vec` — NOT `bit.bit.vec` or `hex.hex.vec`.

## Naming patterns

After reading enough STL source, you'll see consistent argument names:

| Name | Meaning |
|---|---|
| `n` | size in bits (or hex digits, depending on the macro family) |
| `dst`, `src` | destination / source address |
| `carry`, `borrow` | one-bit slot for ripple state |
| `lt`, `eq`, `gt` | three jump destinations for a comparison |
| `_local`-prefixed | a local label that shouldn't be referenced from outside |

See the per-macro pages under [Standard Library](../stl/index.md) for exact signatures.

## File structure

A FlipJump `.fj` file is just a sequence of top-level declarations, in any order:

```fj
// constants (no namespace needed)
my_const = 42

// namespaces group related definitions
ns myapp {
    def helper a { ... }
    def main {
        stl.startup_and_init_all
        .helper 5
        stl.loop
    }
}
```

The assembler resolves names by walking namespaces; you don't need to forward-declare.

## Where to go from here

- **Build something small**: an echo loop, a number printer, a state machine.
- **Read STL source**: the auto-generated macro pages link back to the upstream `.fj` files. Reading a few short macros is the fastest way to internalise the patterns.
- **Browse companion tools**:
  - [c2fj](https://github.com/tomhea/c2fj) — compile C programs to FlipJump (in-depth tour lands in v0.8)
  - [bf2fj](https://github.com/tomhea/bf2fj) — compile Brainfuck to FlipJump (in-depth tour lands in v0.8)
  - [The FlipJump IDE](https://fj.tomhe.app) — in-browser editor + compiler + runtime

# bf2fj — Brainfuck to FlipJump

[**github.com/tomhea/bf2fj**](https://github.com/tomhea/bf2fj)

A direct Brainfuck-to-FlipJump compiler with four optimisation passes. Smaller and faster than running Brainfuck on top of an interpreter implemented in FlipJump.

## Install

```sh
pip install bf2fj
```

## Run

```sh
bf2fj hello_world.bf            # generate hello_world.fj
bf2fj hello_world.bf -r         # generate AND immediately run
```

`-r` (run) shells out to the local `fj` interpreter — make sure the [main FlipJump toolchain](../getting-started/install.md) is installed too.

## Optimisations

The compiler applies four passes to the Brainfuck source before code generation:

1. **Consolidate consecutive data ops** — `+++++` becomes a single "add 5" macro call instead of five separate `+` operations.
2. **Consolidate pointer movements** — `>>>>` becomes "shift right by 4" instead of four separate `>`s.
3. **Replace zeroing loops** — the `[-]` idiom (loop subtracting 1 until zero) is detected and replaced with a direct "set to 0" operation.
4. **Combine zero+modify** — `[-]+++` (zero, then add 3) becomes a single "set to 3" operation.

The cumulative effect is large. On the BF test corpus shipped with the repo, total operation counts drop ~88% — one program went from 2,900,990 ops (naïve translation) to 337,484 ops (with all four passes).

## Useful flags

| Flag | Purpose |
|---|---|
| `-c N` / `--cells N` | Reserve `N` Brainfuck tape cells (default: enough for typical programs). |
| `-r` / `--run` | Compile then immediately run via the local `fj` interpreter. |

## Caveats

- Output is a single `.fj` file matching the input's base name.
- The compiler doesn't currently expose hooks for custom cell sizes or signed-cell semantics beyond the BF spec defaults.

## See also

- [The FlipJump IDE](ide.md) — paste the generated `.fj` and step through it.
- [Standard Library — `bit/memory.fj`](../stl/_generated/file--bit-memory.md) — the tape-cell representation bf2fj uses under the hood.

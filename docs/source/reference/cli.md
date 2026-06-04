# The `fj` command-line tool

`fj` is the FlipJump assembler **and** interpreter in one command. By default it does both: it assembles your `.fj` source files into a `.fjm` memory image and immediately runs it.

```bash
fj a.fj b.fj          # assemble a.fj + b.fj (+ the STL) and run the result
```

The command is installed as the `fj` console-script when you `pip install flipjump` — see [Installation](../getting-started/install.md).

## Usage

```
fj [--asm | --run] [arguments] files [files ...]
```

`files` is one or more `.fj` source files (or, with `--run`, a single `.fjm` file). When you pass several `.fj` files they are concatenated in order, after the standard library.

A few real invocations (from `fj`'s own help text):

```bash
fj  a.fj b.fj                                    # assemble and run
fj  a.fj b.fj  -o out.fjm                        # assemble, save out.fjm, and run
fj  code.fj  -d  -B swap_start exit_label         # assemble and debug

fj --asm  -o o.fjm a.fj  -d dir/debug.fjd         # assemble + save debug info
fj --asm  -o out.fjm a.fj b.fj  --no_stl  -w 32   # assemble, no STL, 32-bit memory

fj --run  prog.fjm                               # just run a prebuilt image
fj --run  o.fjm  -d dir/debug.fjd  -B label       # run and debug
```

## Choosing a phase

By default `fj` assembles **and** runs. These two mutually-exclusive flags pick a single phase:

| Flag | Effect |
|---|---|
| `-a`, `--asm` | Assemble only. Run-time arguments are ignored. Pair with `-o` to keep the output. |
| `-r`, `--run` | Run only. The positional argument is a `.fjm` file; assemble-time arguments are ignored. |

## Universal options

These apply in every mode:

| Option | Meaning |
|---|---|
| `files` | The `.fj` files to assemble — or, with `--run`, the `.fjm` file to run. |
| `-s`, `--silent` | Don't print assemble/run times or run statistics. |
| `-d`, `--debug [PATH]` | Debug-file path, used for breakpoints. When you both assemble and run you may pass `-d` with no path and a temporary file is used. |

## Assemble options

Ignored when `--run` is given.

| Option | Meaning |
|---|---|
| `-o`, `--outfile PATH` | Write the assembled `.fjm` to `PATH`. Without it, assembly is held in memory and (unless `--asm`) run directly. |
| `-w`, `--width WIDTH` | Memory width in bits — one of `8`, `16`, `32`, `64`. **Default `64`.** |
| `-v`, `--version VERSION` | `.fjm` format version (see [The `.fjm` binary format](fjm-format.md)). Defaults to **3 (Compressed)** when `--outfile` is given, **1 (Normal)** otherwise. |
| `-f`, `--flags FLAGS` | Default `.fjm` unpacking & running flags (integer). Default `0`. |
| `--lzma_preset N` | LZMA2 compression preset `0`–`9`, used when `version=3`. |
| `--werror` | Treat all assemble warnings as errors. |
| `--max_recursion_depth N` | Maximum macro-recursion depth the compiler allows. |
| `--no_stl` | Don't assemble/link the [standard library](../stl/index.md). You're then on your own for startup, I/O and everything else. |
| `--stats` | Show macro code-size statistics. |

## Run options

Ignored when `--asm` is given.

| Option | Meaning |
|---|---|
| `-t`, `--trace` | Print every opcode as it executes. Verbose — for the smallest programs only. |
| `--no_output` | Run the program but don't print its output. |
| `--debug-ops-list LENGTH` | On a failing run, show the last `LENGTH` executed opcodes. |
| `-b`, `--breakpoint NAME [NAME ...]` | Pause when execution reaches a label named exactly `NAME`. |
| `-B`, `--breakpoint_contains NAME [NAME ...]` | Pause when reaching any label whose name *contains* `NAME`. |

## Debugging

The `-d`/`-b`/`-B` options drive FlipJump's interactive debugger. Breakpoints are matched against label names, so they need debug information: when you assemble and run in one go, `-d` (no path) keeps it in a temporary file for you; when you split the phases, write the debug file at assemble time (`--asm -o out.fjm -d dir/debug.fjd`) and feed it back at run time (`--run out.fjm -d dir/debug.fjd -B label`).

## See also

- [Installation](../getting-started/install.md) — getting the `fj` command.
- [The `.fjm` binary format](fjm-format.md) — what `-o`, `-v` and `-f` produce.
- [Cheat sheet](cheat-sheet.md) — the language itself on one page.

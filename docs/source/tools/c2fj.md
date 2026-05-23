# c2fj — C to FlipJump

[**github.com/tomhea/c2fj**](https://github.com/tomhea/c2fj)

A C-to-FlipJump compiler that uses RISC-V as an intermediate representation.

```text
   C source   →   RISC-V   →   FlipJump   →   .fjm binary
              picolibc       opcode→macro     fj interpreter
```

## Install

```sh
pip install c2fj
sudo apt install picolibc-riscv64-unknown-elf
```

Linux only; Python 3.8–3.12 per upstream pyproject.toml. The `picolibc` apt package provides the RISC-V C library + cross-compiler.

## Run

```sh
python3 c2fj.py file.c
```

That compiles your C source through the full pipeline (C → ELF → `.fj` fragments → `.fjm`) and immediately runs it through the FlipJump interpreter. The intermediate artifacts are written to the build directory (`--build-dir` overrides where).

For multi-file C projects, drive the compilation with a Makefile. The custom linker script must define three symbols: `_stack_end`, `_sdata`, and `__heap_start`.

## How it works

1. **C → RISC-V** — uses [picolibc](https://github.com/picolibc/picolibc) as a freestanding C library, with custom syscall implementations for I/O. Special assembly patterns in picolibc trigger compiler-recognised intrinsics.
2. **RISC-V → FlipJump** — each RISC-V opcode is implemented as an optimised FlipJump macro (30–40 ops each). A jump table (`jmp.fj`) resolves dynamic addresses; memory loads/stores go through `mem.fj`.
3. **Execution** — run the resulting `.fjm` with the `fj` interpreter.

## Useful flags

| Flag | Purpose |
|---|---|
| `--breakpoints` | Insert breakpoints at C source lines for the interpreter's debugger. |
| `--single-step` | Step one FlipJump op at a time. |
| `--unify_fj` | Bundle every generated `.fj` fragment into a single file. |
| `--finish-after N` | Stop after N FlipJump operations (useful for runaway programs). |
| `--build-dir PATH` | Override where intermediate `.fj` files are written. |

## Caveats

- Programs run **much** slower than native C. Every RISC-V op becomes 30+ FlipJump ops, and every FlipJump op is two memory accesses on top of the host's actual cycle.
- Not all of libc compiles — picolibc covers the freestanding subset.
- Floating point depends on the chosen libc backend; integer-only programs are the smoothest path.

## See also

- [The FlipJump IDE](ide.md) — interactive runtime, ideal for stepping through compiled output.
- [Standard Library](../stl/index.md) — what the c2fj-generated FlipJump code relies on under the hood.

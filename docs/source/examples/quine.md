# Quine

A quine is a program that prints itself. [`programs/quine16.fj`](https://github.com/tomhea/flipjump/blob/main/programs/quine16.fj) is the FlipJump quine — and it's a particularly interesting one because of how the language defines "self".

## What "self" means here

Most quines print their source code. The FlipJump quine prints its compiled **binary** (the `.fjm` file, including the `.fjm` header struct) — verbatim, byte-for-byte. The file's own header comment is explicit:

> "I took the liberty to define a Quine for FlipJump as a binary (fjm) that prints itself (including the header struct)."

Why pick the binary? FlipJump's "source code" is ambiguous: a FlipJump program is fundamentally a stream of `(flip_address, jump_address)` pairs, and that stream can be represented as text, as packed binary, or in many other formats. The binary `.fjm` is the canonical representation that any conforming interpreter accepts, so quining the binary is the most language-invariant choice.

## Why it's notable

FlipJump is self-modifying by design — every variable is implemented by modifying its own jump addresses at runtime. The quine extends that to the whole program: by the time `stl.output` finishes, the program has read its own bytes (from program memory!) and emitted them to stdout. The "data table" of conventional quines is replaced by program memory itself.

## Try it

The upstream file's header comment shows the exact incantation:

```sh
fj --asm -w 16 quine16.fj -o quine16.fjm    # assemble (16-bit word width is required)
fj --run -s quine16.fjm > /tmp/output       # run, capture stdout
diff quine16.fjm /tmp/output                 # should produce NO output if it's truly a quine
echo "quine!"                                # confirmation
```

The `-w 16` is mandatory: the program is hand-tuned for 16-bit words, so it doesn't work at the default 64-bit width.

## The author

The FlipJump quine is by [Luis Fernando Estrozi](https://github.com/lestrozi). The source file is ~1000 lines, **most of which is comments** explaining the construction — well worth reading for anyone interested in self-reference under unusual computational models.

## See also

- [esolangs.org — Quine](https://esolangs.org/wiki/Quine) for the broader background.
- [The FlipJump Instruction](../language/instruction.md) for why self-modifying source matters in FJ in particular.

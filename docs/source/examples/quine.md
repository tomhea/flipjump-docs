# Quine

A quine is a program that prints its own source code. [`programs/quine16.fj`](https://github.com/tomhea/flip-jump/blob/main/programs/quine16.fj) is a 16-bit FlipJump quine.

## Why it's notable

FlipJump is a self-modifying language by design — every variable is implemented by modifying its own jump addresses at runtime. A quine extends this idea to the program text itself: by the time `stl.output` emits the source, the program has effectively reconstructed its own bytes from the layout the assembler chose.

The trick is the same one Lisp / C / Python quines use — a "data table" of the source, and a small piece of code that prints the data then prints itself printing the data. What's distinctive in FlipJump is that "printing yourself" means walking the IP backward over your own instruction stream and emitting each `a;b` pair as bytes.

## Layout sketch

```fj
stl.startup

// Print the literal data block first.
print_data data

// Then print the printer.
print_data printer

// Self-loop halt.
stl.loop

printer:
    // the bytes that, when fed to FlipJump's text representation,
    // reproduce the print_data calls above.

data:
    // the bytes that, when interpreted as a string, are the source
    // of `printer` plus its own bytes.
```

The actual implementation is finicky because of the encoding round-trip — getting the bytes to align so that `data` decodes to the right characters takes careful placement. See the upstream file for the working version.

## Try it

```sh
fj programs/quine16.fj > out.fj
diff programs/quine16.fj out.fj   # the diff should be empty (modulo encoding quirks)
```

Or paste into the [IDE](https://fj.tomhe.app) and run.

## See also

- [esolangs.org — Quine](https://esolangs.org/wiki/Quine) for the broader background.
- [The FlipJump Instruction](../language/instruction.md) for why self-modifying source matters in FJ in particular.

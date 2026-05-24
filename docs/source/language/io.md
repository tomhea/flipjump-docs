# Input / Output

FlipJump has no `read` or `write` instruction. I/O happens at fixed bit-addresses that the runtime watches.

## Output

Flipping a specific bit at the I/O opcode address sends one output bit to stdout. The exact address is exposed by `stl.startup` as the label `IO`:

```fj
ns stl {
    def startup code_start > IO {
        ;code_start
      IO:                       // exposed: this address IS the I/O opcode
        ;0
    }
}
```

After running `stl.startup`, the address of `IO` is known to the rest of the program. To emit a `0` bit, flip the low bit of `IO`; to emit a `1`, flip a different bit. The STL's [`stl.output_bit`](../stl/runlib/output_bit--1.md) and [`stl.output_char`](../stl/runlib/output_char--1.md) wrap the bit-flipping pattern.

Bytes are output **LSB first** by flipping eight consecutive bits in sequence.

## Input

The next input bit is automatically loaded by the runtime at the bit-address `3*w + #w` (this is `dbit + dw` from the I/O opcode). Read it by jumping based on the bit value:

```fj
.if0 input_bit, branch_for_zero, branch_for_one
```

The runtime reloads the next bit on each read. End-of-input is signalled by the input slot being permanently `0` (or by the runtime keeping the program looping until interrupted — implementations vary).

## Higher-level wrappers

User code rarely touches the IO opcode directly. The STL provides:

- Output: see the per-file page [`runlib.fj`](../stl/runlib.md) for `stl.output_bit`, `stl.output_char`, `stl.output`.
- Bit-level input/output: [`bit/input.fj`](../stl/bit/input.md) and [`bit/output.fj`](../stl/bit/output.md).
- Hex-level input/output: [`hex/input.fj`](../stl/hex/input.md) and [`hex/output.fj`](../stl/hex/output.md).

A complete "Hello, World!" program is just `stl.startup_and_init_all` + `stl.output "Hello\n"` + `stl.loop`. See the [Hello World walkthrough](../getting-started/hello-world.md) for a guided tour.

## Reference

The exact I/O addresses (`2*w` for the opcode, `3*w + #w` for the input bit) come from the upstream language design — for more depth see [esolangs.org/FlipJump#Input_/_Output](https://esolangs.org/wiki/FlipJump#Input_/_Output).

# Types and built-in names

FlipJump has no static type system. The four identifiers below are visually highlighted as "types" in the IDE and on this site, but they are actually:

- `w` — a compile-time constant set by the assembler.
- `dw`, `dbit` — assembly-time constants defined in [`runlib.fj`](../stl/_generated/file--runlib.md).
- `bit` — a namespace name (`ns bit { ... }`) and an STL convention for single-bit data.

(w)=
## `w` — word width

The width of one machine word, in bits. Set by the assembler via the `--width` flag (default 64 on most builds, sometimes 8/16/32 for testing). It is **not** declared in source.

```fj
// w = ??       // memory and operands width. Is defined at compile time.
```

Every other size constant derives from `w`.

(dw)=
## `dw` — double word

```fj
dw = 2 * w     // double word size
```

One `dw` is the size of a single FlipJump instruction (one flip address + one jump address). Addresses of consecutive instructions differ by `dw`.

(dbit)=
## `dbit` — bit distance within a variable

```fj
dbit = w + #w  // bit distance from a variable's start to its bit/hex value
```

`dbit` is the offset, within a packed STL bit-variable, between the variable's start and the bit that actually carries its value. It's `w + #w` because a bit-variable layout reserves `w` bits for an instruction header plus `#w` bits for the address offset, before the data bit itself. This shows up everywhere in the STL's pointer arithmetic.

(bit)=
## `bit` — STL convention

`bit` is not a language keyword. It serves two roles:

1. The name of the top-level namespace for bit-level STL operations: [`ns bit { ... }`](../stl/_generated/file--bit-memory.md).
2. The conventional name of a one-bit storage slot, defined as `def bit { ... }` inside that namespace.

```fj
def bit_variable @ x {
  x:
    .bit         // allocate one bit's worth of storage
}
```

The IDE colours `bit` as a plain identifier, **not** as a type — even though it sits next to `dbit`/`dw`/`w` semantically.

## Other common names

These aren't language-defined either, but they appear in many macro signatures:

- `n` — caller-supplied length, typically the number of bits or hex digits to operate on.
- `dst`, `src` — destination and source addresses (or address vectors) for memory operations.
- `carry`, `borrow` — single-bit slots for arithmetic ripple state.

See [Complexity notation](complexity.md) for what `n` and `w` mean inside STL complexity annotations.

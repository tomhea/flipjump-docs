# Complexity notation

Every STL macro page reports `Time` and `Space` complexity using the same shorthand the upstream source uses. This page is the canonical glossary — the auto-generated macro pages link back here so readers can find the meanings in one place.

## Atomic units

(complexity-at)=
### `@` — log₂ of the total program size

`@` stands for `log₂(total number of FlipJump ops in the assembled program)`. For typical programs this is between **15 and 25** (i.e. tens of thousands to tens of millions of ops total).

The reason `@` is logarithmic rather than constant:

> The fundamental directive `wflip address, value` (see [Directives](directives.md)) has a runtime cost proportional to the **number of set bits in `address`** — because it emits one bit-flip per set bit. Address widths in FlipJump are `log₂(program_size)` bits, so the average `wflip` is `log₂(program_size) / 2` ops (as bits are set half of the time), i.e. `@/2`. Because `wflip` is the building block underneath almost every STL macro (every variable read, every conditional, every arithmetic operation chains multiple `wflip`s), the per-op cost of the STL is naturally measured in `@`-units rather than constant ops.

So an annotation of `4@+12`:
- `4@` ≈ `4 * log₂(N)` ops where `N` is the total program size — for a typical 20-bit program that's `4 * 20 = 80` ops
- `+12` is a constant overhead of 12 ops
- Total: ~92 runtime ops for one invocation

A macro that's annotated `@-1` runs in roughly `@` ops too, since the `-1` is dwarfed by `@`.

```text
Complexity: 1     →  1 op (constant; no wflip on the hot path)
Complexity: @     →  two wflips; ~log₂(N) ops
Complexity: 4@    →  ~4·log₂(N) ops
```

`@` is dimensionless from the language's perspective — it captures "this macro is dominated by `wflip`s" without committing to a specific program size. On a real FlipJump implementation, one `@` is "a handful of nanoseconds" for typical program sizes.

(complexity-w)=
### `w` — word width

The machine word width in bits, set at assembly time. See [Types](types.md). Used in complexity to express size-dependent costs:

```text
Time: w@+5     →  w ops + 5
Space: w@+12   →  w ops worth of generated code, plus 12 ops of fixed setup
```

(complexity-dw)=
### `dw` — double word

`2 * w`. See [Types](types.md). Appears when a cost is proportional to the size of a single instruction.

(complexity-dbit)=
### `dbit` — bit distance within a variable

`w + #w`. See [Types](types.md). Appears in complexities of pointer macros where the cost depends on traversing a variable layout.

(complexity-n)=
### `n` — caller-supplied length

Whenever a macro takes a parameter named `n` (or `n_const`, `n_dst`, etc.), the complexity uses that letter to express the cost.

```text
Time: n(4@+12)        →  n iterations of (4@+12) each
Time: n²(2@+8)        →  quadratic in n (used in division)
```

## Compound forms

### `k@+c` — linear in operations plus constant

The most common form. `k@` is the per-iteration cost; `c` is the fixed setup overhead.

| Annotation | Meaning |
|------------|---------|
| `2@+5` | 2 ops + 5 ops of setup = 7 ops total |
| `4@+12` | 4 ops + 12 ops of setup |
| `8@+14` | bit-level add — see [`bit.add1`](../stl/bit/math/add1--3.md) |

### `n(...)` — repeated per element

When a macro operates on an `n`-element vector, the cost is the per-element cost in parens, repeated `n` times.

```text
n(4@+12)    →  per element: 4@+12. Total: 4n ops + 12n setup
```

### `~k` — approximate

A leading `~` means the value is approximate, often because the cost depends on a parameter not visible in the signature. E.g. `~7000` for `stl.startup_and_init_all/0` is "about 7000 ops on a default-width build".

### Composite expressions

Complexities can mix forms:

```text
n²(2@+8) + n*nb(34@+92)    →  hex.div: quadratic in n plus a cross term
6725 + 2.75w+@ + n         →  large constant plus a w-scaled plus n scan
```

These show up in the STL's heavier macros (div, mul, the table-driven hex ops). The exact constants come from counting ops in the macro's expansion.

## How to read a macro page's complexity

A page that says:

```text
Time: n(4@+12)
Space: n(2.5@+39) + 4@+28
```

means: for an input of length `n`, the macro executes `n * (4@ + 12)` ops at runtime, and the macro **expansion** itself emits `n * (2.5@ + 39) + 4@ + 28` worth of FlipJump operations at assembly time.

Time and Space differ because FlipJump pays for both: every emitted op takes program-memory space, and the runtime cost is what actually executes.

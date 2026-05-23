# Complexity notation

Every STL macro page reports `Time` and `Space` complexity using the same shorthand the upstream source uses. This page is the canonical glossary — the auto-generated macro pages link back here so readers can find the meanings in one place.

## Atomic units

(complexity-at)=
### `@` — one FlipJump operation

`@` is the cost of executing one flip-jump op (`a;b`). It is the smallest unit of measure. A macro with complexity `4@` performs four flip-jump operations.

```text
Complexity: 1     →  1 op
Complexity: 4@    →  4 ops
Complexity: @     →  shorthand for 1@ (one op)
```

`@` is dimensionless from the language's perspective — it expresses "how many primitive operations" rather than wall-clock time. On a real FlipJump implementation, one `@` typically takes a few nanoseconds.

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
| `8@+14` | bit-level add — see [`bit.add1`](../stl/_generated/macro--bit.add1--3.md) |

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

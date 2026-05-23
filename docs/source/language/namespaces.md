# Namespaces

A namespace groups related macros, constants, and nested namespaces. Defined with `ns`:

```fj
ns stl {
    def loop {
        ;$ - dw
    }
}
```

Inside the block, all `def`s, `ns`s, and constants belong to the enclosing path. The example above defines `stl.loop`.

## Nesting

Namespaces nest naturally:

```fj
ns hex {
    ns pointers {
        def write_hex { ... }       // fully qualified: hex.pointers.write_hex
    }
}
```

## Dotted access

Outside the defining namespace, use the full dotted path:

```fj
stl.startup                    // unambiguous, absolute
hex.pointers.write_hex
```

Inside a namespace, references resolve in the order:

1. **Leading dot** (`.name`) — current namespace.
2. **Leading double-dot** (`..name`) — parent namespace.
3. **Absolute** (`top.middle.leaf`) — searched from the root.
4. **Bare word** (`name`) — current namespace first, then ancestors, then global.

```fj
ns hex {
    def helper {}

    ns add {
        def step1 { ..helper }          // ..helper = hex.helper
        def step2 { .helper }           // .helper = hex.add.helper (not the outer one!)
        def step3 { hex.helper }        // absolute
        def step4 { helper }            // bare: tries hex.add.helper, then hex.helper, then helper
    }
}
```

The single-dot semantics catch newcomers off guard: `.helper` inside `hex.add` means `hex.add.helper`, **not** `hex.helper`. Use `..helper` (one extra dot) to reach the parent.

## Same namespace, multiple blocks

A namespace may be re-opened with another `ns name { ... }` block. The contents merge.

```fj
ns hex {
    def add dst, src { ... }
}

ns hex {                            // re-opens; doesn't replace
    def sub dst, src { ... }
}
```

Both `hex.add` and `hex.sub` exist after the assembler sees both blocks. This pattern is used throughout the STL to group related macros across header sections within a single file.

## Top-level (no namespace)

Constants like [`dw`](types.md) and [`dbit`](types.md) live at the top level in `runlib.fj`, outside any `ns` block. They are referenced bare from anywhere:

```fj
dw   = 2 * w
dbit = w + #w
```

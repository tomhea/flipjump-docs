# Macros

A macro is a reusable assembly-time code template, defined with `def`:

```fj
def NAME ARGS [@ LOCALS] [< REQUIRES] [> EXPORTS] {
    body...
}
```

All four of `ARGS`, `@ LOCALS`, `< REQUIRES`, `> EXPORTS` are optional. The body is bracketed code that may contain instructions, other macro calls, labels, `rep`, and nested `def`s.

## Parameters

A simple parameterised macro:

```fj
def fj f, j {
    f;j         // expand to one flip-jump op with the caller's addresses
}
```

Call sites pass arguments space- or comma-separated:

```fj
stl.fj  1000, 256
```

## `@ LOCALS` — auto-named labels

`@ name` declares one or more **local labels** the macro can reference. The assembler renames them at each call site so two invocations don't collide.

```fj
def startup @ code_start {
    stl.startup code_start
  code_start:                  // a local label
}
```

## `< REQUIRES` — labels that must exist in the caller

`< .name, .other_name` declares external labels the macro will reference. These are typically dotted names that resolve in the caller's namespace.

```fj
ns hex {
    def add dst, src < .add.dst {
        .tables.jump_to_table_entry dst, src, .add.dst
    }
}
```

The `<` clause is documentation-as-code: it tells human readers and the dependency graph what outer state the macro depends on.

## `> EXPORTS` — labels the macro exposes to the caller

`> name` declares a local label that the **caller** can reference from outside.

```fj
def startup code_start > IO {
    ;code_start
  IO:                       // exposed: outer code can use `IO` after invoking this macro
    ;0
}
```

`stl.startup` exports `IO` — that's how programs know the address of the I/O opcode after calling it (see [Input / Output](io.md)).

## Arity overloading

A name can be defined multiple times with different parameter counts. The assembler picks the matching arity at each call site.

```fj
ns stl {
    def wflip_macro dst, val {           // arity 2
        wflip dst, val
    }
    def wflip_macro dst, val, jmp_addr { // arity 3
        wflip dst, val, jmp_addr
    }
}
```

Both definitions of `stl.wflip_macro` coexist; `stl.wflip_macro 0x100, 0x42` picks the 2-arg version, `stl.wflip_macro 0x100, 0x42, 0x80` picks the 3-arg version. The STL has several macros with multiple overloads — see e.g. [`stl.startup`](../stl/_generated/macro--stl.startup--0.md).

## Repetition: `rep(n, var) body`

`rep(n, i)` expands its body `n` times with `i` bound to `0, 1, ..., n-1`:

```fj
def add n, dst, src {
    rep(n, i) .add1 dst + i*dw, src + i*dw
}
```

`n` and `i` are both assembly-time expressions. `n` must evaluate to a constant.

## Comments inside bodies

Bodies can contain `//` line comments at any position:

```fj
def startup code_start > IO {
    ;code_start    // 0w;1w : first code to run
  IO:
    ;0             // 2w;3w : sets the io_handler to address 0
}
```

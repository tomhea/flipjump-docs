# Hello World

The complete program — three lines:

```fj
stl.startup
stl.output "Hello, World!\n"
stl.loop
```

[View on GitHub](https://github.com/tomhea/flip-jump/blob/main/programs/print_tests/hello_world.fj).

For a line-by-line walk-through see the [Getting Started tutorial](../getting-started/hello-world.md).

## Variant: using a pre-built string variable

The upstream `hello_world_with_str.fj` example builds the string in a separate data label, then prints it via `bit.print_str`:

```fj
    stl.startup

    bit.print_str 20, str
    stl.loop

  str:
    bit.str "Hello, World!\n(:"
```

[View on GitHub](https://github.com/tomhea/flip-jump/blob/main/programs/print_tests/hello_world_with_str.fj).

This pattern (string as data label, length passed at the call site) is the same one you use for any fixed-length-buffer output. The `20` is the maximum bytes to scan — `bit.print_str` stops at the first null byte.

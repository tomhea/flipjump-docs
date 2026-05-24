# Call a function

## Problem

Factor a piece of code into a reusable routine, like a function call in a normal language.

## Code

```fj
stl.startup_and_init_all

stl.fcall greet, ret_addr
stl.fcall greet, ret_addr
stl.loop

greet:
    stl.output "hi!\n"
    stl.fret ret_addr

ret_addr: bit.vec w
```

Output:
```
hi!
hi!
```

## Walkthrough

- `stl.startup_and_init_all` — `stl.fcall`/`stl.fret` use the stack, so we need the full init.
- `stl.fcall target, ret_addr` — saves the return address into `ret_addr`, then jumps to `target`. On return the runtime jumps back to whatever was saved.
- `stl.fret ret_addr` — jumps to the address stored in `ret_addr`.

Note: `ret_addr` is a `bit.vec w` (one word wide — enough to hold a code address). One return slot per call site, NOT a stack of return addresses. For recursive or re-entrant calls you'd need to push/pop the return address onto a real stack.

## Variations

**Recursive calls** require a stack. See [`stl.stack_init`](../stl/ptrlib/stack_init--1.md) + [`hex.pointers.push_ret_address`](../stl/hex/pointers/stack/push_ret_address--1.md) — the upstream `calc.fj` example uses this pattern.

**Passing arguments** — FlipJump has no calling convention. The conventional pattern is to declare a parameter variable, write into it before `fcall`, and have the callee read it:

```fj
// caller
bit.mov w, arg_buf, my_value
stl.fcall print_value, ret_addr

// callee
print_value:
    bit.print_dec_uint w, arg_buf
    stl.fret ret_addr

arg_buf:  bit.vec w
ret_addr: bit.vec w
```

## See also

- [`stl.fcall`](../stl/ptrlib/fcall--2.md), [`stl.fret`](../stl/ptrlib/fret--1.md)
- The upstream [`calc.fj`](https://github.com/tomhea/flip-jump/blob/main/programs/calc.fj) — a real REPL using these primitives.

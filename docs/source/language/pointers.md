# Pointers, stacks & functions

FlipJump's one instruction has no `call`, no `return`, no stack pointer, and no notion of "the address in this variable." Yet real FlipJump programs do recursion, dynamic data structures and reusable routines. They get there with three layered ideas — **pointers**, a **stack**, and a **calling convention** — all built in the standard library's [`ptrlib`](../stl/ptrlib.md). This page explains how they fit together; the per-macro pages have the exact signatures.

## What a pointer is

A *direct* reference names an address at assemble time: `bit.mov w, dst, src` knows where `src` lives. A **pointer** is a variable that *holds* an address, only known at run time. Dereferencing it — reading or writing the memory it points at — is the hard part, because FlipJump can only change the world by flipping bits whose positions are fixed in the code.

The trick is the same self-modifying-code pattern that powers the whole STL (see [How the STL works](../reference/how-the-stl-works.md)): a precomputed dispatch table. `stl.ptr_init` lays down a `read_ptr_byte_table` (it must sit right after startup, at address 256) plus the bit-level tables:

```fj
ns stl {
    def ptr_init {
        hex.pointers.ptr_init
        bit.pointers.ptr_init
    }
}
```

To dereference, the pointer macros index into that table with the pointer's hex digits and emit the right flips. That indirection is why pointer operations cost roughly an order of magnitude more than direct ones — and why a program that uses pointers must run a heavier startup. The usual choice is [`stl.startup_and_init_all`](../stl/runlib.md), which sets up I/O, the pointer tables **and** a stack in one go.

## The stack

`ptrlib` keeps a single global stack with a stack-pointer, `sp`. You size it once at assemble time:

```fj
ns stl {
    // Initializes a stack of size n (capacity of n hexes / return-addresses).
    def stack_init n {
        hex.pointers.stack_init n
    }
}
```

The primitives are the ones you'd expect — [`hex.push`](../stl/hex/pointers/stack/push--2.md) / [`hex.pop`](../stl/hex/pointers/stack/pop--2.md), `sp_add` / `sp_sub` to move the pointer, and [`get_sp dst`](../stl/ptrlib/get_sp--1.md) to copy `sp` into a variable. Because `n` is the storage budget for both data and saved return-addresses, give recursive programs enough headroom.

## The calling convention

FlipJump has no fixed calling convention, so `ptrlib` defines one. There are two flavours.

**Stack-based — reentrant and recursive.** [`stl.call`](../stl/ptrlib/call--1.md) pushes the return address onto the stack, jumps to the routine, and on return pops it back off:

```fj
ns stl {
    def call address @ return_label {
        hex.push_ret_address return_label
        ;address

        pad 2
      return_label:
        hex.pop_ret_address return_label
    }
}
```

A second form, `call address, params_stack_length`, additionally pops that many parameter cells off the stack after returning. The routine ends with [`stl.return`](../stl/ptrlib/return--0.md), which jumps to the address on top of the stack. Because each call's return address lives on the stack, this convention is safe for recursion.

**Register-based — cheaper, non-reentrant.** When a routine never recurses, you can skip the stack entirely. [`stl.fcall target, ret_reg`](../stl/ptrlib/fcall--2.md) stores the return address directly into a one-word variable, and [`stl.fret ret_reg`](../stl/ptrlib/fret--1.md) jumps back to it:

```fj
stl.startup_and_init_all

stl.fcall greet, ret_addr
stl.loop

greet:
    stl.output "hi!\n"
    stl.fret ret_addr

ret_addr: bit.vec w
```

`ret_addr` is a single `bit.vec w` — one return slot per call site, *not* a stack. That's the whole difference: `fcall`/`fret` are faster but can't be re-entered; `call`/`return` carry the return address on the stack and can. For a worked example, passing arguments included, see the [Call a function](../cookbook/function-call.md) recipe.

## Putting it together

1. Run `stl.startup_and_init_all` (or `startup_and_init_pointers` + your own `stack_init`) so the pointer tables and stack exist.
2. Use direct moves where the address is known; reach for pointers only when it isn't.
3. Pick `fcall`/`fret` for flat helper routines, `call`/`return` for anything recursive or reentrant.

## See also

- [Call a function](../cookbook/function-call.md) — the calling convention as a runnable recipe.
- [Swap two variables](../cookbook/swap-two-variables.md) — direct references, for contrast.
- [How the STL works](../reference/how-the-stl-works.md) — why dereferencing needs precomputed tables.
- [`ptrlib`](../stl/ptrlib.md) — every pointer, stack and function macro, auto-documented.
- [Anatomy of a program](../getting-started/anatomy.md) — where startup and init fit in a real file.

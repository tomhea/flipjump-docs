# Prime Sieve

[`programs/prime_sieve.fj`](https://github.com/tomhea/flipjump/blob/main/programs/prime_sieve.fj) computes all primes up to a user-supplied N using the sieve of Eratosthenes, optimised to only test 6k±1 candidates.

## The shape

```fj
hw = w/4
PRIMES_MEMORY_START = (1 << (w-1))
PRIMES_MEMORY_LENGTH = (1 << (w-1))
FIRST_PRIME = 5

prime_sieve_main

segment PRIMES_MEMORY_START
    reserve PRIMES_MEMORY_LENGTH    // sieve table — zeroed by `reserve`

def prime_sieve_main {
    stl.startup_and_init_all
    input_max_prime n, primes_ptr_n
    // ...
  prime_loop_if:
    hex.cmp hw, p, n, prime_loop, prime_loop, end
  prime_loop:
    if1_ptr primes_ptr, next_prime
    print_int hw, p
    hex.inc hw, num_of_primes
    mark_primes mark_primes_ptr, primes_ptr_n, is_add_4, p_2dw_offset, p_4dw_offset
  next_prime:
    set_full_next_prime p, primes_ptr, mark_primes_ptr, p_2dw_offset, p_4dw_offset, is_add_4
    is_add_4+dbit; prime_loop_if
  end:
    stl.output NUMBER_OF_PRIMES_MESSAGE
    print_int hw, num_of_primes
    stl.loop
}
```

## What's interesting

- **Top-level constants** (`hw`, `PRIMES_MEMORY_START`, etc.) define memory layout at compile time. Different `w` (word width) values give different memory budgets.
- **`segment` + `reserve`** allocate a sparse memory region for the sieve table at a fixed high address, separate from the code region.
- **`stl.startup_and_init_all`** is needed (not just `stl.startup`) because the program uses hex pointers and arithmetic — those subsystems need their lookup tables initialised first.
- **`hex.cmp` three-way branch** drives the outer loop: jump to `prime_loop` if `p < n` or `p == n`, jump to `end` if `p > n`.
- **`if1_ptr`** is the conditional dereference: jump to `next_prime` if the sieve table's bit at the current pointer is set.

## Run it

In the [IDE](https://fj.tomhe.app), pick the "Prime Sieve" sample, type a number like `100`, and watch the primes scroll past in real time (assembled). Or locally:

```sh
fj programs/prime_sieve.fj
```

The default 64-bit build sieves up to a few million in a few seconds; smaller word widths cap memory accordingly.

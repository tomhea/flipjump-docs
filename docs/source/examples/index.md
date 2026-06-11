# Examples

A short tour of real FlipJump programs. Each links to the upstream source in the [`tomhea/flip-jump`](https://github.com/tomhea/flipjump/tree/main/programs) repo's `programs/` directory — paste any of them into the [IDE](https://fj.tomhe.app) to try them in seconds.

```{toctree}
:maxdepth: 1

hello-world
prime-sieve
calculator
quine
```

## At a glance

| Example | Lines | Demonstrates |
|---|---:|---|
| [Hello World](hello-world.md) | 3 | minimal output |
| [Prime Sieve](prime-sieve.md) | 322 | algorithm, pointers, decimal I/O |
| [Calculator](calculator.md) | 246 | parser, conditionals, error handling |
| [Quine](quine.md) | 1031 | self-printing FlipJump binary (mostly commentary explaining how it works) |

The upstream repo's [`programs/`](https://github.com/tomhea/flipjump/tree/main/programs) directory has more — multi-file compilation tests, function-call demos, hex arithmetic stress tests. They double as the test corpus that proves a FlipJump release works.

Since flipjump 1.4.0 there's also a [demonstration catalog](https://github.com/tomhea/flipjump/tree/main/programs/catalog) of 1029 small, self-contained, fully-tested programs across 30 categories — arithmetic, strings, state machines, puzzles, simulations and more. It's the best place to find a short working program that does something close to what you're trying to write.

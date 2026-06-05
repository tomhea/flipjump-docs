# flip-jump — the upstream language repo

[**github.com/tomhea/flip-jump**](https://github.com/tomhea/flip-jump)

```{button-link} https://github.com/tomhea/flip-jump
:color: primary
:expand:

🐙 Open the repository
```

The canonical home of the FlipJump language: the assembler, the interpreter, the standard library that this site auto-documents, example programs, the test suite, and the GitHub wiki.

## What lives there

| Directory | Contents |
|---|---|
| [`flipjump/assembler/`](https://github.com/tomhea/flip-jump/tree/main/flipjump/assembler) | The `fj` assembler — turns `.fj` source into `.fjm` binaries |
| [`flipjump/interpreter/`](https://github.com/tomhea/flip-jump/tree/main/flipjump/interpreter) | The runtime that executes `.fjm` binaries |
| [`flipjump/stl/`](https://github.com/tomhea/flip-jump/tree/main/flipjump/stl) | The standard library — source for every macro on this site |
| [`programs/`](https://github.com/tomhea/flip-jump/tree/main/programs) | Real example programs: hello world, prime sieve, calculator, quine |
| [`tests/`](https://github.com/tomhea/flip-jump/tree/main/tests) | The test suite that proves a release works |

## What to do there

- **Read the standard-library source** — every macro page on this site links back to its `.fj` source. Reading two or three short macros side-by-side with their rendered docs is the fastest way to internalise the patterns.
- **File issues** — bugs in the language, missing macros, doc gaps. Issues here also drive what eventually shows up in this docs site.
- **Send PRs** — adding a macro to the STL, fixing an interpreter bug, improving the test suite. Doc PRs for THIS site go to [`tomhea/flipjump-docs`](https://github.com/tomhea/flipjump-docs) instead.
- **Browse the wiki** — [the GitHub wiki](https://github.com/tomhea/flip-jump/wiki) has the original "Learn FlipJump" tutorial that bootstrapped most of this site's language reference.

## Releases

Latest tagged release is visible at [github.com/tomhea/flip-jump/releases](https://github.com/tomhea/flip-jump/releases). This docs site pins a specific upstream commit via a git submodule; a weekly automated job bumps the pin and surfaces upstream STL changes as a PR for review.

## See also

- [The FlipJump IDE](ide.md) — a browser-based editor that runs this repo's toolchain on the server and streams the output back.
- [esolangs.org/FlipJump](esolangs.md) — the language's entry on the esolangs wiki.
- [Standard Library reference](../stl/index.md) — auto-generated from this repo's `flipjump/stl/`.

# FlipJump Claude Skill

`flipjump-dev` is a [Claude skill](https://docs.claude.com/en/docs/claude-code/skills) that teaches Claude Code (and any Claude Agent SDK harness) to write, debug, assemble, and run FlipJump programs correctly the first time.

It lives in its own repo, [`tomhea/skills`](https://github.com/tomhea/skills), and installs as a Claude Code plugin — so it stays up to date automatically instead of you re-downloading a bundle.

## What it does

The skill is small and read-on-demand: it activates whenever you mention FlipJump, `.fj` files, the standard library, or any of its macros. Once active, Claude:

- **Routes to the docs** — fetches macro signatures, syntax, and recipes from this site rather than guessing them, instead of inventing macro names that don't exist.
- **Knows the gotchas** — the memory model's `*dw` stride, the two byte encodings, init-macro dependencies, and why `addr;` IS the flip operation (not a no-op).
- **Picks the right namespace** — when to reach for `bit.*` vs `hex.*`, and the bit-vs-hex size/speed tradeoff.
- **Verifies before declaring done** — runs every program through the `fj` CLI and confirms it halts cleanly with byte-accurate output, instead of staring at the source and hoping.

It deliberately does *not* duplicate the macro catalogue or the cookbook — it points Claude at this site for the exact spelling of any macro, which is what this site is for.

## Install

The skill ships in the `flipjump` plugin on the `tomhe` marketplace. From inside Claude Code:

```text
/plugin marketplace add tomhea/skills
/plugin install flipjump@tomhe
```

Then make sure the `fj` toolchain the skill drives is on your `PATH`:

```bash
pip install flipjump
```

Restart Claude Code if it was already running. The skill activates the next time you mention FlipJump.

## Use it

Just talk about FlipJump — the skill activates on its own. Open a `.fj` file, ask Claude to "write a FlipJump program that …", or mention an STL macro, and it kicks in. You can also point Claude at it explicitly by asking it to use the `flipjump-dev` skill.

From there Claude orients to the one-instruction language, fetches what it needs from this site, writes the program, and runs it through `fj` before telling you it's done.

## Source

The skill is developed at [`tomhea/skills`](https://github.com/tomhea/skills) (MIT licensed). Bug reports and improvements are welcome there.

## Related

- [Getting Started — Install](../getting-started/install.md) — install the `fj` toolchain the skill drives.
- [Cookbook](../cookbook/index.md) — the recipes the skill points Claude at.
- [How the STL Works](../reference/how-the-stl-works.md) — the conceptual model the skill compresses into a few sentences.

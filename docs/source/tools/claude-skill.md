# FlipJump Claude Skill

```{button-link} ../_static/writing-flipjump-stl-code.zip
:color: primary
:expand:
:tooltip: Download the skill bundle (SKILL.md + reference/)

⬇ Download `writing-flipjump-stl-code.zip`
```

## What it is

A [Claude skill](https://docs.claude.com/en/docs/claude-code/skills) that teaches Claude Code (and any Claude Agent SDK harness) to write, debug, assemble, and run FlipJump programs correctly the first time.

The skill is small and read-on-demand: it activates whenever the user mentions FlipJump, `.fj` files, the standard library, or any of its macros. Once active, Claude orients to the one-instruction language, fetches macro signatures from this site rather than guessing them, and runs every program through the `fj` CLI before declaring it done.

## What's in the bundle

| File | Purpose |
|---|---|
| `SKILL.md` | Main entry. Orientation, the bit-vs-hex tradeoff, memory model, doc-comment vocabulary, idioms, the verification loop, and a routing table for the rest of this site. |
| `reference/docs-map.md` | The full fast-routing map: every fjdocs section paired with its GitHub source path and a one-line "what does this answer" note. |
| `reference/fj-tool.md` | Exact `fj` CLI usage — install, assemble + run, debug flags, plus a clearly-marked-optional section on the upstream pytest infrastructure. |

Three files, ~420 lines total.

## Install

1. Download the [zip](../_static/writing-flipjump-stl-code.zip).
2. Unzip into your Claude skills directory:

   ```bash
   # Linux / macOS
   unzip writing-flipjump-stl-code.zip -d ~/.claude/skills/

   # Windows (PowerShell)
   Expand-Archive writing-flipjump-stl-code.zip -DestinationPath $env:USERPROFILE\.claude\skills\
   ```

   The bundle's internal layout (`writing-flipjump-stl-code/SKILL.md` + `writing-flipjump-stl-code/reference/...`) puts everything in the right place automatically.

3. Restart Claude Code (or whichever Claude Agent SDK runtime you use). The skill becomes available the next time the user mentions FlipJump.

## What it covers (and what it deliberately doesn't)

It covers the things this site can't teach a fresh Claude in 30 seconds: which init macro a program needs, why `addr;` IS the flip operation (not a no-op), how `bit`, `hex`, and "byte" all share the same address footprint, when to reach for the `bit.*` vs `hex.*` namespace, and the verification loop that catches subtle mistakes by running the code instead of staring at it.

It does NOT duplicate macro signatures, the full namespace catalogue, or the cookbook recipes. Claude is told to fetch the relevant page from this site whenever it needs the exact spelling of a macro — that's what this site is for.

## Source

The skill bundle is hosted alongside this site at [`tomhea/flipjump-docs`](https://github.com/tomhea/flipjump-docs) — the zip lives at `docs/source/_static/writing-flipjump-stl-code.zip`. Bug reports and improvements welcome there.

## Related

- [Getting Started — Install](../getting-started/install.md) — install the `fj` toolchain the skill drives.
- [Cookbook](../cookbook/index.md) — the recipes the skill points Claude at.
- [How the STL Works](../reference/how-the-stl-works.md) — the conceptual model the skill compresses into three sentences.

# Contributing to flipjump-docs

First off, thank you for considering contributing to FlipJump! It's people like
you that make the esoteric-language community such a great, active, and evolving
community.

This repository is the source for **[fjdocs.tomhe.app](https://fjdocs.tomhe.app)** —
the documentation site for the [FlipJump](https://github.com/tomhea/flipjump)
language — plus the editor integrations under [`editors/`](editors/) (the VS Code
extension and the native JetBrains plugin).

> Changes to the **language, standard library, compiler, or runtime** belong in
> the upstream [tomhea/flip-jump](https://github.com/tomhea/flipjump) repo, not
> here. This repo only documents them (the STL reference pages are auto-generated
> from the pinned `flip-jump` submodule) and ships the editor tooling.

Please don't use the issue tracker for support questions. Instead, use the
[FlipJump Discussions](https://github.com/tomhea/flipjump/discussions).

## Ways to contribute

- Fix typos, broken links, or unclear explanations in the docs.
- Improve or add guides, tutorials, and cookbook examples.
- Improve the editor integrations (grammar, colours, the JetBrains plugin lexer).
- Report a bug or suggest an enhancement (open an issue).

## Getting started

Prerequisites: Python 3.12+, git (and Node 22+ / a JDK 17+ only if you touch the
editor tooling).

```sh
git clone --recurse-submodules https://github.com/tomhea/flipjump-docs.git
cd flipjump-docs
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r docs/requirements.txt && pip install -e ".[dev]"
cd docs && make html        # build the site (treats warnings as errors, like CI)
```

See [`README.md`](README.md) for live-preview and submodule details, and
[`editors/README.md`](editors/README.md) for the editor-tooling workflow.

## Workflow

- **Never push to `main`.** Open a pull request from a feature branch.
- **Keep each PR small** — preferably one change/feature per PR.
- **Branch naming:** `fix/<slug>` for bug fixes, `docs/<slug>` for content,
  `feat/<slug>` for features.
- **Every PR includes a test** for what it changes: `pytest` for the Python
  tooling, a successful `cd docs && make html` (Sphinx `-W`) for content, and
  `actionlint` for workflow files. CI (`.github/workflows/pr-build.yml`) runs all
  of these.
- If you change the editor grammar, colours, or language configuration, run
  `npm run sync` in `editors/` and **repackage the shipped artifacts** (CI diffs
  them against the sources — see [`editors/README.md`](editors/README.md)).

## How to report a bug

Open an issue and include:

1. What you did (ideally a minimal reproduction or the page URL).
2. What you expected to see.
3. What you saw instead (screenshots help for rendering issues).
4. Your environment (OS, browser, or IDE + version for editor issues).

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating, you are expected to uphold it. Report unacceptable behavior to
[flipjumpproject@gmail.com](mailto:flipjumpproject@gmail.com).

Thank you, and welcome! 😸

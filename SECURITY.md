# Security Policy

This repository hosts the FlipJump documentation site
([fjdocs.tomhe.app](https://fjdocs.tomhe.app)) and the editor integrations (the
VS Code extension and the native JetBrains plugin). The extensions only provide
syntax highlighting — they do not execute project code — but we still take
security reports seriously.

## Supported versions

The documentation site is deployed continuously from `main`; only the latest
deployed version is supported. For the editor extensions, the latest published
release is supported.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report vulnerabilities privately by either:

- Using GitHub's [**Report a vulnerability**](https://github.com/tomhea/flipjump-docs/security/advisories/new)
  (Security → Advisories), or
- Emailing **[flipjumpproject@gmail.com](mailto:flipjumpproject@gmail.com)**.

Please include:

- A description of the issue and its potential impact.
- Steps to reproduce (or a proof of concept).
- The affected component (docs site, VS Code extension, or JetBrains plugin) and
  version, where relevant.

We aim to acknowledge reports within a few days and will keep you informed as we
investigate and fix. Once a fix is released we're happy to credit you, unless
you prefer to remain anonymous.

Vulnerabilities in the FlipJump **language, compiler, or standard library**
belong upstream at [tomhea/flip-jump](https://github.com/tomhea/flip-jump) —
please report those there.

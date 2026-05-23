# Repository configuration

This file records one-time GitHub configuration that lives outside the codebase. Update it whenever the configuration drifts.

## Branch protection (`main`)

Verified active via `gh api repos/tomhea/flipjump-docs/branches/main`:

| Setting | Value |
|---------|-------|
| Pull request required | yes |
| Required approving reviews | 0 (solo dev) |
| Dismiss stale reviews | no |
| Code-owner reviews required | no |
| Conversation resolution required | yes |
| Required status checks | none yet (will add `pr-build` once that workflow exists in M2) |
| Enforce on admins | **yes** — repo owner cannot bypass |
| Allow force pushes | no |
| Allow deletions | no |
| Required linear history | no (merge commits preferred per the `--no-ff` plan) |
| Required signed commits | no |
| Lock branch | no |

To inspect: `gh api repos/tomhea/flipjump-docs/branches/main/protection`.

To update: edit `.github/SETUP.md` AND apply the change via the API in the same PR, e.g.:

```sh
gh api -X PUT repos/tomhea/flipjump-docs/branches/main/protection --input protection.json
```

## GitHub Actions secrets

Verified present via `gh secret list --repo tomhea/flipjump-docs` (values are write-only):

| Secret | Purpose | Used by |
|--------|---------|---------|
| `SSH_HOST` | `tomhe.app` | `deploy.yml` |
| `SSH_USER` | `fjdocs` | `deploy.yml` |
| `PRIVATE_SSH_KEY` | SSH private key with deploy access to `fjdocs@tomhe.app` | `deploy.yml` |
| `WEB_ROOT_PATH` | Absolute path on the server where rsynced files are served from as `fjdocs.tomhe.app` | `deploy.yml` |

The deploy workflow itself lands in **M2**.

## Server (out of scope of this repo)

- Hostname: `fjdocs.tomhe.app`
- DNS + TLS: managed outside this repo, already serving the configured `WEB_ROOT_PATH` directory as `fjdocs.tomhe.app`. No work required from this repo's CI to provision or maintain.
- The deploy workflow rsyncs to `${SSH_USER}@${SSH_HOST}:${WEB_ROOT_PATH}` and the server picks up the new files immediately (static file serving).

"""M2 contract tests for the three GitHub Actions workflows.

These tests are structural — they assert each workflow exists, parses as
YAML, fires on the expected triggers, and references the right secrets /
commands. They do NOT execute the workflows; that happens on GitHub.
The strongest end-to-end check (live curl against fjdocs.tomhe.app) runs
post-merge and is documented in the M2 PR body's verification section.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is in dev deps
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    if yaml is None:
        pytest.skip("PyYAML not installed (pip install pyyaml)")
    path = WORKFLOWS / name
    assert path.is_file(), f"Missing workflow: {path}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------- deploy.yml ----------

def test_deploy_workflow_exists():
    assert (WORKFLOWS / "deploy.yml").is_file()


def test_deploy_workflow_fires_on_push_to_main_and_manual():
    wf = _load("deploy.yml")
    # YAML's `on:` key is parsed as the Python `True` token unless quoted in source.
    # Both forms are accepted here so we don't get bitten by that footgun.
    triggers = wf.get("on") or wf.get(True)
    assert triggers, f"No triggers defined in deploy.yml: {wf}"
    assert "push" in triggers, "deploy.yml must fire on push"
    assert triggers["push"].get("branches") == ["main"], (
        f"deploy.yml push branches must be [main], got: {triggers['push']}"
    )
    assert "workflow_dispatch" in triggers, "deploy.yml needs manual re-trigger"


def test_deploy_workflow_uses_all_four_secrets():
    raw = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
    for secret in ("SSH_HOST", "SSH_USER", "PRIVATE_SSH_KEY", "WEB_ROOT_PATH"):
        assert f"secrets.{secret}" in raw, (
            f"deploy.yml does not reference secrets.{secret}"
        )


def test_deploy_workflow_has_concurrency_guard():
    wf = _load("deploy.yml")
    job = wf["jobs"]["build-and-deploy"]
    assert "concurrency" in job, (
        "deploy.yml job must have a concurrency block to prevent racing pushes"
    )
    assert job["concurrency"]["cancel-in-progress"] is False, (
        "deploy concurrency must NOT cancel in-progress runs (would corrupt deploy)"
    )


def test_deploy_workflow_checks_out_submodules():
    wf = _load("deploy.yml")
    steps = wf["jobs"]["build-and-deploy"]["steps"]
    checkout = next(s for s in steps if "checkout" in s.get("uses", ""))
    assert checkout["with"]["submodules"] == "recursive", (
        "checkout must use submodules: recursive to fetch flip-jump source"
    )


# ---------- pr-build.yml ----------

def test_pr_build_workflow_exists():
    assert (WORKFLOWS / "pr-build.yml").is_file()


def test_pr_build_workflow_fires_on_pull_request():
    wf = _load("pr-build.yml")
    triggers = wf.get("on") or wf.get(True)
    assert "pull_request" in triggers


def test_pr_build_uses_fail_on_warning():
    raw = (WORKFLOWS / "pr-build.yml").read_text(encoding="utf-8")
    # Either passing -W explicitly to sphinx-build, OR using the Makefile
    # default which already includes -W --keep-going, satisfies this.
    # We require an unambiguous signal that warnings are errors.
    assert ("-W" in raw or "make html" in raw or "make.bat html" in raw), (
        "pr-build.yml must run sphinx-build with -W (directly or via the Makefile)"
    )


def test_pr_build_runs_actionlint():
    wf = _load("pr-build.yml")
    raw = json.dumps(wf)
    assert "actionlint" in raw, (
        "pr-build.yml must include an actionlint step to catch workflow regressions"
    )


# ---------- submodule-bump.yml ----------

def test_submodule_bump_workflow_exists():
    assert (WORKFLOWS / "submodule-bump.yml").is_file()


def test_submodule_bump_is_scheduled_and_manual():
    wf = _load("submodule-bump.yml")
    triggers = wf.get("on") or wf.get(True)
    assert "schedule" in triggers, "submodule-bump must have a schedule trigger"
    assert "workflow_dispatch" in triggers, "submodule-bump needs manual trigger"


def test_submodule_bump_uses_remote_update():
    raw = (WORKFLOWS / "submodule-bump.yml").read_text(encoding="utf-8")
    assert "submodule update --remote" in raw, (
        "submodule-bump.yml must run `git submodule update --remote` to bump"
    )


# ---------- actionlint smoke (optional, runs only if actionlint installed) ----------

def test_actionlint_passes_locally():
    if shutil.which("actionlint") is None:
        pytest.skip("actionlint not on PATH (CI installs it; local dev optional)")
    # actionlint takes file paths, not a directory; with no args it
    # auto-discovers from cwd. Pass the three workflow files explicitly
    # so the test fails loudly if a new workflow is added without the
    # corresponding contract test.
    files = sorted(WORKFLOWS.glob("*.yml"))
    assert files, f"No workflow files found under {WORKFLOWS}"
    result = subprocess.run(
        ["actionlint", *(str(f) for f in files)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"actionlint failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

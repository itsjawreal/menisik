from __future__ import annotations

import argparse
import os
from pathlib import Path


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        key = str(expanded)
        if key in seen:
            continue
        seen.add(key)
        unique.append(expanded)
    return unique


def _normalize_path(value: str | Path) -> str:
    return str(Path(value)).replace("\\", "/")


def _quote(value: str) -> str:
    if any(ch.isspace() for ch in value):
        return f'"{value}"'
    return value


def _openclaw_root(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    if os.environ.get("OPENCLAW_HOME"):
        return Path(os.environ["OPENCLAW_HOME"]).expanduser()
    return Path.home() / ".openclaw"


def _openclaw_roots(explicit: str | None = None) -> list[Path]:
    if explicit:
        explicit_path = Path(explicit).expanduser()
        roots = [explicit_path]
        if explicit_path.name.startswith("."):
            roots.append(explicit_path.with_name(explicit_path.name[1:]))
        return _unique_paths(roots)
    roots: list[Path] = []
    if os.environ.get("OPENCLAW_HOME"):
        roots.append(Path(os.environ["OPENCLAW_HOME"]).expanduser())
    roots.extend([Path.home() / ".openclaw", Path.home() / "openclaw"])
    return _unique_paths(roots)


def _workspace_skill_root(explicit: str | None = None, openclaw_root: str | None = None) -> Path:
    if explicit:
        explicit_path = Path(explicit).expanduser()
        if explicit_path.name == "skills":
            return explicit_path
        return explicit_path / "skills"
    if os.environ.get("OPENCLAW_WORKSPACE"):
        return Path(os.environ["OPENCLAW_WORKSPACE"]).expanduser() / "skills"
    for home_root in _openclaw_roots(openclaw_root):
        workspace_root = home_root / "workspace" / "skills"
        if workspace_root.parent.exists():
            return workspace_root
    return _openclaw_root(openclaw_root) / "skills"


def _all_skill_roots(explicit: str | None = None, openclaw_root: str | None = None) -> list[Path]:
    if explicit or os.environ.get("OPENCLAW_WORKSPACE"):
        return [_workspace_skill_root(explicit, openclaw_root)]
    roots: list[Path] = []
    for home_root in _openclaw_roots(openclaw_root):
        roots.append(home_root / "workspace" / "skills")
        roots.append(home_root / "skills")
    return _unique_paths(roots)


def _skill_text(invoke: str) -> str:
    return f"""---
name: github-contribution-engine
description: Use the local GitHub Contribution Engine wrapper to run health checks, show contribution reports, inspect repos, and execute safe contribution workflows from OpenClaw.
metadata: {{"openclaw": {{"requires": {{"bins": ["python3"]}}}}}}
---

## EXECUTION RULES

**Rule 1 - Execute immediately.**
When the user asks to check health, show the latest contribution report, inspect a repo, or run one contribution, execute the wrapper immediately.
Do NOT only describe a plan. Do NOT ask for the repo path if the user already gave a GitHub URL or `owner/repo`.

**Rule 2 - Prefer safe defaults.**
Use preview / dry-run behavior unless the user explicitly asks to submit a real PR.
For natural-language chat requests, prefer `message --text "..."` so the contribution engine can route the request safely.

**Rule 3 - Show exact output first.**
Paste the exact stdout from the wrapper before any short explanation.
Do NOT claim success without the real tool output.

**Rule 4 - No assistant filler.**
Do NOT say "Got it", "Let me check", or "Would you like me to proceed?" before running the wrapper.
Do NOT replace wrapper tables with emoji summaries or prose paraphrases.

**Rule 5 - No numbered menus for supported actions.**
Do NOT answer with choices like `1`, `2`, or `3` when a supported wrapper command already exists.
Run the command, return the exact stdout, then add at most one short next-step sentence if needed.

## Commands

- wrapper invoke: `{invoke}`
- health check: `doctor`
- latest contribution report: `contrib_report`
- inspect one repo: `repo_inspect --repo owner/repo`
- preview one queued contribution: `contrib_once --count 1`
- preview one targeted contribution: `contrib_targeted --repo owner/repo --count 1`
- check maintainer feedback / PR state: `contrib_check`
- respond to maintainer feedback: `contrib_respond`
- route natural language safely: `message --text "buat 1 kontribusi"`

## Common chat mappings

- `cek kesehatan contribution engine`
  - run: `doctor`
- `tampilkan report kontribusi terakhir`
  - run: `contrib_report`
- `cek repo owner/repo dulu`
  - run: `repo_inspect --repo owner/repo`
- `buat 1 kontribusi`
  - run: `message --text "buat 1 kontribusi"`
- `buat satu pull request ke https://github.com/owner/repo`
  - run: `message --text "buat satu pull request ke https://github.com/owner/repo"`

## Notes

- Use this wrapper instead of raw shell commands.
- The wrapper already maps supported commands onto `github-contribution-engine`.
- If the user gives a GitHub URL, pass it exactly in `--text` or convert it to `owner/repo` for explicit repo commands.
"""


def _wrapper_text(engine_bin: str) -> str:
    return f"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ENGINE_BIN = {engine_bin!r}
REPO_ROOT = str(Path(ENGINE_BIN).resolve().parents[2])


def run_engine(args: list[str]) -> int:
    env = dict(os.environ)
    env.setdefault("GITHUB_CONTRIBUTION_ENGINE_ROOT", REPO_ROOT)
    proc = subprocess.run(
        [ENGINE_BIN, *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr and proc.returncode != 0:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenClaw wrapper for github-contribution-engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Run the contribution engine doctor report.")
    sub.add_parser("contrib_report", help="Show the latest contribution report.")
    sub.add_parser("contrib_check", help="Check open PR state and maintainer feedback.")
    sub.add_parser("contrib_respond", help="Handle maintainer feedback only.")

    repo_inspect = sub.add_parser("repo_inspect", help="Inspect one repo safely.")
    repo_inspect.add_argument("--repo", required=True)

    contrib_once = sub.add_parser("contrib_once", help="Preview one queued contribution.")
    contrib_once.add_argument("--count", type=int, default=1)
    contrib_once.add_argument("--goal", default="bugfix")
    contrib_once.add_argument("--first-pr", action="store_true")
    contrib_once.add_argument("--live", action="store_true")

    contrib_targeted = sub.add_parser("contrib_targeted", help="Preview one targeted contribution.")
    contrib_targeted.add_argument("--repo", required=True)
    contrib_targeted.add_argument("--count", type=int, default=1)
    contrib_targeted.add_argument("--goal", default="bugfix")
    contrib_targeted.add_argument("--first-pr", action="store_true")
    contrib_targeted.add_argument("--live", action="store_true")

    route = sub.add_parser("route", help="Show the canonical action for a natural-language request.")
    route.add_argument("--text", required=True)

    message = sub.add_parser("message", help="Execute a natural-language request safely.")
    message.add_argument("--text", required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "doctor":
        return run_engine(["--doctor"])
    if args.command == "contrib_report":
        return run_engine(["--contrib-report"])
    if args.command == "contrib_check":
        return run_engine(["--contrib-check"])
    if args.command == "contrib_respond":
        return run_engine(["--contrib-respond"])
    if args.command == "repo_inspect":
        return run_engine(["--repo-inspect", args.repo])
    if args.command == "contrib_once":
        payload = ["--contrib", "--count", str(args.count), "--goal", args.goal]
        if args.first_pr:
            payload.append("--first-pr")
        if not args.live:
            payload.append("--dry-run")
        return run_engine(payload)
    if args.command == "contrib_targeted":
        payload = ["--contrib", args.repo, "--count", str(args.count), "--goal", args.goal]
        if args.first_pr:
            payload.append("--first-pr")
        if not args.live:
            payload.append("--dry-run")
        return run_engine(payload)
    if args.command == "route":
        return run_engine(["--command-text", args.text, "--dry-run"])
    if args.command == "message":
        return run_engine(["--command-text", args.text])
    raise SystemExit(f"Unsupported command: {{args.command}}")


if __name__ == "__main__":
    raise SystemExit(main())
"""


def install_openclaw_assets(
    *,
    engine_bin: str,
    python_bin: str,
    openclaw_root: str | None = None,
    openclaw_workspace: str | None = None,
) -> tuple[Path, Path]:
    roots = _openclaw_roots(openclaw_root)
    skill_roots = _all_skill_roots(openclaw_workspace, openclaw_root)
    primary_root = roots[0]
    primary_tool_path = primary_root / "tools" / "contribution.py"
    primary_skill_path = skill_roots[0] / "github-contribution-engine" / "SKILL.md"
    normalized_python = _normalize_path(python_bin)
    normalized_engine = _normalize_path(engine_bin)

    for root in roots:
        tool_path = root / "tools" / "contribution.py"
        tool_path.parent.mkdir(parents=True, exist_ok=True)
        tool_path.write_text(_wrapper_text(normalized_engine), encoding="utf-8")
        try:
            tool_path.chmod(0o755)
        except OSError:
            pass

    for skill_root in skill_roots:
        skill_dir = skill_root / "github-contribution-engine"
        skill_dir.mkdir(parents=True, exist_ok=True)
        matching_root = next((root for root in roots if skill_root.is_relative_to(root)), primary_root)
        matching_tool = matching_root / "tools" / "contribution.py"
        invoke = f"{_quote(normalized_python)} {_quote(_normalize_path(matching_tool))}"
        (skill_dir / "SKILL.md").write_text(_skill_text(invoke=invoke), encoding="utf-8")

    return primary_skill_path, primary_tool_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install OpenClaw skill and wrapper files for github-contribution-engine.",
    )
    parser.add_argument("--engine-bin", required=True, help="Absolute path to github-contribution-engine executable.")
    parser.add_argument("--python-bin", required=True, help="Absolute path to the Python interpreter OpenClaw should use.")
    parser.add_argument("--openclaw-root", default="", help="Optional override for the OpenClaw home directory.")
    parser.add_argument("--openclaw-workspace", default="", help="Optional override for the OpenClaw workspace directory that should receive workspace skills.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skill_path, tool_path = install_openclaw_assets(
        engine_bin=args.engine_bin,
        python_bin=args.python_bin,
        openclaw_root=args.openclaw_root or None,
        openclaw_workspace=args.openclaw_workspace or None,
    )
    print(f"Installed OpenClaw skill: {skill_path}")
    print(f"Installed OpenClaw wrapper: {tool_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

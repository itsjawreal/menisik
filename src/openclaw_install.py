from __future__ import annotations

import argparse
import os
from pathlib import Path


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


def _skill_text(tool_path: str, invoke: str) -> str:
    return f"""# SKILL: github-contribution-engine
description: Acceptance-first GitHub contribution engine. Executes health checks, reports, repo inspection, and safe contribution flows.
version: 1.0.0
tool_path: {tool_path}
invoke: {invoke}

## EXECUTION RULES — Read this first, every time

**Rule 1 — Execute immediately.**
When the user asks to check health, show the latest contribution report, inspect a repo, or run one contribution, execute the wrapper immediately.
Do NOT only describe a plan. Do NOT ask for the repo path if the user already gave a GitHub URL or `owner/repo`.

**Rule 2 — Prefer safe defaults.**
Use preview / dry-run behavior unless the user explicitly asks to submit a real PR.
For natural-language chat requests, prefer `message --text "..."` so the contribution engine can route the request safely.

**Rule 3 — Show exact output first.**
Paste the exact stdout from the wrapper before any short explanation.
Do NOT claim success without the real tool output.

## Commands

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
import subprocess
import sys

ENGINE_BIN = {engine_bin!r}


def run_engine(args: list[str]) -> int:
    proc = subprocess.run(
        [ENGINE_BIN, *args],
        capture_output=True,
        text=True,
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
) -> tuple[Path, Path]:
    root = _openclaw_root(openclaw_root)
    tools_dir = root / "tools"
    skill_dir = root / "skills" / "github-contribution-engine"
    tools_dir.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=True)

    tool_path = tools_dir / "contribution.py"
    skill_path = skill_dir / "SKILL.md"

    tool_path.write_text(_wrapper_text(_normalize_path(engine_bin)), encoding="utf-8")
    try:
        tool_path.chmod(0o755)
    except OSError:
        pass

    normalized_python = _normalize_path(python_bin)
    normalized_tool = _normalize_path(tool_path)
    invoke = f"{_quote(normalized_python)} {_quote(normalized_tool)}"
    skill_path.write_text(
        _skill_text(tool_path=_normalize_path(tool_path), invoke=invoke),
        encoding="utf-8",
    )
    return skill_path, tool_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install OpenClaw skill and wrapper files for github-contribution-engine.",
    )
    parser.add_argument("--engine-bin", required=True, help="Absolute path to github-contribution-engine executable.")
    parser.add_argument("--python-bin", required=True, help="Absolute path to the Python interpreter OpenClaw should use.")
    parser.add_argument("--openclaw-root", default="", help="Optional override for the OpenClaw home directory.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skill_path, tool_path = install_openclaw_assets(
        engine_bin=args.engine_bin,
        python_bin=args.python_bin,
        openclaw_root=args.openclaw_root or None,
    )
    print(f"Installed OpenClaw skill: {skill_path}")
    print(f"Installed OpenClaw wrapper: {tool_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

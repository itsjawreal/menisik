#!/usr/bin/env python3
"""Compatibility wrapper for the contribution-engine CLI.

The old multi-step crypto-builder pipeline has been retired from this repo.
This wrapper now forwards to `app.builder` so existing local scripts,
scheduled tasks, and habits still work after the product transition.
"""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from app.builder import main as builder_main
from src.config import AI_BACKEND


def _default_args() -> list[str]:
    configured = (ROOT / ".env").read_text(encoding="utf-8") if (ROOT / ".env").exists() else ""
    autorun = "CONTRIB_AUTORUN_ARGS"
    for raw_line in configured.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == autorun and value.strip():
            return shlex.split(value.strip(), posix=False)
    return ["--contrib", "--1"]


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        argv = _default_args()

    if not any(arg in {"--contrib", "--pr", "--contrib-check", "--pr-check", "--contrib-respond", "--pr-respond", "--contrib-report", "--repo-inspect", "--doctor"} for arg in argv):
        argv = ["--contrib", *argv]

    backend = "Codex" if AI_BACKEND == "codex" else "Claude"
    print(f"[run.py] forwarding to contribution engine using {backend}: {' '.join(argv)}", flush=True)
    builder_main(argv)


if __name__ == "__main__":
    main()

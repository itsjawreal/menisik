PR #60 direction good. Scope narrow. Failure mode concrete.

Fix before sending:

- Move new CLI tests under `agent/tests/`. CI runs `pytest` from repo root and existing suite lives there.
- Use `from backtest import validation` or `from backtest.validation import _parse_run_dir`. Root-level `from agent.backtest import validation` breaks repo conventions.
- Add test for missing argument. Current code changes CLI behavior here but does not lock it down.
- Add test for non-directory path. PR body claims this case, current tests do not prove it.

Suggested patch file:

- `artifacts/vibe-trading-pr60-improvement.patch`

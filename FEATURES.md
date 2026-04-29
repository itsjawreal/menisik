# Contribution Engine Features

## Core Capabilities

- Search GitHub for active open-source repositories that fit the configured niche.
- Inspect a pinned repository before attempting a contribution.
- Generate narrow contribution patches through CLI-based AI backends.
- Submit PRs through fork, branch, push, and `gh pr create`.
- Track PR lifecycle, maintainer feedback, and operator-visible bottlenecks.

## Contribution Goals

- `bugfix`
  Default mode. Finds evidence-backed defects from local code patterns and aims for narrow behavioral fixes.

- `feature_upgrade`
  Maintainer-signaled enhancement mode. Only acts when code already contains explicit TODO/FIXME-style intent.

- `feature_add`
  Issue-backed enhancement mode. Requires narrow file targeting plus maintainer intent from live issues.

## Search And Targeting

- Contribution lanes:
  - `general`
  - `crypto`
  - `devtools`
  - `frontend`
  - `data`
  - `infra`
  - `ml`
  - `docs`

- Lane overrides:
  - `CONTRIB_LANE`
  - `CONTRIB_TOPIC_KEYWORDS`
  - `CONTRIB_SEARCH_QUERIES`

- Targeted mode:
  - `python -m app.builder --contrib owner/repo --1`
  - supports broad-repo overrides for deliberate operator use

- First-PR mode:
  - `python -m app.builder --contrib --goal bugfix --first-pr --1`
  - biases search toward smaller, active, test-backed repos that are more likely to accept a first real PR

## Quality Guardrails

- Scope validation for repo breadth.
- Qualification based on concrete evidence and narrow patch area.
- Self-review rejection for unjustified behavior changes.
- Evidence quality rejection for speculative fixes.
- Syntax validation of generated files.
- Minimal-diff enforcement.
- One-open-PR-per-repo pacing.

## Operator UX

- `--doctor`
  Machine and portability readiness checks.

- `--contrib-report`
  Recent run summaries, queue state, and next-step hints.

- `--repo-inspect`
  Repo scope, lane fit, and first-PR fit preview without submitting anything.

## Portability

- Dynamic GitHub owner selection via `GITHUB_OWNER` or active `gh` login.
- `gh` subprocesses automatically ignore poisoned localhost proxy values such as `127.0.0.1:9`.
- Windows helpers use relative repo paths instead of hardcoded machine paths.

## Current Gaps

- API-key-only LLM mode is not implemented yet.
- Large-repo heuristics are still conservative by design.
- Scheduler portability beyond local Windows automation is still incomplete.

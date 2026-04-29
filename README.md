# GitHub Contribution Engine

Autonomous contribution engine for finding, verifying, submitting, tracking, and learning from GitHub pull requests.

This repo is now dedicated to contribution workflows only. The old crypto tool generation/adapt pipeline was archived to `E:\newbot\newauto\genoshide\crypto-builder-oldm`.

## What It Does

- Discovers active open-source repositories worth contributing to.
- Scans code locally for narrow, evidence-backed contribution opportunities.
- Qualifies opportunities before spending AI calls.
- Uses Codex or Claude CLI to produce focused patches and PR bodies.
- Submits PRs through GitHub CLI.
- Tracks PR lifecycle, maintainer feedback, rejections, queue state, and run summaries in SQLite.
- Learns from outcomes so repeated weak targets are deprioritized.

The engine optimizes for contribution quality over contribution count. It should behave like a careful contributor, not a PR spam bot.

## Main Commands

```powershell
python -m app.builder --contrib --1
python -m app.builder --contrib owner/repo --1
python -m app.builder --contrib owner/repo --goal feature_upgrade --1
python -m app.builder --contrib owner/repo --goal feature_add --1
python -m app.builder --contrib --goal bugfix --first-pr --1
python -m app.builder --contrib-check
python -m app.builder --contrib-respond
python -m app.builder --contrib-report
python -m app.builder --doctor
python -m app.builder --repo-inspect owner/repo
```

Compatibility aliases are still available:

```powershell
python -m app.builder --pr --1
python -m app.builder --pr-check
python -m app.builder --pr-respond
```

## Engine Design

Core modules:

- `src/contribution_engine.py`: run orchestration, pacing, operator reports.
- `src/contribution_store.py`: SQLite schema and persistence.
- `src/opportunity_engine.py`: local pattern scanner and qualification policy.
- `src/repo_intelligence.py`: repo score adjustments from memory.
- `src/pr_generator.py`: GitHub target search, AI patch execution, PR tracking, and feedback handling.
- `src/fork.py`: fork, branch, push, and PR creation through `gh`.

The main state unit is an `Opportunity`, not a repo. Opportunities move through states like `SCAN`, `QUALIFY`, `EXECUTE`, `VERIFY`, `READY`, `SUBMIT`, and `REJECT`.

Behavioral policy is defined primarily in [skill.md](E:/newbot/newauto/genoshide/crypto-builder/skill.md), with repo-specific operating guidance in [AGENTS.md](E:/newbot/newauto/genoshide/crypto-builder/AGENTS.md).

## Quality Policy

The engine favors small, testable PRs:

- concrete failure mode required
- one clear target file preferred
- broad refactors rejected
- speculative "safer/cleaner" changes rejected
- one open PR per repo at a time
- queued opportunities are retained for later pacing

Every proposed patch should begin from a concrete failure mode and enough local evidence to explain the value without hand-waving.

Contribution goals:

- `bugfix`: default mode, sourced from local scanner evidence
- `feature_upgrade`: narrow enhancement work only when the code already contains explicit maintainer TODO/FIXME intent
- `feature_add`: stricter enhancement mode that expects issue-backed maintainer intent and a narrow target file match
- `--first-pr`: search-mode operator flag that biases repo discovery toward smaller, active, test-backed repos for a first real PR

V1 pattern classes:

- `missing_timeout`
- `unchecked_response_shape`
- `unsafe_file_write_or_path`
- `overbroad_exception_handling`
- `missing_regression_test_for_obvious_bugfix`
- `missing_input_validation`
- `resource_cleanup_gap`

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Authenticate GitHub CLI:

```powershell
gh auth login
gh auth status
```

Optional `.env` values:

```env
AI_BACKEND=codex
GITHUB_TOKEN=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
CONTRIB_AUTORUN_ARGS=--contrib --1
CONTRIB_LANE=general
CONTRIB_TOPIC_KEYWORDS=
CONTRIB_SEARCH_QUERIES=
PR_MIN_STARS=300
PR_MAX_STARS=6000
PR_COUNT=1
PR_TARGETED_MAX_TOTAL_FILES=130
PR_TARGETED_MAX_PY_FILES=75
PR_TARGETED_ALLOW_BROAD=false
CONTRIB_FIRST_PR_MODE=false
```

Notes:

- `CODEX_CMD=codex` is already portable if Codex CLI is on `PATH`.
- `CLAUDE_CMD=claude` is preferred over a user-specific Windows path.
- `CONTRIB_AUTORUN_ARGS` controls what `python run.py` and scheduled tasks do by default.
- `CONTRIB_LANE` supports built-in presets: `general`, `crypto`, `devtools`, `frontend`, `data`, `infra`, `ml`, `docs`.
- `CONTRIB_TOPIC_KEYWORDS` and `CONTRIB_SEARCH_QUERIES` override the preset when you need custom targeting.
- `PR_TARGETED_MAX_TOTAL_FILES` and `PR_TARGETED_MAX_PY_FILES` only affect pinned/targeted repo runs.
- `PR_TARGETED_ALLOW_BROAD=true` disables targeted repo breadth guardrails entirely; use it only when you intentionally want to work on a large repo.
- `CONTRIB_FIRST_PR_MODE=true` makes search mode prefer smaller repos with tests and fresher activity for a first production PR attempt.
- You should keep secrets only in `.env`, not in docs or scripts.

Examples:

```env
# General-purpose developer tooling
CONTRIB_LANE=devtools

# Frontend ecosystem targeting
CONTRIB_LANE=frontend

# Custom niche override
CONTRIB_LANE=general
CONTRIB_TOPIC_KEYWORDS=observability,otel,tracing,metrics
CONTRIB_SEARCH_QUERIES=python:python observability library,typescript:typescript tracing sdk
```

## Portability

Before opening this project to wider users, run:

```powershell
python -m app.builder --doctor
```

This checks:

- Python, `git`, and `gh` availability
- GitHub auth visibility
- configured AI backend and CLI presence
- whether only API keys are present without a supported CLI backend
- whether env settings contain machine-specific absolute paths

Current portability status:

- Codex CLI and Claude CLI workflows are supported now.
- API-key-only LLM operation is not implemented yet, so users without a supported CLI backend will currently be blocked.

## Verification

```powershell
python -m py_compile app\builder.py src\ai.py src\config.py src\contribution_engine.py src\contribution_store.py src\fork.py src\notify.py src\opportunity_engine.py src\pr_engine.py src\pr_generator.py src\repo_intelligence.py src\scraper.py src\security.py src\state.py
python -m unittest discover -s tests -v
```

## Active Docs

- [FEATURES.md](E:/newbot/newauto/genoshide/crypto-builder/FEATURES.md): capability map for the current engine
- [PRODUCT_STATUS.md](E:/newbot/newauto/genoshide/crypto-builder/PRODUCT_STATUS.md): current strengths, bottlenecks, and recommended usage
- [skill.md](E:/newbot/newauto/genoshide/crypto-builder/skill.md): source of truth for contribution-engine behavior
- [AGENTS.md](E:/newbot/newauto/genoshide/crypto-builder/AGENTS.md): repo mission, architecture, and verification rules
- [.agent.md](E:/newbot/newauto/genoshide/crypto-builder/.agent.md): local agent execution persona
- [ALUR.md](E:/newbot/newauto/genoshide/crypto-builder/ALUR.md): concise end-to-end contribution flow

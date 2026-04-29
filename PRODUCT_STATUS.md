# Product Status

## Current State

This repository is now operating as a GitHub contribution engine with:

- repo discovery
- targeted repo inspection
- bugfix / feature-upgrade / issue-backed feature-add contribution modes
- PR submission through forks and GitHub CLI
- PR lifecycle memory in SQLite
- maintainer feedback response flow
- operator diagnostics and reporting

## What Is Working Well

- End-to-end PR creation is working on real public repositories.
- The engine can now push to the currently active GitHub user instead of a hardcoded owner.
- Proxy-poisoned `gh` environments are handled inside the engine.
- Contribution reports and doctor output are much easier to operate day-to-day.

## Current Bottlenecks

- Large repositories still often collapse into `target_area_too_broad`.
- `feature_upgrade` is naturally sparse because it depends on explicit maintainer intent.
- API-key-only generation is still missing.
- Some external repos have their own local test/runtime issues, which can limit validation depth.

## Best Current Use Case

The engine is strongest today when used for:

- small or medium Python/TypeScript repos
- active repos with tests
- narrow bugfixes
- explicit TODO/FIXME enhancement gaps
- first real PR attempts through `--first-pr`

## Recommended Operator Commands

```powershell
python -m app.builder --doctor
python -m app.builder --repo-inspect owner/repo
python -m app.builder --contrib --goal bugfix --first-pr --1
python -m app.builder --contrib owner/repo --goal bugfix --1
python -m app.builder --contrib-report
```

## Next Product Priorities

- stronger first-PR repo selection heuristics
- narrower target-file scoring inside large repos
- API-key-only provider adapter
- portable scheduler options for open-source users

# OpenClaw Notes

## Role

OpenClaw is a documented integration target for operator-specific use.

## Use When

- evaluating compatibility with another agent shell
- documenting how the contribution engine can be run outside the default backend
- preparing multi-provider operator guidance

## Expectations

- preserve the same repo selection, qualification, validation, and PR standards
- keep provider notes implementation-focused
- defer to [../../skill.md](../../skill.md) and [../../AGENTS.md](../../AGENTS.md) for policy

## Operator Guidance

- document command differences and environment assumptions here
- avoid duplicating general contribution rules
- add concrete setup notes only when they are verified
- prefer calling the MCP tools in `src.contribution_mcp.server` over sending raw shell commands
- use `route_command` first when the user speaks in natural language instead of canonical action names

## Install Path

Recommended install command:

```powershell
uv tool install git+https://github.com/BigNounce90/github-contribution-engine.git
```

Verify the installed commands:

```powershell
github-contribution-engine --doctor
contribution-mcp
```

If the commands are not found after install, make sure uv's bin directory is on `PATH`.

For one-step VPS onboarding plus native OpenClaw assets:

```bash
bash scripts/install_vps.sh
```

That setup flow can install:

- the Python environment
- `github-contribution-engine`
- `contribution-mcp`
- `~/.openclaw/skills/github-contribution-engine/SKILL.md`
- `~/.openclaw/tools/contribution.py`

## OpenClaw MCP Config

If your OpenClaw environment supports standard MCP server registration, use:

```json
{
  "mcpServers": {
    "contribution-engine": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "git+https://github.com/BigNounce90/github-contribution-engine.git",
        "contribution-mcp"
      ]
    }
  }
}
```

## OpenClaw Native Skill

This repo also supports a native OpenClaw wrapper path, modeled after `wallet-mcp`.

Installed files:

- `~/.openclaw/skills/github-contribution-engine/SKILL.md`
- `~/.openclaw/tools/contribution.py`

The native wrapper is useful when your Telegram / Discord / OpenClaw agent behaves like a general chat assistant instead of calling MCP tools directly.

Preferred commands from that skill:

- `doctor`
- `contrib_report`
- `repo_inspect --repo owner/repo`
- `message --text "buat 1 kontribusi"`
- `message --text "tampilkan report kontribusi terakhir"`

For natural-language chat channels, `message --text "..."`
is the safest default because it lets the engine route the request first.

Local clone variant:

```json
{
  "mcpServers": {
    "contribution-engine": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/github-contribution-engine",
        "run",
        "contribution-mcp"
      ]
    }
  }
}
```

## Suggested Tool Flow

For natural-language channels such as Telegram or Discord routed through OpenClaw:

1. Call `route_command(text=...)`
2. Inspect the returned canonical action
3. Call the matching MCP tool:
   - `doctor`
   - `repo_inspect`
   - `contrib_once`
   - `contrib_targeted`
   - `contrib_check`
   - `contrib_report`

Example:

- user says `buat 1 kontribusi`
- OpenClaw calls `route_command(text="buat 1 kontribusi")`
- result maps to `contrib_once` with `dry_run=true`
- OpenClaw then calls `contrib_once(dry_run=true)`

## Safety Notes

- natural-language contribution requests default to preview mode unless the request explicitly asks for live submission
- `route_command` is safer than forwarding raw shell commands from chat
- keep GitHub auth and local CLI readiness healthy by checking `github-contribution-engine --doctor`

## Known Boundary

This file documents a supported path, not a separate product mode.

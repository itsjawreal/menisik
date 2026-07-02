# Release Notes — v0.2.0

This is the planned breaking release that completes the **rover → menisik** rename (phase 2). Phase 1 (0.1.2) renamed the package, entry points, CLI display strings, docs, and the GitHub repo slug while keeping `rover*` aliases. Phase 2 migrates everything that was deliberately deferred because it could break operator or MCP client configs.

## Breaking changes

- **`rover*` entry points removed.** `rover`, `rover-engine`, `rover-mcp`, and `rover-daemon` were warning-only aliases through `0.1.x` and are now gone. Use `menisik`, `menisik-engine` (new in this release), `menisik-mcp`, and `menisik-daemon`.
- **MCP server registers as `menisik`** (was `rover`). MCP clients must rename their server key:
  - Claude Desktop / Claude Code: `mcpServers.rover` → `mcpServers.menisik`
  - OpenClaw: `mcp.servers.rover` → `mcp.servers.menisik`
  - Hermes: `mcp_servers.rover` → `mcp_servers.menisik`
  - The tool set and behavior are unchanged. Re-running `--install-openclaw` / `--install-hermes` / `--install-mcp` performs the rename and removes the stale `rover` entry so the server is not registered twice.

## Migrations with compatibility fallbacks (no action strictly required)

- **Env vars:** `MENISIK_NOTIFY_*` replaces `ROVER_NOTIFY_*`; storage overrides are now `MENISIK_STORAGE_MODE`, `MENISIK_HOME`, `MENISIK_STATE_DIR`, `MENISIK_CACHE_DIR`, `MENISIK_ARTIFACT_DIR`, `MENISIK_CONFIG_DIR`. The old `ROVER_*` spellings are still read as fallbacks and log a one-time deprecation warning per run.
- **Local storage:** defaults moved from `~/.rover`-style dirs (`~/.local/state/rover`, `~/.rover`, repo-local `.rover`, etc.) to their `menisik` equivalents. On startup, an existing legacy dir is migrated automatically when the new location does not exist yet; if the move fails, the engine keeps reading the legacy location and warns.
- **Installers:** OpenClaw assets are now written as `skills/menisik/SKILL.md` and `tools/menisik.py` (with `rover.py`/`contribution.py` kept as compatibility copies), and stale `rover` MCP/skill entries are cleaned up. `doctor` reports leftover `rover`-named paths as ok-legacy and suggests re-running the installer to migrate.
- **Services:** install scripts now register `menisik-mcp` / `menisik-daemon` systemd units and the `MenisikDaemon` Windows task, removing the old `rover`-named units/tasks so nothing runs twice.
- **Chat surfaces:** the Telegram bot and OpenClaw skill accept the `menisik <subcommand>` prefix; the `rover <subcommand>` prefix still works as a deprecated alias, and intent-based routing (`Rover, fix bug in owner/repo`) is unchanged.

## Still deprecated (warning-only)

- `--pr`, `--pr-check`, `--pr-respond` CLI flags — prefer `--contrib`, `--contrib-check`, `--contrib-respond`. Removal target: the next intentionally breaking CLI release.
- `ROVER_*` env spellings and `rover`-named integration paths — supported as fallbacks for now.
- `github-contribution-engine` OpenClaw compatibility paths — supported until replacement integrations are proven stable.

## Also in this release

- Fixed a parse error in `scripts/uninstall_windows.ps1` (`"$Label:"` was parsed as a scoped variable, preventing the script from running).

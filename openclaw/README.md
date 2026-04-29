# OpenClaw Native Integration

This folder contains the source material used to install a native OpenClaw
skill and wrapper for the GitHub Contribution Engine.

Installed assets land in the operator home directory:

- preferred: `~/.openclaw/workspace/skills/github-contribution-engine/SKILL.md`
- fallback: `~/.openclaw/skills/github-contribution-engine/SKILL.md`
- `~/.openclaw/tools/contribution.py`

The supported installer path is:

```bash
bash scripts/install_vps.sh
```

That setup script can install the OpenClaw assets automatically in one flow.

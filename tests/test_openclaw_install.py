from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.openclaw_install import install_openclaw_assets


class OpenClawInstallTests(unittest.TestCase):
    def test_install_writes_workspace_skill_and_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_path, tool_path = install_openclaw_assets(
                engine_bin="/srv/engine/.venv/bin/github-contribution-engine",
                python_bin="/srv/engine/.venv/bin/python",
                openclaw_root=str(root / ".openclaw"),
                openclaw_workspace=str(root / ".openclaw" / "workspace"),
            )

            self.assertTrue(skill_path.exists())
            self.assertTrue(tool_path.exists())

            skill_text = skill_path.read_text(encoding="utf-8")
            tool_text = tool_path.read_text(encoding="utf-8")

            self.assertIn("---", skill_text)
            self.assertIn("name: github-contribution-engine", skill_text)
            self.assertIn("description: Use the local GitHub Contribution Engine wrapper", skill_text)
            self.assertIn("message --text", skill_text)
            self.assertIn("contrib_report", skill_text)
            self.assertIn("Do NOT answer with choices like `1`, `2`, or `3`", skill_text)
            self.assertIn("/srv/engine/.venv/bin/python", skill_text)
            self.assertIn(".openclaw/tools/contribution.py", skill_text.replace("\\", "/"))
            self.assertIn(".openclaw/workspace/skills/github-contribution-engine/SKILL.md", str(skill_path).replace("\\", "/"))
            self.assertIn("ENGINE_BIN = '/srv/engine/.venv/bin/github-contribution-engine'", tool_text)
            self.assertIn('REPO_ROOT = str(Path(ENGINE_BIN).resolve().parents[2])', tool_text)
            self.assertIn('cwd=REPO_ROOT', tool_text)
            self.assertIn('env.setdefault("GITHUB_CONTRIBUTION_ENGINE_ROOT", REPO_ROOT)', tool_text)
            self.assertIn('return run_engine(["--command-text", args.text])', tool_text)

    def test_install_writes_workspace_and_shared_skill_dirs_when_workspace_not_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_path, _ = install_openclaw_assets(
                engine_bin="/srv/engine/.venv/bin/github-contribution-engine",
                python_bin="/srv/engine/.venv/bin/python",
                openclaw_root=str(root / ".openclaw"),
            )

            self.assertIn(".openclaw/workspace/skills/github-contribution-engine/SKILL.md", str(skill_path).replace("\\", "/"))
            self.assertTrue((root / ".openclaw" / "skills" / "github-contribution-engine" / "SKILL.md").exists())

    def test_install_writes_legacy_openclaw_paths_for_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_openclaw_assets(
                engine_bin="/srv/engine/.venv/bin/github-contribution-engine",
                python_bin="/srv/engine/.venv/bin/python",
                openclaw_root=str(root / ".openclaw"),
            )

            legacy_wrapper = root / "openclaw" / "tools" / "contribution.py"
            legacy_workspace_skill = (
                root / "openclaw" / "workspace" / "skills" / "github-contribution-engine" / "SKILL.md"
            )
            legacy_shared_skill = root / "openclaw" / "skills" / "github-contribution-engine" / "SKILL.md"

            self.assertTrue(legacy_wrapper.exists())
            self.assertTrue(legacy_workspace_skill.exists())
            self.assertTrue(legacy_shared_skill.exists())

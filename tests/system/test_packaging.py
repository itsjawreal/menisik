from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class PackagingTests(unittest.TestCase):
    def test_pyproject_declares_cli_and_mcp_scripts(self) -> None:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('name = "menisik"', text)
        self.assertIn('menisik = "app.contribute:main"', text)
        self.assertIn('menisik-engine = "app.builder:main"', text)
        self.assertIn('menisik-mcp = "src.contribution_mcp.server:main"', text)
        self.assertIn('menisik-daemon = "src.daemon.runner:main"', text)

    def test_pyproject_removed_rover_aliases_at_0_2_0(self) -> None:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('version = "0.2.0"', text)
        self.assertNotIn('rover = "app.contribute:main"', text)
        self.assertNotIn('rover-engine = "app.builder:main"', text)
        self.assertNotIn('rover-mcp = "src.contribution_mcp.server:main"', text)
        self.assertNotIn('rover-daemon = "src.daemon.runner:main"', text)


if __name__ == "__main__":
    unittest.main()

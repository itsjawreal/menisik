from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.platform.hermes_install import install_hermes_config


class HermesInstallTests(unittest.TestCase):
    def test_install_writes_menisik_mcp_server_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            written = install_hermes_config(
                menisik_mcp_bin="/srv/engine/.venv/bin/menisik-mcp",
                hermes_config_path=str(config_path),
            )

            self.assertEqual(written, config_path)
            text = config_path.read_text(encoding="utf-8")
            self.assertIn("mcp_servers:", text)
            self.assertIn("  menisik:", text)
            self.assertIn('command: "/srv/engine/.venv/bin/menisik-mcp"', text)

    def test_install_preserves_existing_servers_and_replaces_menisik_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                "mcp_servers:\n"
                "  other:\n"
                '    command: "other-mcp"\n'
                "  menisik:\n"
                '    command: "old-menisik"\n'
                "    args: []\n",
                encoding="utf-8",
            )

            install_hermes_config(
                menisik_mcp_bin="/srv/engine/.venv/bin/menisik-mcp",
                hermes_config_path=str(config_path),
            )

            text = config_path.read_text(encoding="utf-8")
            self.assertIn('command: "other-mcp"', text)
            self.assertIn('command: "/srv/engine/.venv/bin/menisik-mcp"', text)
            self.assertNotIn('command: "old-menisik"', text)

    def test_install_removes_stale_rover_block_so_server_is_not_doubled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                "mcp_servers:\n"
                "  other:\n"
                '    command: "other-mcp"\n'
                "  rover:\n"
                '    command: "/old/rover-mcp"\n'
                "    args: []\n"
                "    enabled: true\n",
                encoding="utf-8",
            )

            install_hermes_config(
                menisik_mcp_bin="/srv/engine/.venv/bin/menisik-mcp",
                hermes_config_path=str(config_path),
            )

            text = config_path.read_text(encoding="utf-8")
            self.assertIn('command: "other-mcp"', text)
            self.assertIn("  menisik:", text)
            self.assertNotIn("  rover:", text)
            self.assertNotIn("/old/rover-mcp", text)

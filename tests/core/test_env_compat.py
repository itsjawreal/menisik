from __future__ import annotations

import importlib
import os
import unittest
from unittest import mock

import src.core.config as config


class NotifyEnvCompatTests(unittest.TestCase):
    def tearDown(self) -> None:
        importlib.reload(config)

    def test_menisik_notify_env_wins_over_legacy_rover_env(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "MENISIK_NOTIFY_TRANSPORT": "telegram",
                "ROVER_NOTIFY_TRANSPORT": "openclaw",
            },
            clear=False,
        ):
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.MENISIK_NOTIFY_TRANSPORT, "telegram")

    def test_legacy_rover_notify_env_is_read_with_deprecation_warning(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ROVER_NOTIFY_TRANSPORT": "telegram",
                "ROVER_NOTIFY_INTERVAL_SECONDS": "45",
                "ROVER_NOTIFY_PROGRESS": "true",
            },
            clear=False,
        ):
            for key in (
                "MENISIK_NOTIFY_TRANSPORT",
                "MENISIK_NOTIFY_INTERVAL_SECONDS",
                "MENISIK_NOTIFY_PROGRESS",
            ):
                os.environ.pop(key, None)
            with self.assertLogs("src.core.config", level="WARNING") as captured:
                reloaded = importlib.reload(config)
            self.assertEqual(reloaded.MENISIK_NOTIFY_TRANSPORT, "telegram")
            self.assertEqual(reloaded.MENISIK_NOTIFY_INTERVAL_SECONDS, 45)
            self.assertTrue(reloaded.MENISIK_NOTIFY_PROGRESS)
        warning_text = "\n".join(captured.output)
        self.assertIn("ROVER_NOTIFY_TRANSPORT", warning_text)
        self.assertIn("MENISIK_NOTIFY_TRANSPORT", warning_text)

    def test_deprecation_warning_emitted_once_per_legacy_key(self) -> None:
        with mock.patch.dict(
            os.environ, {"ROVER_NOTIFY_STALL_SECONDS": "120"}, clear=False
        ):
            os.environ.pop("MENISIK_NOTIFY_STALL_SECONDS", None)
            reloaded = importlib.reload(config)
            self.assertEqual(reloaded.MENISIK_NOTIFY_STALL_SECONDS, 120)
            with mock.patch.object(reloaded.log, "warning") as warn:
                reloaded._env_raw("MENISIK_NOTIFY_STALL_SECONDS")
                reloaded._env_raw("MENISIK_NOTIFY_STALL_SECONDS")
        # already warned during reload; repeated reads stay silent
        warn.assert_not_called()


class EnvFileQuoteTests(unittest.TestCase):
    def tearDown(self) -> None:
        importlib.reload(config)

    def test_unquote_env_value_strips_matching_quotes_only(self) -> None:
        self.assertEqual(config._unquote_env_value('"-p -"'), "-p -")
        self.assertEqual(config._unquote_env_value("'-p -'"), "-p -")
        self.assertEqual(config._unquote_env_value("plain"), "plain")
        self.assertEqual(config._unquote_env_value('"unterminated'), '"unterminated')
        self.assertEqual(config._unquote_env_value('""'), "")
        self.assertEqual(config._unquote_env_value(""), "")

    def test_quoted_claude_args_in_env_file_parse_as_separate_cli_args(self) -> None:
        # Regression: CLAUDE_ARGS="-p -" (dotenv-quoted) was loaded with the quotes
        # kept, so shlex produced a single bogus argv token '"-p -"' and the Claude
        # CLI received it as the prompt instead of print-mode flags.
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("stub", encoding="utf-8")
            (root / "app").mkdir()
            (root / "app" / "builder.py").write_text("", encoding="utf-8")
            (root / "src" / "core").mkdir(parents=True)
            (root / "src" / "core" / "config.py").write_text("", encoding="utf-8")
            (root / ".env").write_text(
                'CLAUDE_ARGS="-p -"\n'
                "CODEX_ARGS=\"exec --skip-git-repo-check -s read-only -\"\n",
                encoding="utf-8",
            )
            with mock.patch.dict(
                os.environ,
                {"GITHUB_CONTRIBUTION_ENGINE_ROOT": str(root)},
                clear=False,
            ):
                for key in ("CLAUDE_ARGS", "CODEX_ARGS"):
                    os.environ.pop(key, None)
                reloaded = importlib.reload(config)
                self.assertEqual(reloaded.CLAUDE_ARGS, ["-p", "-"])
                self.assertEqual(
                    reloaded.CODEX_ARGS,
                    ["exec", "--skip-git-repo-check", "-s", "read-only", "-"],
                )


if __name__ == "__main__":
    unittest.main()

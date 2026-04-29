from __future__ import annotations

import unittest

from src.agent_models import (
    SUPPORTED_AGENT_TOOLS,
    SUPPORTED_MODEL_SERIES,
    get_runtime_profile,
    supports_agent_tool,
    supports_model_series,
)


class AgentModelSupportTests(unittest.TestCase):
    def test_supported_agent_tools_include_form_targets(self) -> None:
        self.assertIn("Codex", SUPPORTED_AGENT_TOOLS)
        self.assertIn("Claude Code", SUPPORTED_AGENT_TOOLS)
        self.assertIn("Aider", SUPPORTED_AGENT_TOOLS)

    def test_supported_model_series_include_form_targets(self) -> None:
        self.assertIn("GPT", SUPPORTED_MODEL_SERIES)
        self.assertIn("Claude", SUPPORTED_MODEL_SERIES)
        self.assertIn("Gemini", SUPPORTED_MODEL_SERIES)

    def test_support_lookup_accepts_known_values(self) -> None:
        self.assertTrue(supports_agent_tool("Codex"))
        self.assertTrue(supports_model_series("GPT"))

    def test_runtime_profile_has_non_empty_labels(self) -> None:
        profile = get_runtime_profile()
        self.assertTrue(profile.agent_tool)
        self.assertTrue(profile.model_series)

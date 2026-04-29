from __future__ import annotations

from dataclasses import dataclass

from src.config import AGENT_TOOL, MODEL_SERIES


SUPPORTED_AGENT_TOOLS = [
    "Codex",
    "Claude Code",
    "OpenCode",
    "Aider",
    "Cline",
    "Cursor",
    "Windsurf",
    "Other",
]

SUPPORTED_MODEL_SERIES = [
    "GPT",
    "Claude",
    "Gemini",
    "DeepSeek",
    "MiMo",
    "Doubao",
    "MiniMax",
    "Other",
]


@dataclass(frozen=True)
class AgentRuntimeProfile:
    agent_tool: str
    model_series: str
    backend: str


def get_runtime_profile() -> AgentRuntimeProfile:
    backend = "claude-cli" if AGENT_TOOL == "Claude Code" else "codex-cli"
    return AgentRuntimeProfile(
        agent_tool=AGENT_TOOL,
        model_series=MODEL_SERIES,
        backend=backend,
    )


def supports_agent_tool(name: str) -> bool:
    return name in SUPPORTED_AGENT_TOOLS


def supports_model_series(name: str) -> bool:
    return name in SUPPORTED_MODEL_SERIES

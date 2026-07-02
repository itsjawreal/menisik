from __future__ import annotations

import argparse
import re
from pathlib import Path


def _normalize_path(value: str | Path) -> str:
    return str(Path(value).expanduser()).replace("\\", "/")


def _require_absolute_file(path: str, label: str) -> str:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise ValueError(f"{label} must be an absolute path: {path}")
    return _normalize_path(candidate)


def _yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _render_menisik_block(menisik_mcp_bin: str) -> str:
    return "\n".join(
        [
            "  menisik:",
            f"    command: {_yaml_quote(menisik_mcp_bin)}",
            "    args: []",
            "    enabled: true",
        ]
    )


def _upsert_menisik_block(text: str, block: str) -> str:
    normalized = text if text.endswith("\n") or not text else text + "\n"
    root_re = r"(?ms)^mcp_servers:\s*\n(?P<body>(?:^  .*(?:\n|$))*)"
    menisik_re = r"(?ms)^  menisik:\s*\n(?:^    .*(?:\n|$))*"
    legacy_rover_re = r"(?ms)^  rover:\s*\n(?:^    .*(?:\n|$))*"

    match = re.search(root_re, normalized)
    if not match:
        suffix = "" if not normalized.strip() else "\n"
        return normalized + suffix + "mcp_servers:\n" + block + "\n"

    body = match.group("body")
    # Drop the pre-rename server block so the engine is not registered twice.
    body = re.sub(legacy_rover_re, "", body)
    if re.search(menisik_re, body):
        new_body = re.sub(menisik_re, block + "\n", body)
    else:
        new_body = body + block + "\n"
    return normalized[: match.start("body")] + new_body + normalized[match.end("body") :]


def install_hermes_config(
    *,
    menisik_mcp_bin: str,
    hermes_config_path: str | None = None,
) -> Path:
    normalized_menisik_mcp = _require_absolute_file(menisik_mcp_bin, "menisik_mcp_bin")
    config_path = Path(hermes_config_path).expanduser() if hermes_config_path else (Path.home() / ".hermes" / "config.yaml")
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated = _upsert_menisik_block(existing, _render_menisik_block(normalized_menisik_mcp))
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    return config_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Menisik MCP config into Hermes.")
    parser.add_argument("--menisik-mcp-bin", default="", help="Absolute path to the menisik-mcp executable.")
    parser.add_argument("--rover-mcp-bin", default="", help="Deprecated alias for --menisik-mcp-bin.")
    parser.add_argument("--config-path", default="", help="Optional override for ~/.hermes/config.yaml.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    menisik_mcp_bin = args.menisik_mcp_bin or args.rover_mcp_bin
    if not menisik_mcp_bin:
        raise SystemExit("--menisik-mcp-bin is required (or its deprecated --rover-mcp-bin alias).")
    path = install_hermes_config(
        menisik_mcp_bin=menisik_mcp_bin,
        hermes_config_path=args.config_path or None,
    )
    print(f"Installed Hermes config: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

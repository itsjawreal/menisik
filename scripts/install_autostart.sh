#!/usr/bin/env bash
# Install menisik-mcp as a systemd user service that starts automatically
# when WSL starts (with loginctl linger enabled).
#
# Usage:
#   bash scripts/install_autostart.sh
#
# To uninstall:
#   bash scripts/install_autostart.sh --uninstall

set -euo pipefail

SERVICE_NAME="menisik-daemon"
LEGACY_SERVICE_NAME="rover-daemon"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/$SERVICE_NAME.service"
LEGACY_SERVICE_FILE="$SERVICE_DIR/$LEGACY_SERVICE_NAME.service"
MENISIK_MCP_BIN="$HOME/.local/bin/menisik-mcp"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"

_green()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
_yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
_red()    { printf '\033[0;31m%s\033[0m\n' "$*"; }
_bold()   { printf '\033[1m%s\033[0m\n' "$*"; }

remove_legacy_service() {
    if [[ -f "$LEGACY_SERVICE_FILE" ]]; then
        _yellow "Removing legacy $LEGACY_SERVICE_NAME autostart service..."
        systemctl --user stop    "$LEGACY_SERVICE_NAME" 2>/dev/null || true
        systemctl --user disable "$LEGACY_SERVICE_NAME" 2>/dev/null || true
        rm -f "$LEGACY_SERVICE_FILE"
    fi
}

# ── Uninstall ────────────────────────────────────────────────
if [[ "${1:-}" == "--uninstall" ]]; then
    _yellow "Removing menisik-mcp autostart service..."
    systemctl --user stop   "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$SERVICE_FILE"
    remove_legacy_service
    systemctl --user daemon-reload 2>/dev/null || true
    _green "Done. menisik-mcp autostart removed."
    exit 0
fi

# ── Preflight ────────────────────────────────────────────────
_bold "=== Menisik MCP Autostart Installer ==="
echo

if [[ ! -f "$MENISIK_MCP_BIN" ]]; then
    # Fallbacks: venv bin, then the deprecated rover-mcp spellings
    for candidate in \
        "$PROJECT_DIR/.venv/bin/menisik-mcp" \
        "$HOME/.local/bin/rover-mcp" \
        "$PROJECT_DIR/.venv/bin/rover-mcp"; do
        if [[ -f "$candidate" ]]; then
            MENISIK_MCP_BIN="$candidate"
            break
        fi
    done
    if [[ ! -f "$MENISIK_MCP_BIN" ]]; then
        _red "menisik-mcp not found at $HOME/.local/bin/menisik-mcp"
        _red "Run 'pip install -e .' or the install script first."
        exit 1
    fi
fi

if ! command -v systemctl &>/dev/null; then
    _red "systemctl not found. Enable systemd in WSL: add 'systemd=true' under [boot] in /etc/wsl.conf, then restart WSL."
    exit 1
fi

mkdir -p "$SERVICE_DIR" "$LOG_DIR"

# ── Write service file ───────────────────────────────────────
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Menisik MCP Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
ExecStart=$MENISIK_MCP_BIN
Restart=on-failure
RestartSec=10
StandardOutput=append:$LOG_DIR/menisik-mcp.log
StandardError=append:$LOG_DIR/menisik-mcp.log
Environment=HOME=$HOME

[Install]
WantedBy=default.target
EOF

_green "Service file written: $SERVICE_FILE"

# Drop the pre-rename service so the daemon is not registered twice.
remove_legacy_service

# ── Enable + start ───────────────────────────────────────────
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

# Enable linger so the service starts without an interactive login
if command -v loginctl &>/dev/null; then
    loginctl enable-linger "$(whoami)" 2>/dev/null || true
fi

sleep 1
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    _green "menisik-mcp is running (systemd user service)."
else
    _yellow "menisik-mcp may not have started yet. Check with:"
    echo "  systemctl --user status $SERVICE_NAME"
    echo "  tail -f $LOG_DIR/menisik-mcp.log"
fi

echo
_bold "=== Next step ==="
echo "On Windows, run the following to auto-start WSL on login:"
echo
echo "  PowerShell (as user, not admin):"
echo "  & '$PROJECT_DIR/scripts/install_autostart_windows.ps1'"
echo
echo "Or manually add this to Windows Task Scheduler:"
echo "  Trigger          : At log on"
echo "  Action (Execute) : C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Python\\Python311\\pythonw.exe"
echo "  Arguments        : -m src.daemon"
echo "  Start in         : \\\\wsl.localhost\\Ubuntu-20.04\\home\\$(whoami)\\project\\menisik"

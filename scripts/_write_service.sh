#!/usr/bin/env bash
# Repo root: auto-detected from this script's location, overridable via PROJECT env var.
PROJECT="${PROJECT:-$(cd "$(dirname "$0")/.." && pwd)}"
SERVICE_FILE=$HOME/.config/systemd/user/menisik-mcp.service
LOG_DIR=$PROJECT/logs
DAEMON_BIN=$HOME/.local/bin/menisik-daemon

mkdir -p "$LOG_DIR"

cat > "$SERVICE_FILE" <<'UNIT'
[Unit]
Description=Menisik Daemon (PR monitor + Telegram bot)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
UNIT

# Inject paths
sed -i "s|^Restart=on-failure|WorkingDirectory=$PROJECT\nExecStart=$DAEMON_BIN\nRestart=on-failure|" "$SERVICE_FILE"
sed -i "/RestartSec=10/a StandardOutput=append:$LOG_DIR/menisik-daemon.log\nStandardError=append:$LOG_DIR/menisik-daemon.log\nEnvironment=HOME=$HOME" "$SERVICE_FILE"

systemctl --user daemon-reload
systemctl --user stop rover-mcp 2>/dev/null || true
systemctl --user disable rover-mcp 2>/dev/null || true
systemctl --user restart menisik-mcp
sleep 2
systemctl --user status menisik-mcp --no-pager

from __future__ import annotations

import json
import urllib.request

from src.config import TELEGRAM_TOKEN, TELEGRAM_CHAT


def notify(message: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": message}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass

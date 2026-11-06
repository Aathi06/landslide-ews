"""Send a message through a Telegram bot.

Setup: create a bot with @BotFather, then export
    TELEGRAM_BOT_TOKEN=...   TELEGRAM_CHAT_ID=...
Never put these in git. If they are missing, send_telegram() does nothing and returns False (dry run).
"""
import os

import httpx

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(text: str, token: str | None = None, chat_id: str | None = None) -> bool:
    """True if Telegram accepted the message. False if not configured or the request failed."""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        r = httpx.post(API_URL.format(token=token), json={"chat_id": chat_id, "text": text}, timeout=10)
        return r.status_code == 200 and bool(r.json().get("ok"))
    except (httpx.HTTPError, ValueError):
        return False

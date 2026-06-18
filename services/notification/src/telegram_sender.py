"""
Telegram Notification Sender — Smart Campus
"""

import os
import requests
from typing import Dict, Optional
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "mock-token-123456")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "mock-chat-id")
TELEGRAM_API_BASE = "https://api.telegram.org"


async def send_telegram(
    notification_id: str,
    alert_type: str,
    severity: str,
    message: str,
    source_service: str,
    related_event_id: Optional[str] = None,
) -> Dict:
    """
    Gửi thông báo qua Telegram.
    """
    try:
        # Tạo nội dung tin nhắn
        severity_emoji = {
            "LOW": "🟦",
            "MEDIUM": "🟨",
            "HIGH": "🟥",
            "CRITICAL": "⛔",
        }.get(severity.upper(), "ℹ️")

        telegram_message = f"""
{severity_emoji} **CẢNH BÁO SMART CAMPUS**

**Mã thông báo:** {notification_id}
**Mức độ:** {severity}
**Loại:** {alert_type}
**Nguồn:** {source_service}
**Nội dung:** {message}
**Thời gian:** {datetime.now(timezone.utc).isoformat(timespec="seconds")}
{"**Sự kiện liên quan:** " + related_event_id if related_event_id else ""}
        """

        # Nếu là mock token, chỉ in ra console
        if TELEGRAM_BOT_TOKEN == "mock-token-123456":
            print(f"[TELEGRAM MOCK] Gửi đến chat {TELEGRAM_CHAT_ID}:")
            print(telegram_message)
            return {
                "status": "sent",
                "channel": "telegram",
                "mode": "mock",
                "message": f"Message {notification_id} sent to Telegram (mock)",
            }

        # Gửi thực tế (nếu có token)
        url = f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": telegram_message,
            "parse_mode": "Markdown",
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        return {
            "status": "sent",
            "channel": "telegram",
            "mode": "real",
            "message": f"Message {notification_id} sent to Telegram successfully",
        }

    except Exception as e:
        print(f"[TELEGRAM ERROR] Failed to send notification {notification_id}: {str(e)}")
        return {
            "status": "failed",
            "channel": "telegram",
            "error": str(e),
        }

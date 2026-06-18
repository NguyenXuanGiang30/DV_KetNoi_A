"""
SMS Notification Sender (Mock) — Smart Campus
"""

import os
from typing import Dict, Optional, List
from datetime import datetime, timezone

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")
PHONE_NUMBERS = os.getenv("PHONE_NUMBERS", "+84903000000").split(";")


async def send_sms(
    notification_id: str,
    alert_type: str,
    severity: str,
    message: str,
    source_service: str,
    related_event_id: Optional[str] = None,
    recipients: Optional[List[str]] = None,
) -> Dict:
    """
    Gửi thông báo qua SMS (Mock implementation).
    Trong thực tế sẽ gọi đến Twilio, Nexmo, hoặc nhà cung cấp SMS khác.
    """
    try:
        phone_list = recipients or PHONE_NUMBERS

        # Tạo nội dung SMS (tối đa 160 ký tự cho một SMS)
        sms_content = f"[{severity}] {alert_type}: {message} (ID: {notification_id})"
        
        # Truncate nếu quá dài
        if len(sms_content) > 160:
            sms_content = sms_content[:157] + "..."

        # Mock implementation - chỉ in ra console
        print(f"[SMS MOCK] Gửi SMS đến {len(phone_list)} số điện thoại:")
        for phone in phone_list:
            print(f"  📱 {phone}: {sms_content}")

        return {
            "status": "sent",
            "channel": "sms",
            "mode": "mock",
            "recipients": phone_list,
            "message": f"SMS {notification_id} sent to {len(phone_list)} recipients (mock)",
        }

    except Exception as e:
        print(f"[SMS ERROR] Failed to send SMS {notification_id}: {str(e)}")
        return {
            "status": "failed",
            "channel": "sms",
            "error": str(e),
        }

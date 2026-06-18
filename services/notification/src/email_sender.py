"""
Email Notification Sender — Smart Campus
"""

import os
import smtplib
from typing import Dict, Optional, List
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "notification@smart-campus.local")
EMAIL_TO_LIST = os.getenv("EMAIL_TO_LIST", "admin@smart-campus.local").split(";")


async def send_email(
    notification_id: str,
    alert_type: str,
    severity: str,
    message: str,
    source_service: str,
    related_event_id: Optional[str] = None,
    recipients: Optional[List[str]] = None,
) -> Dict:
    """
    Gửi thông báo qua Email.
    """
    try:
        recipients_list = recipients or EMAIL_TO_LIST

        # Tạo nội dung email
        severity_color = {
            "LOW": "#0066CC",
            "MEDIUM": "#FFCC00",
            "HIGH": "#FF6600",
            "CRITICAL": "#CC0000",
        }.get(severity.upper(), "#0066CC")

        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {severity_color}; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                    .content {{ margin-top: 20px; line-height: 1.6; }}
                    .field {{ margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-left: 4px solid {severity_color}; }}
                    .label {{ font-weight: bold; color: {severity_color}; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ CẢNH BÁO SMART CAMPUS</h1>
                        <p>Mức độ: <strong>{severity}</strong></p>
                    </div>
                    <div class="content">
                        <div class="field">
                            <div class="label">Mã thông báo:</div>
                            {notification_id}
                        </div>
                        <div class="field">
                            <div class="label">Loại cảnh báo:</div>
                            {alert_type}
                        </div>
                        <div class="field">
                            <div class="label">Nguồn:</div>
                            {source_service}
                        </div>
                        <div class="field">
                            <div class="label">Nội dung:</div>
                            {message}
                        </div>
                        {f'<div class="field"><div class="label">Sự kiện liên quan:</div>{related_event_id}</div>' if related_event_id else ""}
                        <div class="field">
                            <div class="label">Thời gian:</div>
                            {datetime.now(timezone.utc).isoformat(timespec="seconds")}
                        </div>
                    </div>
                    <div class="footer">
                        <p>Đây là thông báo tự động từ hệ thống Smart Campus</p>
                        <p>Vui lòng không trả lời email này</p>
                    </div>
                </div>
            </body>
        </html>
        """

        # Nếu là localhost (mock), chỉ in ra console
        if SMTP_SERVER == "localhost" and SMTP_PORT == 1025:
            print(f"[EMAIL MOCK] Gửi đến {', '.join(recipients_list)}:")
            print(f"Subject: [{severity}] {alert_type}: {message}")
            print(f"Body:\n{html_content}")
            return {
                "status": "sent",
                "channel": "email",
                "mode": "mock",
                "recipients": recipients_list,
                "message": f"Email {notification_id} sent to {len(recipients_list)} recipients (mock)",
            }

        # Gửi email thực tế
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{severity}] {alert_type}: {message}"
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(recipients_list)

        msg.attach(MIMEText(html_content, "html"))

        # Kết nối SMTP và gửi
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients_list, msg.as_string())

        return {
            "status": "sent",
            "channel": "email",
            "mode": "real",
            "recipients": recipients_list,
            "message": f"Email {notification_id} sent to {len(recipients_list)} recipients",
        }

    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send notification {notification_id}: {str(e)}")
        return {
            "status": "failed",
            "channel": "email",
            "error": str(e),
        }

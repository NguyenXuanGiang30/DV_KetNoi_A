"""
Dashboard Storage — Smart Campus
Lưu thông báo để hiển thị trên dashboard
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import json

# In-memory storage cho dashboard (trong production sẽ dùng database)
DASHBOARD_NOTIFICATIONS: List[Dict] = []
MAX_STORED_NOTIFICATIONS = 1000


class DashboardStorage:
    """
    Quản lý lưu trữ thông báo cho dashboard.
    """

    @staticmethod
    def save_notification(
        notification_id: str,
        alert_type: str,
        severity: str,
        message: str,
        source_service: str,
        related_event_id: Optional[str] = None,
        channels_sent: Optional[List[str]] = None,
    ) -> Dict:
        """
        Lưu thông báo vào dashboard storage.
        """
        try:
            notification_item = {
                "notification_id": notification_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "source_service": source_service,
                "related_event_id": related_event_id,
                "channels_sent": channels_sent or [],
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "read": False,
                "acknowledged": False,
            }

            DASHBOARD_NOTIFICATIONS.append(notification_item)

            # Giữ chỉ những notification mới nhất
            if len(DASHBOARD_NOTIFICATIONS) > MAX_STORED_NOTIFICATIONS:
                DASHBOARD_NOTIFICATIONS.pop(0)

            print(
                f"[DASHBOARD] Thông báo {notification_id} đã được lưu vào dashboard storage"
            )

            return {
                "status": "saved",
                "channel": "dashboard",
                "notification_id": notification_id,
            }

        except Exception as e:
            print(f"[DASHBOARD ERROR] Failed to save notification {notification_id}: {str(e)}")
            return {
                "status": "failed",
                "channel": "dashboard",
                "error": str(e),
            }

    @staticmethod
    def get_recent_notifications(limit: int = 20) -> List[Dict]:
        """
        Lấy thông báo gần đây từ dashboard.
        """
        return DASHBOARD_NOTIFICATIONS[-limit:][::-1]

    @staticmethod
    def mark_as_read(notification_id: str) -> bool:
        """
        Đánh dấu thông báo là đã đọc.
        """
        for notif in DASHBOARD_NOTIFICATIONS:
            if notif["notification_id"] == notification_id:
                notif["read"] = True
                return True
        return False

    @staticmethod
    def acknowledge_notification(notification_id: str) -> bool:
        """
        Xác nhận thông báo (nhân viên đã xử lý).
        """
        for notif in DASHBOARD_NOTIFICATIONS:
            if notif["notification_id"] == notification_id:
                notif["acknowledged"] = True
                return True
        return False

    @staticmethod
    def get_statistics() -> Dict:
        """
        Lấy thống kê thông báo.
        """
        total = len(DASHBOARD_NOTIFICATIONS)
        unread = sum(1 for n in DASHBOARD_NOTIFICATIONS if not n.get("read", False))
        unacknowledged = sum(
            1 for n in DASHBOARD_NOTIFICATIONS if not n.get("acknowledged", False)
        )
        
        severity_count = {}
        for notif in DASHBOARD_NOTIFICATIONS:
            severity = notif.get("severity", "UNKNOWN")
            severity_count[severity] = severity_count.get(severity, 0) + 1

        return {
            "total_notifications": total,
            "unread_count": unread,
            "unacknowledged_count": unacknowledged,
            "severity_distribution": severity_count,
        }

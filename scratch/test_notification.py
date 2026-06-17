import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add services/notification/src to python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "services" / "notification" / "src"))

load_dotenv(dotenv_path=BASE_DIR / ".env")

from main import send_telegram_alert, send_email_alert

def test_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id or "your_bot_token" in token:
        print("[WARNING] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured in .env. Skipping Telegram test.")
        return
        
    print("[INFO] Sending test Telegram message...")
    res = send_telegram_alert(
        message="This is a test notification from the Smart Campus Dev Environment!",
        severity="INFO",
        alert_type="SYSTEM_TEST"
    )
    if res:
        print("[OK] Telegram alert sent successfully!")
    else:
        print("[FAIL] Telegram alert failed.")

def test_email():
    user = os.getenv("SMTP_USER")
    if not user or "your_email" in user:
        print("[WARNING] SMTP credentials not configured in .env. Skipping Email test.")
        return
        
    print("[INFO] Sending test Email...")
    res = send_email_alert(
        message="This is a test notification from the Smart Campus Dev Environment!",
        severity="INFO",
        alert_type="SYSTEM_TEST"
    )
    if res:
        print("[OK] Email alert sent successfully!")
    else:
        print("[FAIL] Email alert failed.")

if __name__ == "__main__":
    print("--- Notification Service Test Script ---")
    test_telegram()
    test_email()
    print("----------------------------------------")

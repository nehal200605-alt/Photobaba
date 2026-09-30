import os
from dotenv import load_dotenv

load_dotenv()

# Required
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN missing!")

# Optional APIs (baad me add karenge)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Railway public URL (auto-detect karega)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8080))

# Admin ID (sirf tu use karega, optional)
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

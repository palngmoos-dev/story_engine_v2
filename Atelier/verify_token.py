import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("Error: No token found in .env")
    exit(1)

url = f"https://api.telegram.org/bot{token}/getMe"
try:
    r = requests.get(url, timeout=10)
    print(r.text)
except Exception as e:
    print(f"Error connecting to Telegram: {e}")

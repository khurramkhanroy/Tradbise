import datetime
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import pytz
import requests
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8982239237:AAGJCgl8qT6c4wPG42yyVXf_wuu7_DM8Pr4"
)
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7211531020")

last_morning_msg_date = None


# ==================== TELEGRAM UTILS ====================
def send_telegram_alert(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f"Telegram error: {e}")


def check_daily_good_morning():
  global last_morning_msg_date
  pkt = pytz.timezone("Asia/Karachi")
  now_pkt = datetime.datetime.now(pkt)

  if now_pkt.hour == 8 and now_pkt.minute < 5:
    today_str = now_pkt.strftime("%Y-%m-%d")
    if last_morning_msg_date != today_str:
      morning_msg = (
          "☀️ *Good Morning Boss!*\n\nYour Tradebise 1H Signal Monitor (XAUUSD"
          " & BTCUSD) is Active 24/7! 🚀📈"
      )
      send_telegram_alert(morning_msg)
      last_morning_msg_date = today_str


# ==================== TRADEBISE SCRAPER ====================
def check_tradebise_market():
  url = "https://tradebise.com/signals"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }

  pkt = pytz.timezone("Asia/Karachi")
  current_time = datetime.datetime.now(pkt).strftime("%I:%M %p")

  print(
      f"[{current_time}] Fetching Tradebise website (5-Min Monitoring"
      " Cycle)..."
  )

  try:
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
      print(f"Website status code: {res.status_code}")
      return

    msg = (
        "🚨 *TRADEBISE 1H SIGNAL MONITOR*\n\n"
        f"⏰ *Check Time:* `{current_time} PKT`\n"
        "🎯 *Monitored Pairs:* XAUUSD (Gold) | BTCUSD (Bitcoin)\n"
        "📊 *Timeframe:* 1-Hour (1H)\n\n"
        "➡️ Tradebise page updated. Check latest 1H signals here:\n"
        "🔗 https://tradebise.com/signals"
    )

    send_telegram_alert(msg)

  except Exception as e:
    print(f"Scraper error: {e}")


# ==================== RENDER DUMMY WEBSERVER ====================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(
        b"Tradebise XAUUSD & BTCUSD 1H Signal Monitor is Active!"
    )


def run_dummy_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
  server.serve_forever()


# ==================== MAIN LOOP ====================
if __name__ == "__main__":
  threading.Thread(target=run_dummy_server, daemon=True).start()

  send_telegram_alert(
      "🚀 *Tradebise 1H Signal Monitor Online!*\n\nMonitoring *XAUUSD* &"
      " *BTCUSD* every 5 minutes."
  )

  while True:
    check_daily_good_morning()
    check_tradebise_market()
    sys.stdout.flush()
    time.sleep(300)
  

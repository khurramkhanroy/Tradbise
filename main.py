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

PAIRS_URLS = {
    "GOLD (XAUUSD)": "https://tradebise.com/signals/xauusd",
    "BITCOIN (BTCUSD)": "https://tradebise.com/signals/btcusdt",
}

last_signal_text = {"GOLD (XAUUSD)": None, "BITCOIN (BTCUSD)": None}
last_morning_msg_date = None


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
          "☀️ *Good Morning Boss!*\n\nTradebise Direct Monitor Active 24/7! 🚀📈"
      )
      send_telegram_alert(morning_msg)
      last_morning_msg_date = today_str


def fetch_and_parse_signal(pair_name, url):
  global last_signal_text
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }

  pkt = pytz.timezone("Asia/Karachi")
  current_time = datetime.datetime.now(pkt).strftime("%I:%M %p")

  try:
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
      return

    soup = BeautifulSoup(res.text, "html.parser")

    # Garbage / Loading texts ko filter karna
    text_content = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text_content.split("\n") if line.strip()]

    # Strict filtering: Agar content "Search market" ya lazy-loading header ho toh ignore karein
    filtered_lines = [
        line
        for line in lines
        if line.lower()
        not in [
            "search market",
            "tradebise",
            "signals",
            "home",
            "watchlist",
            "menu",
        ]
    ]

    # Check if BUY or SELL is strictly present in page content
    full_text = " ".join(filtered_lines).upper()
    if "BUY" not in full_text and "SELL" not in full_text:
      print(
          f"[{pair_name}] No active BUY/SELL signal found (Page still loading"
          " or Neutral)."
      )
      return

    extracted_payload = "\n".join(filtered_lines[:12])

    if extracted_payload and extracted_payload != last_signal_text[pair_name]:
      msg = (
          "🚨 *TRADEBISE SIGNAL DETECTED* 🚨\n\n"
          f"📌 *Asset:* `{pair_name}`\n"
          f"⏰ *Time:* `{current_time} PKT`\n\n"
          "📊 *Signal Details:*\n"
          "-----------------------------------\n"
          f"{extracted_payload}\n"
          "-----------------------------------\n\n"
          f"🔗 [Open Direct Dashboard]({url})"
      )

      send_telegram_alert(msg)
      last_signal_text[pair_name] = extracted_payload
    else:
      print(f"[{pair_name}] Duplicate/No update.")

  except Exception as e:
    print(f"Scraper error for {pair_name}: {e}")


def run_monitoring_cycle():
  for pair_name, url in PAIRS_URLS.items():
    fetch_and_parse_signal(pair_name, url)
    time.sleep(3)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Tradebise Monitor Active")


def run_dummy_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
  server.serve_forever()


if __name__ == "__main__":
  threading.Thread(target=run_dummy_server, daemon=True).start()

  send_telegram_alert(
      "🚀 *Tradebise Filtered Monitor Fixed & Active!*\n\nAb 'Search market'"
      " jaise kachra messages nahi aayenge."
  )

  while True:
    check_daily_good_morning()
    run_monitoring_cycle()
    sys.stdout.flush()
    time.sleep(300)
                           

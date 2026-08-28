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

# Target direct links for monitoring
PAIRS_URLS = {
    "GOLD (XAUUSD)": "https://tradebise.com/signals/xauusd",
    "BITCOIN (BTCUSD)": "https://tradebise.com/signals/btcusdt",
}

last_signal_text = {"GOLD (XAUUSD)": None, "BITCOIN (BTCUSD)": None}
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
          "☀️ *Good Morning Boss!*\n\nTradebise Direct Monitor (XAUUSD & BTCUSD)"
          " is Active 24/7! 🚀📈"
      )
      send_telegram_alert(morning_msg)
      last_morning_msg_date = today_str


# ==================== TRADEBISE SCRAPER ====================
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

    # Extract dynamic signal details container
    signal_box = soup.find(
        "div",
        class_=lambda c: c
        and any(x in c.lower() for x in ["signal", "result", "card", "analysis"]),
    )

    if not signal_box:
      signal_box = soup.body

    if signal_box:
      extracted_text = signal_box.get_text(separator="\n", strip=True)

      # Filtering out non-signal noise / basic checks
      if "WAIT" in extracted_text.upper() and len(extracted_text) < 50:
        print(f"[{pair_name}] Currently in WAIT status.")
        return

      # Send alert only if a NEW signal is generated or text changes
      if extracted_text and extracted_text != last_signal_text[pair_name]:
        # Clean up lines for neat display
        lines = [
            line.strip() for line in extracted_text.split("\n") if line.strip()
        ]
        formatted_details = "\n".join(lines[:15])  # Top details tarteeb-wise

        msg = (
            "🚨 *NEW TRADEBISE SIGNAL DETECTED* 🚨\n\n"
            f"📌 *Asset:* `{pair_name}`\n"
            f"⏰ *Time:* `{current_time} PKT`\n\n"
            "📊 *Website Details (Tarteeb-wise):*\n"
            "-----------------------------------\n"
            f"{formatted_details}\n"
            "-----------------------------------\n\n"
            f"🔗 [Direct Chart Link]({url})"
        )

        send_telegram_alert(msg)
        last_signal_text[pair_name] = extracted_text
      else:
        print(f"[{pair_name}] No change in signal details.")

  except Exception as e:
    print(f"Scraper error for {pair_name}: {e}")


def run_monitoring_cycle():
  pkt = pytz.timezone("Asia/Karachi")
  current_time = datetime.datetime.now(pkt).strftime("%I:%M %p")
  print(f"[{current_time}] Visiting Gold & BTC direct links...")

  for pair_name, url in PAIRS_URLS.items():
    fetch_and_parse_signal(pair_name, url)
    time.sleep(3)


# ==================== DUMMY WEBSERVER ====================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(
        b"Tradebise XAUUSD & BTCUSD Direct Link Scraper Active 24/7!"
    )


def run_dummy_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
  server.serve_forever()


# ==================== MAIN LOOP ====================
if __name__ == "__main__":
  threading.Thread(target=run_dummy_server, daemon=True).start()

  send_telegram_alert(
      "🚀 *Tradebise Direct Link Monitor Online!*\n\nChecking *XAUUSD (Gold)*"
      " & *BTCUSD (Bitcoin)* direct links every 5 minutes."
  )

  while True:
    check_daily_good_morning()
    run_monitoring_cycle()
    sys.stdout.flush()
    time.sleep(300)
                           

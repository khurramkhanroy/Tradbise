import datetime
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import pytz
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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


def get_headless_driver():
  options = Options()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-gpu")
  options.add_argument(
      "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  )
  service = Service(ChromeDriverManager().install())
  return webdriver.Chrome(service=service, options=options)


def fetch_and_parse_signal():
  global last_signal_text
  pkt = pytz.timezone("Asia/Karachi")
  current_time = datetime.datetime.now(pkt).strftime("%I:%M %p")

  driver = None
  try:
    driver = get_headless_driver()

    for pair_name, url in PAIRS_URLS.items():
      try:
        print(f"[{current_time}] Opening {pair_name} page...")
        driver.get(url)

        # 1.5 Minute (90 Seconds) mandatory wait for chart & signal generation
        print(
            f"Waiting 90 seconds for {pair_name} chart auto-load and AI"
            " analysis..."
        )
        time.sleep(90)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        full_text = soup.get_text(separator="\n", strip=True)

        lines = [
            line.strip() for line in full_text.split("\n") if line.strip()
        ]

        # Filter out static layout junk
        ignore_keywords = [
            "sign up free",
            "unlock 30 days",
            "log in",
            "user",
            "free",
            "extreme volatility",
            "prediction meets perfection",
            "search market",
        ]
        clean_lines = [
            line
            for line in lines
            if not any(ign in line.lower() for ign in ignore_keywords)
        ]

        # Verification check: Actual signal metrics must be present
        analysis_content = "\n".join(clean_lines)
        if not any(
            key in analysis_content.upper()
            for key in ["ENTRY", "TARGET", "STOP LOSS", "TP", "BUY", "SELL"]
        ):
          print(
              f"[{pair_name}] Signal output not fully ready yet. Skipping noise."
          )
          continue

        formatted_signal = "\n".join(clean_lines[:12])

        if formatted_signal and formatted_signal != last_signal_text[pair_name]:
          msg = (
              "🚨 *ACCURATE TRADEBISE SIGNAL DETECTED* 🚨\n\n"
              f"📌 *Asset:* `{pair_name}`\n"
              f"⏰ *Time:* `{current_time} PKT`\n\n"
              "📊 *Signal & Analysis Details:*\n"
              "-----------------------------------\n"
              f"{formatted_signal}\n"
              "-----------------------------------\n\n"
              f"🔗 [Direct Chart Link]({url})"
          )
          send_telegram_alert(msg)
          last_signal_text[pair_name] = formatted_signal

      except Exception as inner_e:
        print(f"Error processing {pair_name}: {inner_e}")

  except Exception as e:
    print(f"Driver initialization failed: {e}")
  finally:
    if driver:
      driver.quit()


# ==================== DUMMY WEBSERVER ====================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Tradebise 90s Delay Scraper Active")


def run_dummy_server():
  port = int(os.environ.get("PORT", 10000))
  server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
  server.serve_forever()


if __name__ == "__main__":
  threading.Thread(target=run_dummy_server, daemon=True).start()

  send_telegram_alert(
      "🚀 *Tradebise Bot Updated!*\nNow waiting full 90 seconds on page for"
      " chart & signal processing."
  )

  while True:
    fetch_and_parse_signal()
    sys.stdout.flush()
    time.sleep(300)
      

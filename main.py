import email
import imaplib
import threading
import time
from bs4 import BeautifulSoup
from flask import Flask

# --- CONFIGURAZIONE ---
IMAP_SERVER = "imap.gmail.com"
EMAIL_USER = "gargiuloemanuele6@gmail.com"
EMAIL_PASS = "skrgbcdbtgofpqlb"
TARGET_SENDER = "noreply@tradingview.com"

# Inizializziamo Flask per tenere vivo il servizio su Render
app = Flask(__name__)


@app.route("/")
def home():
  return "Il bot TradingView è attivo e in ascolto!"


def pulisci_html(testo_html):
  soup = BeautifulSoup(testo_html, "html.parser")
  return soup.get_text(separator="\n", strip=True)


def controlla_email():
  print("Bot cloud avviato... In ascolto dei segnali.")
  while True:
    try:
      mail = imaplib.IMAP4_SSL(IMAP_SERVER)
      mail.login(EMAIL_USER, EMAIL_PASS)
      mail.select("inbox")

      status, messages = mail.search(None, f'(UNSEEN FROM "{TARGET_SENDER}")')

      for num in messages[0].split():
        status, data = mail.fetch(num, "(RFC822)")
        for response_part in data:
          if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            corpo_grezzo = ""
            if msg.is_multipart():
              for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ["text/plain", "text/html"]:
                  payload = part.get_payload(decode=True)
                  if payload:
                    corpo_grezzo = payload.decode(errors="ignore")
                    break
            else:
              payload = msg.get_payload(decode=True)
              if payload:
                corpo_grezzo = payload.decode(errors="ignore")

            corpo_testo = pulisci_html(corpo_grezzo)

            if "AZIONE:" in corpo_testo:
              print("\n--- SEGNALE DI TRADING VALIDATO ---")
              print(corpo_testo)
            else:
              print("[Ignorata] Avviso di servizio TradingView.")

      mail.logout()
    except Exception as e:
      print(f"Errore durante il controllo delle email: {e}")

    time.sleep(60)


if __name__ == "__main__":
  # Avviamo il controllo email in un thread separato
  t = threading.Thread(target=controlla_email)
  t.daemon = True
  t.start()

  # Avviamo il server Flask sulla porta richiesta da Render (o di default sulla 5000)
  import os

  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)

import os, telebot, threading, flask

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_VOGUE")
bot = telebot.TeleBot(TOKEN)

# --- RESET WEBHOOK (Fondamentale se il bot è "muto") ---
bot.remove_webhook()

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ Test OK: Il bot riceve i messaggi!")

# --- SERVER PER HEALTH CHECK ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "HEALTHY"

if __name__ == "__main__":
    print("Avvio Diagnostica...")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

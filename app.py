import os
import telebot
import google.generativeai as genai
import threading
import time
import gradio as gr

# Recupero le chiavi
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# MASTER PROMPT VOGUE
ISTRUZIONI_SISTEMA = """
Sei Moltbot, assistente fotografo per Valeria Cross.
1. USA SEMPRE il file caricato come riferimento volto.
2. SOGGETTO: Valeria Cross (60 anni, italiano, occhiali Vogue Havana, capelli grigio platino).
3. FISICO: Transmaschile, 180cm, 85kg, Coppa D.
4. TECNICA: 85mm, f/2.8, Global Illumination, Frequency Separation.
5. WATERMARK: 'feat. Valeria Cross 👠' (corsivo champagne, basso a sinistra).
"""

def avvia_bot():
    genai.configure(api_key=API_KEY)
    
    # CORREZIONE: Usiamo il nome standard 'gemini-1.5-flash'
    # Ora che hai aggiornato requirements.txt, questo funzionerà.
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=ISTRUZIONI_SISTEMA)

    bot = telebot.TeleBot(TOKEN)
    try:
        bot.remove_webhook()
    except:
        pass

    @bot.message_handler(func=lambda m: True)
    def rispondi(m):
        try:
            risposta = model.generate_content(m.text)
            bot.reply_to(m, risposta.text)
        except Exception as e:
            bot.reply_to(m, f"⚠️ Errore: {e}")

    bot.infinity_polling(skip_pending=True)

# Dummy server
def interfaccia_web(x): return "Online"
threading.Thread(target=avvia_bot, daemon=True).start()
gr.Interface(fn=interfaccia_web, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

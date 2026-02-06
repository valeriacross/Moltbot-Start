import os
import telebot
import google.generativeai as genai
import threading
import time
import requests
import gradio as gr
import io

# Recupero chiavi
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Configurazione Google
genai.configure(api_key=API_KEY)

# ISTRUZIONI MASTER (Identità Valeria)
SYSTEM_PROMPT = """
Sei Moltbot, esperto fotografo Vogue. 
SPECIFICHE FISICHE OBBLIGATORIE:
- Valeria Cross: 180cm, 85kg, coppa D, transmaschile.
- Tratti: 60 anni, italiano, capelli grigio platino, occhiali Vogue Havana.
PARAMETRI TECNICI:
- Ottica 85mm, f/2.8, Global Illumination.
- Risoluzione massima (4.2MPX).
- Watermark: 'feat. Valeria Cross 👠' in basso a sinistra (corsivo champagne).
"""

def avvia_bot():
    # USIAMO IL NOME ESATTO DALLO SCREENSHOT
    text_model = genai.GenerativeModel('gemini-flash-latest', system_instruction=SYSTEM_PROMPT)
    imagen = genai.GenerativeModel('imagen-3.0-generate-001') 
    
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(func=lambda m: True)
    def scatta(m):
        wait_msg = bot.reply_to(m, "📸 Moltbot sta preparando il set... Attendi.")
        try:
            # 1. Gemini Flash crea il prompt testuale
            prompt_res = text_model.generate_content(f"Genera prompt Imagen per: {m.text}")
            
            # 2. Imagen genera l'immagine (Billing Attivo sblocca questo passaggio)
            img_res = imagen.generate_content(prompt_res.text)
            
            # 3. Spedizione su Telegram
            for image in img_res.images:
                img_io = io.BytesIO()
                image._pil_image.save(img_io, format='PNG')
                img_io.seek(0)
                bot.send_photo(m.chat.id, img_io, caption="Ecco lo scatto definitivo. ✨")
            
            bot.delete_message(m.chat.id, wait_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Errore Tecnico: {e}", m.chat.id, wait_msg.message_id)

    bot.infinity_polling(skip_pending=True)

# Ping Keep-Alive
def ping():
    while True:
        try: requests.get("https://moltbot-start.onrender.com")
        except: pass
        time.sleep(600)

threading.Thread(target=avvia_bot, daemon=True).start()
threading.Thread(target=ping, daemon=True).start()
gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

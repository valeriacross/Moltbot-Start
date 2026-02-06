import os
import telebot
import google.generativeai as genai
import threading
import time
import requests
import gradio as gr
from PIL import Image
import io

# Chiavi
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Configurazione Google
genai.configure(api_key=API_KEY)

# MASTER PROMPT VOGUE (Identità Valeria)
SYSTEM_PROMPT = """
Sei Moltbot, assistente fotografo di Valeria Cross. 
PARAMETRI FISSI PER OGNI IMMAGINE:
- Soggetto: Valeria Cross (60 anni, italiana, occhiali Vogue Havana, capelli grigio platino).
- Fisico: 180cm, 85kg, coppa D, transmaschile.
- Tecnica: 85mm, f/2.8, Global Illumination, 8K.
- Watermark obbligatorio: 'feat. Valeria Cross 👠' in basso a sinistra, corsivo champagne.
"""

def avvia_bot():
    # Modelli: Flash per pensare, Imagen per creare
    text_model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
    imagen = genai.GenerativeModel('imagen-3.0-generate-001') # Ora che hai il billing, questo si attiva
    
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(func=lambda m: True)
    def gestisci(m):
        msg = bot.reply_to(m, "📸 Moltbot sta preparando il set... un momento.")
        try:
            # 1. Gemini crea il prompt tecnico perfetto
            prompt_response = text_model.generate_content(f"Crea il prompt per Imagen per questa richiesta: {m.text}")
            prompt_tecnico = prompt_response.text
            
            # 2. Imagen genera l'immagine
            result = imagen.generate_content(prompt_tecnico)
            
            # 3. Estrai e invia l'immagine
            for image in result.images:
                img_byte_arr = io.BytesIO()
                image._pil_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                bot.send_photo(m.chat.id, img_byte_arr, caption="Ecco il tuo scatto, Valeria. ✨")
            
            bot.delete_message(m.chat.id, msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"⚠️ Errore durante lo scatto: {e}", m.chat.id, msg.message_id)

    bot.infinity_polling(skip_pending=True)

# Ping per tenere sveglio Render
def keep_alive():
    while True:
        try: requests.get("https://moltbot-start.onrender.com")
        except: pass
        time.sleep(600)

threading.Thread(target=avvia_bot, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()
gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

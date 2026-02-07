import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr
from PIL import Image

# Setup Chiavi
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Identità Valeria Cross
SYSTEM_PROMPT = """Soggetto: Valeria Cross, 60 anni, transmaschile, 180cm, 85kg, coppa D. 
Look: Capelli grigio platino, occhiali Vogue Havana. 
Stile: Vogue Editoriale, 85mm, f/2.8, 8K, watermark 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        # Modelli dallo screenshot di AI Studio
        text_model = genai.GenerativeModel('gemini-flash-latest')
        # Imagen 3 per le immagini
        imagen = genai.GenerativeModel('imagen-3.0-generate-001')
        
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Moltbot in azione...")
            try:
                # 1. Crea il prompt tecnico
                p_res = text_model.generate_content(f"{SYSTEM_PROMPT}. Crea prompt per: {m.text}")
                
                # 2. Genera l'immagine (Sintassi standard corretta)
                response = imagen.generate_content(p_res.text)
                
                # 3. Estrai e invia
                if response.candidates:
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if part.inline_data:
                                bot.send_photo(m.chat.id, part.inline_data.data, caption="Valeria Cross ✨")
                
                bot.delete_message(m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait.message_id)

        bot.infinity_polling(skip_pending=True)
    except Exception as startup_error:
        print(f"CRASH: {startup_error}")

def web_service():
    gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

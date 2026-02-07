import os
import telebot
from google import genai
from google.genai import types
import io
import threading
import gradio as gr
import traceback
import sys

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 60 anni.
Viso: Maschile saggio, barba grigia corta (6cm), occhiali Vogue Havana ottagonali.
Corpo: Silhouette femminile voluttuosa, seno coppa D, fianchi morbidi, 180cm, 85kg.
Rendering: Global Illumination, Fresnel Effect, subsurface scattering, 8K.
Stile: Vogue Editorial. Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        def genera_valeria(m, prompt_text, images=None):
            wait = bot.reply_to(m, "📸 Moltbot in azione...")
            try:
                contents = [SYSTEM_PROMPT, f"Genera: {prompt_text}"]
                if images:
                    contents.extend(images)

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        safety_settings=[types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")]
                    )
                )
                
                image_sent = False
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            photo_stream = io.BytesIO(part.inline_data.data)
                            photo_stream.name = 'valeria_cross.png'
                            bot.send_photo(m.chat.id, photo_stream, caption="feat. Valeria Cross 👠")
                            image_sent = True
                            break
                
                if image_sent:
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Il modello ha risposto ma non ha prodotto immagini (possibile filtro sicurezza).", m.chat.id, wait.message_id)
            
            except Exception:
                # Recupera i dettagli dell'errore (tipo e riga)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                fname = os.path.split(exc_traceback.tb_frame.f_code.co_filename)[1]
                errore_dettagliato = f"❌ **ERRORE TECNICO**\n\n" \
                                     f"**Tipo:** {exc_type.__name__}\n" \
                                     f"**Messaggio:** {exc_value}\n" \
                                     f"**File:** {fname}\n" \
                                     f"**Linea:** {exc_traceback.tb_lineno}"
                bot.edit_message_text(errore_dettagliato, m.chat.id, wait.message_id, parse_mode="Markdown")

        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            try:
                file_info = bot.get_file(m.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                img_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
                prompt = m.caption if m.caption else "Ritratto di Valeria Cross."
                genera_valeria(m, prompt, [img_part])
            except Exception as e:
                bot.reply_to(m, f"❌ Errore nel caricamento foto: {e}")

        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            genera_valeria(m, m.text)

        print("Moltbot Online con Error Reporting.")
        bot.infinity_polling(skip_pending=True)
    
    except Exception as e:
        print(f"CRASH AVVIO: {e}")

def web_service():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

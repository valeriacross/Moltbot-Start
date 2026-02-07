import os
import telebot
from google import genai
from google.genai import types
import io
import threading
import gradio as gr
import sys

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

# MASTER PROMPT: Focus su VOLUMI e CONTRASTO (per evitare il risultato "piatto")
SYSTEM_PROMPT = """ARTISTIC CONCEPT: 'The Gender Fluid Diva'. 
Subject: Valeria Cross, 60yo distinguished man.
Face: Masculine, wise, platinum hair, short grey beard, octagonal Havana glasses.
Body Architecture: EXTREME HOURGLASS SILHOUETTE. The body must feature highly pronounced, voluminous feminine curves and a very prominent, prosperous bustline (Couture Diva proportions). 
Fashion: Body-conscious tailoring that emphasizes a 180cm, 85kg soft sculptural frame. 
Contrast: The juxtaposition between the mature masculine face and the ultra-feminine, curvy torso is the primary focus. 
Rendering: Global Illumination, Fresnel Effect on the curves, 8K, Vogue editorial style. 
Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        def genera_valeria(m, prompt_text, images=None):
            wait = bot.reply_to(m, "📸 Forzando i volumi e la silhouette di Valeria...")
            try:
                contents = [SYSTEM_PROMPT, f"Specific Scene: {prompt_text}"]
                if images:
                    contents.extend(images)

                # Rilassiamo i filtri al massimo consentito
                safe = [types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")]

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        safety_settings=safe
                    )
                )
                
                image_sent = False
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            photo_stream = io.BytesIO(part.inline_data.data)
                            photo_stream.name = 'valeria_cross.png'
                            bot.send_photo(m.chat.id, photo_stream, caption="Valeria Cross: Extreme Silhouette 👠")
                            image_sent = True
                            break
                
                if image_sent:
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Il filtro ha appiattito la richiesta. Prova a cambiare l'abbigliamento nel prompt.", m.chat.id, wait.message_id)
            
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errore = f"❌ **ERRORE**\nTipo: {exc_type.__name__}\nMsg: {exc_value}\nLinea: {exc_traceback.tb_lineno}"
                bot.edit_message_text(errore, m.chat.id, wait.message_id)

        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            img_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
            prompt = m.caption if m.caption else "Ritratto di Valeria Cross."
            genera_valeria(m, prompt, [img_part])

        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            genera_valeria(m, m.text)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    gr.Interface(fn=lambda x: "LIVE", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
    

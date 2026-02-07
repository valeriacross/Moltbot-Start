import os
import telebot
from google import genai
from google.genai import types
import io
import threading
import gradio as gr

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Nuova inizializzazione Client (SDK 2026)
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 60 anni.
Dettagli: Capelli grigio platino (15cm sopra, lati corti), barba grigia corta (6cm), occhiali Vogue Havana ottagonali.
Fisico: 180cm, 85kg, coppa D, forme morbide, pelle realistica con rughe.
Rendering: Global Illumination, Ambient Occlusion, Fresnel Effect, subsurface scattering.
Stile: Vogue Photography, 8K, 85mm f/2.8. Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def welcome(m):
            bot.reply_to(m, "Moltbot Nano Banana Online! (Versione SDK Aggiornata) 🍌")

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Generazione in corso con Gemini 2.5 Flash Image...")
            try:
                # Task per il modello
                prompt_full = f"{SYSTEM_PROMPT}\n\nGenera un'immagine di: {m.text}"

                # Chiamata con la nuova libreria
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=prompt_full,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"]
                    )
                )
                
                image_sent = False
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
                    bot.edit_message_text("❌ Nessuna immagine generata.", m.chat.id, wait.message_id)

            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {str(e)}", m.chat.id, wait.message_id)

        print("Moltbot in ascolto...")
        # Il parametro skip_pending aiuta a evitare il loop infinito post-crash
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    gr.Interface(fn=lambda x: "Moltbot Nano Banana Live", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

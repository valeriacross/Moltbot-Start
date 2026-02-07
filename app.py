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

# Inizializzazione Client Google GenAI (Nuovo SDK 2026)
client = genai.Client(api_key=API_KEY)

# Master Prompt: Identità Valeria Cross + Parametri di Rendering
SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 60 anni.
Viso: Maschile saggio, rughe definite, barba grigia corta (6cm), occhiali Vogue Havana ottagonali.
Corpo: Silhouette femminile voluttuosa, seno coppa D, fianchi morbidi, altezza 180cm, peso 85kg.
Riferimento Visivo: Usa le immagini fornite per mantenere la coerenza assoluta del volto.
Rendering: Global Illumination, Fresnel Effect, subsurface scattering, 8K, Vogue Editorial style.
Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        def genera_valeria(m, prompt_text, images=None):
            wait = bot.reply_to(m, "📸 Moltbot sta elaborando Valeria con riferimento visivo...")
            try:
                # Prepariamo il contenuto: Prompt di sistema + Richiesta + Foto
                contents = [SYSTEM_PROMPT, f"Genera questa scena: {prompt_text}"]
                if images:
                    contents.extend(images)

                # Chiamata al modello Nano Banana
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
                    bot.edit_message_text("⚠️ Immagine non generata (possibile filtro di sicurezza).", m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {str(e)}", m.chat.id, wait.message_id)

        # Gestore per le FOTO (Usa come riferimento per il volto)
        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Trasformiamo la foto in un formato comprensibile per Google
            img_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
            
            # Se c'è una didascalia la usiamo come prompt, altrimenti prompt base
            prompt = m.caption if m.caption else "Ritratto editoriale di Valeria Cross."
            genera_valeria(m, prompt, [img_part])

        # Gestore per il TESTO
        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            genera_valeria(m, m.text)

        print("Moltbot Nano Banana Online (Multimodale).")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
es=["TEXT", "IMAGE"]
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

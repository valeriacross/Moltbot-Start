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

# Inizializzazione Client con la nuova libreria (SDK 2026)
client = genai.Client(api_key=API_KEY)

# Master Prompt con le specifiche fisiche e di rendering per Valeria
SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 60 anni.
Corpo: Silhouette femminile voluttuosa, seno coppa D, peso 85kg, altezza 180cm, pelle depilata.
Viso: Maschile saggio, capelli grigio platino (15cm sopra, corti ai lati), barba grigia corta (6cm), occhiali Vogue Havana ottagonali.
Dettagli Tecnici: Usa le immagini fornite come riferimento ASSOLUTO per il volto.
Rendering: Global Illumination, Ambient Occlusion, Fresnel Effect, subsurface scattering, frequency separation sulla pelle.
Stile: Vogue Editorial, 85mm, f/2.8, 8K, realismo fotografico estremo.
Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        def elabora_richiesta(m, prompt_text, image_parts=None):
            wait = bot.reply_to(m, "📸 Moltbot sta elaborando il volto di riferimento...")
            try:
                # Contenuto: Prompt di sistema + Richiesta utente + Foto
                contents = [SYSTEM_PROMPT, f"Genera: {prompt_text}"]
                if image_parts:
                    contents.extend(image_parts)

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
                    bot.edit_message_text("⚠️ Il modello ha filtrato l'immagine o non l'ha generata.", m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {str(e)}", m.chat.id, wait.message_id)

        # Gestione FOTO (per il Face Reference)
        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            # Scarica la foto inviata (la versione a risoluzione più alta)
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Formatta per Google
            image_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
            
            # Usa la didascalia come prompt, se presente
            prompt = m.caption if m.caption else "Genera Valeria in questa posa."
            elabora_richiesta(m, prompt, [image_part])

        # Gestione TESTO
        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            elabora_richiesta(m, m.text)

        print("Moltbot Nano Banana Online (Multimodale).")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    # Gradio serve per mantenere attiva la porta 10000 su Render
    gr.Interface(fn=lambda x: "LIVE", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    # Avvia bot e web service in parallelo
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
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

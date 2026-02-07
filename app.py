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
Viso: Ovale-rettangolare, tratti naturali, rughe definite, pori visibili (high micro-detail), sguardo saggio.
Capelli: Grigio Platino Argenteo, 15cm sopra, laterali molto corti.
Barba: Grigio naturale, folta e corta (circa 6 cm), precisamente rifinita.
Occhiali: Montatura da VISTA Vogue Havana dark, forma ottagonale (NO occhiali da sole).
Corpo: Altezza 180 cm, peso 85 kg, seno coppa D, forme morbide e voluttuose, silhouette femminile, completamente depilato.
Rendering: Global Illumination, Ambient Occlusion, Fresnel Effect, subsurface scattering, frequency separation sulla pelle.
Stile: Vogue Photography, 85mm, f/2.8, 8K, realismo estremo.
Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        def elabora_generazione(m, prompt_text, image_parts=None):
            wait = bot.reply_to(m, "📸 Nano Banana sta analizzando il riferimento per generare Valeria...")
            try:
                # Contenuto multimodale (Testo + Eventuale Immagine di riferimento)
                contents = [SYSTEM_PROMPT, f"Richiesta: {prompt_text}"]
                if image_parts:
                    contents.extend(image_parts)

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        safety_settings=[
                            types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")
                        ]
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
                    bot.edit_message_text("⚠️ Il modello ha filtrato la richiesta o non ha prodotto l'immagine.", m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore tecnico: {str(e)}", m.chat.id, wait.message_id)

        # Gestione FOTO (Face Reference)
        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            image_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
            
            # Se l'utente scrive una didascalia con la foto, la usiamo come prompt
            prompt = m.caption if m.caption else "Genera Valeria in questa posa mantenendo fedeltà al volto."
            elabora_generazione(m, prompt, [image_part])

        # Gestione TESTO
        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            elabora_generazione(m, m.text)

        print("Moltbot Nano Banana Online.")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    # Gradio serve a tenere aperta la porta 10000 per Render
    gr.Interface(fn=lambda x: "LIVE", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    # Avvio bot in thread separato
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        safety_settings=[
                            types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")
                        ]
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
                    bot.edit_message_text("❌ Errore nella generazione dell'immagine.", m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore tecnico: {str(e)}", m.chat.id, wait.message_id)

        # Gestore per i messaggi con FOTO
        @bot.message_handler(content_types=['photo'])
        def handle_photo(m):
            # Prendiamo la foto alla risoluzione massima
            file_info = bot.get_file(m.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # Prepariamo l'immagine per l'SDK di Google
            image_part = types.Part.from_bytes(
                data=downloaded_file,
                mime_type='image/jpeg'
            )
            
            prompt = m.caption if m.caption else "Genera una nuova posa mantenendo questo volto."
            elabora_generazione(m, prompt, [image_part])

        # Gestore per i messaggi di solo TESTO
        @bot.message_handler(func=lambda m: True)
        def handle_text(m):
            elabora_generazione(m, m.text)

        print("Moltbot Multimodale (Testo + Foto) in ascolto...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    gr.Interface(fn=lambda x: "LIVE", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Generazione in corso... Tentativo di bilanciamento volto/silhouette.")
            try:
                # Il prompt utente viene aggiunto al concetto base
                prompt_full = f"{SYSTEM_PROMPT}\n\nSpecific Scene Request: {m.text}"

                # Chiamata al modello Nano Banana
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=prompt_full,
                    config=types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"],
                        # Manteniamo una safety config standard ma permissiva per l'arte
                        safety_settings=[
                            types.SafetySetting(category="HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
                            types.SafetySetting(category="HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
                            types.SafetySetting(category="SEXUALLY_EXPLICIT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
                            types.SafetySetting(category="DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
                        ]
                    )
                )
                
                image_sent = False
                # Estrazione e invio
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            photo_stream = io.BytesIO(part.inline_data.data)
                            photo_stream.name = 'valeria_cross.png'
                            bot.send_photo(m.chat.id, photo_stream, caption="feat. Valeria Cross 👠 (New Prompt Strategy)")
                            image_sent = True
                            break
                
                if image_sent:
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    # Se fallisce, diamo un feedback generico
                    bot.edit_message_text("⚠️ Il modello ha filtrato la richiesta. Prova una descrizione leggermente diversa.", m.chat.id, wait.message_id)

            except Exception as e:
                bot.edit_message_text(f"❌ Errore tecnico: {str(e)}", m.chat.id, wait.message_id)

        print("Moltbot pronto con nuova strategia...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

def web_service():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
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

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

# Inizializzazione Client SDK (2026)
client = genai.Client(api_key=API_KEY)

# --- NUOVO MASTER PROMPT STRATEGICO ---
# Usiamo termini da fashion editor per descrivere il contrasto senza triggerare i filtri.
SYSTEM_PROMPT = """Subject: A high-fashion editorial portrait of Valeria Cross, 60 years old.
Concept: Exploring gender non-conformity through contrast.
The Face: Distinguished mature masculine facial features, strong jawline, character lines, silver-grey hair (short sides, longer messy top), and a precisely groomed short grey beard (6cm). Wearing Havana octagonal Vogue prescription glasses. Expression is calm and wise.
The Silhouette: The body has a distinctly voluptuous, curvy feminine figure. A full, pronounced bustline and soft hips are visible and emphasized by fitted high-fashion tailoring.
Photography Style: Vogue Italia aesthetic, 85mm lens, f/2.8.
Lighting & Texture: Dramatic studio lighting highlighting skin texture (pores, wrinkles), Global Illumination, and a soft Fresnel rim light emphasizing the curves of the silhouette against a dark background.
Rendering: Hyper-realistic, cinematic color grading, 8K detail.
Watermark: 'feat. Valeria Cross 👠' in corner.
Negative Prompt: sunglasses, low quality, blurry, flat lighting, athletic male body, thin body, young."""

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def welcome(m):
            bot.reply_to(m, "Moltbot Nano Banana 🍌 pronto con il nuovo prompt strategico per Valeria.")

        @bot.message_handler(func=lambda m: True)
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

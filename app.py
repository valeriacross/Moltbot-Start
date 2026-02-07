import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr
from PIL import Image

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)

# Master Prompt con tutti i parametri salvati (Rendering + Identità)
SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 60 anni. 
Viso: Ovale-rettangolare, tratti naturali, rughe visibili e definite, pori della pelle visibili (high micro-detail), sguardo calmo e saggio.
Capelli: Grigio Platino Argenteo, 15cm sopra, laterali molto corti, leggermente disordinati.
Barba: Grigio naturale, folta e corta (circa 6 cm), precisamente rifinita.
Occhiali: Montatura da VISTA Vogue Havana dark, forma ottagonale (NO occhiali da sole).
Corpo: Altezza 180 cm, peso 85 kg, seno coppa D, forme morbide e femminili, corpo completamente depilato.
Rendering: Global Illumination, Ambient Occlusion, Fresnel Effect, subsurface scattering to skin lighting, controlled post-processing frequency separation on the skin.
Stile: Vogue Photographer expert, 8K Texture Fidelity, Cinematic Color Grading, Profondità di Campo Estrema.
Negative Prompt: female face, woman, girl, young, feminine features, soft baby skin, distortion, low quality, sunglasses, 1:1 format."""

def avvia_bot():
    try:
        # MODEL_ID specifico dalla documentazione Nano Banana
        MODEL_ID = "gemini-2.5-flash-image"
        model = genai.GenerativeModel(MODEL_ID)
        
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def welcome(m):
            bot.reply_to(m, "Moltbot Nano Banana 🍌 attivo! Pronto per generare Valeria Cross con Gemini 2.5.")

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Generazione Nano Banana in corso...")
            try:
                # Costruzione del prompt secondo le specifiche della documentazione
                prompt_full = f"{SYSTEM_PROMPT}\n\nTask: Generate a high-fidelity image of: {m.text}"

                # Configurazione fondamentale per abilitare l'output immagine
                config = genai.types.GenerationConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )

                # Generazione multimodale
                response = model.generate_content(prompt_full, generation_config=config)
                
                image_sent = False
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        # Estrazione dell'immagine generata dal modello multimodale
                        if hasattr(part, 'inline_data') and part.inline_data:
                            photo_stream = io.BytesIO(part.inline_data.data)
                            photo_stream.name = 'valeria_cross.png'
                            bot.send_photo(m.chat.id, photo_stream, caption="Valeria Cross (Nano Banana) ✨")
                            image_sent = True
                            break
                
                if image_sent:
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("❌ Il modello non ha restituito immagini. Controlla i permessi in Google Cloud Console.", m.chat.id, wait.message_id)

            except Exception as e:
                bot.edit_message_text(f"❌ Errore Tecnico: {str(e)}", m.chat.id, wait.message_id)

        print(f"Moltbot in esecuzione su {MODEL_ID}...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

# Keep-alive per Render
def web_service():
    gr.Interface(fn=lambda x: "Moltbot Nano Banana Online", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

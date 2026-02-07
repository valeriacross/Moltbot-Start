import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)

# Master Prompt: Identità Valeria Cross + Parametri di Rendering
SYSTEM_PROMPT = """Soggetto: Valeria Cross, uomo italiano transmaschile di 59-60 anni.
Viso: Ovale-rettangolare, tratti naturali, rughe visibili e definite, pori della pelle visibili (high micro-detail), sguardo calmo e saggio, espressione pacata.
Capelli: Grigio Platino Argenteo, 15cm sopra, laterali molto corti, leggermente disordinati, aspetto autentico.
Barba: Grigio naturale, folta e corta (circa 6 cm, Short Trim), precisamente rifinita.
Occhiali: Montatura da VISTA Vogue Havana dark, forma ottagonale (fondamentale: NO occhiali da sole).
Corpo: Altezza 180 cm, peso 85 kg, seno coppa D, fisico morbido con forme femminili, completamente depilato.
Rendering e Luci: Global Illumination, Ambient Occlusion, Fresnel Effect, subsurface scattering to skin lighting, controlled post-processing frequency separation on the skin.
Stile: Vogue Photographer expert, 8K Texture Fidelity, Cinematic Color Grading, Profondità di Campo Estrema (nitidissimo sul viso).
Negative Prompt: female face, woman, girl, young, teenager, feminine features, soft baby skin, unrealistic face shape, distortion, low quality, sunglasses, 1:1 format."""

def avvia_bot():
    try:
        # ID Modello Nano Banana confermato dalla tua documentazione
        MODEL_ID = "gemini-2.5-flash-image"
        model = genai.GenerativeModel(MODEL_ID)
        
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def welcome(m):
            bot.reply_to(m, "Moltbot Nano Banana 🍌 attivo! Pronto per generare Valeria Cross con i parametri di rendering avanzati.")

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Generazione Nano Banana in corso... Applicazione Global Illumination e Subsurface Scattering.")
            try:
                # Prompt completo per il modello
                prompt_full = f"{SYSTEM_PROMPT}\n\nTask: Generate a high-fidelity image based on this request: {m.text}"

                # Configurazione specifica per Nano Banana (Multi-modalità)
                config = {
                    "response_modalities": ["TEXT", "IMAGE"]
                }

                # Chiamata al modello
                response = model.generate_content(prompt_full, generation_config=config)
                
                image_sent = False
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        # Estrazione dell'immagine generata
                        if hasattr(part, 'inline_data') and part.inline_data:
                            photo_stream = io.BytesIO(part.inline_data.data)
                            photo_stream.name = 'valeria_cross.png'
                            bot.send_photo(m.chat.id, photo_stream, caption="feat. Valeria Cross 👠")
                            image_sent = True
                            break
                
                if image_sent:
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("❌ Il modello non ha restituito immagini. Verifica i filtri di sicurezza in AI Studio.", m.chat.id, wait.message_id)

            except Exception as e:
                bot.edit_message_text(f"❌ Errore Tecnico: {str(e)}", m.chat.id, wait.message_id)

        print(f"Moltbot Nano Banana in esecuzione...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"CRASH: {e}")

# Web Service per Render (necessario per mantenere il servizio 'Live')
def web_service():
    # Porta 10000 obbligatoria per Render
    gr.Interface(fn=lambda x: "Moltbot Online", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    # Avvia il bot in un thread separato
    threading.Thread(target=avvia_bot, daemon=True).start()
    # Avvia il web service Gradio (blocca il main thread)
    web_service()

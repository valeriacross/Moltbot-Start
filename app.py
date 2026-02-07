import os
import telebot
import io
import threading
import gradio as gr
from google import genai
from google.genai import types
from PIL import Image

# --- CONFIGURAZIONE ---
# Prende i token dalle variabili d'ambiente di Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Inizializza il client di Google
client = genai.Client(api_key=API_KEY)

# PROMPT DI SISTEMA GENERICO E MINIMALE
# Istruisce solo sul formato richiesto (2:3) e sulla qualità.
SYSTEM_PROMPT = """INSTRUCTION: Generate highly detailed, photorealistic images.
ASPECT RATIO requirement: The output MUST be in vertical 2:3 format (portrait).
QUALITY requirement: Max resolution, 8K detail, realistic lighting."""

def avvia_bot():
    # Inizializza il bot Telegram
    bot = telebot.TeleBot(TOKEN)

    # Gestore unico per testo e immagini
    @bot.message_handler(content_types=['photo', 'text'])
    def handle_message(message):
        # Messaggio di attesa
        wait_msg = bot.reply_to(message, "🎨 Generazione immagine generica (Target 2:3)...")
        
        try:
            # Preparazione dei contenuti per Gemini
            contents = [SYSTEM_PROMPT]
            user_prompt = ""

            # Se c'è una foto, la scarica e la aggiunge
            if message.content_type == 'photo':
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                img_part = types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg')
                contents.append(img_part)
                user_prompt = message.caption if message.caption else "Usa questa immagine come riferimento."
            else:
                # Solo testo
                user_prompt = message.text

            # Aggiunge il prompt dell'utente
            contents.append(f"USER REQUEST: {user_prompt}")

            # Configurazione standard (Filtri medi per immagini "safe")
            # NOTA: Non usiamo aspect_ratio qui perché l'SDK attuale lo rifiuta e crasha.
            # Ci affidiamo solo al SYSTEM_PROMPT per il formato.
            config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_MEDIUM_AND_ABOVE"),
                ]
            )

            # Chiamata all'API di Google
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=contents,
                config=config
            )
            
            # Estrazione e invio dell'immagine
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        img_stream = io.BytesIO(part.inline_data.data)
                        bot.send_photo(message.chat.id, img_stream, caption="Generato con Gemini 2.5 Flash")
                        bot.delete_message(message.chat.id, wait_msg.message_id)
                        return
            
            # Se arriviamo qui, non c'è immagine (filtro attivo)
            bot.edit_message_text("⚠️ Immagine non generata (Filtro di sicurezza standard attivo).", message.chat.id, wait_msg.message_id)

        except Exception as e:
            # Gestione errori generica
            error_msg = f"❌ Errore: {str(e)}"
            bot.edit_message_text(error_msg, message.chat.id, wait_msg.message_id)
            print(f"DEBUG ERROR: {e}")

    # Avvia il bot in modalità polling (ignora i vecchi messaggi)
    bot.infinity_polling(skip_pending=True)

# Web service fittizio per tenere sveglio Render
def web_service():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

# Avvio dei thread
if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
    

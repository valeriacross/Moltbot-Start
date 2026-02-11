import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.api_core import exceptions

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# MODELLO: Imagen 3 Fast (Veloce e specifico per immagini)
MODEL_ID = "imagen-3.0-fast-generate-001" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        # Se non c'è testo, mettiamo un default
        testo = prompt_utente if prompt_utente else "A beautiful scenery"

        # Chiamata specifica per IMAGEN (generate_image)
        # Se c'è un'immagine, la usiamo come 'image' per l'image-to-image
        
        args = {
            "model": MODEL_ID,
            "prompt": testo,
            "config": {
                "number_of_images": 1,
                "safety_settings": [
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
                ]
            }
        }

        # Se l'utente ha allegato una foto, la passiamo come riferimento
        if immagine_riferimento:
            # Nel nuovo SDK, passiamo l'immagine direttamente
            from google.genai import types
            args["image"] = types.Image(data=immagine_riferimento, mime_type="image/jpeg")

        response = client.models.generate_image(**args)
        
        # Recupero l'immagine dai risultati specifici di Imagen
        if response and response.generated_images:
            return response.generated_images[0].image_bytes
            
        return None

    except Exception as e:
        print(f"❌ Errore Imagen: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Imagen 3 Fast Online.", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Imagen 3 Fast sta disegnando...")
                
                prompt = ""
                img_data = None
                
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)
                    prompt = m.caption
                else:
                    prompt = m.text
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    # Invio con estensione corretta
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="generazione.jpg", 
                        caption="✅ Immagine generata."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Non è stato possibile generare l'immagine (Filtri o Errore).", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- GRADIO WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_image(prompt)
        return io.BytesIO(img_bytes).read() if img_bytes else None

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image", title="Imagen 3 Fast Control")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

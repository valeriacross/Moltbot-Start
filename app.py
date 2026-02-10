import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# MODELLO: Gemini 2.0 Flash (Veloce, Generalista)
MODEL_ID = "gemini-2.0-flash"

# --- GENERAZIONE ---
def generate_image(prompt_utente, immagine_utente=None):
    try:
        # Nessun Master Prompt nascosto. Solo quello che scrivi tu.
        if not prompt_utente: 
            prompt_utente = "Una foto artistica."

        contents = []
        
        # Se c'è una foto di riferimento (es. per lo stile), la allega
        if immagine_utente:
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))
        
        # Aggiunge il prompt dell'utente
        contents.append(prompt_utente)

        # CONFIGURAZIONE BASIC
        # - Safety al minimo (BLOCK_NONE) per massima libertà
        # - Nessun aspect_ratio forzato (decide il modello in base al prompt)
        config_raw = {
            "response_modalities": ["IMAGE"],
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config_raw
        )
        
        if response and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        return None
    except Exception as e:
        print(f"❌ Errore Generazione: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print("✅ Bot Basic Online (Nessuna Identità).", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Generazione...")
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                img_data = None
                
                # Se l'utente manda una foto, la usiamo come riferimento (img2img)
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)

                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="image.jpg", 
                        caption="✅ Fatto."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore o Filtro Google.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_image(prompt)
        return io.BytesIO(img_bytes).read() if img_bytes else None

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image", title="Basic Generator")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

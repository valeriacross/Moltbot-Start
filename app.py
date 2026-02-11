import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Motore: Nano Banana Pro (Stabile)
MODEL_ID = "nano-banana-pro-preview" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        # Costruiamo la lista dei contenuti
        contents = []
        
        # Se c'è un'immagine allegata, la inseriamo come primo elemento
        if immagine_riferimento:
            contents.append(types.Part.from_bytes(data=immagine_riferimento, mime_type="image/jpeg"))
        
        # Aggiungiamo il testo (se non c'è, mettiamo un default)
        testo = prompt_utente if prompt_utente else "Generate based on this image."
        contents.append(testo)

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
        print("✅ Bot Multimodale (Testo + Immagine) Online.", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Elaborazione in corso...")
                
                prompt = ""
                img_data = None
                
                if m.content_type == 'photo':
                    # Scarichiamo la foto (la versione a risoluzione più alta)
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)
                    # Il testo è nella caption della foto
                    prompt = m.caption
                else:
                    # È solo testo
                    prompt = m.text
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="output.jpg", 
                        caption="✅ Elaborazione completata."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore Generazione o Filtro.", m.chat.id, wait.message_id)
            
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

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

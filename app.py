import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# CAMBIO MOTORE: Usiamo FLASH perché non soffre di "doppia personalità"
# È più diretto e meno "moralista" del Pro.
MODEL_ID = "gemini-2.0-flash" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        # Costruiamo la lista dei contenuti
        contents = []
        
        # Se c'è un'immagine allegata (riferimento), la inseriamo per prima
        if immagine_riferimento:
            contents.append(types.Part.from_bytes(data=immagine_riferimento, mime_type="image/jpeg"))
        
        # Aggiungiamo il testo del prompt
        testo = prompt_utente if prompt_utente else "Generate image based on reference."
        contents.append(testo)

        # Configurazione Standard per Flash
        config_raw = {
            "response_modalities": ["IMAGE"],
            # I filtri sono al minimo, ma Flash è comunque più permissivo di natura
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
        
        # Estrazione dell'unica immagine generata
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
        print("✅ Bot Flash Online (Fix Doppia Generazione).", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "⚡ Flash sta elaborando...")
                
                prompt = ""
                img_data = None
                
                if m.content_type == 'photo':
                    # Scarica la foto (la versione più grande disponibile)
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)
                    prompt = m.caption # Usa la didascalia come prompt
                else:
                    prompt = m.text # Usa solo il testo
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="flash_output.jpg", 
                        caption="✅ Generazione completata."
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

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image", title="Flash Generator")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

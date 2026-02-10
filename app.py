import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# USIAMO NANO BANANA PRO (L'unico che ha dimostrato di funzionare con "Ciao")
MODEL_ID = "nano-banana-pro-preview" 

# --- GENERAZIONE ---
def generate_image(prompt_utente):
    try:
        if not prompt_utente: return None

        # Configurazione standard
        config_raw = {
            "response_modalities": ["IMAGE"],
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        # Invio diretto del prompt (senza master prompt, senza facce)
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt_utente],
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
        print("✅ Bot Basic (Motore Stabile) Online.", flush=True)

        @bot.message_handler(content_types=['text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Generazione...")
                
                risultato = generate_image(m.text)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="image.jpg", 
                        caption="✅ Fatto."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore Generazione.", m.chat.id, wait.message_id)
            
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
    

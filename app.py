import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# ID MODELLO PRESO DALLA TUA LISTA
MODEL_ID = "nano-banana-pro-preview" 

def heartbeat():
    while True:
        print(f"💓 Heartbeat: {MODEL_ID} è attivo", flush=True)
        time.sleep(30)

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ MOTORE CONFIGURATO: {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                print(f"📩 Richiesta ricevuta da {m.chat.id}", flush=True)
                wait = bot.reply_to(m, "💎 Elaborazione NANOBANANA PRO (Formato 2:3)...")
                
                img_part = None
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    download = bot.download_file(file_info.file_path)
                    img_part = types.Part.from_bytes(data=download, mime_type='image/jpeg')
                
                prompt_user = m.caption if m.content_type == 'photo' else m.text
                
                # CONFIGURAZIONE TECNICA PRO
                # Forziamo il 2:3 e la sicurezza minima per evitare blocchi inutili
                config_gen = types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    aspect_ratio="2:3",
                    safety_settings=[
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")
                    ]
                )

                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[prompt_user, img_part] if img_part else [prompt_user],
                    config=config_gen
                )
                
                if response and response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            bot.send_photo(m.chat.id, io.BytesIO(part.inline_data.data), caption=f"💎 {MODEL_ID} | 2:3")
                            bot.delete_message(m.chat.id, wait.message_id)
                            return
                
                bot.edit_message_text("⚠️ Filtro Google attivo o contenuto non supportato.", m.chat.id, wait.message_id)
            except Exception as e:
                print(f"❌ Errore: {e}", flush=True)
                bot.send_message(m.chat.id, f"❌ Errore tecnico: {e}")

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash: {e}", flush=True)

def web():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    web()
    

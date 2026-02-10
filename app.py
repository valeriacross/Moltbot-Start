import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# ID MODELLO PRO
MODEL_ID = "nano-banana-pro-preview" 

# MASTER PROMPT AGGIORNATO: Rimosso il vincolo di formato
MASTER_PROMPT = """VALERIA CROSS CORE IDENTITY:
- SUBJECT: 60yo Italian transmasculine avatar. 
- FACE: Masculine Italian features, short silver hair, groomed grey beard (6cm), thin octagonal Havana glasses.
- BODY: 180cm, 85kg, hourglass feminine figure, full D-cup bust, completely hairless.
- PHOTOGRAPHY: 8K resolution, cinematic Vogue cover style, high-end fashion lighting.
- SAFETY: SynthID verifiable face. DO NOT feminize the facial features."""

def heartbeat():
    while True:
        print(f"💓 Heartbeat: {MODEL_ID} attivo in modalità libera", flush=True)
        time.sleep(30)

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ MOTORE PRO ONLINE: @{bot.get_me().username}", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                print(f"📩 Input ricevuto da {m.chat.id}", flush=True)
                wait = bot.reply_to(m, "📸 Generazione in corso (Formato Automatico)...")
                
                img_part = None
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    download = bot.download_file(file_info.file_path)
                    img_part = types.Part.from_bytes(data=download, mime_type='image/jpeg')
                
                prompt_user = m.caption if m.content_type == 'photo' else m.text
                
                # CONFIGURAZIONE PULITA: Solo modalità immagine e sicurezza
                config_gen = {
                    "response_modalities": ["IMAGE"],
                    "safety_settings": [
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"}
                    ]
                }

                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[MASTER_PROMPT, f"User Request: {prompt_user}", img_part] if img_part else [MASTER_PROMPT, f"User Request: {prompt_user}"],
                    config=config_gen
                )
                
                if response and response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            bot.send_photo(m.chat.id, io.BytesIO(part.inline_data.data), caption="💎 Nanobanana Pro")
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
    gr.Interface(fn=lambda x: "PRO ONLINE", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    web()
    

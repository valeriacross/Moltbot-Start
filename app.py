import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

def heartbeat():
    while True:
        print("💓 Heartbeat: Alive", flush=True)
        time.sleep(30)

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Connesso: @{bot.get_me().username}", flush=True)
        client = genai.Client(api_key=API_KEY)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                print(f"📩 Msg da {m.chat.id}", flush=True)
                w = bot.reply_to(m, "📸 Generazione...")
                img = []
                if m.content_type == 'photo':
                    f = bot.get_file(m.photo[-1].file_id)
                    d = bot.download_file(f.file_path)
                    img = [types.Part.from_bytes(data=d, mime_type='image/jpeg')]
                
                p = m.caption if m.content_type == 'photo' else m.text
                # Configurazione su riga singola per evitare IndentationError
                s = [types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")]
                cfg = types.GenerateContentConfig(response_modalities=["IMAGE"], safety_settings=s)
                
                res = client.models.generate_content(model="gemini-2.5-flash-image", contents=[f"Image: {p}"] + img, config=cfg)
                
                if res and res.candidates and res.candidates[0].content.parts:
                    for part in res.candidates[0].content.parts:
                        if part.inline_data:
                            bot.send_photo(m.chat.id, io.BytesIO(part.inline_data.data))
                            bot.delete_message(m.chat.id, w.message_id)
                            return
                bot.edit_message_text("⚠️ Filtro.", m.chat.id, w.message_id)
            except Exception as e:
                print(f"❌ Errore: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash: {e}", flush=True)

def web():
    gr.Interface(fn=lambda x: "OK", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    web()
    

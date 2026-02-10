import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

def heartbeat():
    """Mantiene il log attivo per Render."""
    while True:
        print("💓 Heartbeat: Il server è sveglio...", flush=True)
        time.sleep(30)

def avvia_bot():
    try:
        if not TOKEN:
            print("❌ ERRORE: TELEGRAM_TOKEN mancante!", flush=True)
            return

        bot = telebot.TeleBot(TOKEN)
        
        # Test immediato connessione
        me = bot.get_me()
        print(f"✅ TELEGRAM CONNESSO: @{me.username}", flush=True)

        client = genai.Client(api_key=API_KEY)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                print(f"📩 Messaggio da {m.chat.id}", flush=True)
                wait = bot.reply_to(m, "📸 Generazione in corso...")
                
                img_parts = []
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    download = bot.download_file(file_info.file_path)
                    img_parts = [types.Part.from_bytes(data=download, mime_type='image/jpeg')]
                
                prompt_user = m.caption if m.content_type == 'photo' else m.text
                
                # Configurazione lineare per evitare IndentationError
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[f"Generate a generic safe image: {prompt_user}"] + img_parts,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        safety_settings=[
                            types.SafetySetting(
                                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", 
                                threshold="BLOCK_ONLY_HIGH"
                            )
                        ]
                    )
                )
                
                if response and response.candidates and response.candidates[0].content:
                    for p in response.candidates[0].content.parts:
                        if p.inline_data:
                            bot.send_photo(m.chat.id, io.BytesIO(p.inline_data.data), caption="Generato 1:1")
                            bot.delete_message(m.chat.id, wait.message_id)
                            return
                
                bot.edit_message_text("⚠️ Filtro sicurezza attivo.", m.chat.id, wait.message_id)
            except Exception as e:
                print(f"❌ Errore: {e}", flush=True)
                bot.send_message(m.chat.id, f"❌ Errore tecnico: {e}")

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 CRASH AVVIO: {e}", flush=True)

def web():
    # Porta 10000 per Cron-job
    gr.Interface(fn=lambda x: "Bot Online", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    print("🚀 Avvio...", flush=True)
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    web()
                            

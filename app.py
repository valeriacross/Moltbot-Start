import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Prompt ultra-semplice senza parametri di formato
MASTER_PROMPT = "Generate a high-quality, realistic image based on the user request. Safe content only."

def heartbeat():
    """Stampa un log ogni 30 secondi per segnalare che il bot è vivo."""
    while True:
        print("💓 Bot Heartbeat: Servizio Attivo...", flush=True)
        time.sleep(30)

def avvia_bot():
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(content_types=['photo', 'text'])
    def handle(m):
        wait = bot.reply_to(m, "📸 Generazione in corso...")
        try:
            img_parts = []
            if m.content_type == 'photo':
                file_info = bot.get_file(m.photo[-1].file_id)
                download = bot.download_file(file_info.file_path)
                img_parts = [types.Part.from_bytes(data=download, mime_type='image/jpeg')]
            
            prompt_user = m.caption if m.content_type == 'photo' else m.text
            
            # Configurazione base: niente aspect_ratio, niente risoluzioni extra
            config_gen = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")]
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[MASTER_PROMPT, f"User: {prompt_user}"] + img_parts,
                config=config_gen
            )
            
            if response and response.candidates and response.candidates[0].content:
                for p in response.candidates[0].content.parts:
                    if p.inline_data:
                        bot.send_photo(m.chat.id, io.BytesIO(p.inline_data.data), caption="Generato 1:1")
                        bot.delete_message(m.chat.id, wait.message_id)
                        return
            
            bot.edit_message_text("⚠️ Filtro sicurezza attivo o errore generazione.", m.chat.id, wait.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait.message_id)

    bot.infinity_polling(skip_pending=True)

def web():
    # Gradio serve per aprire la porta 10000 richiesta da Render
    gr.Interface(fn=lambda x: "Bot Online", inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    # Avvia il battito cardiaco in background
    threading.Thread(target=heartbeat, daemon=True).start()
    # Avvia il bot Telegram
    threading.Thread(target=avvia_bot, daemon=True).start()
    # Avvia il servizio web (porta 10000)
    web()
    

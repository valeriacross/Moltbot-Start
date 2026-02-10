import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "nano-banana-pro-preview" 

# Carichiamo l'immagine master all'avvio
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except:
        print("⚠️ master_face.png non trovato. Il bot userà solo il testo.")
        return None

MASTER_FACE = get_master_face()

# Prompt basato sul tuo JSON
MASTER_PROMPT = """VALERIA CROSS MASTER IDENTITY:
Mandatory facial identity from attached master_face.png. 
60yo Italian male, silver-white wavy hair, full trimmed white beard. 
Dark brown eyes, crow's feet, nasolabial folds, skin pores. 
Hexagonal-rounded dark brown tortoiseshell glasses.
BODY: 180cm, 85kg, hourglass feminine figure, full D-cup bust, hairless.
STYLE: 8K Vogue photography, warm lighting. DO NOT feminize the face."""

def heartbeat():
    while True:
        print(f"💓 Heartbeat: {MODEL_ID} con Master Face attivo", flush=True)
        time.sleep(30)

def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ BOT PRO CON VOLTO FISSO ONLINE", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "💎 Generazione in corso con Identità Valeria Cross...")
                
                contents = [MASTER_PROMPT]
                if MASTER_FACE: contents.append(MASTER_FACE) # Inseriamo sempre la faccia master
                
                # Se l'utente manda un'altra foto (es. per la posa), aggiungiamo anche quella
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    download = bot.download_file(file_info.file_path)
                    contents.append(types.Part.from_bytes(data=download, mime_type='image/jpeg'))
                
                prompt_user = m.caption if m.content_type == 'photo' else m.text
                contents.append(f"SCENE TO GENERATE: {prompt_user}")

                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        safety_settings=[types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")]
                    )
                )
                
                if response and response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            bot.send_photo(m.chat.id, io.BytesIO(part.inline_data.data), caption="💎 Valeria Cross | Identità Protetta")
                            bot.delete_message(m.chat.id, wait.message_id)
                            return
                
                bot.edit_message_text("⚠️ Filtro Google attivo.", m.chat.id, wait.message_id)
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
    

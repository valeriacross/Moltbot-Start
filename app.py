import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Motore: Nano Banana Pro (Supporta Faccia + Identità)
MODEL_ID = "nano-banana-pro-preview"

# --- GESTIONE FACCIA (MANDATORIA) ---
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except:
        print("⚠️ ERRORE: master_face.png MANCANTE.")
        return None

MASTER_FACE = get_master_face()

# --- MASTER PROMPT ---
MASTER_PROMPT = """MANDATORY IDENTITY:
1. FACE: Use the facial features from the attached reference image ONLY. (60yo male, silver beard, glasses).
2. BODY: Female hourglass figure, D-cup, 180cm, 85kg.
3. FORMAT RULE: Generate cinematic, horizontal (16:9) or vertical compositions. NEVER generate square (1:1) images.
4. OUTFIT: Follow user instructions strictly."""

# --- GENERAZIONE ---
def generate_avatar(prompt_utente, immagine_utente=None):
    try:
        if not MASTER_FACE: return None 

        # Se prompt vuoto, default generico
        if not prompt_utente: prompt_utente = "Cinematic shot."

        contents = [MASTER_PROMPT, MASTER_FACE]
        
        if immagine_utente:
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))
        
        contents.append(f"SCENE REQUEST: {prompt_utente}")

        # CONFIGURAZIONE SICUREZZA TOTALE (SBLOCCATA)
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
        print("✅ Bot Attivo.", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "📸 Elaborazione...")
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                img_data = None
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)

                risultato = generate_avatar(prompt, img_data)
                
                if risultato:
                    # FIX: Aggiunto visible_file_name per avere l'estensione .jpg
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="output.jpg", 
                        caption="Generazione Completata"
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Immagine bloccata dai filtri Google o errore tecnico.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_avatar(prompt)
        return io.BytesIO(img_bytes).read() if img_bytes else None

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

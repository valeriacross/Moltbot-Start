import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Motore: Nano Banana Pro (Supporta Faccia)
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

# --- MASTER PROMPT (Senza nome reale, Senza vincoli outfit) ---
MASTER_PROMPT = """MANDATORY IDENTITY: NAMELESS AVATAR.
1. FACE: Use the facial features from the attached reference image ONLY. (60yo male, silver beard, glasses).
2. BODY: Female hourglass figure, D-cup, 180cm, 85kg.
3. COMPOSITION RULE: Cinematic rectangular framing. DO NOT GENERATE SQUARE (1:1) IMAGES.
4. OUTFIT & SCENE: Follow user instructions strictly."""

# --- GENERAZIONE ---
def generate_avatar(prompt_utente, immagine_utente=None):
    try:
        if not MASTER_FACE: return None 

        # Se il prompt è vuoto, default generico
        if not prompt_utente: 
            prompt_utente = "Standing pose, cinematic lighting."

        # Costruzione Contenuto
        contents = [MASTER_PROMPT, MASTER_FACE]
        
        if immagine_utente:
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))
        
        contents.append(f"SCENE REQUEST: {prompt_utente}")

        # CONFIGURAZIONE PULITA
        # Rimosso aspect_ratio fisso (lo decide il motore/prompt)
        # Rimosso Hate Speech e altre categorie inutili
        config_raw = {
            "response_modalities": ["IMAGE"],
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
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
        print("✅ Bot Attivo: Nameless Avatar | No 1:1", flush=True)

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
                    # Invio come Documento (Senza nome forzato)
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        caption=f"Generazione Completata"
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore Generazione.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- GRADIO WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_avatar(prompt)
        return io.BytesIO(img_bytes).read() if img_bytes else None

    ui = gr.Interface(fn=web_interface, inputs="text", outputs="image", title="Avatar Control")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
            

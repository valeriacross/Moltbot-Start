import os, telebot, io, threading, time, sys, flask
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Modello Nanobanana (L'unico di cui ti fidi)
MODEL_ID = "nano-banana-pro-preview" 

# --- GESTIONE FACCIA MANDATORIA ---
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except Exception as e:
        print(f"❌ ERRORE: master_face.png non trovato! {e}")
        return None

MASTER_FACE = get_master_face()

def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        if not MASTER_FACE: return None, "Manca il file master_face.png"

        contents = [
            "MANDATORY IDENTITY: Use features from master_face.png. 60yo male, silver beard, glasses.",
            "STYLE: Cinematic, high resolution, 2K detail.",
            "FORMAT: 16:9 or 3:4. NEVER 1:1 SQUARE.",
            MASTER_FACE
        ]
        
        if immagine_riferimento:
            contents.append(types.Part.from_bytes(data=immagine_riferimento, mime_type="image/jpeg"))
        
        contents.append(f"PROMPT: {prompt_utente}")

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF")
                ]
            )
        )
        
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data, None
        return None, "Il modello non ha restituito immagini."
    except Exception as e:
        return None, str(e)

# --- TELEGRAM BOT ---
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text', 'photo'])
def handle(m):
    wait = bot.reply_to(m, "⏳ Nanobanana sta lavorando...")
    prompt = m.caption if m.content_type == 'photo' else m.text
    img_data = None
    if m.content_type == 'photo':
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    risultato, errore = generate_image(prompt, img_data)
    if risultato:
        bot.send_document(m.chat.id, io.BytesIO(risultato), visible_file_name="output.jpg")
        bot.delete_message(m.chat.id, wait.message_id)
    else:
        bot.edit_message_text(f"❌ ERRORE:\n{errore}", m.chat.id, wait.message_id)

# --- FIX PER RENDER (PORT BINDING) ---
# Crea un server web finto che risponde sulla porta chiesta da Render
app = flask.Flask(__name__)
@app.route('/')
def health(): return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print(f"✅ Avvio Bot con {MODEL_ID}...")
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling()
    

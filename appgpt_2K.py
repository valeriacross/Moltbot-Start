import os
import io
import threading
import flask
import telebot
from google import genai
from google.genai import types

# ==============================
# CONFIG
# ==============================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-2.0-flash-exp-image-generation"

# ==============================
# MASTER FACE
# ==============================

def load_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part(
                inline_data=types.Blob(
                    mime_type="image/png",
                    data=f.read()
                )
            )
    except Exception:
        print("ERRORE: master_face.png non trovato")
        return None

MASTER_FACE = load_master_face()

# ==============================
# GENERAZIONE FACE LOCK
# ==============================

def generate_image(prompt_utente):

    if not MASTER_FACE:
        return None, "master_face.png mancante"

    try:

        SYSTEM_PROMPT = """
You must strictly preserve the exact identity
from the provided reference image.

IDENTITY RULES:
- Maintain exact facial bone structure
- Maintain beard density and shape
- Maintain skin texture
- Maintain age appearance
- No reinterpretation
- No beautification
- No younger version

BODY RULES:
- Feminine hourglass body
- Cup D breasts
- Narrow waist
- Wide hips
- Height 180cm
- Weight 85kg
- Completely hairless body
- Smooth feminine skin

Face consistency has absolute priority.
"""

        full_prompt = f"""
{SYSTEM_PROMPT}

SCENE DESCRIPTION:
{prompt_utente}

Photorealistic.
Natural skin texture.
Realistic lighting.
High detail.
"""

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=full_prompt),
                        MASTER_FACE
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.8,
                response_modalities=["IMAGE"]
            )
        )

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    return part.inline_data.data, None

        return None, "Nessuna immagine generata"

    except Exception as e:
        return None, str(e)


# ==============================
# TELEGRAM BOT
# ==============================

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text'])
def handle_message(m):

    wait_msg = bot.reply_to(m, "Generazione Face Lock in corso...")

    result, error = generate_image(m.text)

    if result:
        bot.send_document(
            m.chat.id,
            io.BytesIO(result),
            visible_file_name="face_lock_2K.png"
        )
        bot.delete_message(m.chat.id, wait_msg.message_id)
    else:
        bot.edit_message_text(
            f"ERRORE:\n{error}",
            m.chat.id,
            wait_msg.message_id
        )


# ==============================
# SERVER RENDER
# ==============================

server = flask.Flask(__name__)

@server.route('/')
def health():
    return "Bot Online - Face Lock Priority Mode"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: server.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()

    bot.infinity_polling()

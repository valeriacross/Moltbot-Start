import os
import io
import threading
import flask
import telebot
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-2.0-flash-exp-image-generation"

# --- CARICAMENTO FACCIA MASTER ---
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(
                data=f.read(),
                mime_type="image/png"
            )
    except Exception:
        print("⚠️ ERRORE: master_face.png non trovato!")
        return None

MASTER_FACE = get_master_face()

# --- GENERAZIONE CON FACE LOCK ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        if not MASTER_FACE:
            return None, "Manca il file master_face.png"

        BODY_MANDATE = """
CRITICAL MANDATE: The final image MUST depict a strictly FEMININE BODY shape, regardless of facial structure.

BODY SPECS:
Curvaceous hourglass figure,
Full prosperous feminine breasts (Cup D),
Soft feminine body contours,
Narrow waist,
Wide hips,
Height 180cm,
Weight 85kg.

SKIN CONDITION:
Completely HAIRLESS body from neck down.
Smooth feminine skin on arms, chest, legs.
NO BODY HAIR AT ALL.
"""

        IDENTITY_CONTEXT = """
IDENTITY CONTEXT:
The subject MUST use the exact facial structure, skin texture,
beard characteristics, age details and proportions derived
from the provided master_face.png reference image.

The face must remain older male with beard,
no feminization of facial bone structure.
No face drift.
No younger reinterpretation.
"""

        NEGATIVE_PROMPTS = """
NEGATIVE PROMPT - BODY:
Masculine body shape,
flat chest,
male torso,
broad male shoulders,
muscular male frame,
body hair,
hairy chest,
hairy arms,
hairy legs.

NEGATIVE PROMPT - FACE:
Young face,
female face underneath,
beautified skin,
blurred face,
face distortion.
"""

        full_prompt = f"""
{BODY_MANDATE}

{IDENTITY_CONTEXT}

SCENE DETAILS:
{prompt_utente}

STRICTLY AVOID:
{NEGATIVE_PROMPTS}
"""

        contents = [
            full_prompt,
            MASTER_FACE
        ]

        if immagine_riferimento:
            contents.append(
                types.Part.from_bytes(
                    data=immagine_riferimento,
                    mime_type="image/jpeg"
                )
            )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"]
            )
        )

        if response.candidates:
            parts = response.candidates[0].content.parts
            for part in parts:
                if part.inline_data:
                    return part.inline_data.data, None

        return None, "Il modello non ha generato immagine."

    except Exception as e:
        return None, str(e)


# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(m):
    wait_msg = bot.reply_to(m, "⏳ Generazione con face-lock in corso...")

    prompt = m.caption if m.content_type == 'photo' else m.text
    img_data = None

    if m.content_type == 'photo':
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    risultato, errore = generate_image(prompt, img_data)

    if risultato:
        bot.send_document(
            m.chat.id,
            io.BytesIO(risultato),
            visible_file_name="generazione.png"
        )
        bot.delete_message(m.chat.id, wait_msg.message_id)
    else:
        bot.edit_message_text(
            f"❌ ERRORE:\n{errore}",
            m.chat.id,
            wait_msg.message_id
        )

# --- WEB SERVER PER RENDER ---
server = flask.Flask(__name__)

@server.route('/')
def health():
    return "Bot Online - Face Lock Active"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: server.run(
            host='0.0.0.0',
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()

    bot.infinity_polling()

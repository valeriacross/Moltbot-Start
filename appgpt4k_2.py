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

MODEL_ID = "imagen-3.0-generate-002"

# ==============================
# MASTER FACE
# ==============================

def load_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Image(image_bytes=f.read())
    except Exception:
        print("⚠ master_face.png non trovato")
        return None

MASTER_FACE = load_master_face()

# ==============================
# GENERAZIONE IMMAGINE
# ==============================

def generate_image(prompt_utente, img_ref=None):
    try:

        BODY_SPECS = """
Feminine hourglass body.
Cup D breasts.
Narrow waist.
Wide hips.
Height 180cm.
Weight 85kg.
Completely hairless body.
Smooth feminine skin.
"""

        FACE_LOCK = """
Use exact facial structure, beard,
skin texture and age from master_face reference image.
Maintain older male face.
No face drift.
No feminization of bone structure.
"""

        NEGATIVE = """
No masculine torso.
No body hair.
No flat chest.
No young face.
No facial distortion.
"""

        full_prompt = f"""
{BODY_SPECS}

{FACE_LOCK}

SCENE DESCRIPTION:
{prompt_utente}

Avoid:
{NEGATIVE}
"""

        reference_images = []

        if MASTER_FACE:
            reference_images.append(MASTER_FACE)

        if img_ref:
            reference_images.append(
                types.Image(image_bytes=img_ref)
            )

        response = client.models.generate_images(
            model=MODEL_ID,
            prompt=full_prompt,
            images=reference_images if reference_images else None,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )

        if response.generated_images:
            return response.generated_images[0].image.image_bytes, None

        return None, "Nessuna immagine generata"

    except Exception as e:
        return None, str(e)


# ==============================
# TELEGRAM BOT
# ==============================

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(m):

    wait_msg = bot.reply_to(m, "⚙ Generazione 4K in corso...")

    prompt = m.caption if m.content_type == "photo" else m.text
    img_data = None

    if m.content_type == "photo":
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    result, error = generate_image(prompt, img_data)

    if result:
        bot.send_document(
            m.chat.id,
            io.BytesIO(result),
            visible_file_name="4K_image.png"
        )
        bot.delete_message(m.chat.id, wait_msg.message_id)
    else:
        bot.edit_message_text(
            f"❌ ERRORE:\n{error}",
            m.chat.id,
            wait_msg.message_id
        )


# ==============================
# SERVER PER RENDER
# ==============================

server = flask.Flask(__name__)

@server.route('/')
def health():
    return "Bot Online - Imagen 3 Active"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: server.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()

    bot.infinity_polling()

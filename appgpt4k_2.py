import os
import io
import threading
import flask
import telebot
from PIL import Image
from google import genai

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "nanobanana_pro_preview"

# --- GESTIONE FACCIA MANDATORIA ---
def get_master_face_bytes():
    try:
        with open("master_face.png", "rb") as f:
            return f.read()
    except Exception:
        print("⚠️ ERRORE: master_face.png non trovato!")
        return None

MASTER_FACE_BYTES = get_master_face_bytes()

# --- FUNZIONE DI UPSCALING 4K ---
def upscale_to_4k(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    upscaled = img.resize((3840, 3840), Image.LANCZOS)
    output = io.BytesIO()
    upscaled.save(output, format="PNG", quality=95)
    return output.getvalue()

# --- GENERAZIONE IMMAGINE + UPSCALE ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        if not MASTER_FACE_BYTES:
            return None, "Manca il file master_face.png"

        BODY_MANDATE = """
CRITICAL MANDATE: The final image MUST depict a strictly FEMININE BODY shape, completely HAIRLESS,
curvaceous hourglass figure, full D-cup breasts, soft contours, narrow waist, wide hips.
"""

        NEGATIVE_PROMPTS = """
NEGATIVE PROMPT - BODY: masculine body shape, broad male shoulders, flat chest, muscular frame, body hair
NEGATIVE PROMPT - FACE: young female face, blurry face, face drift
"""

        full_prompt = f"""
{BODY_MANDATE}

SCENE DETAILS: {prompt_utente}

AVOID STRICTLY: {NEGATIVE_PROMPTS}
"""

        # --- CHIAMATA IMAGEN 4 ULTRA ---
        response = client.models.generate_images(
            model=MODEL_ID,
            prompt=full_prompt
        )

        if response.generated_images:
            # Upscale a 4K
            image_bytes = response.generated_images[0].image.image_bytes
            image_4k = upscale_to_4k(image_bytes)
            return image_4k, None

        return None, "Nessuna immagine generata."

    except Exception as e:
        return None, str(e)

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(m):
    wait_msg = bot.reply_to(m, "⏳ Generazione 4K in corso...")

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
            visible_file_name="generazione_4K.png"
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
    return "Bot Online - 4K Enabled"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: server.run(
            host='0.0.0.0',
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()

    bot.infinity_polling()

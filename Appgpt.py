import os, telebot, io, threading, flask
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "imagen-4.0-ultra-generate-001"

# --- GESTIONE FACCIA MANDATORIA ---
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return f.read()
    except Exception:
        print("⚠️ ERRORE: master_face.png non trovato!")
        return None

MASTER_FACE_BYTES = get_master_face()

# --- GENERAZIONE IMMAGINE 4K ---
def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        if not MASTER_FACE_BYTES:
            return None, "Manca il file master_face.png"

        BODY_MANDATE = """
CRITICAL MANDATE: The final image MUST depict a strictly FEMININE BODY shape, regardless of the facial features.
BODY SPECS: Curvaceous hourglass figure, full prosperous feminine breasts (Cup D), soft body contours, narrow waist, wide hips. Height 180cm, weight 85kg.
SKIN CONDITION: Completely HAIRLESS body from neck down. Smooth, feminine skin on arms, chest, legs. NO BODY HAIR AT ALL.
"""

        IDENTITY_CONTEXT = """
CONTEXT: High-fashion Vogue editorial photograph. The subject has the specific facial features derived from the master_face.png reference (older male face with beard) applied onto the voluptuous feminine body described above.
"""

        NEGATIVE_PROMPTS = """
NEGATIVE PROMPT - BODY (STRICT): MASCULINE BODY SHAPE, broad male shoulders, flat chest, male torso, muscular frame, hairy chest, hairy arms, hairy legs, prominent Adam's apple.
NEGATIVE PROMPT - FACE: young face, female face underneath the male features, blurry face.
"""

        full_prompt = f"""
{BODY_MANDATE}

{IDENTITY_CONTEXT}

SCENE DETAILS: {prompt_utente}

AVOID STRICTLY: {NEGATIVE_PROMPTS}
"""

        # --- CHIAMATA IMAGEN 4 ULTRA ---
        response = client.models.generate_images(
            model=MODEL_ID,
            prompt=full_prompt,
            config=types.GenerateImagesConfig(
                image_size="3840x3840",   # 4K square (~14.7MP)
                aspect_ratio="1:1"
            )
        )

        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            return image_bytes, None

        return None, "Nessuna immagine generata."

    except Exception as e:
        return None, str(e)


# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['text', 'photo'])
def handle(m):
    wait = bot.reply_to(m, "⏳ Generazione 4K in corso...")

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
        bot.delete_message(m.chat.id, wait.message_id)
    else:
        bot.edit_message_text(
            f"❌ ERRORE:\n{errore}",
            m.chat.id,
            wait.message_id
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

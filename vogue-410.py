import os, io, threading, logging, flask, telebot, html
from datetime import datetime
import pytz
from telebot import types
from google import genai
from google.genai import types as genai_types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- HEADER VERSIONE ---
VERSION = "4.1.2 (Better UX & Prompt Preview, Safe Strings)"

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "nano-banana-pro-preview"
LISBON_TZ = pytz.timezone('Europe/Lisbon')

# --- VARIABILI DI STATO ---
user_ar = defaultdict(lambda: "2:3")       # aspect ratio
user_qty = defaultdict(lambda: 1)          # numero scatti
pending_prompts = {}                       # richieste in attesa di conferma
user_stats = defaultdict(lambda: {"ok": 0, "fail": 0})  # semplici statistiche per utente

executor = ThreadPoolExecutor(max_workers=2)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                return genai_types.Part.from_bytes(
                    data=f.read(),
                    mime_type="image/png"
                )
        return None
    except Exception as e:
        logger.error(f"❌ Errore master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- COSTRUZIONE PROMPT ---
def build_master_prompt(user_text, ar_scelto):
    identity = (
        "IDENTITY: Nameless Italian transmasculine avatar. "
        "BODY: Soft feminine harmonious hourglass body, prosperous full breasts (Cup D), 180cm, 85kg. "
        "SKIN: Completely hairless (arms, legs, chest, breasts - hair NO!). "
        "FACE: Male Italian face, ~60 years old. Oval-rectangular. Ultra-detailed skin (pores, wrinkles, bags). "
        "EXPRESSION: calm, half-smile, NO teeth. EYES: dark brown/green. "
        "BEARD: light grey/silver, groomed, 6–7 cm. "
        "GLASSES: MANDATORY thin octagonal Vogue, Havana dark (NEVER removed)."
    )
    technical = (
        "HAIR: Light grey/silver, short elegant Italian style, volume. Sides 1–2 cm, nape exposed. Top less than 15 cm. "
        "Hair NEVER touching neck, shoulders, or clavicles. "
        "IMAGE CONCEPT: High-fashion photoshoot, 8K, cinematic realism. "
        "CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
    )
    rendering = (
        "RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. "
        "WATERMARK: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, very small size, opacity 90%)."
    )
    negatives = (
        "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. "
        "[Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders, buzz cut, military. "
        "[Body] body/chest/leg hair (HAIR NO!). masculine body shape, flat chest, 1:1 format."
    )

    # Niente triple-quote, niente f-string multiline: solo concatenazione sicura
    prompt = (
        "--- MASTER PROMPT ---
"
        "IDENTITY: " + identity + "

"
        "TECHNICAL: " + technical + "

"
        "SCENE: " + str(user_text) + "
"
        "FORMAT: " + str(ar_scelto) + "

"
        "RENDERING: " + rendering + "

"
        "NEGATIVES: " + negatives
    )

    return prompt

# --- CORE GENERAZIONE ---
def execute_generation(full_prompt, img_rif_bytes=None):
    try:
        contents = [full_prompt, MASTER_PART]
        if img_rif_bytes:
            contents.append(
                genai_types.Part.from_bytes(
                    data=img_rif_bytes,
                    mime_type="image/jpeg"
                )
            )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    {"category": c, "threshold": "BLOCK_NONE"}
                    for c in [
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_HARASSMENT",
                        "HARM_CATEGORY_DANGEROUS_CONTENT",
                    ]
                ],
            ),
        )

        if not response.candidates:
            return None, "❌ Errore API: No candidates."

        candidate = response.candidates[0]
        if candidate.finish_reason != "STOP":
            return None, f"🛡️ Safety: {candidate.finish_reason}"

        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None

        return None, "❌ Nessun dato immagine restituito."
    except Exception as e:
        logger.exception("Errore durante execute_generation")
        return None, f"Crash interno: {type(e).__name__}: {str(e)}"

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- /start e /settings ---
@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
        types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"),
    )
    markup.row(
        types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
        types.InlineKeyboardButton("2 Foto", callback_data="qty_2"),
    )
    bot.send_message(
        m.chat.id,
        f"<b>👠 VOGUE v{VERSION}</b>
Scegli il formato e la quantità:",
        reply_markup=markup,
    )

# --- GESTIONE CALLBACK AR / QTY ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("ar_", "qty_")))
def handle_settings_callbacks(call):
    uid = call.from_user.id

    if call.data.startswith("ar_"):
        ar_value = call.data.split("_", 1)[1]
        user_ar[uid] = ar_value
        bot.answer_callback_query(call.id, f"Formato impostato: {ar_value}")
    elif call.data.startswith("qty_"):
        qty_value = int(call.data.split("_", 1)[1])
        user_qty[uid] = qty_value
        bot.answer_callback_query(call.id, f"Quantità impostata: {qty_value} scatti")

    # Aggiorna il messaggio di settings per mostrare le scelte correnti
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                f"<b>👠 VOGUE v{VERSION}</b>
"
                f"Formato attuale: <b>{user_ar[uid]}</b>
"
                f"Quantità attuale: <b>{user_qty[uid]}</b>

"
                "Puoi cambiare formato/quantità o inviare un prompt/testo/foto."
            ),
            reply_markup=call.message.reply_markup,
        )
    except Exception as e:
        logger.error(f"Errore aggiornando messaggio di settings: {e}")

# --- CONFERMA GENERAZIONE ---
@bot.callback_query_handler(func=lambda call: call.data in ["confirm_gen", "cancel_gen"])
def handle_confirmation(call):
    uid = call.from_user.id

    # Rimuove i bottoni ma lascia il testo del prompt in chat
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None,
        )
    except Exception as e:
        logger.error(f"Errore rimozione reply_markup: {e}")

    if call.data == "cancel_gen":
        pending_prompts.pop(uid, None)
        bot.send_message(call.message.chat.id, "❌ <b>Generazione annullata.</b>")
        return

    data = pending_prompts.get(uid)
    if not data:
        bot.send_message(call.message.chat.id, "⚠️ Nessuna richiesta in attesa.")
        return

    bot.send_message(
        call.message.chat.id,
        "🚀 <b>Generazione avviata...</b>
"
        "Gli scatti verranno inviati qui man mano che sono pronti."
    )

    # Riepilogo parametri
    bot.send_message(
        call.message.chat.id,
        f"📸 Richiesti <b>{data['qty']}</b> scatti.
"
        f"Formato: <b>{data['ar']}</b>"
    )

    def run_task(idx):
        res, err = execute_generation(data['full_p'], data['img'])
        if res:
            user_stats[uid]["ok"] += 1
            bot.send_document(
                call.message.chat.id,
                io.BytesIO(res),
                visible_file_name=f"vogue_{idx+1}.jpg",
            )
        else:
            user_stats[uid]["fail"] += 1
            bot.send_message(
                call.message.chat.id,
                f"❌ Scatto {idx+1} fallito: {err}",
            )

    for i in range(data['qty']):
        executor.submit(run_task, i)

    pending_prompts.pop(uid, None)

# --- GESTIONE TESTO / FOTO ---
@bot.message_handler(content_types=['text', 'photo'])
def ask_confirmation(m):
    uid = m.from_user.id
    user_text = m.caption if m.content_type == 'photo' else m.text
    if not user_text:
        return

    img_data = None
    if m.content_type == 'photo':
        try:
            file_info = bot.get_file(m.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)
        except Exception as e:
            logger.error(f"Errore download foto utente {uid}: {e}")
            bot.reply_to(
                m,
                "⚠️ Non sono riuscito a scaricare la foto, procedo solo con il testo."
            )

    full_verbose_prompt = build_master_prompt(user_text, user_ar[uid])

    pending_prompts[uid] = {
        'full_p': full_verbose_prompt,
        'qty': user_qty[uid],
        'img': img_data,
        'ar': user_ar[uid],
    }

    logger.info(
        f"Nuova richiesta da {uid}: AR={user_ar[uid]}, qty={user_qty[uid]}"
    )

    # Anteprima prompt leggibile e copiabile
    safe_prompt = html.escape(full_verbose_prompt)

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen")
    )
    markup.row(
        types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen")
    )

    bot.reply_to(
        m,
        (
            "📝 <b>Anteprima Prompt (copiabile):</b>
"
            "<code>" + safe_prompt + "</code>

"
            f"<b>Formato:</b> {user_ar[uid]}
"
            f"<b>Quantità:</b> {user_qty[uid]}

"
            "Vuoi procedere con la generazione?"
        ),
        reply_markup=markup,
    )

# --- SERVER ---
app = flask.Flask(__name__)

@app.route('/')
def h():
    return f"Vogue v{VERSION} Online"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: app.run(
            host='0.0.0.0',
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True,
    ).start()
    bot.infinity_polling()

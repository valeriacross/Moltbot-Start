import os, logging, telebot, html, time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from C_shared100 import GeminiClient, HealthServer, is_allowed, genai_types
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK, VALERIA_NEGATIVE

# --- VERSIONE ---
VERSION = "1.0.1"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN      = os.environ.get("TELEGRAM_TOKEN")
MODEL_TEXT = "gemini-3-flash-preview"

gemini = GeminiClient()
server = HealthServer("VOGUE", VERSION)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
pending_photo = {}   # uid → bytes foto in attesa
last_prompt   = {}   # uid → ultimo prompt generato

# --- DNA VALERIA CROSS — assemblato da C_shared100.py ---
VALERIA_DNA = (
    f"{VALERIA_FACE}"
    f"{VALERIA_BODY_STRONG}"
    f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
    f"NEGATIVE: {VALERIA_NEGATIVE}"
)

# --- ANALISI FOTO ---
def analyze_photo(img_bytes):
    """Analizza foto con Gemini e restituisce descrizione strutturata della scena."""
    if not gemini.available:
        return None, "⚠️ API key non configurata."
    try:
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        prompt = (
            "Analyze this image for editorial photo recreation. "
            "Return a structured description with these exact sections:\n\n"
            "SCENE: [exact location, environment, architecture, background elements — be specific]\n"
            "OUTFIT: [every garment with color, fabric, cut, fit, details, footwear, accessories]\n"
            "LIGHTING: [light source, direction, quality, color temperature, shadows, mood]\n"
            "POSE: [body position, weight distribution, hands, energy, framing]\n"
            "CAMERA: [full body / medium / portrait, angle, depth of field]\n"
            "MOOD: [overall atmosphere, color grade, cinematic style]\n\n"
            "Be precise and visual. Do NOT describe the person's face, age, gender or identity. "
            "Focus only on scene, outfit, light, pose and technical elements."
        )
        result = gemini.generate(prompt, contents=[img_part])
        if result:
            return result, None
        return None, "⚠️ Nessuna risposta da Gemini."
    except Exception as e:
        logger.error(f"❌ Analisi foto fallita: {e}")
        return None, f"❌ Errore analisi: {html.escape(str(e))}"

# --- COSTRUZIONE PROMPT ---
def build_prompt(scene_description):
    """Assembla il prompt completo con DNA Valeria + descrizione scena."""
    prompt = (
        f"{VALERIA_DNA}\n\n"
        f"--- SCENE REFERENCE ---\n"
        f"{scene_description}\n\n"
        f"--- GENERATION INSTRUCTIONS ---\n"
        f"Generate a single editorial photograph of the described subject in the scene above.\n"
        f"Preserve ALL outfit details, colors, fabrics exactly as described.\n"
        f"Preserve the exact location and background — never replace with studio or neutral background.\n\n"
        f"NEGATIVE: wrong background, studio backdrop, missing outfit details, color shift, "
        f"face drift, missing beard, missing glasses, flat chest, male body."
    )
    return prompt

# --- KEYBOARD POST-PROMPT ---
def get_after_prompt_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 Nuova foto",      callback_data="vogue_new"),
        InlineKeyboardButton("🔁 Riusa prompt",    callback_data="vogue_reuse"),
    )
    markup.row(
        InlineKeyboardButton("🏠 Home",            callback_data="vogue_home"),
    )
    return markup

# --- /start ---
@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name
    pending_photo.pop(uid, None)
    last_prompt.pop(uid, None)
    logger.info(f"👠 /start da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>👠 VOGUE v{VERSION}</b>\n\n"
        f"Inviami una foto e genero il prompt per Flow con il DNA di Valeria Cross."
    )

# --- /info ---
@bot.message_handler(commands=['info'])
def cmd_info(m):
    api_status = "✅ Configurata" if gemini.available else "❌ Mancante"
    bot.send_message(m.chat.id,
        f"<b>ℹ️ VOGUE v{VERSION}</b>\n\n"
        f"Modello: <code>{MODEL_TEXT}</code>\n"
        f"API Key: {api_status}\n\n"
        f"<i>Genera prompt testuali per Flow — nessuna immagine generata dal bot.</i>"
    )

# --- /dna ---
@bot.message_handler(commands=['dna'])
def cmd_dna(m):
    bot.send_message(m.chat.id,
        f"<b>🧬 DNA Valeria Cross:</b>\n\n<code>{html.escape(VALERIA_DNA)}</code>"
    )

# --- CALLBACK POST-PROMPT ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("vogue_"))
def handle_vogue_callback(call):
    uid = call.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Callback non autorizzato: uid={uid}")
        return
    cid = call.message.chat.id
    data = call.data
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    if data == "vogue_new":
        last_prompt.pop(uid, None)
        bot.send_message(cid, "📸 Inviami una nuova foto.")

    elif data == "vogue_reuse":
        prompt = last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile. Invia una foto.")
            return
        bot.send_message(cid, "🔁 <b>Prompt Flow-ready</b> (reinviato)\n\nCopia e incolla su Flow:")
        chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
            if idx == len(chunks) - 1:
                bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>",
                    reply_markup=get_after_prompt_keyboard())
            else:
                bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>")

    elif data == "vogue_home":
        last_prompt.pop(uid, None)
        bot.send_message(cid,
            f"<b>👠 VOGUE v{VERSION}</b>\n\nInviami una foto."
        )

# --- HANDLER FOTO ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📸 Foto ricevuta da {username} (id={uid})")

    wait = bot.send_message(m.chat.id, "🔍 <b>Analizzo la foto...</b>")

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.delete_message(m.chat.id, wait.message_id)
        bot.send_message(m.chat.id, f"❌ Errore download foto: {html.escape(str(e))}")
        return

    scene_desc, err = analyze_photo(img_bytes)

    try: bot.delete_message(m.chat.id, wait.message_id)
    except Exception: pass

    if not scene_desc:
        bot.send_message(m.chat.id, err or "❌ Analisi fallita. Riprova.")
        return

    prompt = build_prompt(scene_desc)
    last_prompt[uid] = prompt

    bot.send_message(m.chat.id, "✅ <b>Prompt Flow-ready</b>\n\nCopia e incolla su Flow:")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=get_after_prompt_keyboard())
        else:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

    logger.info(f"✅ Prompt generato per {username} ({len(prompt)} chars)")

# --- HANDLER TESTO ---
@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text and m.text.startswith('/'):
        return
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Testo non autorizzato: uid={uid} username={m.from_user.username}")
        return
    text = m.text.strip()
    prompt = build_prompt(f"SCENE DESCRIBED BY USER:\n{text}")
    last_prompt[uid] = prompt
    bot.send_message(m.chat.id, "✅ <b>Prompt Flow-ready</b>\n\nCopia e incolla su Flow:")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=get_after_prompt_keyboard())
        else:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")
    logger.info(f"📝 Prompt da testo per {uid} ({len(prompt)} chars)")

# --- MAIN ---
if __name__ == '__main__':
    import time
    logger.info(f"👠 VOGUE v{VERSION} — avvio")
    server.start()
    if not gemini.available:
        logger.warning("⚠️ GOOGLE_API_KEY non configurata — analisi foto disabilitata")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            err = str(e)
            if "409" in err or "Conflict" in err:
                logger.warning("⚠️ 409 Conflict — altra istanza attiva. Attendo 15s e riprovo...")
                time.sleep(15)
            else:
                logger.error(f"❌ Polling error: {e}")
                time.sleep(5)

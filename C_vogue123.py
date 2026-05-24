import os, logging, telebot, html, time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from C_shared100 import GeminiClient, HealthServer, is_allowed, genai_types, analyze_scene
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK, VALERIA_NEGATIVE
from C_shared100 import VALERIA_DNA, generate_caption, generate_mini_caption, generate_mini_prompt, SHARED_VERSION, SHARED_DATE

# --- VERSIONE ---
VERSION = "1.2.3"

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
pending_photo   = {}   # uid → bytes foto in attesa
last_prompt     = {}   # uid → ultimo prompt generato
pending_caption = {}   # uid → True se in attesa foto per /caption

# --- ANALISI FOTO — usa analyze_scene() centralizzata da C_shared100 ---
def analyze_photo(img_bytes):
    """Wrapper su analyze_scene() — interfaccia invariata per il resto del bot."""
    result, err = analyze_scene(img_bytes, client=gemini)
    if result:
        return result, None
    return None, err or "⚠️ Analisi immagine non disponibile."

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
        InlineKeyboardButton("📸 Nuova foto", callback_data="vogue_new"),
        InlineKeyboardButton("🏠 Home",       callback_data="vogue_home"),
    )
    markup.row(
        InlineKeyboardButton("📝 Mini caption", callback_data="vogue_minicaption"),
        InlineKeyboardButton("📋 Mini prompt",  callback_data="vogue_miniprompt"),
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

# --- /shared ---
@bot.message_handler(commands=['shared'])
def cmd_shared(m):
    bot.send_message(m.chat.id,
        f"📦 <b>C_shared100.py</b> v{SHARED_VERSION} — {SHARED_DATE}"
    )

# --- /dna ---
@bot.message_handler(commands=['dna'])
def cmd_dna(m):
    bot.send_message(m.chat.id,
        f"<b>🧬 DNA Valeria Cross:</b>\n\n<code>{html.escape(VALERIA_DNA)}</code>"
    )

# --- /caption ---
@bot.message_handler(commands=['caption'])
def cmd_caption(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /caption non autorizzato: uid={uid} username={m.from_user.username}")
        return
    pending_caption[uid] = True
    logger.info(f"📝 /caption da {m.from_user.username or m.from_user.first_name} (id={uid})")
    bot.send_message(m.chat.id, "📸 Inviami la foto per la caption.")

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

    elif data == "vogue_minicaption":
        prompt = last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile.")
            return
        wait = bot.send_message(cid, "📝 <b>Genero la mini caption...</b>")
        cap, err = generate_mini_caption(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, cap if cap else err or "❌ Errore.", parse_mode="HTML")

    elif data == "vogue_miniprompt":
        prompt = last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile.")
            return
        wait = bot.send_message(cid, "📋 <b>Genero il mini prompt...</b>")
        mini, err = generate_mini_prompt(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, mini if mini else err or "❌ Errore.", parse_mode="HTML")

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

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Errore download foto: {html.escape(str(e))}")
        return

    # --- flusso /caption ---
    if pending_caption.pop(uid, False):
        wait = bot.send_message(m.chat.id, "✍️ <b>Genero la caption...</b>")
        caption, err = generate_caption(img_bytes, gemini)
        try: bot.delete_message(m.chat.id, wait.message_id)
        except Exception: pass
        if not caption:
            bot.send_message(m.chat.id, err or "❌ Caption fallita. Riprova.", parse_mode="HTML")
        else:
            bot.send_message(m.chat.id, caption)
        logger.info(f"✅ Caption generata per {username}")
        return

    # --- flusso normale: genera prompt Flow ---
    wait = bot.send_message(m.chat.id, "🔍 <b>Analizzo la foto...</b>")

    scene_desc, err = analyze_photo(img_bytes)

    try: bot.delete_message(m.chat.id, wait.message_id)
    except Exception: pass

    if not scene_desc:
        bot.send_message(m.chat.id, err or "❌ Analisi fallita. Riprova.", parse_mode="HTML")
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

    # --- Caption automatica ---
    caption_text, _ = generate_caption(img_bytes, gemini)
    if caption_text:
        bot.send_message(m.chat.id, caption_text, parse_mode=None)

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

import os, telebot, html, threading, flask, re, logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
VERSION = "7.0.1"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
executor = ThreadPoolExecutor(max_workers=4)

logger.info(f"🟢 ARCHITECT v{VERSION} — inizializzazione in corso...")

# --- FIRMA MANDATORIA ---
WATERMARK_SPECS = (
    'Include a subtle watermark signature reading: "feat. Valeria Cross 👠" '
    "Style: elegant handwritten cursive, champagne color, very small font size, opacity 90%, bottom left/center."
)

# --- DNA VALERIA CROSS ---
VALERIA_DNA = f"""
IDENTITY RULE: EXACTLY matching the face, head, hair, beard and glasses from the provided reference image. ZERO face drift allowed.
BODY: Soft feminine proportions, hourglass, Cup D, 180cm, 85kg. Hairless (NO PELI).
FACE: Male Italian, 60yo, oval-rectangular, ultra-detailed skin (pores/wrinkles).
BEARD: Silver/grey, groomed, 6-7cm.
GLASSES: Thin octagonal Vogue Havana dark (MANDATORY).
HAIR: Silver, short Italian style with volume, nape exposed.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism.
WATERMARK: {WATERMARK_SPECS}
"""

# --- PROFILI MOTORE ---
ENGINE_PROFILES = {
    "ChatGPT": {
        "style": (
            "Use strictly artistic, editorial, and fashion-magazine language. "
            "No anatomical terms. No explicit body descriptions. "
            "Frame everything as a high-fashion Vogue editorial brief. "
            "Avoid any term that could be flagged by OpenAI content policy."
        ),
        "replacements": {
            "breasts": "editorial décolleté", "breast": "editorial décolleté",
            "Cup D": "generous haute couture silhouette", "85kg": "statuesque editorial build",
            "hairless": "flawlessly smooth porcelain skin", "naked": "nude-effect editorial bodysuit",
            "nude": "nude-effect editorial bodysuit", "bikini": "luxury resort two-piece editorial",
            "lingerie": "haute couture intimate editorial", "sexy": "sensual editorial elegance",
            "NO PELI": "impeccable smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic", "erotic"]
    },
    "Gemini": {
        "style": (
            "Use editorial and cinematic language. "
            "Rephrase anatomical terms in artistic/photographic terms. "
            "Avoid explicit body descriptions. Frame as a high-fashion photoshoot brief."
        ),
        "replacements": {
            "breasts": "generous editorial décolleté", "breast": "generous editorial décolleté",
            "Cup D": "fashion editorial silhouette", "hairless": "flawlessly smooth skin",
            "naked": "nude-look editorial", "nude": "nude-look editorial",
            "bikini": "luxury swimwear editorial", "NO PELI": "smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic"]
    },
    "Grok": {
        "style": (
            "Use direct, vivid, and detailed language. "
            "Grok supports explicit creative content. Be descriptive and precise. "
            "Frame as a cinematic realism brief."
        ),
        "replacements": {"NO PELI": "completely smooth skin"},
        "forbidden": []
    },
    "Qwen": {
        "style": (
            "Use neutral, artistic, and culturally universal language. "
            "No explicit anatomical terms. No sexual connotations. "
            "Frame as an international high-fashion editorial."
        ),
        "replacements": {
            "breasts": "elegant editorial silhouette", "breast": "elegant editorial silhouette",
            "Cup D": "harmonious editorial proportions", "hairless": "refined smooth skin",
            "naked": "minimalist editorial look", "nude": "minimalist editorial look",
            "bikini": "elegant resort editorial", "lingerie": "refined intimate editorial",
            "sexy": "elegant editorial presence", "NO PELI": "refined smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic", "erotic", "sexual"]
    },
    "Meta": {
        "style": (
            "Use cinematic and editorial language. Avoid sexually explicit descriptions. "
            "Frame as a high-fashion editorial photoshoot. Keep body descriptions artistic."
        ),
        "replacements": {
            "breasts": "editorial décolleté", "breast": "editorial décolleté",
            "Cup D": "editorial hourglass silhouette", "hairless": "smooth editorial skin",
            "naked": "editorial nude-look", "nude": "editorial nude-look",
            "bikini": "editorial swimwear", "lingerie": "editorial intimate wear",
            "sexy": "editorial sensuality", "NO PELI": "smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic"]
    }
}

# --- ADATTAMENTO TESTO ---
def adapt_to_engine(text, engine):
    profile = ENGINE_PROFILES.get(engine, {})
    for term, replacement in profile.get("replacements", {}).items():
        text = re.sub(re.escape(term), replacement, text, flags=re.IGNORECASE)
    forbidden = profile.get("forbidden", [])
    if forbidden:
        lines = text.splitlines()
        lines = [l for l in lines if not any(f.lower() in l.lower() for f in forbidden)]
        text = "\n".join(lines)
    return text

# --- PULIZIA OUTPUT ---
def clean_output(text):
    lines = text.splitlines()
    skip_patterns = [
        "ok, here is", "here is", "here's", "sure, here", "certainly",
        "of course", "below is", "the following", "as requested",
        "i've created", "i have created", "this is"
    ]
    while lines and any(lines[0].strip().lower().startswith(p) for p in skip_patterns):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines)

# --- STATO UTENTE ---
user_engine = {}
user_last_input = {}

# --- MENU ---
def get_engine_kb(is_loop=False):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🤖 CHATGPT", callback_data="eng_ChatGPT"),
        InlineKeyboardButton("✨ GEMINI", callback_data="eng_Gemini")
    )
    markup.row(
        InlineKeyboardButton("🦁 GROK", callback_data="eng_Grok"),
        InlineKeyboardButton("🧠 QWEN", callback_data="eng_Qwen")
    )
    markup.row(InlineKeyboardButton("♾️ META", callback_data="eng_Meta"))
    if is_loop:
        markup.row(InlineKeyboardButton("🔄 NUOVA RICHIESTA DA ZERO", callback_data="action_reset"))
    return markup

# --- COMANDI ---
@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    user_last_input.pop(uid, None)
    logger.info(f"🔄 /start da {username} (id={uid})")
    bot.send_message(m.chat.id, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il modello target:", reply_markup=get_engine_kb())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>📂 ARCHITECT — Guida rapida</b>\n\n"
        f"<b>Come si usa:</b>\n"
        f"1. Scegli il motore target (/motore)\n"
        f"2. Invia un testo con la tua idea, oppure una foto (con didascalia opzionale)\n"
        f"3. Architect genera un Master Prompt ottimizzato per quel motore\n"
        f"4. Puoi riadattarlo per un altro motore senza reinserire l'idea\n\n"
        f"<b>Comandi:</b>\n"
        f"/start o /reset — ricomincia da zero\n"
        f"/motore — scegli il motore target\n"
        f"/help — questa guida\n"
        f"/info — versione e motori disponibili\n\n"
        f"<b>Motori supportati:</b>\n"
        f"🤖 ChatGPT — ✨ Gemini — 🦁 Grok — 🧠 Qwen — ♾️ Meta"
    )

@bot.message_handler(commands=['info'])
def cmd_info(m):
    uid = m.from_user.id
    current_engine = user_engine.get(uid, "Nessuno selezionato")
    bot.send_message(m.chat.id,
        f"<b>ℹ️ ARCHITECT Info</b>\n\n"
        f"Versione: <b>{VERSION}</b>\n"
        f"Motore attuale: <b>{current_engine}</b>\n"
        f"Motori disponibili: ChatGPT, Gemini, Grok, Qwen, Meta"
    )

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_") or c.data == "action_reset")
def handle_callbacks(c):
    cid = c.message.chat.id
    uid = c.from_user.id
    username = c.from_user.username or c.from_user.first_name

    if c.data == "action_reset":
        user_engine.pop(uid, None)
        user_last_input.pop(uid, None)
        logger.info(f"🔄 Reset da {username} (id={uid})")
        bot.edit_message_text("🔄 Reset completato. Scegli un modello:", cid, c.message.message_id, reply_markup=get_engine_kb())
        return

    engine_choice = c.data.split("_")[1]
    user_engine[uid] = engine_choice
    bot.answer_callback_query(c.id, f"Target: {engine_choice}")
    logger.info(f"⚙️ {username} (id={uid}) → motore: {engine_choice}")

    if uid in user_last_input:
        bot.edit_message_text(f"⚙️ <b>Riadattamento per {engine_choice}...</b>", cid, c.message.message_id)
        saved = user_last_input[uid]
        executor.submit(execute_generation, cid, saved['text'], engine_choice, saved['img'])
    else:
        bot.edit_message_text(f"✅ Target: <b>{engine_choice}</b>\nInvia l'idea da processare.", cid, c.message.message_id)

# --- GENERAZIONE DA TESTO ---
def generate_monolith_prompt(user_input, engine):
    try:
        profile = ENGINE_PROFILES.get(engine, {})
        engine_style = profile.get("style", "Use professional editorial language.")
        instr = (
            f"Write a professional MASTER PROMPT optimized for {engine}.\n\n"
            f"ENGINE STYLE RULES (mandatory):\n{engine_style}\n\n"
            f"STEPS:\n"
            f"1. Open with: 'EXACTLY matching the face, head, hair, beard and glasses from the provided reference image.'\n"
            f"2. Integrate the user idea with Valeria Cross DNA below.\n"
            f"3. CRITICAL: Do NOT use the name 'Valeria Cross' or 'DNA of Valeria Cross' anywhere in the output. "
            f"The target engine does not know who Valeria Cross is. "
            f"Instead, fully expand ALL physical attributes inline: describe the face, beard, glasses, hair, body proportions "
            f"in explicit detail within the prompt text itself.\n"
            f"4. Add strong negative prompts: 'young female face, long dark hair, no beard, obscured face, low quality, 1:1 ratio'.\n"
            f"5. Output: single monolithic block, prolix, technical, Vogue editorial style.\n\n"
            f"DNA:\n{VALERIA_DNA}\n\n"
            f"USER IDEA:\n{user_input}"
        )
        logger.info(f"   📤 Chiamata API testo ({engine})...")
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=[instr])
        if response.text:
            logger.info(f"   ✅ Risposta ricevuta ({len(response.text)} chars)")
            return response.text.strip()
        logger.warning("   ⚠️ Risposta API vuota.")
        return "⚠️ Risposta vuota."
    except Exception as e:
        logger.error(f"   ❌ Errore API testo: {e}", exc_info=True)
        return f"ERRORE API: {str(e)}"

# --- GENERAZIONE DA IMMAGINE ---
def generate_from_image(img_bytes, extra_text, engine):
    try:
        profile = ENGINE_PROFILES.get(engine, {})
        engine_style = profile.get("style", "Use professional editorial language.")
        instr = (
            f"Analyze the provided image in detail. Extract: scene, environment, lighting, pose, outfit, mood, photographic style.\n"
            f"Then write a professional MASTER PROMPT optimized for {engine}, replacing the subject with Valeria Cross DNA.\n\n"
            f"ENGINE STYLE RULES (mandatory):\n{engine_style}\n\n"
            f"STEPS:\n"
            f"1. Open with: 'EXACTLY matching the face, head, hair, beard and glasses from the provided reference image.'\n"
            f"2. Keep ONLY the visual elements from the image (scene, outfit, light, pose). Replace the original subject entirely with Valeria Cross DNA.\n"
            f"3. CRITICAL: Do NOT use the name 'Valeria Cross' or 'DNA of Valeria Cross' anywhere in the output. "
            f"The target engine does not know who Valeria Cross is. "
            f"Instead, fully expand ALL physical attributes inline: describe the face, beard, glasses, hair, body proportions "
            f"in explicit detail within the prompt text itself.\n"
            f"4. If extra instructions are provided, integrate them.\n"
            f"5. Add strong negative prompts: 'young female face, long dark hair, no beard, obscured face, low quality, 1:1 ratio'.\n"
            f"6. Output: single monolithic block, prolix, technical, Vogue editorial style.\n\n"
            f"DNA:\n{VALERIA_DNA}\n\n"
        )
        if extra_text:
            instr += f"EXTRA INSTRUCTIONS:\n{extra_text}"
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        logger.info(f"   📤 Chiamata API immagine ({engine})...")
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[instr, img_part]
        )
        if response.text:
            logger.info(f"   ✅ Risposta ricevuta ({len(response.text)} chars)")
            return response.text.strip()
        logger.warning("   ⚠️ Risposta API vuota.")
        return "⚠️ Risposta vuota."
    except Exception as e:
        logger.error(f"   ❌ Errore API immagine: {e}", exc_info=True)
        return f"ERRORE API: {str(e)}"

# --- REVIEW E FIX CONTRADDIZIONI ---
def review_and_fix(prompt, engine):
    """Secondo passaggio API: rileva e corregge contraddizioni nel prompt generato."""
    try:
        review_instr = (
            f"You are a prompt quality reviewer. Carefully read the following image generation prompt "
            f"and fix ALL contradictions, inconsistencies and conflicts. Return ONLY the corrected prompt, "
            f"no explanations, no preamble.\n\n"
            f"MANDATORY FIXES — apply all of these:\n\n"
            f"1. HAIR: Valeria Cross has SHORT silver/grey hair (sides 1-2cm, top max 15cm, nape exposed). "
            f"Remove or replace ANY mention of: long hair, brown hair, dark hair, flowing hair, loose waves, "
            f"slicked back long hair, wet long hair, hair falling on shoulders. "
            f"Replace with: short silver Italian cut, slightly disheveled, voluminous top.\n\n"
            f"2. NEGATIVE PROMPTS CONFLICTS: Scan the negative prompts section. "
            f"Remove from negatives any term that contradicts a positive element in the prompt. Examples:\n"
            f"   - If prompt contains watermark → remove 'watermark' from negatives\n"
            f"   - If prompt contains beard → remove 'no beard' from negatives\n"
            f"   - If prompt contains glasses → remove 'no glasses' from negatives\n"
            f"   - If prompt contains text/signature → remove 'text', 'logo' from negatives\n\n"
            f"3. SUBJECT BLEED: Remove any physical description belonging to the original reference subject "
            f"(e.g. young face, female features, dark eyes if contradicting DNA, feminine name). "
            f"Valeria Cross DNA: Male Italian face 60yo, silver beard 6-7cm, octagonal Vogue glasses, "
            f"silver short hair, hourglass body, smooth skin.\n\n"
            f"4. WATERMARK TEXT: The watermark signature text MUST read exactly: 'feat. Valeria Cross 👠' "
            f"in elegant champagne cursive, very small, bottom center/left, 90% opacity. "
            f"If the prompt contains any other watermark text (e.g. '60yo Italian Elegance', 'Valeria', anything else) "
            f"replace it with the exact text above. Never invent alternative watermark text.\n\n"
            f"5. NAME REMOVAL: Remove any occurrence of 'Valeria Cross' or 'DNA of Valeria Cross' from the prompt body. "
            f"Replace with the explicit physical description already present in the prompt, or expand from DNA if missing.\n\n"
            f"6. KEEP INTACT: scene, outfit, lighting, environment, pose, mood, camera settings, "
            f"photographic style, watermark spec, all creative elements not related to the subject's identity. "
            f"Exception: if the prompt references a real magazine brand as a visual element (e.g. 'VOGUE' logo, 'Harper's Bazaar' masthead) "
            f"replace it with a generic description like 'luxury fashion magazine cover typography' to avoid trademark text in the output.\n\n"
            f"PROMPT TO REVIEW:\n\n{prompt}"
        )
        logger.info(f"   🔍 Review contraddizioni ({engine})...")
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=[review_instr])
        if response.text:
            fixed = response.text.strip()
            logger.info(f"   ✅ Review completata ({len(fixed)} chars)")
            return fixed
        logger.warning("   ⚠️ Review: risposta vuota, uso prompt originale.")
        return prompt
    except Exception as e:
        logger.warning(f"   ⚠️ Review fallita, uso prompt originale: {e}")
        return prompt


def execute_generation(cid, text, engine, img_bytes=None):
    logger.info(f"🚀 execute_generation | engine={engine} | img={'sì' if img_bytes else 'no'} | text={str(text)[:60]}")
    if img_bytes:
        raw = generate_from_image(img_bytes, text, engine)
    else:
        raw = generate_monolith_prompt(text, engine)

    if raw.startswith("ERRORE API:"):
        logger.error(f"❌ Errore generazione: {raw}")
        bot.send_message(cid, f"❌ <b>Errore:</b>\n<code>{html.escape(raw)}</code>")
        return

    # Review e fix contraddizioni
    reviewed = review_and_fix(raw, engine)
    adapted = adapt_to_engine(clean_output(reviewed), engine)
    logger.info(f"✅ Prompt generato, revisionato e adattato per {engine} ({len(adapted)} chars)")
    bot.send_message(cid, f"✅ <b>Master Prompt → {engine}:</b>\n\n<code>{html.escape(adapted)}</code>")
    bot.send_message(cid, "🔄 Vuoi riadattarlo per un altro motore o iniziare da zero?", reply_markup=get_engine_kb(is_loop=True))

# --- HANDLER TESTO ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    if uid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return
    logger.info(f"✏️ Testo da {username} (id={uid}) → {user_engine[uid]}: «{m.text[:60]}»")
    user_last_input[uid] = {'text': m.text, 'img': None}
    wait = bot.send_message(cid, f"🚀 <b>Generazione per {user_engine[uid]}...</b>")
    def task():
        execute_generation(cid, m.text, user_engine[uid])
        try:
            bot.delete_message(cid, wait.message_id)
        except Exception:
            pass
    executor.submit(task)

# --- HANDLER FOTO ---
@bot.message_handler(content_types=['photo'])
def build_prompt_from_image(m):
    cid = m.chat.id
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    if uid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
        logger.info(f"🖼️ Foto da {username} (id={uid}), {len(img_bytes)} bytes → {user_engine[uid]}")
    except Exception as e:
        logger.error(f"❌ Errore download foto da {username}: {e}")
        bot.reply_to(m, f"❌ Errore nel scaricare la foto: {html.escape(str(e))}")
        return
    extra_text = m.caption if m.caption else None
    user_last_input[uid] = {'text': extra_text, 'img': img_bytes}
    wait = bot.send_message(cid,
        f"🔍 <b>Analisi immagine per {user_engine[uid]}...</b>\n"
        f"⏳ Estrazione scena e generazione prompt in corso.")
    def task():
        execute_generation(cid, extra_text, user_engine[uid], img_bytes=img_bytes)
        try:
            bot.delete_message(cid, wait.message_id)
        except Exception:
            pass
    executor.submit(task)

# --- SERVER ---
app = flask.Flask(__name__)

@app.route('/')
def h():
    return f"ARCHITECT_V{VERSION}_ONLINE"

if __name__ == "__main__":
    logger.info(f"🟢 Avvio ARCHITECT v{VERSION}")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

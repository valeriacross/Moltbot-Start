import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "1.0.8"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN   = os.environ.get("TELEGRAM_TOKEN_SORPRESA")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client  = genai.Client(api_key=API_KEY)
MODEL_ID      = "gemini-3-pro-image-preview"
MODEL_TEXT_ID = "gemini-3-flash-preview"

executor = ThreadPoolExecutor(max_workers=4)

# --- MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("masterface.png"):
            with open("masterface.png", "rb") as f:
                data = f.read()
            logger.info("✅ masterface.png caricata.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        logger.warning("⚠️ masterface.png non trovata.")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento masterface: {e}")
        return None

MASTER_PART = get_face_part()

# --- VALERIA IDENTITY ---
VALERIA_IDENTITY = (
    "MASTER PROMPT — GEMINI OPTIMIZED — SYNTHETIC FACE IDENTITY LOCK\n\n"
    "The male facial identity used in this generation is fully synthetic. "
    "SynthID verifiable. NOT a real person. ZERO face drift allowed. Absolute identity preservation.\n\n"
    "**Facial identity:** 60-year-old Italian male face, oval-rectangular shape. "
    "Ultra-detailed mature skin texture with visible pores, deep-set character wrinkles, crow's feet. "
    "Calm half-smile, no teeth. "
    "Thin octagonal Vogue Havana dark tortoiseshell frame eyeglasses (MANDATORY, always present).\n\n"
    "**Hair:** Short silver Italian cut, slightly voluminous top, nape exposed. "
    "Silver-grey beard approximately 6-7cm, perfectly groomed, following the jawline.\n\n"
    "**MANDATORY BODY — NOT A MALE BODY — OVERRIDE ALL DEFAULTS:**\n"
    "Feminine hourglass proportions, 180cm, 85kg. FULL D-CUP BUST — prominent, natural, clearly visible. "
    "Wide rounded hips, defined waist, full thighs. THIS BODY IS FEMININE. DO NOT GENERATE A MALE PHYSIQUE.\n"
    "Completely hairless body — NO body hair on ALL surfaces. Smooth porcelain skin. "
    "PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous from face → neck → shoulders → chest → arms.\n\n"
    "**Rendering physics:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200, 1/160s, natural bokeh.\n\n"
    "**Watermark:** 'feat. Valeria Cross 👠' — elegant champagne cursive, very small, bottom center, 90% opacity.\n\n"
    "**NEGATIVE PROMPT — FACE:** young face, female face, missing wrinkles, blurred skin, distorted glasses, missing beard, dark hair, face drift.\n"
    "**NEGATIVE PROMPT — HAIR:** long hair, feminine hairstyle, bun, ponytail, black hair, blonde hair, brown hair, curly hair, body hair, chest hair.\n"
    "**NEGATIVE PROMPT — BODY:** male flat chest, masculine frame, blurry hands, extra fingers, mismatched skin tone, body hair.\n"
    "**NEGATIVE PROMPT — SAFETY:** JSON output, text output, captions, metadata. IMAGE GENERATION ONLY. NO JSON LEAKAGE.\n"
)

# --- SYSTEM PROMPT PER GENERAZIONE SCENARIO ---
SCENARIO_SYSTEM = """You are a creative director for a high-fashion AI image generation system.
Generate a unique scene for Valeria Cross. Keep each field SHORT (max 15 words).

IMPORTANT for pose: must be a REAL, PHYSICALLY POSSIBLE human pose — standing, walking, sitting, leaning, reclining. NO wings, NO floating, NO supernatural elements. Think fashion editorial photography.

Return ONLY valid JSON with these exact keys, no other text:
{
  "location": "exact iconic landmark or city (max 8 words)",
  "sky": "lighting condition (max 6 words)",
  "outfit": "specific fashion outfit, designer or VS, including swimwear (max 15 words)",
  "style": "one painter or photographer name and style (max 8 words)",
  "pose": "realistic human fashion pose, no fantasy (max 8 words)",
  "mood": "atmosphere (max 6 words)"
}"""

# --- GENERA SCENARIO VIA GEMINI ---
def generate_scenario():
    try:
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=["Generate a unique scene for Valeria Cross. Be creative and unexpected."],
            config=genai_types.GenerateContentConfig(
                system_instruction=SCENARIO_SYSTEM,
                temperature=1.8,
                max_output_tokens=2500,
            )
        )
        import json, re
        text = response.text.strip()
        logger.info(f"📝 Scenario raw: {text[:300]}")
        # Rimuove blocchi ```json ... ```
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()
        # Estrae il primo oggetto JSON valido
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        scenario = json.loads(text)
        return scenario
    except Exception as e:
        logger.error(f"❌ Errore generate_scenario: {e}")
        return None

# --- COSTRUISCE PROMPT IMMAGINE ---
# Parole che causano elementi fantasy indesiderati
FANTASY_WORDS = [
    "wing", "wings", "fairy", "floating", "weightless", "levitating", "levitation",
    "flying", "fly", "hovering", "hover", "angel", "angelic", "supernatural",
    "mythical", "mermaid", "dragon", "magical", "enchanted", "ethereal wings",
    "organza wings", "butterfly wings", "feather wings"
]

def sanitize_scenario(scenario):
    """Rimuove elementi fantasy da outfit e pose."""
    import re
    for field in ["outfit", "pose", "mood"]:
        val = scenario.get(field, "")
        for word in FANTASY_WORDS:
            val = re.sub(rf"\b{re.escape(word)}\b", "", val, flags=re.IGNORECASE)
        # Pulisce spazi multipli e virgole orfane
        val = re.sub(r",\s*,", ",", val)
        val = re.sub(r"\s+", " ", val).strip(" ,")
        scenario[field] = val
    return scenario

def build_prompt(scenario):
    scenario = sanitize_scenario(scenario)
    fmt = random.choice(["2:3", "16:9"])
    prompt = (
        f"{VALERIA_IDENTITY}\n\n"
        f"SCENE: {scenario['location']}. {scenario['sky']}.\n\n"
        f"OUTFIT: {scenario['outfit']}\n\n"
        f"POSE: {scenario['pose']}. Body must follow realistic human anatomy and physics — weight supported, no impossible floating positions.\n\n"
        f"MOOD: {scenario['mood']}\n\n"
        f"VISUAL STYLE: {scenario['style']}\n\n"
        f"FORMAT: {fmt}\n\n"
        f"Ultra-detailed 8K cinematic photography. No text, no watermark except the mandatory one."
    )
    return prompt, fmt

# --- GENERA IMMAGINE ---
def execute_generation(full_prompt, formato="2:3"):
    try:
        size_map = {"2:3": "768x1024", "16:9": "1024x576"}
        if MASTER_PART:
            contents = [MASTER_PART, full_prompt]
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")
            contents = [full_prompt]

        def _call():
            return client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=genai_types.ImageConfig(image_size="2K"),
                    safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in
                                      ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH",
                                       "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                )
            )

        for _attempt in range(2):
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                future = _ex.submit(_call)
                try:
                    response = future.result(timeout=120)
                    break
                except _cf.TimeoutError:
                    if _attempt == 0:
                        logger.warning("⚠️ Timeout (120s) — retry tra 15s")
                        time.sleep(15)
                    else:
                        return None, "⏱️ Timeout dopo 2 tentativi."
        else:
            return None, "⏱️ Timeout dopo 2 tentativi."

        if not response.candidates:
            return None, "❌ Nessun candidato dall'API."

        candidate = response.candidates[0]
        finish_str = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
        if finish_str != "STOP":
            return None, f"🛡️ Bloccata: {finish_str}"

        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None

        return None, "❌ Nessuna immagine nella risposta."

    except Exception as e:
        logger.error(f"❌ Eccezione execute_generation: {e}", exc_info=True)
        return None, f"❌ Errore interno: {html.escape(str(e))}"

# --- GENERA CAPTION THREADS ---
def generate_caption(scenario):
    try:
        prompt = (
            f"Write a social media caption for a high-fashion photo. "
            f"Location: {scenario['location']}. "
            f"Outfit: {scenario['outfit']}. "
            f"Mood: {scenario['mood']}. "
            f"Style: {scenario['style']}. "
            f"Rules: 1-2 evocative sentences, rich with emojis (4-6), poetic and fashion-forward tone. "
            f"Return ONLY the caption text, nothing else."
        )
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[prompt],
            config=genai_types.GenerateContentConfig(max_output_tokens=150)
        )
        return response.text.strip()
    except Exception:
        return None

# --- BOT ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
last_scenario = {}
last_prompt   = {}

# --- KEYBOARDS ---
def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎲 Surprise me!", callback_data="tira"))
    return markup

def get_confirm_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Genera!", callback_data="conferma"),
        InlineKeyboardButton("🎲 Rigenera scena", callback_data="tira")
    )
    return markup

def get_retry_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Nuova scena", callback_data="tira"),
        InlineKeyboardButton("🔁 Riprova questa", callback_data="riprova")
    )
    return markup

# --- FORMAT SCENARIO ---
def format_scenario(s):
    return (
        f"📍 <b>Location:</b> {s['location']}\n"
        f"🌤 <b>Sky:</b> {s['sky']}\n"
        f"👗 <b>Outfit:</b> {s['outfit']}\n"
        f"🎨 <b>Style:</b> {s['style']}\n"
        f"💃 <b>Pose:</b> {s['pose']}\n"
        f"✨ <b>Mood:</b> {s['mood']}"
    )

# --- /start ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Ogni volta che premi il pulsante, Gemini sceglie liberamente:\n"
        f"📍 Una location iconica nel mondo\n"
        f"🌤 Un cielo e un'atmosfera\n"
        f"👗 Un outfit da sfilata o Victoria's Secret\n"
        f"🎨 Uno stile pittorico o fotografico\n\n"
        f"Nessuna lista predefinita. Tutto davvero random.",
        reply_markup=get_main_keyboard())

# --- /info ---
@bot.message_handler(commands=['info'])
def handle_info(message):
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Genera scenari completamente liberi tramite Gemini.\n"
        f"Formati: <b>2:3</b> o <b>16:9</b> (random)\n"
        f"Comandi: /start /info /lastprompt")

# --- /lastprompt ---
@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    prompt = last_prompt.get(uid)
    if not prompt:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data in ["tira", "conferma", "riprova"])
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name

    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    if call.data == "tira":
        wait = bot.send_message(cid, "🎲 Gemini sta scegliendo la scena...")

        def pick_scene():
            scenario = generate_scenario()
            try: bot.delete_message(cid, wait.message_id)
            except Exception: pass
            if not scenario:
                bot.send_message(cid, "❌ Errore nella generazione della scena. Riprova.",
                    reply_markup=get_main_keyboard())
                return
            last_scenario[uid] = scenario
            bot.send_message(cid,
                f"🎲 <b>Scena estratta:</b>\n\n{format_scenario(scenario)}\n\nVuoi generare?",
                reply_markup=get_confirm_keyboard())
            logger.info(f"🎲 {username} (id={uid}) — scena: {scenario['location']} | {scenario['style']}")

        executor.submit(pick_scene)

    elif call.data == "conferma":
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            try:
                t = time.time()
                full_p, fmt = build_prompt(scenario)
                last_prompt[uid] = full_p
                img, err = execute_generation(full_p, formato=fmt)
                elapsed = round(time.time() - t, 1)
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ {elapsed}s | {fmt}",
                        reply_markup=get_retry_keyboard())
                    caption = generate_caption(scenario)
                    if caption:
                        bot.send_message(cid, f"{caption}\n#genderfluid #selfexpression #bodypositivity")
                    logger.info(f"✅ {username} (id={uid}) — {elapsed}s | {fmt} | {scenario['location']}")
                else:
                    bot.send_message(cid, f"❌ <b>Generazione fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")

        executor.submit(run)

    elif call.data == "riprova":
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        bot.send_message(cid, "🔁 Riprovo la stessa scena...\n⏳ Generazione in corso...")

        def run_retry():
            try:
                t = time.time()
                full_p, fmt = build_prompt(scenario)
                last_prompt[uid] = full_p
                img, err = execute_generation(full_p, formato=fmt)
                elapsed = round(time.time() - t, 1)
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ Retry — {elapsed}s | {fmt}",
                        reply_markup=get_retry_keyboard())
                    caption = generate_caption(scenario)
                    if caption:
                        bot.send_message(cid, f"{caption}\n#genderfluid #selfexpression #bodypositivity")
                    logger.info(f"✅ {username} retry (id={uid}) — {elapsed}s")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run_retry() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")

        executor.submit(run_retry)

# --- FLASK ---
app = flask.Flask(__name__)

@app.route('/')
def health():
    return f"surprise v{VERSION} ok", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- MAIN ---
if __name__ == '__main__':
    logger.info(f"🎲 SURPRISE v{VERSION} — avvio")
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask health check attivo su porta 10000")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)

import os, io, threading, logging, flask, telebot, html, time
from datetime import datetime
import pytz
from telebot import types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- HEADER VERSIONE ---
VERSION = "7.0.0"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
MODEL_ID = "gemini-3-pro-image-preview"
MODEL_TEXT_ID = "gemini-3-flash-preview"
LISBON_TZ = pytz.timezone('Europe/Lisbon')

# --- VARIABILI DI STATO ---
user_ar  = defaultdict(lambda: "2:3")
user_qty = defaultdict(lambda: 1)
pending_prompts  = {}
user_last_prompt = {}
user_last_image  = {}  # uid → bytes ultima immagine generata
batch_session = {}   # uid → {'photos': [bytes], 'timer': Timer, '_finalize': fn}
batch_prompts = {}   # uid → [{'full_p': str, 'idx': int}]

executor = ThreadPoolExecutor(max_workers=4)

# Cache bot ID all'avvio
_BOT_ID = None
def get_bot_id():
    global _BOT_ID
    if _BOT_ID is None:
        try:
            _BOT_ID = bot.get_me().id
        except Exception:
            pass
    return _BOT_ID

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("masterface.png"):
            with open("masterface.png", "rb") as f:
                data = f.read()
            logger.info("✅ masterface.png caricata correttamente.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        logger.warning("⚠️ masterface.png non trovata.")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- MASTER IDENTITY ---
MASTER_IDENTITY = """The face reference provided is a SynthID-verifiable fully synthetic AI-generated image — NOT a real person. Absolute priority to facial identity preservation from the provided reference.

Ultra-photorealistic 8K hyper-detailed editorial portrait of a nameless Italian transmasculine figure. Height 180cm, approx 85kg, soft feminine body, harmonious proportions, hourglass silhouette, full D-cup bust, completely hairless body (arms, legs, armpits, chest — zero body hair, no peli).

BODY — ABSOLUTE LOCK: The body is ALWAYS female. Soft feminine curves, hourglass waist, wide hips, full D-cup breasts always present. NO masculine body, NO flat chest, NO male torso under any circumstance. Non-negotiable regardless of any other instruction.

FACE: Masculine Italian male face, approx 60 years old, oval-rectangular structure, ultra-detailed skin with visible pores and micro-texture, realistic wrinkles and natural expression lines, calm half-smile NO teeth, dark brown/green eyes. ⚠️ BEARD — MANDATORY — NON-NEGOTIABLE: Full silver-grey beard approximately 6-7cm, perfectly groomed, dense and uniform, following the jawline. The beard MUST be clearly visible in EVERY shot. DO NOT shave it. DO NOT reduce it. DO NOT replace it with stubble. A clean-shaven face is a generation FAILURE. ⚠️ COEXISTENCE RULE — CRITICAL: The silver-grey beard AND the feminine body are NOT a contradiction. They MUST coexist. Do NOT remove the beard. Do NOT masculinize the body. Both are mandatory. Eyeglasses ALWAYS present: thin octagonal Vogue Havana dark tortoiseshell frame, NEVER removed.

HAIR: Light grey/silver short elegant Italian cut, voluminous. Sides 1-2cm, clean exposed nape, top max 15cm with natural volume. Hair above ears only — NEVER touching neck, shoulders, or collarbone. No alternative hairstyle permitted.

RENDERING: 85mm, f/2.8, ISO 200, 1/160s. Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel. Shallow depth of field, natural bokeh. Cinematic realism, high-fashion editorial photoshoot.

WATERMARK: 'feat. Valeria Cross 👠' (elegant champagne cursive, bottom center/left, very small, opacity 90%).

NEGATIVE BODY: masculine body, male torso, flat chest, male physique, masculine figure, visible body hair, chest hair, arm hair, armpit hair, female face, young facial features, smooth artificial skin, CGI look, plastic materials.
NEGATIVE HAIR: long hair, medium hair, ponytail, bun, braid, hair touching neck or shoulders or collarbone, buzz cut, shaved head, black hair, brown hair.

NO JSON, NO TEXT OUTPUT, NO METADATA — image generation only."""

# --- TRADUZIONE IN INGLESE ---
def translate_to_english(user_text):
    try:
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[
                f"Detect the language of the following text. "
                f"If it is already in English, return it exactly as-is. "
                f"If it is in any other language, translate it to English faithfully, "
                f"preserving all formatting, structure, and technical details. "
                f"Return only the translated text, no explanations, no preamble.\n\n{user_text}"
            ],
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2000,
            )
        )
        if response.text:
            translated = response.text.strip()
            logger.info(f"🌐 Testo tradotto in inglese ({len(translated)} chars)")
            return translated
        return user_text
    except Exception as e:
        logger.warning(f"⚠️ Traduzione fallita, uso testo originale: {e}")
        return user_text

# --- OCR: ESTRAZIONE TESTO DA IMMAGINE-PROMPT ---
def extract_text_from_image(img_bytes):
    """Usa Gemini vision per estrarre testo da uno screenshot di prompt."""
    try:
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[
                img_part,
                "This image contains a text prompt for image generation. "
                "Extract ALL the text exactly as written, preserving every detail, "
                "paragraph, and formatting. Return only the extracted text, nothing else."
            ],
            config=genai_types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
            )
        )
        if response.text:
            extracted = response.text.strip()
            logger.info(f"📖 Testo estratto da immagine ({len(extracted)} chars)")
            return extracted
        return None
    except Exception as e:
        logger.warning(f"⚠️ OCR fallito: {e}")
        return None

def describe_scene_for_faceswap(img_bytes):
    """Usa Flash per descrivere scena, outfit, luce e posa — per faceswap testuale."""
    try:
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[
                img_part,
                "Analyze this image in detail for editorial photo recreation. Describe:\n"
                "1. SCENE & BACKGROUND: location, environment, architecture, setting, atmosphere\n"
                "2. OUTFIT: every garment, fabric, color, cut, fit, accessories, shoes\n"
                "3. LIGHTING: light source, direction, quality, color temperature, shadows, mood\n"
                "4. POSE & BODY LANGUAGE: body position, weight distribution, hand placement, general energy\n"
                "5. CAMERA: framing (full body/medium/portrait), angle, depth of field, lens feel\n"
                "6. COLOR GRADE & MOOD: overall tone, color palette, cinematic style\n\n"
                "Be precise and visual. Do NOT mention the person's face, identity or gender. "
                "Focus only on scene, clothes, light, pose and technical elements. "
                "Return a structured description, one section per point."
            ],
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1500,
            )
        )
        if response.text:
            desc = response.text.strip()
            logger.info(f"🎬 Scena descritta per faceswap ({len(desc)} chars)")
            return desc
        return None
    except Exception as e:
        logger.warning(f"⚠️ Descrizione scena fallita: {e}")
        return None


def build_batch_prompt_for_photo(img_bytes, ar, idx):
    """Analizza una foto e genera un prompt ottimizzato per Vogue — usato nel batch."""
    try:
        scene_desc = describe_scene_for_faceswap(img_bytes)
        if not scene_desc:
            return None
        scene_text = (
            f"Editorial reinterpretation of this scene for Valeria Cross. "
            f"Scene reference:\n{scene_desc}\n\n"
            f"Invent a creative scene inspired by this setting — same mood, different angle or moment."
        )
        optimized, err = optimize_prompt_with_gemini(scene_text, ar)
        return optimized
    except Exception as e:
        logger.error(f"❌ build_batch_prompt_for_photo [{idx}]: {e}")
        return None

def optimize_prompt_with_gemini(user_text, ar):

    try:
        user_message = (
            f"MASTER IDENTITY (use this for the subject — do not modify):\n{MASTER_IDENTITY}\n\n"
            f"USER PROMPT TO ADAPT:\n{user_text}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. From the USER PROMPT extract every scene element: location, environment, background, "
            f"lighting, pose, camera angle, outfit/clothing, mood, photographic style, props, color grading, grain, technique. "
            f"Keep ALL of them — even unusual ones like 'POV from inside a glass' or 'film grain' or 'vintage 35mm'.\n"
            f"2. Replace ONLY the subject's physical description with the MASTER IDENTITY above.\n"
            f"3. Write a single complete prompt in plain English, continuous flowing text separated by commas, "
            f"that combines ALL scene elements from the user prompt with ALL elements of the MASTER IDENTITY. "
            f"Both must be fully present. Do not omit anything from either source.\n"
            f"4. CRITICAL FORMAT RULES — violating these invalidates the output:\n"
            f"   - NO labels, NO headers, NO keys (forbidden: 'IDENTITY:', 'BODY:', 'FACE:', 'SCENE:', 'RENDERING:', 'FORMAT:', 'NEGATIVE:' or any similar)\n"
            f"   - NO bullet points, NO numbered lists, NO markdown, NO line breaks between sections\n"
            f"   - NO separate blocks or sections of any kind\n"
            f"   - ONE single paragraph of flowing comma-separated descriptive text from start to finish\n"
            f"   - Negative prompts must appear at the end as two inline clauses: "
            f"'negative body: [body/face negatives], negative hair: [hair negatives]'\n"
            f"   - End with: 'No JSON, no text output, no metadata. Ratio {ar}.'\n"
            f"5. MIRROR SELFIE RULE: If the user prompt contains any of these keywords — selfie, mirror, mirror selfie, bathroom, restroom, reflection — then a smartphone held in hand IS a required prop in the scene. Ensure the phone is explicitly present as a positive element in the output prompt. Never add phone, smartphone or cellphone to the negative prompts in this case.\n"
            f"6. Output ONLY the final prompt. Zero explanations, zero preamble, zero postamble."
        )

        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[user_message],
            config=genai_types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=4000,
            )
        )
        if response.text:
            optimized = response.text.strip()
            # Controllo troncamento: il prompt completo deve contenere almeno watermark e negative
            required_keywords = ["watermark", "negative", "feat. valeria cross"]
            is_truncated = not any(kw in optimized.lower() for kw in required_keywords)
            if is_truncated:
                logger.warning(f"⚠️ Prompt sembra troncato ({len(optimized)} chars) — uso fallback.")
                return None, "⚠️ Ottimizzazione incompleta: prompt troncato."
            logger.info(f"✅ Prompt ottimizzato ({len(optimized)} chars)")
            return optimized, None
        logger.warning("⚠️ Risposta ottimizzazione vuota.")
        return None, "⚠️ Ottimizzazione prompt fallita: risposta vuota."
    except Exception as e:
        logger.error(f"❌ Errore ottimizzazione prompt: {e}", exc_info=True)
        return None, f"❌ Errore ottimizzazione:\n<code>{html.escape(str(e))}</code>"

# --- SANITIZZAZIONE PROMPT ---
def sanitize_prompt(text):
    blocklist = [
        "FILTER BYPASS", "BYPASS ACTIVATED", "NO OBSCURED FEATURES",
        "SAFETY OVERRIDE", "IGNORE SAFETY", "DISABLE FILTER"
    ]
    lines = text.splitlines()
    lines = [l for l in lines if not any(b in l.upper() for b in blocklist)]
    text = "\n".join(lines)
    # Rimuovi markdown che confonde Gemini
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold** → testo
    text = re.sub(r'\*(.+?)\*', r'\1', text)        # *italic* → testo
    text = re.sub(r'`(.+?)`', r'\1', text)          # `code` → testo
    return text.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")

# --- CAPTION DA IMMAGINE ---
def generate_caption_from_image(img_bytes):
    """Genera caption social dall'immagine originale — max 10 parole + 4/5 emoji.
    Analizza stile, ambientazione, soggetto. Non usa il prompt Valeria."""
    try:
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        instr = (
            "Look at this image carefully. Generate a social media caption for it.\n"
            "Rules:\n"
            "- Start with 4 or 5 emoji that match the style, setting, mood and subject of the image\n"
            "- Follow with a short phrase of maximum 10 words\n"
            "- The phrase must be eye-catching, evocative, and descriptive of what you see\n"
            "- Do NOT mention the person's gender, age, or physical appearance\n"
            "- Focus on: mood, style, location, colors, atmosphere, fashion\n"
            "- No hashtags, no punctuation at the end\n"
            "- Return ONLY the caption on a single line, nothing else\n"
            "Example: '🌊✨👙🌅 golden hour on the mediterranean coast'\n"
            "Example: '🖤🌹💃🎭 dark glamour at the theatre'"
        )
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[instr, img_part]
        )
        if response.text:
            return response.text.strip(), None
        return None, "⚠️ Nessuna caption generata."
    except Exception as e:
        logger.error(f"❌ Errore caption: {e}", exc_info=True)
        return None, f"❌ Errore: {html.escape(str(e))}"

caption_waiting = {}  # uid → True, in attesa di foto dopo /caption

# --- GENERAZIONE IMMAGINI ---
# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- /start e /settings ---
@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📋 /start da {username} (id={uid})")
    # Reset completo di tutti gli stati
    user_last_image.pop(uid, None)
    user_last_prompt.pop(uid, None)
    caption_waiting.pop(uid, None)
    pending_prompts.pop(uid, None)
    batch_prompts.pop(uid, None)
    if uid in batch_session:
        session = batch_session.pop(uid)
        if session.get('timer'):
            try: session['timer'].cancel()
            except Exception: pass
    bot.send_message(m.chat.id, "✅ <b>Reset completo.</b> Tutte le sessioni cancellate.")
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
        types.InlineKeyboardButton("3:2", callback_data="ar_3:2"),
        types.InlineKeyboardButton("4:3", callback_data="ar_4:3")
    )
    markup.row(
        types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"),
        types.InlineKeyboardButton("3:4", callback_data="ar_3:4"),
        types.InlineKeyboardButton("9:16 📱", callback_data="ar_9:16")
    )
    markup.row(
        types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
        types.InlineKeyboardButton("2 Foto", callback_data="qty_2")
    )
    bot.send_message(
        m.chat.id,
        f"<b>👠 VOGUE v{VERSION}</b>\n"
        f"Formato: <b>{user_ar[uid]}</b> | Quantità: <b>{user_qty[uid]}</b>\n\n"
        f"Scegli il formato e la quantità:",
        reply_markup=markup
    )

# --- /help ---
@bot.message_handler(commands=['help'])
def help_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"❓ /help da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>👠 VOGUE Bot — Guida rapida</b>\n\n"
        f"Scrivi una scena o incolla un prompt — il bot ottimizzerà tutto.\n"
        f"Puoi anche inviare una foto con didascalia come riferimento.\n\n"
        f"<b>Comandi:</b>\n"
        f"/start o /settings — formato e quantità\n"
        f"/lastprompt — mostra l'ultimo prompt inviato all'API\n"
        f"/help — questa guida\n"
        f"/info — versione e stato\n"
        f"/prompt — mostra il master identity"
    )

# --- /info ---
@bot.message_handler(commands=['info'])
def info_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"ℹ️ /info da {username} (id={uid})")
    now = datetime.now(LISBON_TZ).strftime("%d/%m/%Y %H:%M:%S")
    master_status = "✅ Caricata" if MASTER_PART else "⚠️ Non trovata"
    bot.send_message(m.chat.id,
        f"<b>ℹ️ Informazioni Bot</b>\n\n"
        f"Versione: <b>{VERSION}</b>\n"
        f"Modello: <code>{MODEL_ID}</code>\n"
        f"Ora server: <b>{now}</b>\n"
        f"Master face: {master_status}\n"
        f"Formato: <b>{user_ar[uid]}</b> | Quantità: <b>{user_qty[uid]}</b>"
    )

# --- /prompt ---
@bot.message_handler(commands=['prompt'])
def prompt_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📄 /prompt da {username} (id={uid})")
    safe = html.escape(MASTER_IDENTITY)
    bot.send_message(m.chat.id, f"<b>📄 Master Identity:</b>\n\n<code>{safe}</code>")

# --- /lastprompt ---
@bot.message_handler(commands=['lastprompt'])
def lastprompt_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🔍 /lastprompt da {username} (id={uid})")
    prompt_data = user_last_prompt.get(uid)
    if not prompt_data:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    prompt = prompt_data['full_p'] if isinstance(prompt_data, dict) else prompt_data
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt inviato all'API</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

# --- /caption ---
@bot.message_handler(commands=['caption'])
def caption_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📝 /caption da {username} (id={uid})")
    caption_waiting[uid] = True
    bot.send_message(m.chat.id,
        "📝 <b>Caption</b>\n\n"
        "Invia la foto per cui vuoi generare la caption.\n"
        "Analizzo stile, ambientazione e soggetto — max 10 parole + 4/5 emoji."
    )

# --- CALLBACK: AR e QTY ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("ar_") or call.data.startswith("qty_"))
def handle_settings_callback(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    if call.data.startswith("ar_"):
        user_ar[uid] = call.data.replace("ar_", "")
        logger.info(f"⚙️ {username} (id={uid}) → formato: {user_ar[uid]}")
        bot.answer_callback_query(call.id, f"✅ Formato: {user_ar[uid]}")
    elif call.data.startswith("qty_"):
        user_qty[uid] = int(call.data.replace("qty_", ""))
        logger.info(f"⚙️ {username} (id={uid}) → quantità: {user_qty[uid]}")
        bot.answer_callback_query(call.id, f"✅ Quantità: {user_qty[uid]} foto")

    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
            types.InlineKeyboardButton("3:2", callback_data="ar_3:2"),
            types.InlineKeyboardButton("4:3", callback_data="ar_4:3")
        )
        markup.row(
            types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"),
            types.InlineKeyboardButton("3:4", callback_data="ar_3:4"),
            types.InlineKeyboardButton("9:16 📱", callback_data="ar_9:16")
        )
        markup.row(
            types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
            types.InlineKeyboardButton("2 Foto", callback_data="qty_2")
        )
        bot.edit_message_text(
            f"<b>👠 VOGUE v{VERSION}</b>\n"
            f"Formato: <b>{user_ar[uid]}</b> | Quantità: <b>{user_qty[uid]}</b>\n\n"
            f"Scegli il formato e la quantità:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"⚠️ Impossibile aggiornare settings: {e}")

# --- CALLBACK: RIPROVA ---
@bot.callback_query_handler(func=lambda call: call.data == "retry_prompt")
def handle_retry(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    data = user_last_prompt.get(uid)
    if not data or not isinstance(data, dict):
        bot.answer_callback_query(call.id, "⚠️ Nessun prompt disponibile. Invia una nuova scena.")
        return

    qty = user_qty[uid]
    logger.info(f"🔁 {username} (id={uid}) → riprova stesso prompt | qty={qty}")
    bot.answer_callback_query(call.id, "🔁 Riprovo...")

    bot.send_message(
        call.message.chat.id,
        f"🔁 <b>Riprova avviata!</b>\n"
        f"📸 Sto creando <b>{qty}</b> foto con lo stesso prompt...\n"
        f"⏳ Tempo stimato: ~{qty * 20}–{qty * 35} secondi. Attendi."
    )

    def run_retry(idx):
        t_start = time.time()
        logger.info(f"   🔁 Riprova scatto {idx+1}/{qty} per {username}...")
        res, err = None, "Generazione disabilitata — usa Flow."

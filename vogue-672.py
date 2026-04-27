import os, io, threading, logging, flask, telebot, html, time
from datetime import datetime
import pytz
from telebot import types
from google import genai
from google.genai import types as genai_types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- HEADER VERSIONE ---
VERSION = "6.7.2"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
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
def execute_generation(full_prompt, img_rif_bytes=None):
    try:
        full_prompt = sanitize_prompt(full_prompt)
        contents = [full_prompt]
        if MASTER_PART:
            contents.append(MASTER_PART)
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")
        if img_rif_bytes:
            try:
                contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"❌ Errore preparazione immagine riferimento: {e}")
                return None, "❌ Errore nel processare l'immagine allegata."

        import concurrent.futures as _cf
        def _call():
            logger.info(f"   📤 Prompt a Gemini ({len(full_prompt)} chars): {full_prompt[:300]!r}")
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
                        logger.warning("⚠️ Timeout generazione (120s) — retry automatico tra 15s")
                        import time; time.sleep(15)
                    else:
                        logger.error("❌ Timeout generazione (120s) — anche il retry è fallito")
                        return None, "⏱️ Timeout: Gemini non ha risposto dopo 2 tentativi. Riprova tra qualche minuto."
        else:
            return None, "⏱️ Timeout: Gemini non ha risposto dopo 2 tentativi. Riprova tra qualche minuto."

        if not response.candidates:
            logger.warning("⚠️ API: nessun candidato.")
            return None, "❌ L'API non ha restituito risultati. Riprova."

        candidate = response.candidates[0]
        finish_reason = candidate.finish_reason
        finish_str = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)
        if finish_str != "STOP":
            logger.warning(f"⚠️ Generazione bloccata: {finish_str}")
            return None, f"🛡️ Generazione bloccata.\nMotivo: <code>{finish_str}</code>"

        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None

        logger.warning("⚠️ Nessuna immagine nella risposta.")
        return None, "❌ Nessuna immagine nella risposta. Riprova con una scena diversa."

    except Exception as e:
        logger.error(f"❌ Eccezione in execute_generation: {e}", exc_info=True)
        return None, f"❌ Errore interno:\n<code>{html.escape(str(e))}</code>"

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
        res, err = execute_generation(data['full_p'], data.get('img'))
        elapsed = round(time.time() - t_start, 1)

        retry_markup = types.InlineKeyboardMarkup()
        retry_markup.add(types.InlineKeyboardButton("🔁 Riprova stesso prompt", callback_data="retry_prompt"))

        if res:
            user_last_image[uid] = res  # salva ultima immagine generata per reply
            try:
                bot.send_document(
                    call.message.chat.id,
                    io.BytesIO(res),
                    visible_file_name=f"vogue_retry_{idx+1}.jpg",
                    caption=f"✅ Scatto {idx+1}/{qty} — {elapsed}s",
                    reply_markup=retry_markup
                )
                logger.info(f"   ✅ Riprova scatto {idx+1}/{qty} inviato a {username} in {elapsed}s")
            except Exception as e:
                logger.error(f"   ❌ Errore invio riprova scatto {idx+1}: {e}")
        else:
            logger.warning(f"   ❌ Riprova scatto {idx+1}/{qty} fallita ({elapsed}s): {err}")
            try:
                bot.send_message(call.message.chat.id,
                    f"❌ <b>Scatto {idx+1} fallito</b> ({elapsed}s)\n{err}",
                    reply_markup=retry_markup)
            except Exception as send_e:
                logger.error(f"   ❌ Errore invio messaggio fallimento riprova {idx+1}: {send_e}")
                bot.send_message(call.message.chat.id,
                    f"❌ Scatto {idx+1} fallito ({elapsed}s) — errore nel mostrare i dettagli.",
                    reply_markup=retry_markup)

    for i in range(qty):
        executor.submit(run_retry, i)

# --- CALLBACK: SOLO CAPTION ---
@bot.callback_query_handler(func=lambda call: call.data == "caption_only")
def handle_caption_only(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception: pass

    data = pending_prompts.get(uid)
    if not data or not (data.get('caption_img') or data.get('img')):
        bot.send_message(call.message.chat.id,
            "⚠️ Immagine originale non disponibile. Usa /caption e invia la foto.")
        return

    bot.send_message(call.message.chat.id, "📝 <b>Genero caption...</b>\n⏳ Attendi qualche secondo.")
    logger.info(f"📝 caption_only per {username} (id={uid})")
    caption_src = data.get('caption_img') or data.get('img')

    def run_caption():
        cap, err = generate_caption_from_image(caption_src)
        if cap:
            bot.send_message(call.message.chat.id,
                f"📝 <b>Caption:</b>\n\n<code>{html.escape(cap)}</code>")
            logger.info(f"✅ Caption inviata a {username}")
        else:
            bot.send_message(call.message.chat.id, f"❌ Caption fallita: {err}")

    executor.submit(run_caption)
    pending_prompts.pop(uid, None)

# --- CALLBACK: CONFERMA / ANNULLA ---
@bot.callback_query_handler(func=lambda call: call.data in ["confirm_gen", "cancel_gen"])
def handle_confirmation(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logger.warning(f"⚠️ Impossibile rimuovere markup: {e}")

    if call.data == "cancel_gen":
        pending_prompts.pop(uid, None)
        logger.info(f"❌ {username} (id={uid}) ha annullato.")
        bot.send_message(call.message.chat.id, "❌ <b>Generazione annullata.</b>")
        return

    data = pending_prompts.get(uid)
    if not data:
        logger.warning(f"⚠️ Nessun pending_prompt per {username} (id={uid})")
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la scena.")
        return

    qty = data['qty']
    user_last_prompt[uid] = data  # salva dict completo con full_p e img
    logger.info(f"🚀 {username} (id={uid}) → generazione | qty={qty} | ar={user_ar[uid]}")

    bot.send_message(
        call.message.chat.id,
        f"🚀 <b>Generazione avviata!</b>\n"
        f"📸 Sto creando <b>{qty}</b> foto...\n"
        f"⏳ Tempo stimato: ~{qty * 20}–{qty * 35} secondi. Attendi."
    )

    # Genera caption dall'immagine originale in parallelo alla generazione
    img_for_caption = data.get('caption_img') or data.get('img')

    def run_task(idx):
        t_start = time.time()
        logger.info(f"   🎨 Scatto {idx+1}/{qty} per {username}...")
        res, err = execute_generation(data['full_p'], data['img'])
        elapsed = round(time.time() - t_start, 1)

        retry_markup = types.InlineKeyboardMarkup()
        retry_markup.add(types.InlineKeyboardButton("🔁 Riprova stesso prompt", callback_data="retry_prompt"))

        if res:
            user_last_image[uid] = res  # salva ultima immagine generata per reply
            try:
                bot.send_document(
                    call.message.chat.id,
                    io.BytesIO(res),
                    visible_file_name=f"vogue_{idx+1}.jpg",
                    caption=f"✅ Scatto {idx+1}/{qty} — {elapsed}s",
                    reply_markup=retry_markup
                )
                logger.info(f"   ✅ Scatto {idx+1}/{qty} inviato a {username} in {elapsed}s")
                # Caption dall'immagine originale dopo l'ultimo scatto
                if idx == qty - 1 and img_for_caption:
                    cap, cap_err = generate_caption_from_image(img_for_caption)
                    if cap:
                        bot.send_message(call.message.chat.id,
                            f"📝 <b>Caption:</b>\n\n<code>{html.escape(cap)}</code>")
                    else:
                        logger.warning(f"⚠️ Caption fallita dopo generazione: {cap_err}")
            except Exception as e:
                logger.error(f"   ❌ Errore invio scatto {idx+1}: {e}")
                bot.send_message(call.message.chat.id,
                    f"❌ Scatto {idx+1}: generato ma errore nell'invio.\n<code>{html.escape(str(e))}</code>")
        else:
            logger.warning(f"   ❌ Scatto {idx+1}/{qty} fallito ({elapsed}s): {err}")
            try:
                bot.send_message(call.message.chat.id,
                    f"❌ <b>Scatto {idx+1} fallito</b> ({elapsed}s)\n{err}",
                    reply_markup=retry_markup)
            except Exception as send_e:
                logger.error(f"   ❌ Errore invio messaggio fallimento scatto {idx+1}: {send_e}")
                bot.send_message(call.message.chat.id,
                    f"❌ Scatto {idx+1} fallito ({elapsed}s) — errore nel mostrare i dettagli.",
                    reply_markup=retry_markup)

    for i in range(qty):
        executor.submit(run_task, i)

    pending_prompts.pop(uid, None)

# --- HANDLER MESSAGGI PRINCIPALI ---
@bot.message_handler(content_types=['text', 'photo'])
def ask_confirmation(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name

    user_text = m.caption if m.content_type == 'photo' else m.text

    img_data = None
    if m.content_type == 'photo':
        try:
            file_info = bot.get_file(m.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)
            logger.info(f"🖼️ Foto ricevuta da {username} (id={uid}), {len(img_data)} bytes")
        except Exception as e:
            logger.error(f"❌ Errore download foto da {username}: {e}")
            bot.reply_to(m, "❌ Errore nel scaricare la foto allegata. Riprova.")
            return

        # ── MODALITÀ /caption ─────────────────────────────────────────────────
        if caption_waiting.pop(uid, False):
            bot.send_message(m.chat.id, "📝 <b>Genero caption...</b>\n⏳ Attendi qualche secondo.")
            def run_caption_standalone():
                cap, err = generate_caption_from_image(img_data)
                if cap:
                    bot.send_message(m.chat.id,
                        f"📝 <b>Caption:</b>\n\n<code>{html.escape(cap)}</code>")
                    logger.info(f"✅ Caption standalone inviata a {username}")
                else:
                    bot.send_message(m.chat.id, f"❌ Caption fallita: {err}")
            executor.submit(run_caption_standalone)
            return

        # Se la caption è assente o molto corta → BATCH (se sessione aperta) o FACESWAP EDITORIALE (prima foto)
        if not user_text or len(user_text.strip()) < 30:
            # Se sessione batch già aperta → accumula
            in_batch = uid in batch_session and len(batch_session[uid].get('photos', [])) > 0
            if not in_batch:
                # Prima foto senza testo: offri scelta tra faceswap e batch
                markup_choice = types.InlineKeyboardMarkup()
                markup_choice.row(
                    types.InlineKeyboardButton("🔄 Faceswap editoriale", callback_data="choice_faceswap"),
                    types.InlineKeyboardButton("📦 Batch (aggiungi foto)", callback_data="choice_batch")
                )
                # Salva temporaneamente la foto
                batch_session[uid] = {'photos': [img_data], 'timer': None, '_pending_choice': True}
                bot.reply_to(m,
                    "📷 <b>Foto ricevuta.</b>\n\n"
                    "• <b>Faceswap editoriale</b> — analizza la scena e genera subito\n"
                    "• <b>Batch</b> — aggiungi altre foto (max 4) e genera N prompt diversi",
                    reply_markup=markup_choice)
                return

            # Sessione batch aperta → accumula
            if uid in batch_session and batch_session[uid].get('timer'):
                batch_session[uid]['timer'].cancel()
            batch_session[uid]['photos'].append(img_data)
            n = len(batch_session[uid]['photos'])

            def _finalize_batch(uid=uid, cid=m.chat.id, username=username):
                photos = batch_session.pop(uid, {}).get('photos', [])
                if not photos:
                    return
                n = len(photos)
                ar = user_ar.get(uid, "2:3")
                bot.send_message(cid, f"⚙️ <b>Elaboro {n} foto...</b>\n⏳ Attendi ~{n * 15}-{n * 25}s")

                results = [None] * n
                def process(idx, img):
                    results[idx] = build_batch_prompt_for_photo(img, ar, idx)

                futures = [executor.submit(process, i, photos[i]) for i in range(n)]
                for f in futures:
                    f.result()

                ok = [(i, r) for i, r in enumerate(results) if r]
                if not ok:
                    bot.send_message(cid, "❌ Nessun prompt generato. Riprova.")
                    return

                batch_prompts[uid] = [{"full_p": r, "idx": i} for i, r in ok]
                bot.send_message(cid, f"✅ <b>{len(ok)} prompt pronti</b> — scegli quale generare:")

                for pos, (i, full_p) in enumerate(ok):
                    preview = full_p[:3500] + "\n<i>... (troncato)</i>" if len(full_p) > 3500 else full_p
                    markup = types.InlineKeyboardMarkup()
                    markup.row(types.InlineKeyboardButton(
                        f"🚀 Genera prompt {pos+1}", callback_data=f"batch_gen_{uid}_{i}"))
                    bot.send_message(cid,
                        f"📋 <b>Prompt {pos+1}/{len(ok)}:</b>\n\n<code>{html.escape(preview)}</code>",
                        reply_markup=markup)

            if n < 4:
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton(f"✅ Elabora ({n} foto)", callback_data="batch_process"),
                    types.InlineKeyboardButton("➕ Aggiungi foto", callback_data="batch_add")
                )
                bot.reply_to(m, f"📷 <b>Foto {n} ricevuta.</b>\nPuoi aggiungerne ancora {4-n} o procedere.",
                    reply_markup=markup)
            else:
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton("✅ Elabora (4 foto — max)", callback_data="batch_process"))
                bot.reply_to(m, "📷 <b>Foto 4 ricevuta.</b> Massimo raggiunto.", reply_markup=markup)

            # Timer 60s per auto-elaborazione se l'utente non fa nulla
            t = threading.Timer(60, _finalize_batch)
            batch_session[uid]['timer'] = t
            batch_session[uid]['_finalize'] = _finalize_batch
            t.start()
            return

        # Se la caption è assente o molto corta → FACESWAP EDITORIALE (foto singola con testo corto non batch)
        if not user_text or len(user_text.strip()) < 30:
            logger.info(f"🔄 Faceswap editoriale per {username} (id={uid})")
            wait_msg = bot.reply_to(m, "🎬 <b>Analisi scena in corso...</b>")
            scene_desc = describe_scene_for_faceswap(img_data)
            try:
                bot.delete_message(m.chat.id, wait_msg.message_id)
            except Exception:
                pass
            if not scene_desc:
                bot.reply_to(m, "❌ Non riesco ad analizzare la scena. Riprova.")
                return
            qty = user_qty.get(uid, 1)
            ar = user_ar.get(uid, "2:3")
            faceswap_prompt = (
                f"{MASTER_IDENTITY}\n\n"
                f"**TASK: EDITORIAL REINTERPRETATION**\n"
                f"Recreate this scene entirely from scratch with the Valeria Cross master identity as the subject. "
                f"Use the scene description below as reference — do NOT copy mechanically.\n\n"
                f"**SCENE REFERENCE:**\n{scene_desc}\n\n"
                f"**POSE & EXPRESSION — EDITORIAL REINTERPRETATION:**\n"
                f"Reinterpret the pose editorially — keep the general energy and body orientation "
                f"but introduce a natural variation: subtle shift of weight, slight head turn, "
                f"repositioned hand or adjusted angle. "
                f"Expression: calm, self-aware, characteristic Valeria Cross half-smile. Never blank, never forced.\n\n"
                f"**TECHNICAL:** 8K, cinematic, photorealistic, {ar} format. "
                f"Unified lighting matching the scene. Perfect skin continuity face→neck→body. "
                f"Watermark: 'feat. Valeria Cross 👠' — champagne cursive, bottom center, very small, 90% opacity.\n\n"
                f"**NEGATIVE PROMPT:** copy of original image, faceswap artifacts, mismatched lighting, "
                f"disconnected neck, body hair, chest hair, wrong identity, female face, young face, "
                f"missing beard, missing glasses, dark hair, stiff mechanical pose."
            )
            pending_prompts[uid] = {
                'full_p': faceswap_prompt,
                'qty': qty,
                'img': None,          # faceswap genera da testo — NO img reference
                'caption_img': img_data,  # solo per caption
            }
            # Salva subito in last_prompt — disponibile anche se generazione fallisce
            user_last_prompt[uid] = {'full_p': faceswap_prompt, 'img': None, 'caption_img': img_data}
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
            markup.row(types.InlineKeyboardButton("📝 Solo Caption", callback_data="caption_only"))
            markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))
            confirm_text = (
                f"🔄 <b>Faceswap editoriale</b>\n"
                f"📐 Formato: <b>{ar}</b> | 📸 Foto: <b>{qty}</b>\n\n"
                f"Scena analizzata e ricostruita — generazione da zero, posa reinterpretata.\n"
                f"💡 Usa /lastprompt dopo la generazione per vedere il prompt completo.\n\n"
                f"Procedere?"
            )
            bot.send_message(m.chat.id, confirm_text, reply_markup=markup)
            return

    if not user_text or not user_text.strip():
        bot.reply_to(m, "⚠️ Scrivi una scena come testo o come didascalia alla foto.")
        return

    logger.info(f"✏️ Input da {username} (id={uid}): «{user_text[:80]}{'...' if len(user_text) > 80 else ''}»")

    # ── ARCHITECT BYPASS ─────────────────────────────────────────────────────
    ARCH_TAG = "[MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]"
    if ARCH_TAG in user_text:
        certified_prompt = user_text.replace(ARCH_TAG, "").strip()
        logger.info(f"🏛️ Architect Certified — skip ottimizzazione, generazione diretta")

        pending_prompts[uid] = {
            'full_p': certified_prompt,
            'qty':    user_qty[uid],
            'img':    img_data,
        }

        preview_prompt = certified_prompt
        if len(preview_prompt) > 3500:
            preview_prompt = preview_prompt[:3500] + "\n<i>... (troncato)</i>"

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
        markup.row(types.InlineKeyboardButton("📝 Solo Caption", callback_data="caption_only"))
        markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

        bot.reply_to(
            m,
            f"🏛️ <b>Architect Certified</b> — prompt pre-ottimizzato ({user_ar[uid]} | {user_qty[uid]} foto):\n\n"
            f"<code>{html.escape(preview_prompt)}</code>\n\n"
            f"Procedere con la generazione?",
            reply_markup=markup
        )
        return

    # ── CLOSET BYPASS ─────────────────────────────────────────────────────────
    CLOSET_TAG = "MASTER PROMPT — GEMINI OPTIMIZED — SYNTHETIC FACE IDENTITY LOCK"
    if user_text.startswith(CLOSET_TAG):
        logger.info(f"👗 Closet Certified — skip ottimizzazione, generazione diretta")

        pending_prompts[uid] = {
            'full_p': user_text,
            'qty':    user_qty[uid],
            'img':    img_data,
        }

        preview_prompt = user_text
        if len(preview_prompt) > 3500:
            preview_prompt = preview_prompt[:3500] + "\n<i>... (troncato)</i>"

        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
        markup.row(types.InlineKeyboardButton("📝 Solo Caption", callback_data="caption_only"))
        markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

        bot.reply_to(
            m,
            f"👗 <b>Closet Certified</b> — prompt pre-ottimizzato ({user_ar[uid]} | {user_qty[uid]} foto):\n\n"
            f"<code>{html.escape(preview_prompt)}</code>\n\n"
            f"Procedere con la generazione?",
            reply_markup=markup
        )
        return

    # ── REPLY CON MODIFICA ────────────────────────────────────────────────────
    if (m.reply_to_message and
        m.reply_to_message.from_user.id == get_bot_id() and
        m.content_type == 'text'):

        last_img = user_last_image.get(uid)
        if last_img:
            modify_text = user_text.strip()
            logger.info(f"✏️ {username} (id={uid}) → modifica in reply: {modify_text[:80]}")

            refine_prompt = (
                f"{MASTER_IDENTITY}\n\n"
                f"Using the provided image as the exact visual reference for identity, outfit, pose and style, "
                f"generate a new image applying ONLY this change: {modify_text}. "
                f"Keep everything else identical to the reference image."
            )

            # Salva subito il refine_prompt come last_prompt — così "Riprova" riprova il filtro, non l'immagine precedente
            user_last_prompt[uid] = {'full_p': refine_prompt, 'img': last_img}

            wait_msg = bot.reply_to(m, "✏️ <b>Applico la modifica...</b>")

            def run_refine():
                try:
                    t_start = time.time()
                    res, err = execute_generation(refine_prompt, last_img)
                    elapsed = round(time.time() - t_start, 1)
                    try:
                        bot.delete_message(m.chat.id, wait_msg.message_id)
                    except Exception:
                        pass
                    retry_markup = types.InlineKeyboardMarkup()
                    retry_markup.add(types.InlineKeyboardButton("🔁 Riprova stesso prompt", callback_data="retry_prompt"))
                    if res:
                        user_last_image[uid] = res
                        bot.send_document(
                            m.chat.id,
                            io.BytesIO(res),
                            visible_file_name="vogue_refined.jpg",
                            caption=f"✅ Modifica applicata — {elapsed}s",
                            reply_markup=retry_markup
                        )
                        logger.info(f"   ✅ Refine inviato a {username} in {elapsed}s")
                    else:
                        bot.send_message(m.chat.id,
                            f"❌ <b>Modifica fallita</b> ({elapsed}s)\n{err}",
                            reply_markup=retry_markup)
                except Exception as e:
                    logger.error(f"❌ Eccezione in run_refine: {e}", exc_info=True)
                    bot.send_message(m.chat.id, f"❌ <b>Errore interno nella modifica.</b>\n<code>{html.escape(str(e))}</code>")

            executor.submit(run_refine)
            return
    # ─────────────────────────────────────────────────────────────────────────

    wait_msg = bot.reply_to(m, "🌐 <b>Traduzione in corso...</b>")

    # Step 1: traduzione
    ar_snapshot = user_ar[uid]
    future_tr = executor.submit(translate_to_english, user_text)
    try:
        translated_text = future_tr.result(timeout=20)
    except Exception as e:
        logger.warning(f"⚠️ Traduzione fallita per {username}: {e} — uso testo originale")
        translated_text = user_text

    try:
        bot.edit_message_text("🧠 <b>Ottimizzazione prompt in corso...</b>",
            m.chat.id, wait_msg.message_id, parse_mode="HTML")
    except Exception:
        pass

    # Step 2: ottimizzazione sul testo già in inglese
    future_opt = executor.submit(optimize_prompt_with_gemini, translated_text, ar_snapshot)
    try:
        optimized_prompt, opt_err = future_opt.result(timeout=40)
    except Exception as e:
        optimized_prompt = None
        opt_err = str(e)

    try:
        bot.delete_message(m.chat.id, wait_msg.message_id)
    except Exception:
        pass

    if not optimized_prompt:
        logger.warning(f"⚠️ Ottimizzazione fallita per {username}, uso prompt diretto. Errore: {opt_err}")
        optimized_prompt = f"{MASTER_IDENTITY}\n\nSCENE: {translated_text}\nFORMAT: {ar_snapshot}"
        bot.send_message(m.chat.id, "⚠️ <b>Ottimizzazione non disponibile, uso prompt standard.</b>")

    sanitized = sanitize_prompt(optimized_prompt)

    pending_prompts[uid] = {
        'full_p': sanitized,
        'qty':    user_qty[uid],
        'img':    img_data,
    }

    preview_prompt = sanitized
    if len(preview_prompt) > 3500:
        preview_prompt = preview_prompt[:3500] + "\n<i>... (troncato)</i>"

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
    markup.row(types.InlineKeyboardButton("📝 Solo Caption", callback_data="caption_only"))
    markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

    bot.reply_to(
        m,
        f"📝 <b>Prompt ottimizzato</b> ({ar_snapshot} | {user_qty[uid]} foto):\n\n"
        f"<code>{html.escape(preview_prompt)}</code>\n\n"
        f"Procedere con la generazione?",
        reply_markup=markup
    )

# --- CHOICE CALLBACK (faceswap vs batch) ---
@bot.callback_query_handler(func=lambda c: c.data in ["choice_faceswap", "choice_batch"])
def handle_choice(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    session = batch_session.get(uid, {})
    photos = session.get('photos', [])
    if not photos:
        bot.send_message(cid, "⚠️ Sessione scaduta. Invia di nuovo la foto.")
        return
    img_data = photos[0]

    if call.data == "choice_faceswap":
        # Pulisce la sessione batch e avvia faceswap
        batch_session.pop(uid, None)
        wait_msg = bot.send_message(cid, "🎬 <b>Analisi scena in corso...</b>")
        def do_faceswap():
            scene_desc = describe_scene_for_faceswap(img_data)
            try: bot.delete_message(cid, wait_msg.message_id)
            except Exception: pass
            if not scene_desc:
                bot.send_message(cid, "❌ Non riesco ad analizzare la scena. Riprova.")
                return
            qty = user_qty.get(uid, 1)
            ar = user_ar.get(uid, "2:3")
            faceswap_prompt = (
                f"{MASTER_IDENTITY}\n\n"
                f"**TASK: EDITORIAL REINTERPRETATION**\n"
                f"Recreate this scene entirely from scratch with the Valeria Cross master identity as the subject. "
                f"Use the scene description below as reference — do NOT copy mechanically.\n\n"
                f"**SCENE REFERENCE:**\n{scene_desc}\n\n"
                f"**POSE & EXPRESSION — EDITORIAL REINTERPRETATION:**\n"
                f"Reinterpret the pose editorially — keep the general energy and body orientation "
                f"but introduce a natural variation: subtle shift of weight, slight head turn, "
                f"repositioned hand or adjusted angle. "
                f"Expression: calm, self-aware, characteristic Valeria Cross half-smile. Never blank, never forced.\n\n"
                f"**TECHNICAL:** 8K, cinematic, photorealistic, {ar} format. "
                f"Unified lighting matching the scene. Perfect skin continuity face→neck→body. "
                f"Watermark: \'feat. Valeria Cross 👠\' — champagne cursive, bottom center, very small, 90% opacity.\n\n"
                f"**NEGATIVE PROMPT:** copy of original image, faceswap artifacts, mismatched lighting, "
                f"disconnected neck, body hair, chest hair, wrong identity, female face, young face, "
                f"missing beard, missing glasses, dark hair, stiff mechanical pose."
            )
            pending_prompts[uid] = {'full_p': faceswap_prompt, 'qty': qty, 'img': None, 'caption_img': img_data}
            user_last_prompt[uid] = {'full_p': faceswap_prompt, 'img': None, 'caption_img': img_data}

            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
            markup.row(types.InlineKeyboardButton("📝 Solo Caption", callback_data="caption_only"))
            markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))
            confirm_text = (
                f"🔄 <b>Faceswap editoriale</b>\n"
                f"📐 Formato: <b>{ar}</b> | 📸 Foto: <b>{qty}</b>\n\n"
                f"Scena analizzata e ricostruita — generazione da zero, posa reinterpretata.\n"
                f"💡 Usa /lastprompt dopo la generazione per vedere il prompt completo.\n\n"
                f"Procedere?"
            )
            bot.send_message(cid, confirm_text, reply_markup=markup)
        executor.submit(do_faceswap)

    elif call.data == "choice_batch":
        # Continua in modalità batch — già ha 1 foto
        n = len(photos)
        batch_session[uid]['_pending_choice'] = False
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton(f"✅ Elabora ({n} foto)", callback_data="batch_process"),
            types.InlineKeyboardButton("➕ Aggiungi foto", callback_data="batch_add")
        )
        bot.send_message(cid,
            f"📦 <b>Modalità batch attiva.</b>\n"
            f"Foto {n}/4 ricevuta. Puoi aggiungerne ancora {4-n} o elaborare subito.",
            reply_markup=markup)

# --- BATCH CALLBACKS ---
@bot.callback_query_handler(func=lambda c: c.data in ["batch_process", "batch_add"])
def handle_batch_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    if call.data == "batch_add":
        bot.send_message(cid, "📷 Invia la prossima foto.")
        return

    session = batch_session.get(uid)
    if not session or not session.get('photos'):
        bot.send_message(cid, "⚠️ Nessuna foto in sessione. Riprova.")
        return
    if session.get('timer'):
        session['timer'].cancel()
    finalize = session.get('_finalize')
    if finalize:
        executor.submit(finalize)

@bot.callback_query_handler(func=lambda c: c.data.startswith("batch_gen_"))
def handle_batch_gen(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    parts = call.data.split("_")
    try:
        idx = int(parts[-1])
    except ValueError:
        bot.send_message(cid, "⚠️ Errore nel recupero del prompt.")
        return

    prompts = batch_prompts.get(uid, [])
    entry = next((p for p in prompts if p['idx'] == idx), None)
    if not entry:
        bot.send_message(cid, "⚠️ Prompt non trovato. Riprova.")
        return

    full_p = entry['full_p']
    qty = user_qty.get(uid, 1)
    user_last_prompt[uid] = {'full_p': full_p, 'img': None}
    logger.info(f"🚀 {username} (id={uid}) → batch_gen idx={idx} | qty={qty}")

    bot.send_message(cid,
        f"🚀 <b>Generazione avviata!</b>\n"
        f"📸 Sto creando <b>{qty}</b> foto...\n"
        f"⏳ Tempo stimato: ~{qty * 20}–{qty * 35} secondi. Attendi.")

    def run_batch_task(task_idx):
        t_start = time.time()
        res, err = execute_generation(full_p, None)
        elapsed = round(time.time() - t_start, 1)
        retry_markup = types.InlineKeyboardMarkup()
        retry_markup.add(types.InlineKeyboardButton("🔁 Riprova stesso prompt", callback_data="retry_prompt"))
        if res:
            user_last_image[uid] = res
            try:
                bot.send_document(cid, io.BytesIO(res),
                    visible_file_name=f"vogue_batch_{task_idx+1}.jpg",
                    caption=f"✅ Scatto {task_idx+1}/{qty} — {elapsed}s",
                    reply_markup=retry_markup)
                logger.info(f"   ✅ Batch scatto {task_idx+1} inviato a {username} in {elapsed}s")
            except Exception as e:
                logger.error(f"   ❌ Errore invio batch scatto {task_idx+1}: {e}")
        else:
            bot.send_message(cid, f"❌ <b>Scatto {task_idx+1} fallito</b> ({elapsed}s)\n{err}",
                reply_markup=retry_markup)

    for i in range(qty):
        executor.submit(run_batch_task, i)

# --- SERVER FLASK ---
app = flask.Flask(__name__)

@app.route('/')
def h():
    return f"Vogue v{VERSION} Online"

if __name__ == "__main__":
    logger.info(f"🟢 Avvio VOGUE Bot v{VERSION}")
    threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))),
        daemon=True
    ).start()
    bot.infinity_polling()

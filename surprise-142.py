import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "1.4.2"

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
    "**MANDATORY BODY — THIS IS NOT A MALE BODY — ABSOLUTE OVERRIDE:**\n"
    "**FULL D-CUP BUST — large, prominent, natural, clearly visible through any outfit. THIS IS THE MOST IMPORTANT BODY RULE.**\n"
    "**Feminine hourglass silhouette: 180cm, 85kg. Defined waist, wide rounded hips, full thighs, soft belly. "
    "DO NOT GENERATE A FLAT CHEST. DO NOT GENERATE A MALE PHYSIQUE. THE BUST MUST BE VISIBLE AND PROMINENT.**\n"
    "Completely hairless body — NO body hair anywhere. Smooth porcelain skin. "
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

LOCATION RULES — choose from these categories, rotating variety each time:
- Iconic world cities: Paris, Milan, New York, Tokyo, London, Dubai, Barcelona, Rome, Athens, Istanbul, Sydney, Rio, Cape Town, Singapore, Monaco, Venice, Marrakech, Kyoto, Buenos Aires, Mumbai
- Luxury settings: 5-star hotel rooftop, private beach resort, infinity pool villa, yacht deck, grand ballroom, luxury penthouse terrace
- Natural iconic landscapes: Amalfi Coast, Santorini, Maldives, Bali rice terraces, Swiss Alps, Sahara desert dunes, Patagonia, Bora Bora, Positano cliffs, Capri island
- Fashion/culture venues: haute couture atelier, art museum hall, opera house foyer, fashion week backstage, Cannes red carpet, Met Gala steps
DO NOT choose: abandoned places, unknown locations, brutalist buildings, obscure landmarks, metro stations, industrial spaces.

Return ONLY valid JSON with these exact keys, no other text:
{
  "location": "specific recognizable place from the categories above (max 8 words)",
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
                temperature=1.2,
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

# --- STILI ARTISTICI (da Sorpresa) ---
ARTISTIC_STYLES = [
    None,  # nessuno stile — photorealistic (stessa probabilità degli altri)
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism",
    "🌀 Dalì — melting surrealist dreamscape, hyper-detailed hallucination, elongated figures, Spanish surrealism",
    "🏛️ De Chirico — metaphysical painting, long dramatic shadows, empty piazzas, classical architecture, eerie stillness",
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles",
    "🖌️ Banksy — urban stencil street art, black and white spray paint, sharp political irony, graffiti aesthetic",
]

STILE_ARTISTICO_OVERRIDES = {
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism": {
        "colore_ok": [
            "soft pastel palette", "cool grey and silver", "warm ivory and cream",
            "stark white and ice", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "white seamless studio", "desert at golden hour, sand dunes, warm haze, minimalist horizon",
            "misty forest at dawn", "snowy mountain peak", "alpine meadow",
            "swing hanging from a giant flower, floating above clouds, dark sky",
        ],
    },
    "🌀 Dalì — melting surrealist dreamscape, hyper-detailed hallucination, elongated figures, Spanish surrealism": {
        "colore_ok": [
            "earthy terracotta and ochre", "warm amber and cognac", "warm ivory and cream",
            "soft pastel palette", "bold red and gold", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "desert at golden hour, sand dunes, warm haze, minimalist horizon",
            "white seamless studio", "snowy mountain peak",
            "swing hanging from a giant flower, floating above clouds, dark sky",
            "misty forest at dawn",
        ],
    },
    "🏛️ De Chirico — metaphysical painting, long dramatic shadows, empty piazzas, classical architecture, eerie stillness": {
        "colore_ok": [
            "earthy terracotta and ochre", "warm amber and cognac", "warm ivory and cream",
            "cool grey and silver", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "ancient roman ruins", "white seamless studio",
            "desert at golden hour, sand dunes, warm haze, minimalist horizon",
            "art deco theatre stage",
            "narrow italian vicolo, laundry hanging, warm stone walls",
        ],
    },
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "bold red and gold",
            "vibrant electric blue tones",
        ],
        "sfondo_ok": [
            "white seamless studio", "art deco theatre stage", "industrial loft",
        ],
    },
    "🖌️ Banksy — urban stencil street art, black and white spray paint, sharp political irony, graffiti aesthetic": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "cool grey and silver",
            "bold red and gold",
        ],
        "sfondo_ok": [
            "urban rooftop at night", "tokyo neon street", "industrial loft",
            "narrow italian vicolo, laundry hanging, warm stone walls",
            "sidewalk café terrace, street life, people passing by",
        ],
    },
}

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

    # Legge stile artistico già estratto in pick_scene
    artistic_style = scenario.get('artistic_style')

    # Override sfondo se stile artistico attivo
    location = scenario['location']
    if artistic_style and artistic_style in STILE_ARTISTICO_OVERRIDES:
        ov = STILE_ARTISTICO_OVERRIDES[artistic_style]
        if ov.get("sfondo_ok"):
            location = random.choice(ov["sfondo_ok"])

    style_block = f"VISUAL STYLE: {scenario['style']}\n\n"
    if artistic_style:
        style_block += f"ARTISTIC STYLE: {artistic_style}\n\n"

    prompt = (
        f"{VALERIA_IDENTITY}\n\n"
        f"⚠️ BODY OVERRIDE — HIGHEST PRIORITY: Subject has FULL PROMINENT D-CUP BUST, clearly visible. "
        f"Feminine hourglass body. DO NOT generate flat chest or male physique under any circumstance.\n\n"
        f"SCENE: {location}. {scenario['sky']}.\n\n"
        f"OUTFIT: {scenario['outfit']}\n\n"
        f"POSE: {scenario['pose']}. Body must follow realistic human anatomy and physics — weight supported, no impossible floating positions.\n\n"
        f"MOOD: {scenario['mood']}\n\n"
        + style_block +
        f"FORMAT: {fmt}\n\n"
        f"Ultra-detailed 8K cinematic photography. No text, no watermark except the mandatory one."
    )
    return prompt, fmt, artistic_style

# --- GENERA IMMAGINE (single step, come Vogue/Cabina) ---
def execute_generation(full_prompt, formato="2:3"):
    try:
        # masterface PRIMA del prompt — identico a Vogue e Cabina
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
    artistic = s.get('artistic_style')
    if artistic:
        # Mostra solo emoji + nome artista (prima del —)
        artist_short = artistic.split(' — ')[0]
        style_line = f"🎨 <b>Style:</b> {s['style']} + {artist_short}"
    else:
        style_line = f"🎨 <b>Style:</b> {s['style']}"
    return (
        f"📍 <b>Location:</b> {s['location']}\n"
        f"🌤 <b>Sky:</b> {s['sky']}\n"
        f"👗 <b>Outfit:</b> {s['outfit']}\n"
        + style_line + "\n"
        f"💃 <b>Pose:</b> {s['pose']}\n"
        f"✨ <b>Mood:</b> {s['mood']}\n"
        f"🏛 <b>Body:</b> Feminine hourglass, 180cm 85kg, D-cup bust, smooth skin"
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
        f"Nessuna lista predefinita. Tutto davvero random.\n\n"
        f"A volte lo stile di un grande artista — Magritte, Dalì, De Chirico, Mondrian o Banksy.",
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
            # Estrae stile artistico qui — visibile nella preview
            artistic = random.choice(ARTISTIC_STYLES)
            scenario['artistic_style'] = artistic
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
        # Caption generata subito dal testo — disponibile anche se la generazione fallisce
        full_p_pre, fmt_pre, style_pre = build_prompt(scenario)
        last_prompt[uid] = full_p_pre
        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            try:
                t = time.time()
                img, err = execute_generation(full_p_pre, formato=fmt_pre)
                elapsed = round(time.time() - t, 1)
                if img:
                    style_label = f" | {style_pre.split(' — ')[0]}" if style_pre else ""
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ {elapsed}s | {fmt_pre}{style_label}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — {elapsed}s | {fmt_pre} | {scenario['location']}")
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
        full_p_retry, fmt_retry, style_retry = build_prompt(scenario)
        last_prompt[uid] = full_p_retry
        bot.send_message(cid, "🔁 Riprovo la stessa scena...\n⏳ Generazione in corso...")

        def run_retry():
            try:
                t = time.time()
                img, err = execute_generation(full_p_retry, formato=fmt_retry)
                elapsed = round(time.time() - t, 1)
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ Retry — {elapsed}s | {fmt_retry}",
                        reply_markup=get_retry_keyboard())
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

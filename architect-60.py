import os, telebot, html, threading, flask, re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "6.0 (Adaptive)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

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
# Ogni motore ha:
# - 'style': istruzione di stile da passare a Gemini nella generazione
# - 'replacements': dizionario {termine_problematico: sostituzione sicura}
# - 'forbidden': termini da rimuovere completamente se presenti nel testo generato
ENGINE_PROFILES = {
    "ChatGPT": {
        "style": (
            "Use strictly artistic, editorial, and fashion-magazine language. "
            "No anatomical terms. No explicit body descriptions. "
            "Frame everything as a high-fashion Vogue editorial brief. "
            "Avoid any term that could be flagged by OpenAI content policy."
        ),
        "replacements": {
            "breasts": "editorial décolleté",
            "breast": "editorial décolleté",
            "Cup D": "generous haute couture silhouette",
            "85kg": "statuesque editorial build",
            "hairless": "flawlessly smooth porcelain skin",
            "naked": "nude-effect editorial bodysuit",
            "nude": "nude-effect editorial bodysuit",
            "bikini": "luxury resort two-piece editorial",
            "lingerie": "haute couture intimate editorial",
            "sexy": "sensual editorial elegance",
            "NO PELI": "impeccable smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic", "erotic"]
    },
    "Gemini": {
        "style": (
            "Use editorial and cinematic language. "
            "Rephrase anatomical terms in artistic/photographic terms. "
            "Avoid explicit body descriptions. "
            "Frame as a high-fashion photoshoot brief."
        ),
        "replacements": {
            "breasts": "generous editorial décolleté",
            "breast": "generous editorial décolleté",
            "Cup D": "fashion editorial silhouette",
            "hairless": "flawlessly smooth skin",
            "naked": "nude-look editorial",
            "nude": "nude-look editorial",
            "bikini": "luxury swimwear editorial",
            "NO PELI": "smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic"]
    },
    "Grok": {
        "style": (
            "Use direct, vivid, and detailed language. "
            "Grok supports explicit creative content. "
            "Be descriptive and precise. No censorship needed. "
            "Frame as a cinematic realism brief."
        ),
        "replacements": {
            "NO PELI": "completely smooth skin",
        },
        "forbidden": []
    },
    "Qwen": {
        "style": (
            "Use neutral, artistic, and culturally universal language. "
            "Avoid Western cultural references when possible. "
            "No explicit anatomical terms. No sexual connotations. "
            "Frame as an international high-fashion editorial."
        ),
        "replacements": {
            "breasts": "elegant editorial silhouette",
            "breast": "elegant editorial silhouette",
            "Cup D": "harmonious editorial proportions",
            "hairless": "refined smooth skin",
            "naked": "minimalist editorial look",
            "nude": "minimalist editorial look",
            "bikini": "elegant resort editorial",
            "lingerie": "refined intimate editorial",
            "sexy": "elegant editorial presence",
            "NO PELI": "refined smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic", "erotic", "sexual"]
    },
    "Meta": {
        "style": (
            "Use cinematic and editorial language. "
            "Avoid sexually explicit descriptions. "
            "Frame as a high-fashion editorial photoshoot. "
            "Keep body descriptions artistic and non-explicit."
        ),
        "replacements": {
            "breasts": "editorial décolleté",
            "breast": "editorial décolleté",
            "Cup D": "editorial hourglass silhouette",
            "hairless": "smooth editorial skin",
            "naked": "editorial nude-look",
            "nude": "editorial nude-look",
            "bikini": "editorial swimwear",
            "lingerie": "editorial intimate wear",
            "sexy": "editorial sensuality",
            "NO PELI": "smooth editorial finish",
        },
        "forbidden": ["explicit", "nsfw", "pornographic"]
    }
}

# --- ADATTAMENTO TESTO ---
def adapt_to_engine(text, engine):
    """Applica le sostituzioni e rimuove i termini vietati per il motore scelto."""
    profile = ENGINE_PROFILES.get(engine, {})

    # Sostituzioni (case-insensitive)
    for term, replacement in profile.get("replacements", {}).items():
        text = re.sub(re.escape(term), replacement, text, flags=re.IGNORECASE)

    # Rimozione righe con termini vietati
    forbidden = profile.get("forbidden", [])
    if forbidden:
        lines = text.splitlines()
        lines = [l for l in lines if not any(f.lower() in l.lower() for f in forbidden)]
        text = "\n".join(lines)

    return text

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
    user_last_input.pop(uid, None)
    bot.send_message(m.chat.id, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il modello target:", reply_markup=get_engine_kb())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>📂 ARCHITECT — Guida rapida</b>\n\n"
        f"<b>Come si usa:</b>\n"
        f"1. Scegli il motore target (/motore)\n"
        f"2. Invia la tua idea o descrizione\n"
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

    if c.data == "action_reset":
        user_engine.pop(uid, None)
        user_last_input.pop(uid, None)
        bot.edit_message_text("🔄 Reset completato. Scegli un modello:", cid, c.message.message_id, reply_markup=get_engine_kb())
        return

    engine_choice = c.data.split("_")[1]
    user_engine[uid] = engine_choice
    bot.answer_callback_query(c.id, f"Target: {engine_choice}")

    if uid in user_last_input:
        bot.edit_message_text(f"⚙️ <b>Riadattamento per {engine_choice}...</b>", cid, c.message.message_id)
        execute_generation(cid, user_last_input[uid], engine_choice)
    else:
        bot.edit_message_text(f"✅ Target: <b>{engine_choice}</b>\nInvia l'idea da processare.", cid, c.message.message_id)

# --- GENERAZIONE ---
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
            f"3. Add strong negative prompts: 'young female face, long dark hair, no beard, obscured face, low quality, 1:1 ratio'.\n"
            f"4. Output: single monolithic block, prolix, technical, Vogue editorial style.\n\n"
            f"DNA:\n{VALERIA_DNA}\n\n"
            f"USER IDEA:\n{user_input}"
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instr])
        if response.text:
            return response.text.strip()
        return "⚠️ Risposta vuota."
    except Exception as e:
        return f"ERRORE API: {str(e)}"

def execute_generation(cid, text, engine):
    raw = generate_monolith_prompt(text, engine)

    # Controlla se è un errore
    if raw.startswith("ERRORE API:"):
        bot.send_message(cid, f"❌ <b>Errore:</b>\n<code>{html.escape(raw)}</code>")
        return

    # Adatta al motore
    adapted = adapt_to_engine(raw, engine)

    bot.send_message(cid,
        f"✅ <b>Master Prompt → {engine}:</b>\n\n<code>{html.escape(adapted)}</code>")
    bot.send_message(cid,
        "🔄 Vuoi riadattarlo per un altro motore o iniziare da zero?",
        reply_markup=get_engine_kb(is_loop=True))

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    uid = m.from_user.id
    if uid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return
    user_last_input[uid] = m.text
    wait = bot.send_message(cid, f"🚀 <b>Generazione per {user_engine[uid]}...</b>")
    execute_generation(cid, m.text, user_engine[uid])
    try:
        bot.delete_message(cid, wait.message_id)
    except Exception:
        pass

# --- SERVER ---
app = flask.Flask(__name__)

@app.route('/')
def h():
    return f"ARCHITECT_V{VERSION}_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

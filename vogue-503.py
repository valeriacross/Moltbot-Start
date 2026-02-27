import os, io, threading, logging, flask, telebot, html, time
from datetime import datetime
import pytz
from telebot import types
from google import genai
from google.genai import types as genai_types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- HEADER VERSIONE ---
VERSION = "5.0.3"

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

executor = ThreadPoolExecutor(max_workers=4)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                data = f.read()
            logger.info("✅ master_face.png caricata correttamente.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        logger.warning("⚠️ master_face.png non trovata.")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- MASTER IDENTITY ---
MASTER_IDENTITY = """IDENTITY: Nameless Italian transmasculine editorial figure.
BODY: Sculptural hourglass silhouette, generous haute couture décolleté, statuesque build 180cm. Flawlessly smooth porcelain skin, impeccable editorial finish on all surfaces.
FACE: Strong Italian male face, ~60 years old. Oval-rectangular. Ultra-detailed editorial skin texture (pores, fine lines, expressive depth).
EXPRESSION: calm, half-smile, NO teeth. EYES: dark brown/green.
BEARD: light grey/silver, groomed, 6–7 cm.
GLASSES: MANDATORY thin octagonal Vogue frames, Havana dark tortoiseshell (NEVER removed).
HAIR: Light grey/silver, short elegant Italian cut, voluminous. Sides 1–2 cm, nape exposed. Top less than 15 cm. Hair NEVER touching neck, shoulders, or clavicles.
RENDERING: High-fashion editorial photoshoot, cinematic realism. Camera: 85mm, f/2.8, ISO 200, 1/160s. Subsurface Scattering, Global Illumination, Fresnel. Shallow depth of field, natural bokeh.
WATERMARK: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, very small, opacity 90%).
NEGATIVE: female/young face, long/medium hair, ponytail, bun, braid, hair touching neck/shoulders, masculine body shape."""

# --- OTTIMIZZAZIONE PROMPT ---
def optimize_prompt_with_gemini(user_text, ar):
    system_instruction = (
        "Sei un esperto di prompt engineering per la generazione di immagini AI.\n"
        "Il tuo compito e' costruire un prompt finale completo, dettagliato e immediatamente utilizzabile\n"
        "su qualsiasi motore di generazione immagini (Gemini, ChatGPT, Grok, Midjourney, ecc.).\n\n"
        "REGOLE FONDAMENTALI:\n"
        "1. Il soggetto principale e' SEMPRE e SOLO quello descritto nel MASTER IDENTITY qui sotto.\n"
        "   Ignora completamente qualsiasi descrizione fisica alternativa presente nel testo utente.\n"
        "2. Dal testo utente estrai SOLO: scena, ambiente, sfondo, luce, posa, abbigliamento, mood,\n"
        "   stile fotografico. Tutto il resto viene dal MASTER IDENTITY.\n"
        "3. Il prompt finale DEVE contenere INTEGRALMENTE tutti gli elementi del MASTER IDENTITY\n"
        "   (corpo, viso, barba, occhiali, capelli, rendering, watermark, negativi) scritti in forma\n"
        "   narrativa fluida, fusi con gli elementi di scena estratti dall'utente.\n"
        "   NON abbreviare, NON omettere, NON riassumere il MASTER IDENTITY.\n"
        f"4. Il formato/ratio dell'immagine e': {ar} -- includilo alla fine del prompt.\n"
        "5. Il prompt output deve essere COMPLETO e AUTOSUFFICIENTE: chiunque lo copi e incolli\n"
        "   su un motore esterno deve ottenere esattamente il risultato corretto senza aggiungere nulla.\n"
        "6. Scrivi SOLO il prompt finale in testo plain continuo, separato da virgole e punti.\n"
        "   Zero spiegazioni, zero prefissi, zero markdown, zero backtick, zero JSON,\n"
        "   zero parentesi graffe, zero parentesi quadre, zero elenchi puntati, zero numerazione.\n"
        "7. VIETATO inserire frasi come 'FILTER BYPASS', 'BYPASS ACTIVATED', 'SAFETY OVERRIDE',\n"
        "   'NO OBSCURED FEATURES' o qualsiasi riferimento a filtri o bypass.\n"
        "8. Tutti i dettagli corporei in linguaggio editoriale fashion neutro. Mai termini anatomici espliciti.\n"
        "9. Il prompt finale deve essere SEMPRE scritto interamente in inglese.\n"
        "   Se il testo utente e' in italiano o qualsiasi altra lingua, traducilo prima di procedere.\n\n"
        "MASTER IDENTITY (NON modificare, NON omettere, integrare COMPLETAMENTE nell'output):\n"
        + MASTER_IDENTITY
    )

    try:
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[f"Testo utente da analizzare e integrare:\n\n{user_text}"],
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
                max_output_tokens=2500,
            )
        )
        if response.text:
            optimized = response.text.strip()
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
    return text.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")

# --- GENERAZIONE IMMAGINI ---
def execute_generation(full_prompt, img_rif_bytes=None):
    try:
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

        response = client.models.generate_content(
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

        if not response.candidates:
            logger.warning("⚠️ API: nessun candidato.")
            return None, "❌ L'API non ha restituito risultati. Riprova."

        candidate = response.candidates[0]
        if candidate.finish_reason != "STOP":
            reason = candidate.finish_reason
            logger.warning(f"⚠️ Generazione bloccata: {reason}")
            return None, f"🛡️ Generazione bloccata.\nMotivo: <b>{reason}</b>"

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
    logger.info(f"📋 /settings da {username} (id={uid})")
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
    prompt = user_last_prompt.get(uid)
    if not prompt:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt inviato all'API</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

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
    user_last_prompt[uid] = data['full_p']
    logger.info(f"🚀 {username} (id={uid}) → generazione | qty={qty} | ar={user_ar[uid]}")

    bot.send_message(
        call.message.chat.id,
        f"🚀 <b>Generazione avviata!</b>\n"
        f"📸 Sto creando <b>{qty}</b> foto...\n"
        f"⏳ Tempo stimato: ~{qty * 20}–{qty * 35} secondi. Attendi."
    )

    def run_task(idx):
        t_start = time.time()
        logger.info(f"   🎨 Scatto {idx+1}/{qty} per {username}...")
        res, err = execute_generation(data['full_p'], data['img'])
        elapsed = round(time.time() - t_start, 1)
        if res:
            try:
                bot.send_document(
                    call.message.chat.id,
                    io.BytesIO(res),
                    visible_file_name=f"vogue_{idx+1}.jpg",
                    caption=f"✅ Scatto {idx+1}/{qty} — {elapsed}s"
                )
                logger.info(f"   ✅ Scatto {idx+1}/{qty} inviato a {username} in {elapsed}s")
            except Exception as e:
                logger.error(f"   ❌ Errore invio scatto {idx+1}: {e}")
                bot.send_message(call.message.chat.id,
                    f"❌ Scatto {idx+1}: generato ma errore nell'invio.\n<code>{html.escape(str(e))}</code>")
        else:
            logger.warning(f"   ❌ Scatto {idx+1}/{qty} fallito ({elapsed}s): {err}")
            bot.send_message(call.message.chat.id,
                f"❌ <b>Scatto {idx+1} fallito</b> ({elapsed}s)\n{err}")

    for i in range(qty):
        executor.submit(run_task, i)

    pending_prompts.pop(uid, None)

# --- HANDLER MESSAGGI PRINCIPALI ---
@bot.message_handler(content_types=['text', 'photo'])
def ask_confirmation(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name

    user_text = m.caption if m.content_type == 'photo' else m.text
    if not user_text or not user_text.strip():
        bot.reply_to(m, "⚠️ Scrivi una scena come testo o come didascalia alla foto.")
        return

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

    logger.info(f"✏️ Input da {username} (id={uid}): «{user_text[:80]}{'...' if len(user_text) > 80 else ''}»")

    wait_msg = bot.reply_to(m, "🧠 <b>Ottimizzazione prompt in corso...</b>")

    ar_snapshot = user_ar[uid]
    future = executor.submit(optimize_prompt_with_gemini, user_text, ar_snapshot)
    try:
        optimized_prompt, opt_err = future.result(timeout=30)
    except Exception as e:
        optimized_prompt = None
        opt_err = str(e)

    try:
        bot.delete_message(m.chat.id, wait_msg.message_id)
    except Exception:
        pass

    if not optimized_prompt:
        logger.warning(f"⚠️ Ottimizzazione fallita per {username}, uso prompt diretto. Errore: {opt_err}")
        optimized_prompt = f"{MASTER_IDENTITY}\n\nSCENE: {user_text}\nFORMAT: {ar_snapshot}"
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
    markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

    bot.reply_to(
        m,
        f"📝 <b>Prompt ottimizzato</b> ({ar_snapshot} | {user_qty[uid]} foto):\n\n"
        f"<code>{html.escape(preview_prompt)}</code>\n\n"
        f"Procedere con la generazione?",
        reply_markup=markup
    )

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

import os, io, threading, logging, flask, telebot, json, html, time
from datetime import datetime
import pytz
from telebot import types
from google import genai
from google.genai import types as genai_types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- HEADER VERSIONE ---
VERSION = "4.1.0 (Robust)"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "nano-banana-pro-preview"
LISBON_TZ = pytz.timezone('Europe/Lisbon')
ADMIN_ID = os.environ.get("ADMIN_TELEGRAM_ID")  # opzionale, per log futuri

# --- VARIABILI DI STATO ---
user_ar = defaultdict(lambda: "2:3")
user_qty = defaultdict(lambda: 1)
pending_prompts = {}

executor = ThreadPoolExecutor(max_workers=2)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                data = f.read()
            logger.info("✅ master_face.png caricata correttamente.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        else:
            logger.warning("⚠️ master_face.png non trovata. Generazione senza immagine di riferimento.")
            return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
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
    return f"--- MASTER PROMPT ---\n{identity}\n\n{technical}\n\nSCENE: {user_text}\nFORMAT: {ar_scelto}\n\n{rendering}\n\n{negatives}"

# --- ANTEPRIMA LEGGIBILE (no JSON) ---
def build_preview_text(user_text, ar, qty):
    return (
        f"📸 <b>Scena:</b> {html.escape(user_text)}\n"
        f"📐 <b>Formato:</b> {ar}\n"
        f"🔢 <b>Quantità:</b> {qty} foto\n"
    )

# --- CORE GENERAZIONE ---
def execute_generation(full_prompt, img_rif_bytes=None):
    try:
        contents = [full_prompt]
        if MASTER_PART:
            contents.append(MASTER_PART)
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART (immagine di riferimento assente).")
        if img_rif_bytes:
            try:
                contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"❌ Errore preparazione immagine riferimento utente: {e}")
                return None, "❌ Errore nel processare l'immagine allegata."

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in
                                  ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH",
                                   "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            )
        )

        if not response.candidates:
            logger.warning("⚠️ API Gemini: nessun candidato nella risposta.")
            return None, "❌ L'API non ha restituito risultati. Riprova."

        candidate = response.candidates[0]
        if candidate.finish_reason != "STOP":
            reason = candidate.finish_reason
            logger.warning(f"⚠️ Generazione bloccata. Motivo: {reason}")
            return None, f"🛡️ Generazione bloccata dal filtro di sicurezza.\nMotivo: <b>{reason}</b>"

        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None

        logger.warning("⚠️ Risposta API ricevuta ma nessuna immagine trovata nelle parti.")
        return None, "❌ Nessuna immagine nella risposta. Riprova con una scena diversa."

    except Exception as e:
        logger.error(f"❌ Eccezione in execute_generation: {e}", exc_info=True)
        return None, f"❌ Errore interno durante la generazione:\n<code>{html.escape(str(e))}</code>"

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- /start e /settings ---
@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📋 /settings richiesto da {username} (id={uid})")
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
        types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3")
    )
    markup.row(
        types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
        types.InlineKeyboardButton("2 Foto", callback_data="qty_2")
    )
    bot.send_message(
        m.chat.id,
        f"<b>👠 VOGUE v{VERSION}</b>\n"
        f"Formato attuale: <b>{user_ar[uid]}</b> | Quantità: <b>{user_qty[uid]}</b>\n\n"
        f"Scegli il formato e la quantità:",
        reply_markup=markup
    )

# --- /help ---
@bot.message_handler(commands=['help'])
def help_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"❓ /help richiesto da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>👠 VOGUE Bot — Guida rapida</b>\n\n"
        f"<b>Come si usa:</b>\n"
        f"Scrivi una scena (es. <i>«in studio fotografico con luce soffusa»</i>) "
        f"oppure invia una foto con una didascalia.\n"
        f"Il bot costruirà il prompt e chiederà conferma prima di generare.\n\n"
        f"<b>Comandi disponibili:</b>\n"
        f"/start o /settings — imposta formato e quantità\n"
        f"/help — questa guida\n"
        f"/info — versione e stato del bot\n"
        f"/prompt — mostra il master prompt base\n\n"
        f"<b>Formati disponibili:</b> 16:9 🎬 | 2:3 🖼️\n"
        f"<b>Quantità:</b> 1 o 2 foto per richiesta"
    )

# --- /info ---
@bot.message_handler(commands=['info'])
def info_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"ℹ️ /info richiesto da {username} (id={uid})")
    now = datetime.now(LISBON_TZ).strftime("%d/%m/%Y %H:%M:%S")
    master_status = "✅ Caricata" if MASTER_PART else "⚠️ Non trovata"
    bot.send_message(m.chat.id,
        f"<b>ℹ️ Informazioni Bot</b>\n\n"
        f"Versione: <b>{VERSION}</b>\n"
        f"Modello: <code>{MODEL_ID}</code>\n"
        f"Ora server: <b>{now}</b>\n"
        f"Master face: {master_status}\n"
        f"Formato attuale: <b>{user_ar[uid]}</b>\n"
        f"Quantità attuale: <b>{user_qty[uid]}</b>"
    )

# --- /prompt ---
@bot.message_handler(commands=['prompt'])
def prompt_cmd(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📄 /prompt richiesto da {username} (id={uid})")
    example = build_master_prompt("[LA TUA SCENA QUI]", user_ar[uid])
    # Suddividiamo se troppo lungo per Telegram (limite 4096 char)
    max_len = 4000
    safe = html.escape(example)
    if len(safe) > max_len:
        safe = safe[:max_len] + "\n<i>... (troncato)</i>"
    bot.send_message(m.chat.id, f"<b>📄 Master Prompt base:</b>\n\n<code>{safe}</code>")

# --- CALLBACK: AR e QTY ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("ar_") or call.data.startswith("qty_"))
def handle_settings_callback(call):
    uid = call.from_user.id
    username = call.from_user.username or call.from_user.first_name

    if call.data.startswith("ar_"):
        new_ar = call.data.replace("ar_", "")
        user_ar[uid] = new_ar
        logger.info(f"⚙️ {username} (id={uid}) → formato cambiato a {new_ar}")
        bot.answer_callback_query(call.id, f"✅ Formato impostato: {new_ar}")

    elif call.data.startswith("qty_"):
        new_qty = int(call.data.replace("qty_", ""))
        user_qty[uid] = new_qty
        logger.info(f"⚙️ {username} (id={uid}) → quantità cambiata a {new_qty}")
        bot.answer_callback_query(call.id, f"✅ Quantità impostata: {new_qty} foto")

    # Aggiorna il messaggio con le nuove preferenze
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
            types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3")
        )
        markup.row(
            types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
            types.InlineKeyboardButton("2 Foto", callback_data="qty_2")
        )
        bot.edit_message_text(
            f"<b>👠 VOGUE v{VERSION}</b>\n"
            f"Formato attuale: <b>{user_ar[uid]}</b> | Quantità: <b>{user_qty[uid]}</b>\n\n"
            f"Scegli il formato e la quantità:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"⚠️ Impossibile aggiornare messaggio settings: {e}")

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
        logger.info(f"❌ {username} (id={uid}) ha annullato la generazione.")
        bot.send_message(call.message.chat.id, "❌ <b>Generazione annullata.</b>")
        return

    data = pending_prompts.get(uid)
    if not data:
        logger.warning(f"⚠️ Conferma ricevuta da {username} (id={uid}) ma nessun pending_prompt trovato.")
        bot.send_message(call.message.chat.id, "⚠️ Sessione scaduta. Invia di nuovo la scena.")
        return

    qty = data['qty']
    logger.info(f"🚀 {username} (id={uid}) → avvia generazione | qty={qty} | ar={user_ar[uid]}")
    bot.send_message(
        call.message.chat.id,
        f"🚀 <b>Generazione avviata!</b>\n"
        f"📸 Sto creando <b>{qty}</b> foto...\n"
        f"⏳ Tempo stimato: ~{qty * 20}–{qty * 35} secondi. Attendi."
    )

    def run_task(idx):
        t_start = time.time()
        logger.info(f"   🎨 Scatto {idx+1}/{qty} in corso per {username} (id={uid})...")
        res, err = execute_generation(data['full_p'], data['img'])
        elapsed = round(time.time() - t_start, 1)
        if res:
            try:
                bot.send_document(
                    call.message.chat.id,
                    io.BytesIO(res),
                    visible_file_name=f"vogue_{idx+1}.jpg",
                    caption=f"✅ Scatto {idx+1}/{qty} completato in {elapsed}s"
                )
                logger.info(f"   ✅ Scatto {idx+1}/{qty} inviato a {username} in {elapsed}s")
            except Exception as e:
                logger.error(f"   ❌ Errore invio scatto {idx+1} a {username}: {e}")
                bot.send_message(call.message.chat.id, f"❌ Scatto {idx+1}: generato ma errore nell'invio.\n<code>{html.escape(str(e))}</code>")
        else:
            logger.warning(f"   ❌ Scatto {idx+1}/{qty} fallito per {username} dopo {elapsed}s: {err}")
            bot.send_message(call.message.chat.id, f"❌ <b>Scatto {idx+1} fallito</b> ({elapsed}s)\n{err}")

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

    # Download immagine allegata
    img_data = None
    if m.content_type == 'photo':
        try:
            file_info = bot.get_file(m.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)
            logger.info(f"🖼️ Foto ricevuta da {username} (id={uid}), size={len(img_data)} bytes")
        except Exception as e:
            logger.error(f"❌ Errore download foto da {username}: {e}")
            bot.reply_to(m, "❌ Errore nel scaricare la foto allegata. Riprova.")
            return

    logger.info(f"✏️ Scena ricevuta da {username} (id={uid}): «{user_text[:80]}{'...' if len(user_text) > 80 else ''}»")

    full_verbose_prompt = build_master_prompt(user_text, user_ar[uid])
    pending_prompts[uid] = {
        'full_p': full_verbose_prompt,
        'qty': user_qty[uid],
        'img': img_data
    }

    preview = build_preview_text(user_text, user_ar[uid], user_qty[uid])

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
    markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

    bot.reply_to(
        m,
        f"📝 <b>Riepilogo richiesta:</b>\n\n{preview}\nProcedere con la generazione?",
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

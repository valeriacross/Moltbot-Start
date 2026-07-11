import os, io, html, logging, threading
import telebot
from concurrent.futures import ThreadPoolExecutor
from C_shared100 import GeminiClient, HealthServer, is_allowed, genai_types, detect_mime_type, SHARED_VERSION, SHARED_DATE

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
# CHANGELOG 3.0.0 (10/07/2026): RISCRITTURA COMPLETA su richiesta esplicita di
# Walter. /generico non ha mai funzionato in modo affidabile fino in fondo —
# il problema di fondo era strutturale, non un bug isolato: Architect faceva
# analisi e scrittura in un'unica chiamata Gemini, senza mai produrre un testo
# intermedio ispezionabile (motivo per cui la clausola BODY ART non poteva
# essere condizionale, sezione 2decies/2undecies dell'HANDOFF, e motivo più
# profondo per cui ogni fix su /generico ha sempre inseguito sintomi diversi
# senza risolvere la causa reale).
#
# Nuovo scopo del bot, totalmente diverso dal precedente:
# - RIMOSSO: /generico, GENERICO_SYSTEM_PROMPT, make_generic(), tutto lo stato
#   pending_generico/_generico_state/_GENERICO_DEBOUNCE, la scelta iniziale
#   Testo/Foto (user_mode, get_mode_kb(), get_after_prompt_kb()),
#   generate_monolith_prompt() (modalità testo), generate_from_image() (con
#   DNA Valeria), _architect_review()/review_and_fix(), VALERIA_DNA e
#   BODY_ART_EXCEPTION_TEXT (nessun DNA da forzare, quindi nessuna eccezione
#   da gestire), EDITORIAL_WRAPPER, send_prompt() con bottoni post-prompt.
# - NUOVO: il bot accetta SOLO foto (nessuna modalità da scegliere). Ogni foto
#   viene analizzata con un unico prompt (analyze_image_full) che chiede a
#   Gemini un JSON dettagliato e completo della scena — soggetto REALE (viso,
#   corpo, capelli, espressione, posa, come appaiono davvero, senza alcuna
#   sostituzione identitaria), outfit, accessori, body art, props, sfondo,
#   luce, camera, palette colori, mood. Se il soggetto è Valeria, la
#   descrizione includerà barba/occhiali/corpo di Valeria — perché è quello
#   che è visibile nella foto, non perché forzato da un DNA statico.
# - Output consegnato come FILE .json scaricabile via bot.send_document(),
#   non più testo in chat — elimina alla radice ogni problema di lunghezza
#   messaggio/debounce che ha afflitto /generico (sezioni 2octies/2undecies).
# - Nessuna chiamata a analyze_scene() di shared: quella funzione è
#   deliberatamente cieca sul soggetto (per design, dato che il soggetto
#   viene sempre sostituito dal DNA Valeria negli altri bot) — qui serve
#   l'esatto opposto, quindi Architect ha un proprio prompt di analisi
#   autonomo e completo, non condiviso.
# - Stesso servizio Koyeb (homely-annabelle/thearchitect), stesso token
#   Telegram (TELEGRAM_TOKEN_ARCHITECT) — nessun bot nuovo, stesso contenitore
#   ripensato dentro, come richiesto esplicitamente da Walter.
# - Comando rinominato: /lastprompt → /lastjson (rimanda l'ultimo file JSON
#   generato, senza rianalizzare la foto).
#
# Nessun'altra parte del progetto tocca questo file: Vogue, Atelier, Filtro,
# Surprise continuano il loro lavoro con il DNA Valeria esattamente come
# prima — Architect smette di essere "un terzo bot uguale" e diventa lo
# strumento di analisi pura, complementare, non sovrapposto.
VERSION = "3.0.1"
TOKEN   = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")

gemini   = GeminiClient()
server   = HealthServer("ARCHITECT", VERSION)
bot      = telebot.TeleBot(TOKEN, parse_mode="HTML")
executor = ThreadPoolExecutor(max_workers=4)

logger.info(f"📐 ARCHITECT v{VERSION} — inizializzazione in corso...")

# --- STATO UTENTE ---
_state_lock = threading.Lock()
last_prompt = {}   # uid → (testo, filename) — ultimo prompt generato, per /lastprompt

# --- PROMPT DI ANALISI — TESTO A SEZIONI, NESSUN DNA ---
# CHANGELOG 3.0.1 (11/07/2026): Walter ha segnalato che l'output JSON della
# 3.0.0 è "ingestibile" e "non pubblicabile" — un JSON strutturato non è un
# prompt pronto all'uso, va prima riformattato a mano. Cambiato l'output da
# JSON a TESTO in formato prompt, sezioni etichettate in chiaro (stesso stile
# di _ANALYZE_PROMPT in shared — OUTFIT/ACCESSORIES/BACKGROUND/ecc. — ma con
# in più una sezione SUBJECT che descrive il soggetto reale per intero, dato
# che qui non c'è nessun DNA da iniettare al posto suo). File consegnato ora
# come .txt invece di .json. Rimossa tutta la logica di parsing/validazione
# JSON (json.loads, _strip_json_fences, retry su JSONDecodeError) — un testo
# libero non ha una sintassi da validare come un JSON. /lastjson → tornato a
# /lastprompt (coerente con gli altri bot del progetto).
ANALYSIS_PROMPT = (
    "Analyze this reference photograph in complete, exhaustive detail, from every point "
    "of view, and write a single ready-to-use image-generation prompt describing it — "
    "plain text, NOT JSON, NOT markdown code fences, NOT a bullet list. Organize it into "
    "the labeled sections shown below, each as a detailed descriptive paragraph, precise "
    "enough that someone could regenerate a very similar image from this text alone.\n\n"
    "Do NOT omit or replace the subject — describe exactly what you see: face, hair, "
    "expression, body, pose, exactly as they appear in the photo. No identity "
    "substitution, no fictional character overlay, no DNA injection of any kind. If the "
    "subject has a beard, glasses, tattoos, a specific body type — describe them as "
    "literally seen. This must be a faithful, literal, neutral description of the actual "
    "photograph, nothing invented.\n\n"
    "Use exactly these section labels, each followed by a colon and a detailed "
    "paragraph. If a section genuinely does not apply, write 'None.' rather than "
    "omitting the label:\n\n"
    "SUBJECT: [Full literal description of the person in the frame — apparent gender "
    "presentation, apparent age range, face shape, skin, facial hair, eyes, eyebrows, "
    "expression, hair color/length/style/texture, glasses or eyewear, body build and "
    "proportions, pose, how the subject is framed by the camera.]\n\n"
    "OUTFIT: [Every garment as a standalone object — exact name, color with HEX code, "
    "fabric, cut, fit, coverage, embellishments, details.]\n\n"
    "ACCESSORIES: [Jewelry, footwear, headwear, bags — exact placement and material.]\n\n"
    "BODY ART: [Tattoos, body paint, or decorative skin markings — pattern style, "
    "colors with HEX, exact placement and coverage area on the body, line density and "
    "level of detail.]\n\n"
    "PROPS & ACTIONS: [Physical objects interacting directly with the subject's body — "
    "exact position, contact point, and action being performed.]\n\n"
    "BACKGROUND: [Exact location, architecture, surfaces, props, environment — be "
    "specific.]\n\n"
    "LIGHTING: [Light source, direction, quality, color temperature, mood.]\n\n"
    "CAMERA: [Framing, angle, depth of field.]\n\n"
    "COLOR PALETTE: [Dominant HEX codes with label.]\n\n"
    "MOOD: [Overall atmosphere, color grade, cinematic style.]\n\n"
    "Output ONLY the labeled sections above, in that order, as plain text — no JSON, no "
    "markdown formatting, no commentary before or after."
)

def analyze_image_full(img_bytes: bytes) -> tuple[str | None, str | None]:
    """Analizza un'immagine e restituisce un prompt testuale completo e fedele — incluso
    il soggetto reale così com'è, nessuna sostituzione identitaria, nessun DNA.
    Ritorna (testo, None) in caso di successo, (None, messaggio_errore) altrimenti."""
    try:
        mime = detect_mime_type(img_bytes)
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
        raw = gemini.generate(ANALYSIS_PROMPT, contents=[img_part], max_tokens=4096)
        if not raw:
            return None, "Risposta vuota da Gemini."
        return raw.strip(), None
    except Exception as e:
        logger.error(f"❌ Errore analyze_image_full: {e}", exc_info=True)
        return None, f"Errore API: {e}"

# --- COMANDI ---
@bot.message_handler(commands=['start', 'reset'])
def start(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name
    with _state_lock:
        last_prompt.pop(uid, None)
    logger.info(f"🔄 /start da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>📐 ARCHITECT v{VERSION}</b>\n\n"
        f"Inviami una foto: ti restituisco un file <b>.txt</b> con il prompt completo "
        f"della scena — soggetto, outfit, accessori, sfondo, luce, tutto quello che è "
        f"visibile — senza alcun DNA Valeria Cross. Descrizione fedele, pronta all'uso."
    )

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>📐 ARCHITECT v{VERSION} — Comandi</b>\n\n"
        f"/start · /reset — Messaggio iniziale\n"
        f"/lastprompt — Reinvia l'ultimo file prompt generato\n"
        f"/info — Versione e informazioni\n"
        f"/shared — Versione shared\n"
        f"/help — Questo messaggio\n\n"
        f"<i>Inviami direttamente una foto per iniziare — non c'è altra modalità.</i>"
    )

@bot.message_handler(commands=['info'])
def cmd_info(m):
    bot.send_message(m.chat.id,
        f"<b>📐 ARCHITECT v{VERSION}</b>\n\n"
        f"Motore: <code>gemini-3.5-flash</code>\n"
        f"Funzione: prompt testuale completo dell'immagine — nessun DNA identitario, "
        f"nessuna sostituzione del soggetto.\n"
        f"Output: file <code>.txt</code> scaricabile, pronto all'uso.\n"
    )

@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /lastprompt non autorizzato: uid={uid}")
        return
    entry = last_prompt.get(uid)
    if not entry:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Invia prima una foto.")
        return
    text, filename = entry
    bot.send_document(m.chat.id,
        document=io.BytesIO(text.encode('utf-8')),
        visible_file_name=filename)

@bot.message_handler(commands=['shared'])
def cmd_shared(m):
    bot.send_message(m.chat.id, f"📦 <b>C_shared100.py</b> v{SHARED_VERSION} — {SHARED_DATE}")

# --- HANDLER TESTO — guida chi scrive per abitudine, nessuna modalità testo ---
@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text and m.text.startswith('/'):
        return
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Testo non autorizzato: uid={uid}")
        return
    bot.send_message(m.chat.id, "📸 Inviami una foto — questo bot analizza solo immagini, non genera più prompt da testo.")

# --- HANDLER FOTO ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid}")
        return
    username = m.from_user.username or m.from_user.first_name
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
        logger.info(f"🖼️ Foto da {username} (id={uid}), {len(img_bytes)} bytes")
    except Exception as e:
        bot.reply_to(m, f"❌ Errore download foto: {html.escape(str(e))}")
        return

    wait = bot.send_message(m.chat.id,
        "🔍 <b>Analisi immagine in corso...</b>\n⏳ Attendi ~20-30 secondi.")

    def task():
        try:
            text, err = analyze_image_full(img_bytes)
            try:
                bot.delete_message(m.chat.id, wait.message_id)
            except Exception:
                pass
            if err:
                bot.send_message(m.chat.id,
                    f"❌ <b>Analisi fallita.</b>\n\n<code>{html.escape(err)}</code>")
                return
            filename = f"prompt_{m.photo[-1].file_unique_id}.txt"
            with _state_lock:
                last_prompt[uid] = (text, filename)
            bot.send_document(m.chat.id,
                document=io.BytesIO(text.encode('utf-8')),
                visible_file_name=filename,
                caption="✅ Prompt completo — nessun DNA Valeria, descrizione fedele dell'immagine, pronto all'uso.")
            logger.info(f"✅ Prompt inviato a {username} ({len(text)} chars)")
        except Exception as e:
            logger.error(f"❌ task crash: {e}", exc_info=True)
            try:
                bot.delete_message(m.chat.id, wait.message_id)
            except Exception:
                pass
            bot.send_message(m.chat.id, f"❌ Errore:\n<code>{html.escape(str(e))}</code>")

    executor.submit(task)

# --- MAIN ---
if __name__ == "__main__":
    import time
    logger.info(f"📐 Avvio ARCHITECT v{VERSION}")
    server.start()
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

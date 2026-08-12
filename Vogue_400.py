import os, logging, telebot, html, time, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from C_shared100 import GeminiClient, HealthServer, is_allowed, genai_types, analyze_scene
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK
from C_shared100 import VALERIA_DNA, generate_caption, review_and_fix, sanitize_user_input, SHARED_VERSION, SHARED_DATE, body_art_clause, multi_subject_clause

# --- VERSIONE ---
# CHANGELOG 2.1.0 (17/07/2026): cambio di motore, non un patch — versione
# alzata di conseguenza su richiesta esplicita di Walter (da 2.0.3 a 2.1.0).
# Rimosso il negative prompt locale in build_prompt() ("NEGATIVE: wrong
# background, studio backdrop..."), tolto import morto di VALERIA_NEGATIVE
# (eliminata da shared 2.4.0). Causa: verificato che il modello dietro
# Flow non ha un campo negativePrompt indipendente — fix generale esteso a
# tutto l'impianto DNA condiviso dopo che due round di negative prompt su
# Atelier (v2.0.7/2.0.8) non hanno retto a test successivi. Il contenuto
# informativo (outfit fedele, location invariata) resta lo stesso,
# riscritto in positivo puro. Il DNA stesso (VALERIA_FACE/BODY_STRONG,
# shared) è stato riscritto in positivo nella stessa sessione — Vogue lo
# eredita automaticamente da VALERIA_DNA, nessun'altra modifica necessaria
# qui oltre alla riga locale. Vedi HANDOFF sezione 2septendecies.
# CHANGELOG 2.0.2 (13/07/2026): MODEL_TEXT allineato al motore reale —
# "gemini-3-flash-preview" → "gemini-3.5-flash". La costante era locale al
# bot (non letta da C_shared100), quindi era rimasta disallineata dal
# passaggio a gemini-3.5-flash fatto in shared 2.3.16 (04/07). Mostrata
# in /info. Nessun'altra modifica.
# CHANGELOG 2.0.1 (08/07/2026): build_prompt() ora inserisce
# body_art_clause(scene_description) subito dopo VALERIA_DNA — la
# clausola "BODY ART EXCEPTION" (introdotta in shared 2.3.17, dentro
# VALERIA_BODY_STRONG) compariva in OGNI prompt anche quando la foto non
# aveva tatuaggi (BODY ART: None), come testo condizionale inerte. Ora è
# stata tolta da VALERIA_DNA e viene aggiunta qui solo se analyze_scene()
# ha davvero trovato body art nella foto. Sul percorso testo (handle_text,
# nessuna foto analizzata) body_art_clause() restituisce sempre stringa
# vuota, comportamento invariato. Vedi C_shared100.py 2.3.18 e HANDOFF
# sezione 2decies.
# CHANGELOG 2.0.0 (20/06/2026): bump di allineamento al nuovo ciclo versioni
# (Vogue, Architect, Atelier, Surprise → 2.0.0). Nessuna modifica funzionale
# in questo bot in questa sessione — i bug noti (#4, _active_cid globale) sono
# stati lasciati invariati su richiesta esplicita (uso singolo utente).
# CHANGELOG 2.2.0 (01/08/2026): supporto foto di riferimento con 2+ soggetti
# distinti (m+f, m+m, f+f...) su richiesta di Walter — rilevamento
# automatico, non un comando. Import multi_subject_clause() da shared
# (2.4.9), inserito in build_prompt() subito dopo body_art_clause() — stesso
# pattern, nessun impatto se la foto ha una sola persona. Rilevamento/analisi
# (campo FIGURES, outfit per figura) vive interamente in _ANALYZE_PROMPT
# (shared) — nessuna modifica alla logica di analisi qui. Non ancora testato
# in produzione. Bump di MINOR (2.1.0 → 2.2.0), non patch: nuova capacità
# aggiunta al bot, non un fix — file rinominato di conseguenza in
# Vogue_220.py (Walter ha corretto un errore di Claude che aveva lasciato
# lo stesso nome file con solo il changelog interno aggiornato, in
# violazione della regola "mai stesso nome qualsiasi sia la modifica").
# CHANGELOG 3.1.0 (10/08/2026): Walter ha testato il video (funziona bene) e
# ha deciso di archiviare Vogue 2.2 — Vogue 3.x diventa la versione di
# riferimento. Tolto "(beta)" dal pulsante e dal messaggio di conferma
# modalità video. Aggiunto un terzo pulsante "🎥 Video" alla tastiera
# post-prompt (get_after_prompt_keyboard) — riusa lo stesso callback
# "vogue_mode_video" già gestito, nessuna nuova logica di callback
# necessaria. "📸 Nuova foto" e "🏠 Home" invariati. Bump di MINOR (3.0.0 →
# 3.1.0): uscita dalla beta + nuovo pulsante, non un semplice fix — file
# rinominato in Vogue_310.py.
# CHANGELOG 3.0.0 (05/08/2026): Vogue 3.0 — fork indipendente da Vogue 2.2, su
# richiesta esplicita di Walter: se non funziona si torna a Vogue_220.py senza
# aver toccato nient'altro. Aggiunto supporto video (beta) accanto a quello
# immagine esistente (invariato byte per byte). Menu esplicito su /start
# ("📷 Immagine" / "🎥 Video (beta)"), scelta salvata in pending_mode[uid] —
# se mandi il tipo sbagliato rispetto alla scelta, messaggio di mismatch
# invece di processare comunque. Nuovo _ANALYZE_PROMPT_VIDEO, isolato QUI
# (non in shared): stesse identiche sezioni di _ANALYZE_PROMPT (shared) così
# body_art_clause()/multi_subject_clause() e build_prompt() restano invariati
# — cambia solo l'istruzione iniziale (considerare l'intera clip, scegliere
# il momento più rappresentativo) e una regola sul movimento. Nuova
# analyze_video(), stessa struttura/classificazione errori di analyze_scene()
# (shared) ma locale qui. Controllo dimensione PRIMA del download
# (m.video.file_size, niente chiamata sprecata) — tetto MAX_VIDEO_BYTES =
# 20MB, il limite reale di Telegram Bot API su getFile, non negoziabile lato
# codice. /caption resta indipendente dalla scelta modalità (flusso a parte,
# già suo). Scelta non discussa esplicitamente con Walter: l'input testuale
# (handle_text, "descrivi la scena a parole") resta anch'esso indipendente
# dalla scelta immagine/video — non è nel menu, quindi non l'ho vincolato;
# da confermare se è la scelta giusta. Nessuna modifica a C_shared100.py.
# Non ancora testato.
# CHANGELOG 4.0.0 (11/08/2026): su richiesta di Walter, invertito lo scopo
# della modalità Immagine — non più una foto ferma, ma un prompt VIDEO con un
# movimento cinematografico INVENTATO coerente con la scena (Walter: "donna
# per strada con un cane" -> "donna che cammina con il cane"). Nuova
# build_prompt_video() — copia esatta di build_prompt() (stesso DNA, stessi
# lock, stessa scene reference) con solo le GENERATION INSTRUCTIONS finali
# cambiate: singolo shot continuo, movimento libero anche drammatico
# (capelli, tessuti) anche SENZA indizi espliciti nella foto, nessuna durata
# specificata (decide Flow) — tutte scelte esplicite di Walter. handle_photo()
# ora chiama build_prompt_video() invece di build_prompt(); handle_video()
# INVARIATO (video -> prompt foto ferma, confermato da Walter che va bene
# così com'è). Messaggio di conferma modalità Immagine aggiornato per
# chiarezza, dato che è un'inversione che sorprende rispetto a prima.
# NOTA NON RISOLTA: review_and_fix() (shared) descrive nelle sue istruzioni
# interne il testo come "image generation prompt" — le correzioni che fa
# (capelli/occhiali/subject bleed/watermark) sono le stesse a prescindere da
# foto/video, ma in teoria potrebbe spingere sottilmente il fraseggio verso
# "fotografia" durante la revisione. Non toccato shared per questo
# esperimento — da tenere d'occhio nei test, non ancora osservato in
# pratica. build_prompt() (foto ferma) resta intatta e usata da handle_video()
# — nessuna modifica al percorso video->foto. Non ancora testato.
VERSION = "4.0.0"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN      = os.environ.get("TELEGRAM_TOKEN")
MODEL_TEXT = "gemini-3.5-flash"

# --- PROMPT ANALISI VIDEO — Vogue 3.0, isolato qui, NON in shared ---
# Stesse identiche sezioni di _ANALYZE_PROMPT (shared) — così body_art_clause()/
# multi_subject_clause() (che cercano "BODY ART:"/"FIGURES:" via regex) continuano a
# funzionare senza modifiche, e build_prompt() non cambia di una riga. Cambia solo
# l'istruzione iniziale (considerare l'intera clip, scegliere il momento più
# rappresentativo) e una regola in più sul movimento.
_ANALYZE_PROMPT_VIDEO = (
    "Analyze this short video clip in its entirety — every frame, not just the first one. "
    "Choose the single moment that best represents the outfit, pose and scene, and return "
    "a structured description of THAT moment as if it were a single photograph, with these "
    "exact sections:\n\n"
    "FIGURES: [How many distinct people are in the frame — exactly one, or two or more. "
    "If two or more: describe each one's individual pose, position in the frame (e.g. "
    "'left figure', 'kneeling figure in front', 'figure standing behind'), and how they "
    "physically interact with each other — literal and specific, the same way PROPS & "
    "ACTIONS is described below. Do not describe any physical identity trait of the "
    "people themselves (no face, gender, hair, body-type details) — only count, position "
    "and physical interaction. Give each figure a short consistent label (e.g. 'left "
    "figure', 'right figure', 'kneeling figure') to be reused in OUTFIT/ACCESSORIES/BODY "
    "ART below. If only one person is present, write 'One figure.']\n\n"
    "OUTFIT: [Every garment as a standalone object — exact name, color with HEX code, fabric, "
    "cut, fit, coverage, embellishments, details. "
    "Describe the garment as if it exists independently — no wearer mentioned.]\n\n"
    "ACCESSORIES: [Every accessory as a standalone object — jewelry, footwear, headwear, bags, "
    "with color+HEX.]\n\n"
    "PROPS & ACTIONS: [Physical objects interacting directly with the subject's body — "
    "exact position, contact point, and action being performed. "
    "Be specific and literal: describe where the object is, how it contacts the body, and what is happening. "
    "Examples: 'single clear ice cube held between lips, partially inserted in mouth', "
    "'four translucent ice cubes stacked vertically on upper chest between collarbones, "
    "melting water running in rivulets down torso', "
    "'liquid dripping from chin onto chest'. "
    "If no props interact with the body: 'None.']\n\n"
    "BODY ART: [Any tattoos, henna, body paint, or decorative markings directly on the skin — "
    "pattern style, color(s) with HEX, exact placement and coverage area on the body (e.g. 'left forearm', "
    "'neck and collarbone', 'covering both shoulders and upper back'), line density and level of detail. "
    "Describe it as a standalone visual design, independent of the wearer. "
    "If no markings are present on the skin: 'None.']\n\n"
    "COLOR PALETTE: [Dominant HEX codes with label.]\n\n"
    "BACKGROUND: [Every distinct background element as a standalone object — furniture, wall decor, "
    "hanging or suspended objects, shelved or displayed items, architectural features, natural elements "
    "(plants, foliage, terrain, animals) — with approximate count or density where multiple similar "
    "elements repeat, for man-made scenes (e.g. 'approximately a dozen vintage clocks of varying sizes, "
    "mounted on the wall and suspended from the ceiling on cords') as well as organic/natural scenes "
    "(e.g. 'dense fern undergrowth filling the foreground, a dozen orchid clusters scattered through the "
    "mid-ground, three birds perched at different heights and depths'), color with HEX where relevant, "
    "and spatial layering (foreground/midground/background). Do not summarize repeated elements into a "
    "single category — enumerate their approximate quantity and variety.]\n\n"
    "LIGHTING: [Light source, direction, quality, color temperature, mood — 1-2 sentences.]\n\n"
    "CAMERA: [Framing. Describe how the subjects/garments are positioned in frame.]\n\n"
    "MOOD: [Overall atmosphere, color grade, cinematic style — 1 sentence.]\n\n"
    "Rules:\n"
    "— Describe garments and accessories as standalone objects\n"
    "— Be precise and detailed on fabrics, colors and environment\n"
    "— For PROPS & ACTIONS: describe physical contact and actions literally, not metaphorically\n"
    "— For BODY ART: describe only markings actually visible on the skin — do not confuse with printed "
    "patterns on garments (those belong in OUTFIT)\n"
    "— If FIGURES describes two or more people: within OUTFIT, ACCESSORIES and BODY ART, describe each "
    "figure's garments/accessories/markings SEPARATELY, labeled with the same short label used in FIGURES "
    "(e.g. 'Left figure: ... Right figure: ...') — never merge different figures' garments into one "
    "generic description. If FIGURES says 'One figure', describe these sections exactly as before, with "
    "no figure labeling.\n"
    "— If the clip shows deliberate motion (hair tossed, fabric swaying, a turn, a step), PROPS & ACTIONS "
    "or CAMERA may briefly note it, but the output must still describe ONE representative still moment — "
    "not a sequence of moments."
)

MAX_VIDEO_BYTES = 20 * 1024 * 1024  # 20MB — tetto reale di Telegram Bot API su getFile

gemini = GeminiClient()
server = HealthServer("VOGUE", VERSION)

# Notifica cambio API key — invia messaggio all'utente attivo
_active_cid: int | None = None

def _notify_key_use(key_num: int, call_count: int):
    if _active_cid:
        try:
            bot.send_message(_active_cid, f"🔑 <b>Key {key_num}</b> · call #{call_count}", parse_mode="HTML")
        except Exception:
            pass

gemini.on_key_use(_notify_key_use)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
pending_photo   = {}   # uid → bytes foto in attesa
pending_mode    = {}   # uid → "image" | "video" — scelta fatta su /start (Vogue 3.0)
last_prompt     = {}   # uid → ultimo prompt generato
pending_caption = {}   # uid → True se in attesa foto per /caption
_caption_timers = {}   # uid → threading.Timer — scade dopo 60s

_active_cid_lock = threading.Lock()
_active_cid: int | None = None

def _expire_caption(uid: int):
    """Callback del timer: rimuove il flag /caption scaduto."""
    if pending_caption.pop(uid, False):
        logger.info(f"⏱️ /caption scaduto per uid={uid}")

# --- ANALISI FOTO — usa analyze_scene() centralizzata da C_shared100 ---
def analyze_photo(img_bytes):
    """Wrapper su analyze_scene() — interfaccia invariata per il resto del bot."""
    result, err = analyze_scene(img_bytes, client=gemini)
    if result:
        return result, None
    return None, err or "⚠️ Analisi immagine non disponibile."

# --- ANALISI VIDEO — Vogue 3.0, isolata qui, NON in shared ---
def analyze_video(video_bytes: bytes, mime: str):
    """Stessa struttura di analyze_scene() (shared) — stessa classificazione errori
    503/429/SAFETY/API key/timeout — ma con _ANALYZE_PROMPT_VIDEO e mime del video invece
    che rilevato da detect_mime_type() (che riconosce solo formati immagine)."""
    if not gemini.available:
        return None, "⚠️ API key non configurata."
    try:
        video_part = genai_types.Part.from_bytes(data=video_bytes, mime_type=mime)
        logger.info(f"🎥 analyze_video: mime={mime} ({len(video_bytes)} bytes)")
        result = gemini.generate(_ANALYZE_PROMPT_VIDEO, contents=[video_part])
        if result:
            logger.info(f"✅ analyze_video: completato ({len(result)} chars)")
            return result, None
        return None, "⚠️ Nessuna risposta da Gemini (causa sconosciuta)."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ analyze_video: {err_text}")
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            if "503" in err_text or "unavailable" in err_text.lower():
                friendly = (
                    "❌ <b>Servizio Gemini non disponibile.</b>\n"
                    "Sovraccarico temporaneo. Riprova tra qualche minuto."
                )
            else:
                friendly = (
                    "❌ <b>Quota API esaurita.</b>\n"
                    "Le 20 richieste giornaliere di questa chiave sono finite.\n"
                    "Reset alle 08:00 ora Lisbona."
                )
        elif "SAFETY" in err_text or "SAFETY BLOCK" in err_text or "sconosciuto" in err_text:
            friendly = (
                "⚠️ <b>Video bloccato dai filtri Gemini.</b>\n"
                "Gemini rifiuta questo video (contenuto sensibile).\n"
                "Prova con un video diverso."
            )
        elif "API key" in err_text or "API_KEY" in err_text or "credentials" in err_text.lower():
            friendly = (
                "❌ <b>Errore chiave API.</b>\n"
                "La chiave Google non è valida o non è configurata correttamente."
            )
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            friendly = (
                "❌ <b>Timeout Gemini.</b>\n"
                "La risposta ha impiegato troppo tempo. Riprova tra qualche secondo."
            )
        else:
            friendly = f"❌ <b>Errore API Gemini:</b>\n<code>{err_text}</code>"
        return None, friendly

# --- COSTRUZIONE PROMPT ---
def build_prompt(scene_description):
    """Assembla il prompt completo con DNA Valeria + descrizione scena."""
    prompt = (
        f"{VALERIA_DNA}\n\n"
        f"{body_art_clause(scene_description)}"
        f"{multi_subject_clause(scene_description)}"
        f"--- SCENE REFERENCE ---\n"
        f"{scene_description}\n\n"
        f"--- GENERATION INSTRUCTIONS ---\n"
        f"Generate a single editorial photograph of the described subject in the scene above.\n"
        f"Preserve ALL outfit details, colors and fabrics exactly as described, with full fidelity.\n"
        f"The exact location and background from the scene reference above is the setting of the image.\n"
    )
    return prompt

# --- Vogue 4.0: da foto -> prompt VIDEO (movimento inventato) ---
def build_prompt_video(scene_description):
    """Stessa identica assemblazione di build_prompt() (DNA, body_art_clause(),
    multi_subject_clause(), SCENE REFERENCE) — cambiano solo le GENERATION INSTRUCTIONS
    finali: invece di una foto ferma, un breve video a scatto unico con un movimento
    cinematografico inventato coerente con la scena, libero di essere drammatico anche
    senza indizi espliciti nella foto originale (capelli, tessuti, un gesto, un passo) —
    nessuna durata specificata, decide Flow."""
    prompt = (
        f"{VALERIA_DNA}\n\n"
        f"{body_art_clause(scene_description)}"
        f"{multi_subject_clause(scene_description)}"
        f"--- SCENE REFERENCE ---\n"
        f"{scene_description}\n\n"
        f"--- GENERATION INSTRUCTIONS ---\n"
        f"Generate a single short video clip (single continuous shot, no cuts) of the described "
        f"subject in the scene above.\n"
        f"Invent a natural, cinematic movement coherent with the scene — the subject may walk, turn, "
        f"shift weight, reach toward something, or move in any way that fits the pose and setting "
        f"described above; hair, fabric, water, smoke or other elements present in the scene may move "
        f"or flow with the motion. The movement can be as dramatic or subtle as best fits the mood of "
        f"the scene, even without an explicit action described in the reference above.\n"
        f"Preserve ALL outfit details, colors and fabrics exactly as described, with full fidelity "
        f"throughout the motion.\n"
        f"The exact location and background from the scene reference above is the setting of the clip, "
        f"unchanged throughout.\n"
    )
    return prompt

# --- KEYBOARD POST-PROMPT ---
def get_after_prompt_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 Nuova foto", callback_data="vogue_new"),
        InlineKeyboardButton("🎥 Video",      callback_data="vogue_mode_video"),
    )
    markup.row(
        InlineKeyboardButton("🏠 Home", callback_data="vogue_home"),
    )
    return markup

# --- KEYBOARD SCELTA MODALITÀ (Vogue 3.0) ---
def get_mode_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📷 Immagine", callback_data="vogue_mode_image"),
        InlineKeyboardButton("🎥 Video", callback_data="vogue_mode_video"),
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
    pending_mode.pop(uid, None)
    last_prompt.pop(uid, None)
    gemini.reset_counters()  # azzera contatori call ad ogni /start
    logger.info(f"👠 /start da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>👠 VOGUE v{VERSION}</b>\n\n"
        f"Cosa mi mandi?",
        reply_markup=get_mode_keyboard()
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
    # Cancella eventuale timer precedente ancora attivo
    if uid in _caption_timers:
        _caption_timers[uid].cancel()
    pending_caption[uid] = True
    t = threading.Timer(60.0, _expire_caption, args=(uid,))
    t.daemon = True
    t.start()
    _caption_timers[uid] = t
    logger.info(f"📝 /caption da {m.from_user.username or m.from_user.first_name} (id={uid})")
    bot.send_message(m.chat.id, "📸 Inviami la foto per la caption. (60 secondi)")

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

    if data == "vogue_mode_image":
        pending_mode[uid] = "image"
        bot.send_message(cid, "📷 <b>Modalità Immagine.</b> Inviami una foto — genero un prompt VIDEO (movimento inventato), non una foto ferma.")

    elif data == "vogue_mode_video":
        pending_mode[uid] = "video"
        bot.send_message(cid,
            "🎥 <b>Modalità Video.</b> Inviami un video — max 20MB, clip brevi "
            "(pochi secondi) consigliate."
        )

    elif data == "vogue_new":
        last_prompt.pop(uid, None)
        bot.send_message(cid, "📸 Inviami una nuova foto." if pending_mode.get(uid) != "video" else "🎥 Inviami un nuovo video.")

    elif data == "vogue_home":
        last_prompt.pop(uid, None)
        pending_mode.pop(uid, None)
        bot.send_message(cid,
            f"<b>👠 VOGUE v{VERSION}</b>\n\nCosa mi mandi?",
            reply_markup=get_mode_keyboard()
        )

# --- HANDLER FOTO ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid} username={m.from_user.username}")
        return
    global _active_cid
    with _active_cid_lock:
        _active_cid = m.chat.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"📸 Foto ricevuta da {username} (id={uid})")

    # --- Vogue 3.0: controllo modalità (non si applica al flusso /caption, indipendente) ---
    if not pending_caption.get(uid, False):
        mode = pending_mode.get(uid)
        if mode is None:
            bot.send_message(m.chat.id, "⚠️ Usa /start e scegli prima Immagine o Video.")
            return
        if mode == "video":
            bot.send_message(m.chat.id, "⚠️ Hai scelto <b>Video</b> — inviami un video, oppure /start per cambiare modalità.")
            return

    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Errore download foto: {html.escape(str(e))}")
        return

    # --- flusso /caption ---
    if pending_caption.pop(uid, False):
        # Cancella il timer di scadenza — la foto è arrivata in tempo
        t = _caption_timers.pop(uid, None)
        if t:
            t.cancel()
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

    prompt = review_and_fix(build_prompt_video(scene_desc), gemini)
    last_prompt[uid] = prompt

    bot.send_message(m.chat.id, "✅ <b>Prompt Video Flow-ready</b> (da foto)\n\nCopia e incolla su Flow:")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=get_after_prompt_keyboard())
        else:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")


    logger.info(f"✅ Prompt generato per {username} ({len(prompt)} chars)")

# --- HANDLER VIDEO (Vogue 3.0) ---
@bot.message_handler(content_types=['video'])
def handle_video(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Video non autorizzato: uid={uid} username={m.from_user.username}")
        return
    global _active_cid
    with _active_cid_lock:
        _active_cid = m.chat.id
    username = m.from_user.username or m.from_user.first_name

    mode = pending_mode.get(uid)
    if mode is None:
        bot.send_message(m.chat.id, "⚠️ Usa /start e scegli prima Immagine o Video.")
        return
    if mode == "image":
        bot.send_message(m.chat.id, "⚠️ Hai scelto <b>Immagine</b> — inviami una foto, oppure /start per cambiare modalità.")
        return

    file_size = m.video.file_size or 0
    logger.info(f"🎥 Video ricevuto da {username} (id={uid}), {file_size} bytes dichiarati")
    if file_size > MAX_VIDEO_BYTES:
        bot.send_message(m.chat.id,
            f"❌ <b>Video troppo pesante.</b>\n"
            f"{file_size / 1024 / 1024:.1f}MB — il limite di Telegram per i bot è 20MB.\n"
            f"Prova con una clip più corta o più compressa."
        )
        return

    try:
        file_info = bot.get_file(m.video.file_id)
        video_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Errore download video: {html.escape(str(e))}")
        return

    mime = m.video.mime_type or "video/mp4"
    wait = bot.send_message(m.chat.id, "🎥 <b>Analizzo il video...</b>\n⏳ Può richiedere qualche secondo in più di una foto.")

    scene_desc, err = analyze_video(video_bytes, mime)

    try: bot.delete_message(m.chat.id, wait.message_id)
    except Exception: pass

    if not scene_desc:
        bot.send_message(m.chat.id, err or "❌ Analisi fallita. Riprova.", parse_mode="HTML")
        return

    prompt = review_and_fix(build_prompt(scene_desc), gemini)
    last_prompt[uid] = prompt

    bot.send_message(m.chat.id, "✅ <b>Prompt Flow-ready</b> (da video)\n\nCopia e incolla su Flow:")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=get_after_prompt_keyboard())
        else:
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

    logger.info(f"✅ Prompt generato da video per {username} ({len(prompt)} chars)")

# --- HANDLER TESTO ---
@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text and m.text.startswith('/'):
        return
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Testo non autorizzato: uid={uid} username={m.from_user.username}")
        return
    global _active_cid
    with _active_cid_lock:
        _active_cid = m.chat.id
    text = m.text.strip()
    wait = bot.send_message(m.chat.id, "🚀 <b>Generazione in corso...</b>\n⏳ Attendi qualche secondo.")
    text = sanitize_user_input(text, gemini)
    prompt = review_and_fix(build_prompt(f"SCENE DESCRIBED BY USER:\n{text}"), gemini)
    last_prompt[uid] = prompt
    try:
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception:
        pass
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

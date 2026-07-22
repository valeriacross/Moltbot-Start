"""
C_shared100.py — Valeria Cross AI · Oggetti comuni a tutti i bot
Versione: 2.4.3

REGOLA: questo file si aggiorna SEMPRE in-place con lo stesso nome C_shared100.py.
Non rinominare mai in C_shared101.py o simili — tutti i bot importano da C_shared100.

CHANGELOG 2.4.3 (22/07/2026):
  - Il fix 2.4.2 sul campo BACKGROUND aveva un solo esempio illustrativo
    ("e.g. 'approximately a dozen vintage clocks...'"), specifico dello
    scenario di test (stanza tea-party con orologi) usato per diagnosticare
    il problema — a differenza di OUTFIT, che non ha esempi e resta
    puramente definizionale. Walter ha chiesto se il fix generalizza a
    scene non fatte di oggetti discreti (es. una giungla) — risposta: il
    meccanismo sì (nessun riferimento hardcoded al caso specifico), ma
    l'unico esempio presente era sbilanciato verso scene "da collezione di
    oggetti", rischio concreto di bias sottile su scene organiche. Aggiunto
    un secondo esempio parallelo per contenuto naturale/organico (fogliame,
    fauna) accanto a quello originale per contenuto man-made, così
    l'istruzione resta domain-agnostic invece di implicitamente orientata
    verso interni con oggetti numerabili. Non ancora testato in produzione
    su nessuno dei due tipi di scena.

CHANGELOG 2.4.2 (22/07/2026):
  - Campo BACKGROUND di _ANALYZE_PROMPT era una singola riga generica
    ("Exact location, architecture, surfaces, props, environment — be
    specific"), l'unico campo del prompt di analisi senza richiesta di
    enumerazione oggetto-per-oggetto — a differenza di OUTFIT/ACCESSORIES/
    BODY ART/PROPS & ACTIONS, tutti esplicitamente "every X as a standalone
    object" con HEX. Causa trovata confrontando un mosaico Atelier reale
    con la foto originale (Walter, sfondo tea-party surrealista denso di
    orologi/lanterne/porcellane sospese): l'analisi generata riassumeva
    tutto in poche frasi di categoria ("shelves packed with...", "numerous
    vintage clocks...") invece di elencare quantità/densità reali — nessun
    lock in fase di generazione può recuperare un dettaglio mai catturato
    nel testo. Riscritto BACKGROUND con lo stesso trattamento esaustivo di
    OUTFIT: enumerazione per oggetto, conteggio/densità approssimativa per
    elementi ripetuti, HEX dove rilevante, profondità spaziale
    (foreground/midground/background). Vedi anche Atelier 2.5.2 per la
    seconda metà del fix (BACKGROUND LOCK lato generazione).
    Non ancora testato in produzione.

CHANGELOG 2.4.1 (22/07/2026):
  - VALERIA_FACE conteneva descrizioni hardcoded di occhiali ("Thin octagonal
    Vogue Havana dark tortoiseshell frame") e barba ("approximately 6-7cm,
    perfectly groomed, dense and uniform") che confermate in contraddizione
    diretta con la foto di riferimento reale che Walter allega di volta in
    volta al prompt in Flow (occhiali rotondi/spessi/scuri nella foto vs.
    ottagonali/sottili/tartarugato nel testo; barba visibilmente più lunga e
    meno uniforme nella foto vs. 6-7cm curata nel testo). Su conferma
    esplicita di Walter, la foto allegata è sempre autorevole su questi due
    punti — il testo non deve più specificare forma/lunghezza, deve rimandare
    alla foto. Aggiunta anche una riga di priorità esplicita in apertura del
    blocco ("the photo wins" in caso di conflitto) — prima non esisteva
    alcun riferimento testuale all'immagine allegata, il modello non aveva
    modo di sapere che la foto va trattata come autorità sopra il testo.
    Non toccato: sezione Hair (nessuna contraddizione accertata, solo un
    dubbio dovuto a una foto di riferimento particolarmente ventosa) e
    VALERIA_BODY_STRONG/SAFE (fuori scope, non discussi in questa sessione).

    Il fix su VALERIA_FACE da solo era inutile: review_and_fix() (usata da
    Vogue 2x e Atelier 3x, ultimo step prima di Flow) e sanitize_user_input()
    (usata da Vogue sul testo utente) avevano la STESSA specifica hardcoded
    ("thin octagonal Vogue Havana dark tortoiseshell", "beard 6-7cm") in
    punti indipendenti — regola 2 (GLASSES MANDATORY) e regola 4 (SUBJECT
    BLEED) di review_and_fix(), più la lista "IMMUTABLE traits" di
    sanitize_user_input(). Reiniettavano la vecchia specifica anche dopo la
    correzione di VALERIA_FACE. Corrette anche queste tre, stessa logica di
    rimando alla foto allegata. Non toccati in questa sessione (su richiesta
    esplicita di Walter, rimandati): i 3 blocchi "IDENTITY LOCK" locali di
    Atelier (build_full_prompt, build_shooting_prompt singolo e mosaico) con
    lo stesso testo "tortoiseshell glasses" hardcoded indipendentemente da
    shared — stesso fix, stessa sessione di lavoro del 17/07 che ha
    introdotto quei blocchi. TODO aperto per la prossima sessione. WALTER_DNA
    in Surprise (feature Pride) e il testo LEGO in Filtro: esplicitamente
    fuori scope, Walter non usa questi due bot al momento.

    Ipotesi di lavoro, non certezza: questo fix riduce ma non elimina la
    percentuale di generazioni che ignorano il volto — resta un limite
    architetturale del modello (sampling probabilistico), non risolvibile
    al 100% solo col prompt.

CHANGELOG 2.4.0 (17/07/2026):
  - Fix generale, non un patch puntuale. Verificato sulla documentazione
    ufficiale Google Cloud (prompting guide Nano Banana) che il modello
    dietro Flow NON ha un campo negativePrompt indipendente — architettura
    multimodale end-to-end, non diffusion con sottrazione vettoriale come
    Stable Diffusion/Midjourney/Imagen. Google raccomanda esplicitamente
    "positive framing, not negative" per questo modello. Causa scatenante:
    HAIR LOCK v2.0.7 e v2.0.8 su Atelier (basati su negative prompt, vedi
    HANDOFF) non hanno retto a test successivi — calvizie ricomparsa
    nonostante due round di negative prompt via via più estesi. Rimosso
    l'intero meccanismo negative prompt dall'impianto DNA condiviso:
    VALERIA_FACE e VALERIA_BODY_STRONG/SAFE riscritte in positivo puro
    (tolte le frasi "DO NOT shave it", "DO NOT GENERATE A MALE PHYSIQUE",
    ecc. — il contenuto informativo resta identico, cambia solo il framing).
    VALERIA_NEGATIVE eliminata interamente (era usata da Vogue via
    VALERIA_DNA e 3 volte in Surprise) — le due garanzie generiche che
    portava (mani corrette, nessun testo sovrapposto) spostate in positivo
    dentro VALERIA_DNA. review_and_fix(): punto 3 (scansione sezione
    negative) rimosso perché non più applicabile; punto 8 (BODY HAIR
    ENFORCEMENT) riscritto per richiedere solo l'affermazione positiva,
    tolta la riga che reiniettava "NEGATIVE PROMPT — BODY" nel testo
    finale — prima questo passaggio avrebbe vanificato qualunque pulizia
    fatta a monte nei singoli bot, dato che è l'ultimo step prima
    dell'invio a Flow. Vogue (203) e Surprise (203) aggiornati in
    parallelo per rimuovere i loro negative prompt locali — vedi
    changelog di ciascun bot. Atelier (209, sessione precedente) già
    allineato. Filtro (202) aveva import morti di VALERIA_FACE/BODY_STRONG/
    BODY_SAFE/NEGATIVE mai usati nei suoi prompt (confermato via grep —
    Filtro non inietta mai il DNA Valeria), ma aveva 3 negative prompt
    locali propri (editorial underwater, LEGO, wrapper "DO NOT ALTER")
    non collegati al DNA — corretti anche quelli nello stesso giro.
    Vedi HANDOFF sezione 2septendecies per il dettaglio completo.

CHANGELOG 2.3.18 (08/07/2026):
  - Risolto: la clausola "BODY ART EXCEPTION" (2.3.17) compariva in OGNI
    prompt generato da tutti i bot, anche con BODY ART: None — testo
    condizionale inerte nel caso comune. Analisi bot-per-bot (non assunta)
    ha rivelato che solo Vogue e Atelier passano davvero da analyze_scene()
    con un campo BODY ART ispezionabile; Filtro ha import morti (VALERIA_DNA
    mai usato nei suoi prompt); Surprise non analizza mai una foto di
    riferimento (clausola sempre morta lì, si risolve gratis); Architect fa
    analisi+scrittura in un'unica chiamata Gemini, senza produrre un campo
    esterno da controllare — non può avere una versione condizionale.
    Rimossa la clausola da VALERIA_BODY_STRONG/SAFE (tornano alla forma
    pre-2.3.17). Aggiunta BODY_ART_EXCEPTION_TEXT (stesso testo, costante
    isolata) e body_art_clause(scene_description) — quest'ultima restituisce
    il testo solo se BODY ART nella scena non è "None"/assente, altrimenti
    stringa vuota. Vogue e Atelier chiamano body_art_clause() dopo
    l'identità. Architect, su scelta esplicita di Walter, concatena
    BODY_ART_EXCEPTION_TEXT direttamente e sempre — stesso comportamento
    che aveva dal 07/07, solo spostato da VALERIA_BODY_STRONG a questa
    costante dedicata (compensazione necessaria per non perdere la
    capacità di preservare body art lì come effetto collaterale di questo
    fix, dato che Architect condivide VALERIA_DNA con Vogue). Filtro e
    Surprise non toccati — non ne avevano bisogno.

CHANGELOG 2.3.17 (07/07/2026):
  - Step 2/2 concordato con Walter dopo test su Atelier con foto di riferimento
    a body art elaborato (vedi HANDOFF sezione 2sexies/2septies). Aggiunto
    campo "BODY ART" a _ANALYZE_PROMPT (dopo PROPS & ACTIONS) — cattura
    tatuaggi/body paint/decorazioni sulla pelle come design visivo standalone,
    con fallback esplicito 'None.' se assenti (stesso pattern di PROPS &
    ACTIONS). Aggiunta clausola "BODY ART EXCEPTION — CONDITIONAL" sia a
    VALERIA_BODY_STRONG che VALERIA_BODY_SAFE: se la scena descrive body art,
    questo sostituisce "smooth porcelain skin" SOLO sulle zone indicate;
    altrimenti la pelle resta liscia ovunque come da default — nessuna
    invenzione di tatuaggi non descritti. Tocca tutti e 5 i bot (tutti
    importano VALERIA_DNA e/o build_valeria_identity, verificato via grep).
    Nessuna modifica a _ANALYZE_PROMPT oltre l'aggiunta del campo — ordine
    delle altre sezioni invariato. Nessun termine body-art nel NEGATIVE
    prompt esistente, quindi nessun conflitto da rimuovere.

CHANGELOG 2.3.16 (04/07/2026):
  - MODEL: "gemini-3-flash-preview" → "gemini-3.5-flash". Motivo: 503 diffusi
    su tutti i bot nonostante il retry/rotazione chiavi già presente in
    generate() — riconducibile al fatto che gemini-3-flash-preview è
    modello preview, con limiti di capacità/priorità più severi per
    definizione rispetto ai modelli GA (fonte: pagina ufficiale deprecation
    Google, che raccomanda esplicitamente la migrazione a gemini-3.5-flash).
    gemini-3.5-flash è GA/stabile, costa 3x il preview attuale ma non ha
    le restrizioni di capacità del livello preview. Scelta di Valeria tra
    gemini-3.5-flash (qualità superiore) e gemini-3.1-flash-lite (più
    economico, alto volume) — se emergono limiti (costo o rate limit) il
    piano di fallback concordato è passare a gemini-3.1-flash-lite o
    tornare a gemini-3-flash-preview. Nessun'altra occorrenza del vecchio
    nome modello nel file (verificato via grep) — tutti i bot ereditano
    MODEL da qui, nessuna modifica ai singoli bot in questo cambio.
    NOTA: i comandi /info di Vogue (MODEL_TEXT), Filtro (MODEL_TEXT_ID),
    Architect/Atelier/Surprise (stringa inline) mostrano ancora
    "gemini-3-flash-preview" in chat — sono costanti locali ai singoli
    bot, non lette da qui, quindi restano disallineate finché non
    vengono aggiornate separatamente nei singoli file bot.

CHANGELOG 2.3.15 (01/07/2026):
  - Solo pulizia documentale, nessuna modifica funzionale. Corretto commento
    obsoleto in _schedule_daily_reset(): il docstring riportava ancora
    "08:00 UTC (= 09:00 Lisbona estate)", residuo del fix 2.3.11 mai
    aggiornato dopo che il codice era stato corretto a hour=7 (07:00 UTC
    = 08:00 Lisbona estate). Il comportamento a runtime non cambia — era
    solo il commento a essere disallineato dal codice reale.

CHANGELOG 2.3.14 (25/06/2026):
  - GeminiClient: aggiunta GOOGLE_API_KEY_5 alla lista variabili d'ambiente.
    Atelier passa da 4 a 5 chiavi (una spostata da Architect, che ora ne ha 1).
    Architect non modificato — GeminiClient usa automaticamente solo le chiavi
    effettivamente presenti nell'environment.

CHANGELOG 2.3.13 (25/06/2026):
  - _ANALYZE_PROMPT: aggiunto campo PROPS & ACTIONS dopo ACCESSORIES.
    Cattura oggetti fisici in contatto diretto col corpo del soggetto (posizione,
    punto di contatto, azione). Prima, prop interattivi come "ice cube held between
    lips" venivano ignorati o descritti vagamente in BACKGROUND — causando prompt
    Atelier privi degli elementi scenici più forti dell'immagine originale.
    Nessuna altra modifica alla pipeline: protezione NSFW (analisi testuale mediata,
    senza visione diretta dell'immagine nei passaggi successivi) invariata.

CHANGELOG 2.3.12 (20/06/2026):
  - Fix robustezza GeminiCounterReset: datetime.utcnow() (deprecato) sostituito con
    datetime.now(timezone.utc). _reset_loop() ora avvolto in try/except — prima,
    una qualsiasi eccezione interna terminava il thread di reset giornaliero per
    sempre, in modo silenzioso, senza log e senza che i contatori si azzerassero più.

CHANGELOG 2.2.0 (31/05/2026):
  - GeminiClient: property current_key_num (1-based) e metodo on_key_rotation(callback).
    Permette ai bot di ricevere notifica immediata del cambio chiave API.

CHANGELOG 2.0.0 (26/05/2026):
  - Fix critico in review_and_fix(): client._model → MODEL.
    GeminiClient non espone _model come attributo pubblico.
    Causava crash silenzioso su tutti i bot che usano review_and_fix.

CHANGELOG 1.8.0 (25/05/2026):
  - Classificazione errore 503 UNAVAILABLE in analyze_scene(), generate_caption(),
    generate_mini_caption(), generate_mini_prompt() e tutti i classificatori.
    Messaggio differenziato: 503 → "Servizio non disponibile, riprova",
    429 → "Quota esaurita, reset 08:00".

CHANGELOG 1.7.0 (25/05/2026):
  - sanitize_user_input(text, client): pre-processa testo utente rimuovendo
    elementi incompatibili con DNA Valeria. Usata da Vogue e Architect.

CHANGELOG 1.6.0 (25/05/2026):
  - review_and_fix(prompt, client): revisione contraddizioni DNA (capelli, occhiali,
    body hair, watermark, subject bleed). Usata da Vogue, Architect e Atelier.

CHANGELOG 1.5.0 (24/05/2026):
  - generate_mini_prompt(text, client): estrae dal prompt Flow un mini-prompt
    strutturato formato Nosurprise (Location/Sky/Outfit/Style/Pose/Mood/Body).

CHANGELOG 1.4.0 (24/05/2026):
  - generate_mini_caption(text, client): genera caption da testo prompt,
    5 emoji + frase no-gender. Usata da Vogue, Architect, Atelier, Nosurprise/Pride.

CHANGELOG 1.3.0 (11/05/2026):
  - CaptionGenerator.extract_caption(): filtro ragionamento interno Gemini.

CHANGELOG 1.2.0 (10/05/2026):
  - GeminiClient.generate(): finish_reason reale su risposta vuota.
  - analyze_scene(): classificazione errori 429/SAFETY/timeout/generico.

CHANGELOG 1.1.0 (10/05/2026):
  - detect_mime_type(): JPEG/PNG/WebP da magic bytes.
  - SHARED_VERSION e SHARED_DATE esportate.

CHANGELOG 1.0.x (09/05/2026):
  - Versioni iniziali: GeminiClient, HealthServer, analyze_scene(),
    generate_caption(), CaptionGenerator, VALERIA_DNA, EDITORIAL_WRAPPER.
"""

import os, html, logging, threading, flask, re
from google import genai
from google.genai import types as genai_types

# Esportati per uso nei bot
__all__ = [
    'GeminiClient', 'CaptionGenerator', 'HealthServer', 'is_allowed',
    'VALERIA_FACE', 'VALERIA_BODY_STRONG', 'VALERIA_BODY_SAFE',
    'VALERIA_WATERMARK',
    'VALERIA_DNA', 'EDITORIAL_WRAPPER',
    'build_valeria_identity', 'generate_caption', 'generate_mini_caption', 'generate_mini_prompt',
    'review_and_fix', 'sanitize_user_input',
    'analyze_scene', 'genai_types', 'MODEL', 'detect_mime_type', 'is_allowed',
    'SHARED_VERSION', 'SHARED_DATE',
]

logger = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash"

# Versione
VERSION = "2.4.3"
SHARED_VERSION = "2.4.3"   # aggiornare ad ogni modifica
SHARED_DATE    = "22/07/2026"  # aggiornare ad ogni modifica

logger.info(f"📦 C_shared100.py v{VERSION} ({SHARED_DATE}) caricato — MODEL={MODEL}")

# ============================================================
# WHITELIST — SICUREZZA
# ============================================================

def _load_allowed() -> set[int]:
    """
    Carica la whitelist da env ALLOWED_USERS (CSV di user ID interi).
    Fallback hardcoded: solo Walter Caponi (273003890).
    """
    raw = os.environ.get("ALLOWED_USERS", "273003890")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

_ALLOWED_USERS: set[int] = _load_allowed()

def is_allowed(uid: int) -> bool:
    """Ritorna True se l'utente è in whitelist. Loggare i tentativi non autorizzati nel bot."""
    return uid in _ALLOWED_USERS

# ============================================================
# VALERIA CROSS — DNA IDENTITÀ
# ============================================================

VALERIA_FACE = (
    "**⚠️ FACE IDENTITY LOCK — ABSOLUTE PRIORITY:** The attached reference photo shows the exact face "
    "to reproduce. The reference photo is authoritative for the face, eyeglasses and beard — if anything "
    "below conflicts with it, the photo wins.\n"
    "60-year-old Italian male face, oval-rectangular shape. "
    "Ultra-detailed mature skin with visible pores, deep character wrinkles, crow's feet. "
    "Calm half-smile, no teeth shown.\n"
    "**Eyeglasses:** Exactly as shown in the attached reference photo — same shape, color and frame "
    "thickness. Always present.\n"
    "**Hair:** Short silver-grey Italian cut, slightly voluminous top, nape exposed.\n"
    "**⚠️ BEARD — MANDATORY — NON-NEGOTIABLE:** Exactly as shown in the attached reference photo — same "
    "length, density, texture and shape, clearly visible in every shot. The beard is a permanent part of "
    "the identity lock, matching the reference image precisely.\n"
    "**Rendering:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200.\n\n"
)

VALERIA_BODY_STRONG = (
    "**MANDATORY BODY — FEMININE SILHOUETTE, HELD EXACTLY AS DESCRIBED:**\n"
    "**Feminine hourglass proportions, 180cm, 85kg. FULL D-CUP BUST — prominent, natural, clearly visible. "
    "Wide rounded hips, defined waist, full thighs.**\n"
    "Completely smooth, hairless skin on the torso, arms and legs. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE — CRITICAL:** The silver-grey beard on the face and the feminine body coexist "
    "together in the same image, exactly as described — the beard stays exactly as specified above, "
    "the body stays exactly as specified here, both simultaneously, unchanged.\n\n"
)

VALERIA_BODY_SAFE = (
    "**MANDATORY BODY — FEMININE SILHOUETTE, HELD EXACTLY AS DESCRIBED:**\n"
    "**Feminine hourglass silhouette, 180cm, 85kg. Soft feminine proportions — defined waist, "
    "wide rounded hips, full figure.**\n"
    "Completely smooth, hairless skin on the torso, arms and legs. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE — CRITICAL:** The silver-grey beard on the face and the feminine body coexist "
    "together in the same image, exactly as described — the beard stays exactly as specified above, "
    "the body stays exactly as specified here, both simultaneously, unchanged.\n\n"
)

VALERIA_WATERMARK = "feat. Valeria Cross 👠"

# BODY ART EXCEPTION — introdotta in 2.3.17, spostata fuori dai blocchi BODY
# statici in 2.3.18. Testo unico condiviso, usato in due modi diversi:
# 1) SEMPRE presente in Architect (che non ha un campo BODY ART esterno da
#    controllare — analisi e scrittura avvengono in un'unica chiamata Gemini,
#    senza produrre un testo intermedio ispezionabile). Architect importa
#    questa costante e la concatena direttamente dopo VALERIA_DNA.
# 2) CONDIZIONALMENTE presente in Vogue e Atelier tramite body_art_clause()
#    sotto — questi bot passano da analyze_scene(), che produce un vero
#    campo "BODY ART: ..." da poter ispezionare prima di decidere se la
#    clausola serve o è testo morto (caso comune: BODY ART: None).
BODY_ART_EXCEPTION_TEXT = (
    "**⚠️ BODY ART EXCEPTION — CONDITIONAL:** If the scene reference includes a BODY ART section describing "
    "tattoos, body paint or decorative skin markings, these OVERRIDE 'smooth porcelain skin' ONLY on the "
    "areas described — reproduce the pattern, colors and placement exactly as given. Skin NOT covered by "
    "described markings stays smooth and porcelain as specified above. If BODY ART states 'None' or is "
    "absent, skin remains fully smooth and unmarked everywhere — do NOT invent tattoos or markings that "
    "were not explicitly described.\n\n"
)

def body_art_clause(scene_description: str) -> str:
    """Restituisce BODY_ART_EXCEPTION_TEXT SOLO se scene_description contiene
    un campo BODY ART con contenuto reale (non 'None'/assente) — altrimenti
    stringa vuota, per non appesantire il prompt nel caso comune (nessun
    tatuaggio nella foto). Usare dopo l'identità (VALERIA_DNA o
    build_valeria_identity()) nei bot che passano da analyze_scene()
    (Vogue, Atelier). NON usare in Architect — vedi nota sopra."""
    if not scene_description:
        return ""
    m = re.search(r'BODY ART:\s*(.+?)(?:\n\n|\Z)', scene_description, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    val = m.group(1).strip()
    if not val or val.lower().startswith("none"):
        return ""
    return BODY_ART_EXCEPTION_TEXT

# DNA completo assemblato — usato da Vogue. NOTA 2.4.0: Architect non lo
# usa più dalla riscrittura v3.0.0 (10/07) — nessun DNA, analisi pura del
# soggetto reale. Il commento precedente ("usato da Vogue e Architect") era
# rimasto stale da prima di quella riscrittura, corretto qui. NOTA 2.3.18:
# non include più BODY_ART_EXCEPTION_TEXT (era qui via VALERIA_BODY_STRONG
# fino alla 2.3.17). Vogue aggiunge body_art_clause(scene_description) dopo
# questa costante. NOTA 2.4.0: rimossa la riga "NEGATIVE: {VALERIA_NEGATIVE}"
# — VALERIA_NEGATIVE eliminata (vedi sezione 2septendecies in HANDOFF: il
# modello dietro Flow non ha un campo negativePrompt indipendente, la guida
# ufficiale Google raccomanda framing solo positivo). Le due garanzie generiche
# che VALERIA_NEGATIVE portava (mani anatomicamente corrette, nessun testo
# sovrapposto oltre al watermark) sono ora espresse in positivo qui sotto.
VALERIA_DNA = (
    f"{VALERIA_FACE}"
    f"{VALERIA_BODY_STRONG}"
    f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
    f"The output is a single photorealistic image. Hands are anatomically correct, five fingers each. "
    f"No text appears anywhere in the image beyond the watermark specified above.\n"
)

# Wrapper editoriale — apre tutti i prompt di Atelier
EDITORIAL_WRAPPER = (
    "This is a professional editorial post-production request for a high-fashion photography project. "
    "Generate a new original image of the described subject in the specified scene, "
    "maintaining the subject's identity and physical characteristics. "
    "This is a legitimate creative and commercial photography workflow. "
)


def build_valeria_identity(safe: bool = False) -> str:
    """Assembla FACE + BODY (strong o safe) — usato da Atelier nei prompt."""
    body = VALERIA_BODY_SAFE if safe else VALERIA_BODY_STRONG
    return VALERIA_FACE + body

# ============================================================
# GENERATE_CAPTION — CAPTION SOCIAL UNIFICATA
# ============================================================

def detect_mime_type(img_bytes: bytes) -> str:
    """Rileva il mime type reale dai magic bytes — evita errori con PNG/WebP passati come JPEG."""
    if img_bytes[:4] == b'\x89PNG':
        return "image/png"
    if len(img_bytes) >= 12 and img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
        return "image/webp"
    return "image/jpeg"  # default — JPEG inizia con \xFF\xD8\xFF


def generate_caption(img_bytes: bytes, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Genera una caption social dall'immagine — usata da Vogue, Architect e Atelier.
    Output: 5 emoji + frase di 5/10 parole in inglese. Nessun riferimento al DNA Valeria.
    Returns: (caption, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."
    try:
        mime = detect_mime_type(img_bytes)
        logger.info(f"📸 generate_caption: mime={mime} ({len(img_bytes)} bytes)")
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
        prompt = (
            "Look at this image and write a short social media caption in English.\n"
            "Format: exactly 5 relevant emojis followed by a phrase of 5 to 10 words.\n"
            "The emojis come first, all together, then the words.\n"
            "Focus only on: location, outfit, colors, atmosphere, mood.\n"
            "Do NOT mention any person, nationality, age or gender.\n"
            "Example: ✨🖤👗🌙📸 Dark elegance in every carefully chosen detail.\n"
            "Output ONLY the caption on a single line — no explanations, no quotes, no extra text."
        )
        result = client.generate(prompt, contents=[img_part])
        if result:
            cleaned = CaptionGenerator.extract_caption(result) or result.strip()
            return cleaned, None
        return None, "⚠️ Nessuna risposta da Gemini (causa sconosciuta)."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ generate_caption(): {err_text}", exc_info=True)
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            return None, ("❌ <b>Servizio Gemini non disponibile.</b> Sovraccarico temporaneo. Riprova tra qualche minuto." if "503" in err_text or "unavailable" in err_text.lower() else "❌ <b>Quota API esaurita.</b> Reset alle 08:00 ora Lisbona.")
        elif "SAFETY" in err_text:
            return None, "❌ <b>Safety block di Gemini.</b> Prova con un'immagine diversa."
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            return None, "❌ <b>Timeout Gemini.</b> Riprova tra qualche secondo."
        else:
            return None, f"❌ <b>Errore caption:</b>\n<code>{err_text}</code>"


def generate_mini_caption(text: str, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Genera una mini caption social da un testo (prompt Flow, descrizione scena, scenario).
    Output: 5 emoji + frase di 5/10 parole in inglese. No gender, no DNA Valeria.
    Usata da Vogue, Architect, Atelier come caption alternativa testuale al prompt Flow.
    Returns: (caption, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."
    try:
        prompt = (
            "Read the following image generation prompt and extract its visual essence.\n"
            "Write a short social media caption in English.\n"
            "Format: exactly 5 relevant emojis followed by a phrase of 5 to 10 words.\n"
            "The emojis come first, all together, then the words.\n"
            "Focus only on: location, outfit, colors, atmosphere, mood, artistic style.\n"
            "Do NOT mention any person, name, nationality, age or gender.\n"
            "Do NOT reference the fact that this is an AI prompt.\n"
            "Example: ✨🖤👗🌙📸 Dark elegance in every carefully chosen detail.\n"
            "Output ONLY the caption on a single line — no explanations, no quotes.\n\n"
            f"PROMPT:\n{text[:2000]}"
        )
        logger.info("📝 generate_mini_caption: chiamata API testo")
        result = client.generate(prompt)
        if result:
            cleaned = CaptionGenerator.extract_caption(result) or result.strip()
            return cleaned, None
        return None, "⚠️ Nessuna risposta da Gemini."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ generate_mini_caption(): {err_text}", exc_info=True)
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            return None, ("❌ <b>Servizio Gemini non disponibile.</b> Sovraccarico temporaneo. Riprova tra qualche minuto." if "503" in err_text or "unavailable" in err_text.lower() else "❌ <b>Quota API esaurita.</b> Reset alle 08:00 ora Lisbona.")
        elif "SAFETY" in err_text:
            return None, "❌ <b>Safety block di Gemini.</b> Riprova."
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            return None, "❌ <b>Timeout Gemini.</b> Riprova tra qualche secondo."
        else:
            return None, f"❌ <b>Errore mini caption:</b>\n<code>{err_text}</code>"


def generate_mini_prompt(text: str, client=None) -> tuple:
    """
    Estrae dal prompt Flow un mini-prompt strutturato — stesso schema di Nosurprise format_scenario.
    Parser locale: zero chiamate Gemini. Estrae sezioni dal testo del prompt.
    Returns: (mini_prompt, error)
    """
    import re as _re

    def _extract(patterns, default='[not specified]'):
        for pattern in patterns:
            m = _re.search(pattern, text, _re.IGNORECASE)
            if m:
                val = m.group(1).strip().strip('.-–—*')
                if len(val) > 4:
                    return val[:120]
        return default

    try:
        location = _extract([
            r'(?:Scene|Location|Setting|Environment)[:\s—-]+([^\n]{10,})',
            r'(?:LOCATION|SCENE)[:\s—-]+([^\n]{10,})',
        ])
        if len(location) > 80:
            location = location.split(',')[0].strip()[:80]

        sky = _extract([
            r'(?:Lighting(?:\s+and\s+camera)?|Sky|Light(?:ing)?|Time of day)[:\s—-]+([^\n]{5,})',
            r'(?:LIGHTING|SKY)[:\s—-]+([^\n]{5,})',
        ])

        outfit = _extract([
            r'(?:Outfit|Clothing|Garments?)[:\s—-]+([^\n]{10,})',
            r'(?:OUTFIT)[:\s—-]+([^\n]{10,})',
            r'(?:wearing|dressed in)\s+([^\n]{10,})',
        ])

        style = _extract([
            r'(?:Style|Photographic style|Rendering)[:\s—-]+([^\n]{5,})',
            r'(?:STYLE|RENDERING)[:\s—-]+([^\n]{5,})',
            r'((?:cinematic|editorial|fashion|documentary|portrait)\s+[^\n]{5,})',
        ])

        pose = _extract([
            r'(?:Pose|Position|Framing|Camera angle)[:\s—-]+([^\n]{5,})',
            r'(?:POSE|COMPOSITION)[:\s—-]+([^\n]{5,})',
        ])

        mood = _extract([
            r'(?:Mood|Atmosphere|Emotional\s+tone)[:\s—-]+([^\n]{5,})',
            r'(?:MOOD|ATMOSPHERE)[:\s—-]+([^\n]{5,})',
        ])

        body = _extract([
            r'(?:Subject\s+body|Body|Physical\s+description)[:\s—-]+([^\n]{5,})',
            r'(?:BODY|SUBJECT BODY)[:\s—-]+([^\n]{5,})',
        ])

        result = (
            f"📍 <b>Location:</b> {location}\n"
            f"🌤 <b>Sky:</b> {sky}\n"
            f"👗 <b>Outfit:</b> {outfit}\n"
            f"🎨 <b>Style:</b> {style}\n"
            f"💃 <b>Pose:</b> {pose}\n"
            f"✨ <b>Mood:</b> {mood}\n"
            f"🏛 <b>Body:</b> {body}"
        )
        return result, None

    except Exception as e:
        return None, f"❌ <b>Errore mini prompt:</b> <code>{str(e)}</code>"


def review_and_fix(prompt: str, client: 'GeminiClient') -> str:
    """
    Revisione e correzione contraddizioni nel prompt generato.
    Corregge capelli, occhiali, body hair, watermark, subject bleed.
    In caso di errore ritorna il prompt originale invariato.
    """
    try:
        review_instr = (
            "You are a prompt quality reviewer. Carefully read the following image generation prompt "
            "and fix ALL contradictions, inconsistencies and conflicts. Return ONLY the corrected prompt, "
            "no explanations, no preamble.\n\n"
            "MANDATORY FIXES — apply all of these:\n\n"
            "1. HAIR: Valeria Cross has SHORT silver/grey hair (sides 1-2cm, top max 15cm, nape exposed). "
            "Remove or replace ANY mention of: long hair, brown hair, dark hair, black hair, curly hair, "
            "flowing hair, loose waves, slicked back long hair, wet long hair, hair falling on shoulders, "
            "hair spread around head, hair fanned out, dark flowing locks, wavy dark hair, hair against background. "
            "Replace with: short silver Italian cut, slightly voluminous top, nape exposed.\n\n"
            "2. GLASSES MANDATORY: Valeria Cross ALWAYS wears eyeglasses, exactly as shown in the attached "
            "reference photo. If the prompt does NOT mention glasses or eyeglasses, ADD this phrase in the "
            "Facial identity section: 'eyeglasses exactly as shown in the attached reference photo "
            "(MANDATORY, always present)'. Also ensure 'no glasses' does NOT appear anywhere in the prompt.\n\n"
            "2b. GLASSES POSE REMOVAL: Remove ANY description of hands or fingers touching, adjusting, holding or "
            "raising to the glasses or temple area. The glasses are simply worn — no hand interaction with them.\n\n"
            "3. MIRROR SELFIE RULE: ONLY if the prompt explicitly contains 'mirror selfie' or both 'selfie' AND 'mirror' together — "
            "then smartphone held in hand IS a required prop. "
            "Do NOT add smartphone for decorative mirrors, antique mirrors, historical scenes, artistic reflections, "
            "or any mirror that is not a selfie context.\n\n"
            "4. SUBJECT BLEED: Remove any physical description belonging to the original reference subject. "
            "Valeria Cross DNA: Male Italian face 60yo, beard and eyeglasses exactly as shown in the attached "
            "reference photo, silver short hair, hourglass body, smooth skin.\n\n"
            "5. WATERMARK TEXT: Must read exactly: 'feat. Valeria Cross 👠' "
            "in elegant champagne cursive, very small, bottom center/left, 90% opacity. "
            "Replace any other watermark text with the exact text above.\n\n"
            "6. NAME REMOVAL: Remove any occurrence of 'Valeria Cross' or 'DNA of Valeria Cross' from the prompt body.\n\n"
            "7. KEEP INTACT: scene, outfit, lighting, environment, pose, mood, camera settings, "
            "photographic style, watermark spec, all creative elements not related to the subject's identity.\n\n"
            "8. BODY STATEMENT: Ensure the Subject body section explicitly states, in positive terms: "
            "'completely smooth, hairless skin on the torso, arms and legs', "
            "'soft feminine hourglass silhouette'.\n\n"
            f"PROMPT TO REVIEW:\n\n{prompt}"
        )
        logger.info("🔍 review_and_fix: avviata")
        result = client.generate(review_instr, max_tokens=8192)
        if result:
            logger.info(f"✅ review_and_fix: completata ({len(result)} chars)")
            return result
        logger.warning("⚠️ review_and_fix: risposta vuota — uso prompt originale")
        return prompt
    except Exception as e:
        logger.warning(f"⚠️ review_and_fix: fallita, uso prompt originale: {e}")
        return prompt


def sanitize_user_input(text: str, client: 'GeminiClient') -> str:
    """
    Pre-processa il testo dell'utente rimuovendo elementi incompatibili con il DNA di Valeria Cross.
    Rimuove: makeup, capelli non coerenti, watermark errati, tratti facciali femminili espliciti.
    Non bloccante — in caso di errore ritorna il testo originale.
    """
    if not text or not text.strip():
        return text
    try:
        instr = (
            "You are a pre-processing filter for an AI image generation system. "
            "The subject of every image is a fixed character with these IMMUTABLE traits:\n"
            "- Male Italian face, ~60 years old, silver/grey short hair (max 15cm, nape exposed)\n"
            "- Beard and eyeglasses exactly as shown in the attached reference photo (ALWAYS present)\n"
            "- NO makeup of any kind (no eyeshadow, no eyeliner, no lipstick, no contour, no mascara)\n"
            "- NO long hair, NO dark hair, NO brown/black/blonde hair\n"
            "- Hourglass feminine body, smooth skin\n\n"
            "Your task: clean the user's idea text by REMOVING or REPLACING these elements:\n"
            "1. Any makeup description → REMOVE entirely\n"
            "2. Any hair description conflicting with short silver hair → REMOVE entirely\n"
            "3. Any watermark not reading 'feat. Valeria Cross' → REMOVE entirely\n"
            "4. Any explicit mention of a young female face or female facial traits → REMOVE\n"
            "5. Keep EVERYTHING else intact: scene, outfit, pose, environment, lighting, camera specs, mood\n\n"
            "Return ONLY the cleaned text. No explanations, no preamble.\n\n"
            f"USER TEXT:\n{text}"
        )
        result = client.generate(instr)
        if result:
            if result != text:
                logger.info("🧹 sanitize_user_input: rimossi elementi conflittuali")
            return result
        return text
    except Exception as e:
        logger.warning(f"⚠️ sanitize_user_input: fallita (non bloccante): {e}")
        return text


# ============================================================
# ANALYZE_SCENE — ANALISI IMMAGINE CENTRALIZZATA
# ============================================================

# Prompt unico — un solo tentativo, nessun retry
_ANALYZE_PROMPT = (
    "Analyze this image. "
    "Return a structured description with these exact sections:\n\n"
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
    "patterns on garments (those belong in OUTFIT)"
)


def analyze_scene(img_bytes: bytes, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Analisi immagine centralizzata — singolo tentativo, nessun retry.
    Returns: (result, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."

    try:
        mime = detect_mime_type(img_bytes)
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
        logger.info(f"🔍 analyze_scene: mime={mime} ({len(img_bytes)} bytes)")
        result = client.generate(_ANALYZE_PROMPT, contents=[img_part])
        if result:
            logger.info(f"✅ analyze_scene: completato ({len(result)} chars)")
            return result, None
        # Non dovrebbe mai arrivare qui — generate() ora rilancia invece di ritornare None
        return None, "⚠️ Nessuna risposta da Gemini (causa sconosciuta)."

    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ analyze_scene: {err_text}")
        # Classifica l'errore per un messaggio utente chiaro
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
                "⚠️ <b>Immagine bloccata dai filtri Gemini.</b>\n"
                "Gemini rifiuta questa foto (contenuto sensibile).\n"
                "Prova con un'immagine diversa."
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


# ============================================================
# GeminiClient
# ============================================================

class GeminiClient:
    """
    Wrapper Singleton attorno a genai.Client con rotation automatica multi-chiave.
    Legge GOOGLE_API_KEY, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, GOOGLE_API_KEY_4, GOOGLE_API_KEY_5 dall'environment.
    Su 429/quota esaurita ruota automaticamente alla chiave successiva.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, api_key: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, api_key: str = None):
        if self._initialized:
            return
        # Raccoglie tutte le chiavi disponibili
        keys = []
        for env_var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3", "GOOGLE_API_KEY_4", "GOOGLE_API_KEY_5"]:
            k = os.environ.get(env_var)
            if k:
                keys.append(k)
        if api_key and api_key not in keys:
            keys.insert(0, api_key)

        self._keys = keys
        self._key_index = 0
        self._clients = [genai.Client(api_key=k) for k in keys] if keys else []
        self._client = self._clients[0] if self._clients else None
        self._rotation_callbacks = []
        self._key_use_callbacks = []        # callback ad ogni chiamata (chiave, count)
        self._call_counts = [0] * len(keys)  # contatore per chiave — si azzera al riavvio
        self._total_calls = 0               # contatore globale — tutte le chiavi sommate

        if not self._clients:
            logger.warning("⚠️ GeminiClient: nessuna GOOGLE_API_KEY configurata.")
        else:
            logger.info(f"🔑 GeminiClient: {len(self._clients)} chiave/i disponibile/i")
        self._initialized = True
        if self._clients:
            self._schedule_daily_reset()

    def _rotate_key(self):
        """Ruota alla chiave successiva — chiamato su 429/quota."""
        if len(self._clients) <= 1:
            return False
        self._key_index = (self._key_index + 1) % len(self._clients)
        self._client = self._clients[self._key_index]
        new_num = self._key_index + 1
        logger.warning(f"🔄 GeminiClient: rotazione chiave → indice {new_num}/{len(self._clients)}")
        # Notifica tutti i callback registrati
        for cb in self._rotation_callbacks:
            try:
                cb(new_num)
            except Exception as cb_err:
                logger.warning(f"⚠️ on_key_rotation callback error: {cb_err}")
        return True

    @property
    def current_key_num(self) -> int:
        """Ritorna il numero (1-based) della chiave API attualmente in uso."""
        return self._key_index + 1

    def on_key_rotation(self, callback):
        """
        Registra una callback chiamata ogni volta che la chiave ruota.
        callback(new_key_num: int) — new_key_num è 1-based.
        Permette ai bot di notificare l'utente del cambio chiave.
        """
        self._rotation_callbacks.append(callback)

    def on_key_use(self, callback):
        """
        Registra una callback chiamata ad OGNI chiamata generate().
        callback(key_num: int, call_count: int) — key_num 1-based, call_count cumulativo per quella chiave.
        Utile per mostrare quale chiave è in uso e quante call ha fatto oggi.
        """
        self._key_use_callbacks.append(callback)

    def reset_counters(self):
        """Azzera tutti i contatori call — chiamare su /start e automaticamente alle 08:00 UTC."""
        self._call_counts = [0] * len(self._clients)
        self._total_calls = 0
        logger.info("🔄 GeminiClient: contatori call azzerati")

    def _schedule_daily_reset(self):
        """Pianifica reset automatico ogni giorno alle 07:00 UTC (= 08:00 Lisbona estate).
        FIX 2.3.12: datetime.utcnow() (deprecato, naive) sostituito con
        datetime.now(timezone.utc) (aware) — evita TypeError silenziosi futuri su
        confronti naive/aware. Il loop è inoltre avvolto in try/except: prima, una
        qualsiasi eccezione interna terminava il thread per sempre senza alcun log,
        e i contatori restavano bloccati fino al riavvio del servizio senza che
        nessuno se ne accorgesse.
        """
        import threading as _t
        import datetime as _dt

        def _reset_loop():
            while True:
                try:
                    now = _dt.datetime.now(_dt.timezone.utc)
                    next_reset = now.replace(hour=7, minute=0, second=0, microsecond=0)
                    if now >= next_reset:
                        next_reset += _dt.timedelta(days=1)
                    wait_secs = (next_reset - now).total_seconds()
                    logger.info(f"⏰ Prossimo reset contatori in {int(wait_secs//3600)}h {int((wait_secs%3600)//60)}m (08:00 UTC)")
                    _t.Event().wait(timeout=wait_secs)
                    self.reset_counters()
                except Exception as e:
                    logger.error(f"❌ GeminiCounterReset: errore nel loop, ritento tra 60s: {e}", exc_info=True)
                    _t.Event().wait(timeout=60)

        t = _t.Thread(target=_reset_loop, daemon=True, name="GeminiCounterReset")
        t.start()

    @property
    def call_counts(self) -> list[int]:
        """Ritorna la lista dei contatori per chiave (0-based index)."""
        return list(self._call_counts)

    @property
    def available(self) -> bool:
        return bool(self._clients)

    def generate(self, prompt: str, contents: list = None, model: str = MODEL, max_tokens: int = 3000) -> str | None:
        """
        Genera testo con Gemini.
        contents: lista di Part aggiuntivi (immagini, ecc.) — vengono messi PRIMA del testo.
        Ritorna il testo generato o None in caso di errore.

        FIX 1.2.0: quando contents non è vuoto (es. immagini), il prompt testuale
        viene wrappato come genai_types.Part per garantire compatibilità con l'API.
        Passare una stringa nuda in una lista mista Part+str causa il fallimento
        silenziosa dell'analisi immagine (Gemini ignora la parte visiva).
        FIX 1.6.0: safety_settings disabilitati — necessario per analisi outfit
        su immagini fashion che altrimenti vengono bloccate dai filtri Gemini.
        """
        if not self._client:
            logger.error("❌ GeminiClient non disponibile.")
            return None
        # Round-robin: ruota la chiave PRIMA di ogni chiamata
        if len(self._clients) > 1:
            self._rotate_key()
        # Incrementa contatori e notifica on_key_use callbacks
        self._total_calls += 1
        if self._call_counts:
            self._call_counts[self._key_index] += 1
        _cur_key = self._key_index + 1
        for _cb in self._key_use_callbacks:
            try:
                _cb(_cur_key, self._total_calls)
            except Exception as _cb_err:
                logger.warning(f"\u26a0\ufe0f on_key_use callback error: {_cb_err}")
        try:
            if contents:
                text_part = genai_types.Part.from_text(text=prompt)
                payload = list(contents) + [text_part]
            else:
                payload = prompt
            safety = [
                genai_types.SafetySetting(
                    category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai_types.SafetySetting(
                    category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai_types.SafetySetting(
                    category=genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                ),
                genai_types.SafetySetting(
                    category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
                ),
            ]
            response = self._client.models.generate_content(
                model=model,
                contents=payload,
                config=genai_types.GenerateContentConfig(
                    safety_settings=safety,
                    max_output_tokens=max_tokens,
                )
            )
            if response.text:
                return response.text.strip()
            # Risposta vuota — estrai il motivo reale da finish_reason
            reason = "sconosciuto"
            try:
                candidate = response.candidates[0] if response.candidates else None
                if candidate:
                    fr = str(candidate.finish_reason)
                    if "SAFETY" in fr:
                        reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                    elif "RECITATION" in fr:
                        reason = "RECITATION — Gemini ha bloccato per potenziale riproduzione di contenuto protetto"
                    elif "MAX_TOKENS" in fr:
                        reason = "MAX_TOKENS — risposta troncata, output troppo lungo"
                    elif "STOP" in fr:
                        reason = "STOP — risposta terminata normalmente ma testo vuoto"
                    else:
                        reason = f"finish_reason: {fr}"
                else:
                    # Nessun candidato — Gemini ha bloccato l'intera richiesta
                    # Controlla prompt_feedback per il motivo
                    try:
                        pf = str(response.prompt_feedback) if hasattr(response, "prompt_feedback") else ""
                        if "SAFETY" in pf or "BLOCK" in pf:
                            reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                        elif pf:
                            reason = f"prompt_feedback: {pf[:80]}"
                        else:
                            reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                    except Exception:
                        reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
            except Exception as fe:
                reason = f"impossibile leggere finish_reason: {fe}"
            raise RuntimeError(f"Gemini ha risposto senza testo — {reason}")
        except Exception as e:
            err_text = str(e)
            logger.error(f"\u274c GeminiClient.generate(): {e}", exc_info=True)
            # Errori transitori: 429/quota, 503/overload, timeout, rete
            # -> tenta TUTTE le chiavi rimanenti prima di arrendersi
            _is_transient = (
                "429" in err_text
                or "503" in err_text
                or "quota" in err_text.lower()
                or "exhausted" in err_text.lower()
                or "unavailable" in err_text.lower()
                or "overloaded" in err_text.lower()
                or "timeout" in err_text.lower()
                or "timed out" in err_text.lower()
                or "connection" in err_text.lower()
            )
            if _is_transient:
                for _attempt in range(len(self._clients) - 1):
                    if not self._rotate_key():
                        break
                    logger.info(f"\U0001f504 Ritento con chiave #{self._key_index + 1} (errore transitorio)...")
                    try:
                        if contents:
                            text_part = genai_types.Part.from_text(text=prompt)
                            payload = list(contents) + [text_part]
                        else:
                            payload = prompt
                        response2 = self._client.models.generate_content(
                            model=model,
                            contents=payload,
                            config=genai_types.GenerateContentConfig(
                                safety_settings=safety,
                                max_output_tokens=max_tokens,
                            )
                        )
                        if response2.text:
                            return response2.text.strip()
                    except Exception as e2:
                        err2 = str(e2)
                        _is_transient2 = (
                            "429" in err2
                            or "503" in err2
                            or "quota" in err2.lower()
                            or "exhausted" in err2.lower()
                            or "unavailable" in err2.lower()
                            or "overloaded" in err2.lower()
                            or "timeout" in err2.lower()
                            or "timed out" in err2.lower()
                            or "connection" in err2.lower()
                        )
                        if _is_transient2:
                            logger.warning(f"\u26a0\ufe0f Chiave #{self._key_index + 1} transitorio, provo la prossima...")
                            continue
                        # Errore non transitorio (SAFETY, parametro errato, ecc.) — stop
                        logger.error(f"\u274c GeminiClient.generate() chiave {self._key_index+1}: {e2}")
                        raise e2
            raise


# ============================================================
# CaptionGenerator
# ============================================================

class CaptionGenerator:
    """
    Genera caption social in stile Valeria Cross.
    Tre varianti di tono:
      - from_scenario()  → Surprise (scena da pool)
      - from_image()     → Vogue / Architect (foto originale)
      - from_filter()    → Filtro (effetto artistico applicato)
    """

    EXAMPLES = (
        "🩰🍷🕊️🎞️🌑 dramatic white layers against a deep burgundy backdrop\n"
        "🌊✨💎🎤🌃 shimmering turquoise beads under the stage lights\n"
        "🌸🪨🩰🕯️✨ delicate pink lace within ancient stone alcove\n"
        "💖🐱🤳✨ pretty in pink and feline fine"
    )

    RULES = (
        "Rules:\n"
        "- Start with 4 or 5 emoji that match the style, setting, mood, colors and fashion\n"
        "- Follow with a short evocative phrase of maximum 10 words\n"
        "- Focus ONLY on: location, outfit, colors, atmosphere, fashion, mood, artistic effect\n"
        "- Do NOT mention any person, nationality, ethnicity, age, gender or physical traits\n"
        "- No hashtags, no punctuation at the end\n"
        "- Return ONLY the caption on a single line, nothing else\n"
    )

    @staticmethod
    def extract_caption(text: str) -> str | None:
        """
        Estrae la caption finale dal testo di Gemini.
        Gemini a volte ragiona ad alta voce prima di rispondere —
        cerca l'ultima riga non vuota che inizia con uno o più emoji.
        Se non trovata, ritorna l'ultima riga non vuota.
        """
        import unicodedata
        def starts_with_emoji(line):
            return line and unicodedata.category(line[0]) in ('So', 'Sm') or (
                len(line) > 1 and ord(line[0]) > 0x1F000)
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        # Cerca l'ultima riga che inizia con emoji
        for line in reversed(lines):
            if starts_with_emoji(line):
                return line
        # Fallback: ultima riga non vuota
        return lines[-1] if lines else None

    def __init__(self, client: GeminiClient):
        self.client = client

    def from_scenario(self, scenario: dict) -> tuple[str | None, str | None]:
        """
        Caption da scenario Surprise (pool).
        scenario: dict con keys location, sky, outfit, style, pose, mood
        """
        context = (
            f"Location: {scenario.get('location', '')}\n"
            f"Sky/Lighting: {scenario.get('sky', '')}\n"
            f"Outfit: {scenario.get('outfit', '')}\n"
            f"Style: {scenario.get('style', '')}\n"
            f"Pose: {scenario.get('pose', '')}\n"
            f"Mood: {scenario.get('mood', '')}"
        )
        prompt = (
            f"Based on this fashion editorial scene, write a social media caption.\n\n"
            f"SCENE:\n{context}\n\n"
            f"{self.RULES}"
            f"Examples:\n{self.EXAMPLES}"
        )
        result = self.client.generate(prompt)
        if result:
            return self.extract_caption(result) or result, None
        return None, "⚠️ Caption non disponibile."

    def from_image(self, img_bytes: bytes) -> tuple[str | None, str | None]:
        """
        Caption da foto originale (Vogue / Architect).
        Legge soggetto, atmosfera e outfit dall'immagine.
        """
        if not self.client.available:
            return None, "⚠️ API non configurata."
        try:
            mime = detect_mime_type(img_bytes)
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
            prompt = (
                "Look at this fashion photo and write a social media caption.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return self.extract_caption(result) or result, None
            return None, "⚠️ Caption non disponibile."
        except Exception as e:
            logger.error(f"❌ CaptionGenerator.from_image(): {e}", exc_info=True)
            return None, f"❌ Errore: {html.escape(str(e))}"

    def from_filter(self, img_bytes: bytes, filter_label: str) -> tuple[str | None, str | None]:
        """
        Caption per Filtro — descrive l'effetto artistico applicato all'immagine.
        filter_label: es. "🌊 Dissolve" o "🌀 Dalì"
        """
        if not self.client.available:
            return None, "⚠️ API non configurata."
        try:
            mime = detect_mime_type(img_bytes)
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
            prompt = (
                f"This image has been processed with the artistic filter: {filter_label}\n\n"
                f"Write a social media caption that evokes the artistic effect and atmosphere "
                f"of the filtered result — not the original photo.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return self.extract_caption(result) or result, None
            return None, "⚠️ Caption non disponibile."
        except Exception as e:
            logger.error(f"❌ CaptionGenerator.from_filter(): {e}", exc_info=True)
            return None, f"❌ Errore: {html.escape(str(e))}"



# ============================================================
# HealthServer
# ============================================================

class HealthServer:
    """
    Flask health check server — porta 10000 (default Koyeb).
    Avvia in thread daemon, non blocca il bot.
    """

    def __init__(self, bot_name: str, version: str, port: int = 10000):
        self.bot_name = bot_name
        self.version  = version
        self.port     = port
        self.app      = flask.Flask(bot_name)

        @self.app.route('/')
        def health():
            return f"{self.bot_name} v{self.version} ok", 200

        @self.app.route('/health')
        def health_detail():
            return {"bot": self.bot_name, "version": self.version, "status": "ok"}, 200

    def start(self):
        """Avvia Flask in thread daemon."""
        t = threading.Thread(
            target=lambda: self.app.run(
                host='0.0.0.0',
                port=int(os.environ.get("PORT", self.port)),
                debug=False,
                use_reloader=False,   # evita fork bomb di Werkzeug in thread daemon
                threaded=True,        # gestisce richieste concurrent senza bloccare
            ),
            daemon=True
        )
        t.start()
        logger.info(f"🌐 HealthServer avviato su porta {self.port}")

"""
C_shared100.py — Valeria Cross AI · Oggetti comuni a tutti i bot
Versione: 1.5.0

CHANGELOG 1.5.0:
  - GeminiClient: implementato pattern Singleton corretto con __new__.
    Ogni chiamata GeminiClient() restituisce la stessa istanza — nessuna
    connessione duplicata, nessun consumo inutile di risorse.

CHANGELOG 1.4.0:
  - HealthServer.start(): aggiunto use_reloader=False e threaded=True a app.run().

CHANGELOG 1.3.0:
  - SICUREZZA: aggiunta funzione is_allowed(uid) — whitelist utenti via env ALLOWED_USERS.

CHANGELOG 1.2.0:
  - FIX CRITICO GeminiClient.generate(): prompt testuale wrappato come Part.from_text()
    in payload misto con immagini. Risolve analisi immagini fallita su tutti i bot.
"""

import os, html, logging, threading, flask
from google import genai
from google.genai import types as genai_types

# Esportati per uso nei bot
__all__ = [
    'GeminiClient', 'CaptionGenerator', 'HealthServer', 'is_allowed',
    'VALERIA_FACE', 'VALERIA_BODY_STRONG', 'VALERIA_BODY_SAFE',
    'VALERIA_WATERMARK', 'VALERIA_NEGATIVE',
    'genai_types', 'MODEL',
]

logger = logging.getLogger(__name__)

MODEL = "gemini-3-flash-preview"

# Versione
VERSION = "1.0.0"

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
    "**⚠️ FACE IDENTITY LOCK — ABSOLUTE PRIORITY — DO NOT OVERRIDE — DO NOT SIMPLIFY:**\n"
    "60-year-old Italian male face, oval-rectangular shape. "
    "Ultra-detailed mature skin with visible pores, deep character wrinkles, crow's feet. "
    "Calm half-smile, no teeth shown. "
    "Thin octagonal Vogue Havana dark tortoiseshell frame eyeglasses — MANDATORY, always present, never removed.\n"
    "**Hair:** Short silver-grey Italian cut, slightly voluminous top, nape exposed.\n"
    "**⚠️ BEARD — MANDATORY — NON-NEGOTIABLE:** "
    "Full silver-grey beard approximately 6-7cm, perfectly groomed, dense and uniform, following the jawline. "
    "The beard MUST be clearly visible in EVERY shot. "
    "DO NOT shave it. DO NOT reduce it. DO NOT replace it with stubble. "
    "A clean-shaven face is a generation FAILURE. The beard is part of the identity lock.\n"
    "**Rendering:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200.\n\n"
)

VALERIA_BODY_STRONG = (
    "**MANDATORY BODY — NOT A MALE BODY — OVERRIDE ALL DEFAULTS:**\n"
    "**Feminine hourglass proportions, 180cm, 85kg. FULL D-CUP BUST — prominent, natural, clearly visible. "
    "Wide rounded hips, defined waist, full thighs. THIS BODY IS FEMININE. DO NOT GENERATE A MALE PHYSIQUE.**\n"
    "Completely hairless body — NO body hair, NO chest hair, NO arm hair, NO leg hair on ALL surfaces. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE RULE — CRITICAL:** The silver-grey beard on the male face AND the feminine body "
    "are NOT a contradiction. They MUST coexist in the same image. The beard stays. The feminine body stays. "
    "Both are mandatory. Do NOT resolve this by removing the beard. "
    "Do NOT resolve this by masculinizing the body. Keep both exactly as described.\n\n"
)

VALERIA_BODY_SAFE = (
    "**MANDATORY BODY — NOT A MALE BODY — OVERRIDE ALL DEFAULTS:**\n"
    "**Feminine hourglass silhouette, 180cm, 85kg. Soft feminine proportions — defined waist, "
    "wide rounded hips, full figure. THIS BODY IS FEMININE. DO NOT GENERATE A MALE PHYSIQUE.**\n"
    "Completely hairless body — NO body hair, NO chest hair, NO arm hair, NO leg hair on ALL surfaces. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE RULE — CRITICAL:** The silver-grey beard on the male face AND the feminine body "
    "are NOT a contradiction. They MUST coexist in the same image. The beard stays. The feminine body stays. "
    "Both are mandatory. Do NOT resolve this by removing the beard. "
    "Do NOT resolve this by masculinizing the body. Keep both exactly as described.\n\n"
)

VALERIA_WATERMARK = "feat. Valeria Cross 👠"

VALERIA_NEGATIVE = (
    "shaved face, clean-shaven, no beard, missing beard, beard removed, stubble instead of beard, "
    "female face, young face, missing glasses, face drift, body hair, chest hair, arm hair, leg hair, "
    "male physique, flat chest, masculine body, desaturated colors, color shift, "
    "extra fingers, JSON output, text overlay."
)

# ============================================================
# GeminiClient
# ============================================================

class GeminiClient:
    """
    Wrapper Singleton attorno a genai.Client.
    Ogni chiamata GeminiClient() restituisce la stessa istanza.
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
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._client = genai.Client(api_key=self.api_key) if self.api_key else None
        if not self._client:
            logger.warning("⚠️ GeminiClient: GOOGLE_API_KEY non configurata.")
        self._initialized = True

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, contents: list = None, model: str = MODEL) -> str | None:
        """
        Genera testo con Gemini.
        contents: lista di Part aggiuntivi (immagini, ecc.) — vengono messi PRIMA del testo.
        Ritorna il testo generato o None in caso di errore.

        FIX 1.2.0: quando contents non è vuoto (es. immagini), il prompt testuale
        viene wrappato come genai_types.Part per garantire compatibilità con l'API.
        Passare una stringa nuda in una lista mista Part+str causa il fallimento
        silenziosa dell'analisi immagine (Gemini ignora la parte visiva).
        """
        if not self._client:
            logger.error("❌ GeminiClient non disponibile.")
            return None
        try:
            if contents:
                # Misto immagini+testo: il prompt va come Part esplicito
                text_part = genai_types.Part.from_text(text=prompt)
                payload = list(contents) + [text_part]
            else:
                # Solo testo: stringa nuda funziona correttamente
                payload = prompt
            response = self._client.models.generate_content(
                model=model,
                contents=payload
            )
            return response.text.strip() if response.text else None
        except Exception as e:
            logger.error(f"❌ GeminiClient.generate(): {e}", exc_info=True)
            return None


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
            return result, None
        return None, "⚠️ Caption non disponibile."

    def from_image(self, img_bytes: bytes) -> tuple[str | None, str | None]:
        """
        Caption da foto originale (Vogue / Architect).
        Legge soggetto, atmosfera e outfit dall'immagine.
        """
        if not self.client.available:
            return None, "⚠️ API non configurata."
        try:
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            prompt = (
                "Look at this fashion photo and write a social media caption.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return result, None
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
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
            prompt = (
                f"This image has been processed with the artistic filter: {filter_label}\n\n"
                f"Write a social media caption that evokes the artistic effect and atmosphere "
                f"of the filtered result — not the original photo.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return result, None
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

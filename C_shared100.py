"""
C_shared100.py — Valeria Cross AI · Oggetti comuni a tutti i bot
Versione: 1.3.0

REGOLA: questo file si aggiorna SEMPRE in-place con lo stesso nome C_shared100.py.
Non rinominare mai in C_shared101.py o simili — tutti i bot importano da C_shared100.

CHANGELOG 1.3.0 (11/05/2026):
  - CaptionGenerator.extract_caption(): filtro post-generazione che estrae
    la caption finale dal testo di Gemini, ignorando il ragionamento interno.
    Applicato in from_scenario(), from_image(), from_filter() e generate_caption().

CHANGELOG 1.2.0 (10/05/2026):
  - GeminiClient.generate(): ispeziona finish_reason quando response.text è vuoto,
    rilancia eccezione con motivo reale invece di return None silenzioso.
  - analyze_scene(): classifica eccezioni e ritorna messaggi espliciti
    (429/quota, SAFETY block, timeout, generico).
  - generate_caption(): stessa classificazione errori.

CHANGELOG 1.1.0 (10/05/2026):
  - detect_mime_type(): rileva JPEG/PNG/WebP dai magic bytes.
    Usata in analyze_scene(), generate_caption() e CaptionGenerator — nessun mime_type hardcoded.
  - SHARED_VERSION e SHARED_DATE esportate — verificabili via /shared su tutti i bot.

CHANGELOG 1.0.2 (09/05/2026):
  - _ANALYZE_PROMPTS (5 tentativi) → _ANALYZE_PROMPT singolo, nessun retry.
  - analyze_scene(): singolo tentativo, espone errore reale.
  - GeminiClient.generate(): rilancia eccezioni invece di return None.

CHANGELOG 1.0.1 (09/05/2026):
  - GeminiClient.generate(): safety_settings BLOCK_NONE su tutte le categorie.
  - Aggiunta analyze_scene() centralizzata.
  - Aggiunta generate_caption() centralizzata.
  - Aggiunta CaptionGenerator con from_scenario(), from_image(), from_filter().
  - Centralizzati VALERIA_DNA, EDITORIAL_WRAPPER, build_valeria_identity().
"""

import os, html, logging, threading, flask
from google import genai
from google.genai import types as genai_types

# Esportati per uso nei bot
__all__ = [
    'GeminiClient', 'CaptionGenerator', 'HealthServer', 'is_allowed',
    'VALERIA_FACE', 'VALERIA_BODY_STRONG', 'VALERIA_BODY_SAFE',
    'VALERIA_WATERMARK', 'VALERIA_NEGATIVE',
    'VALERIA_DNA', 'EDITORIAL_WRAPPER',
    'build_valeria_identity', 'generate_caption', 'generate_mini_caption', 'generate_mini_prompt',
    'review_and_fix', 'sanitize_user_input',
    'analyze_scene', 'genai_types', 'MODEL',
    'SHARED_VERSION', 'SHARED_DATE',
]

logger = logging.getLogger(__name__)

MODEL = "gemini-3-flash-preview"

# Versione
VERSION = "1.8.0"
SHARED_VERSION = "1.8.0"   # aggiornare ad ogni modifica
SHARED_DATE    = "25/05/2026"  # aggiornare ad ogni modifica

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

# DNA completo assemblato — usato da Vogue e Architect
VALERIA_DNA = (
    f"{VALERIA_FACE}"
    f"{VALERIA_BODY_STRONG}"
    f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
    f"NEGATIVE: {VALERIA_NEGATIVE}"
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


def generate_mini_prompt(text: str, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Estrae dal prompt Flow un mini-prompt strutturato con emoji — formato Nosurprise.
    Output: blocco testuale con sezioni Location, Sky, Outfit, Style, Pose, Mood, Body.
    No gender, no nomi propri del soggetto.
    Returns: (mini_prompt, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."
    try:
        prompt = (
            "Read the following image generation prompt carefully.\n"
            "Extract and rewrite its key visual elements in this EXACT structured format:\n\n"
            "📍 Location: [specific place, architecture, environment, geographic context — 1 line]\n"
            "🌤 Sky: [lighting quality, time of day, weather, light direction — 1 line]\n"
            "👗 Outfit: [every garment, fabric, color, brand if mentioned, accessories, shoes — 1 line]\n"
            "🎨 Style: [artistic/photographic style, rendering, mood aesthetic — 1 line]\n"
            "💃 Pose: [body position, framing, camera angle, gaze — 1 line]\n"
            "✨ Mood: [emotional atmosphere, feeling, energy — 1 line]\n"
            "🏛 Body: [physical description of the subject — no name, no gender pronouns — 1 line]\n\n"
            "Rules:\n"
            "— Do NOT use any gender pronouns (he/she/his/her). Use neutral language.\n"
            "— Do NOT invent details not present in the prompt.\n"
            "— If a section has no information in the prompt, write: [not specified]\n"
            "— Keep each line concise but complete.\n"
            "— Output ONLY the 7 structured lines above, nothing else.\n\n"
            f"PROMPT:\n{text[:3000]}"
        )
        logger.info("📋 generate_mini_prompt: chiamata API testo")
        result = client.generate(prompt)
        if result:
            return result.strip(), None
        return None, "⚠️ Nessuna risposta da Gemini."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ generate_mini_prompt(): {err_text}", exc_info=True)
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            return None, ("❌ <b>Servizio Gemini non disponibile.</b> Sovraccarico temporaneo. Riprova tra qualche minuto." if "503" in err_text or "unavailable" in err_text.lower() else "❌ <b>Quota API esaurita.</b> Reset alle 08:00 ora Lisbona.")
        elif "SAFETY" in err_text:
            return None, "❌ <b>Safety block di Gemini.</b> Riprova."
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            return None, "❌ <b>Timeout Gemini.</b> Riprova tra qualche secondo."
        else:
            return None, f"❌ <b>Errore mini prompt:</b>\n<code>{err_text}</code>"


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
            "2. GLASSES MANDATORY: Valeria Cross ALWAYS wears thin octagonal Vogue Havana dark tortoiseshell glasses. "
            "If the prompt does NOT mention glasses or eyeglasses, ADD this phrase in the Facial identity section: "
            "'thin octagonal Vogue Havana dark tortoiseshell frame eyeglasses (MANDATORY, always present)'. "
            "Also ensure 'no glasses' does NOT appear anywhere in the prompt.\n\n"
            "2b. GLASSES POSE REMOVAL: Remove ANY description of hands or fingers touching, adjusting, holding or "
            "raising to the glasses or temple area. The glasses are simply worn — no hand interaction with them.\n\n"
            "3. NEGATIVE PROMPTS CONFLICTS: Scan the negative prompts section. "
            "Remove from negatives any term that contradicts a positive element in the prompt.\n\n"
            "3b. MIRROR SELFIE RULE: If the prompt contains selfie, mirror, mirror selfie, bathroom, restroom, reflection — "
            "smartphone held in hand IS a required prop. Ensure it is present as positive element and removed from negatives.\n\n"
            "4. SUBJECT BLEED: Remove any physical description belonging to the original reference subject. "
            "Valeria Cross DNA: Male Italian face 60yo, silver beard 6-7cm, octagonal Vogue glasses, "
            "silver short hair, hourglass body, smooth skin.\n\n"
            "5. WATERMARK TEXT: Must read exactly: 'feat. Valeria Cross 👠' "
            "in elegant champagne cursive, very small, bottom center/left, 90% opacity. "
            "Replace any other watermark text with the exact text above.\n\n"
            "6. NAME REMOVAL: Remove any occurrence of 'Valeria Cross' or 'DNA of Valeria Cross' from the prompt body.\n\n"
            "7. KEEP INTACT: scene, outfit, lighting, environment, pose, mood, camera settings, "
            "photographic style, watermark spec, all creative elements not related to the subject's identity.\n\n"
            "8. BODY HAIR ENFORCEMENT: Ensure Subject body section explicitly states: "
            "'completely hairless body', 'no body hair, no chest hair, no arm hair, no leg hair', "
            "'soft feminine hourglass silhouette'. "
            "In NEGATIVE PROMPT — BODY ensure: 'body hair, chest hair, arm hair, leg hair, hairy torso, hairy arms'.\n\n"
            f"PROMPT TO REVIEW:\n\n{prompt}"
        )
        logger.info("🔍 review_and_fix: avviata")
        response = client._client.models.generate_content(
            model=client._model,
            contents=review_instr,
            config=genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8192,
            )
        )
        if response and response.text:
            fixed = response.text.strip()
            logger.info(f"✅ review_and_fix: completata ({len(fixed)} chars)")
            return fixed
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
            "- Silver/grey beard 6-7cm, thin octagonal dark glasses (ALWAYS present)\n"
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
    "COLOR PALETTE: [Dominant HEX codes with label.]\n\n"
    "BACKGROUND: [Exact location, architecture, surfaces, props, environment — be specific.]\n\n"
    "LIGHTING: [Light source, direction, quality, color temperature, mood — 1-2 sentences.]\n\n"
    "CAMERA: [Framing. Describe how the subjects/garments are positioned in frame.]\n\n"
    "MOOD: [Overall atmosphere, color grade, cinematic style — 1 sentence.]\n\n"
    "Rules:\n"
    "— Describe garments and accessories as standalone objects\n"
    "— Be precise and detailed on fabrics, colors and environment"
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
        elif "SAFETY" in err_text:
            friendly = (
                "❌ <b>Safety block di Gemini.</b>\n"
                "Gemini ha rifiutato l'analisi di questa immagine.\n"
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
        FIX 1.6.0: safety_settings disabilitati — necessario per analisi outfit
        su immagini fashion che altrimenti vengono bloccate dai filtri Gemini.
        """
        if not self._client:
            logger.error("❌ GeminiClient non disponibile.")
            return None
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
                    max_output_tokens=3000,
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
                        reason = "SAFETY BLOCK — Gemini ha rifiutato il contenuto (finish_reason: SAFETY)"
                    elif "RECITATION" in fr:
                        reason = "RECITATION — Gemini ha bloccato per potenziale riproduzione di contenuto protetto"
                    elif "MAX_TOKENS" in fr:
                        reason = "MAX_TOKENS — risposta troncata, output troppo lungo"
                    elif "STOP" in fr:
                        reason = "STOP — risposta terminata normalmente ma testo vuoto"
                    else:
                        reason = f"finish_reason: {fr}"
            except Exception as fe:
                reason = f"impossibile leggere finish_reason: {fe}"
            raise RuntimeError(f"Gemini ha risposto senza testo — {reason}")
        except Exception as e:
            logger.error(f"❌ GeminiClient.generate(): {e}", exc_info=True)
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

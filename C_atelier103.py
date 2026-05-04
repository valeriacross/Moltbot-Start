import os, telebot, html, threading, io, logging, time
from PIL import Image
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed, genai_types
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_BODY_SAFE, VALERIA_WATERMARK, VALERIA_NEGATIVE

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
VERSION = "1.0.3"
TOKEN   = os.environ.get("TELEGRAM_TOKEN_CLOSET")

gemini  = GeminiClient()
caption = CaptionGenerator(gemini)
server  = HealthServer("ATELIER", VERSION)

bot      = telebot.TeleBot(TOKEN, parse_mode="HTML")
executor = ThreadPoolExecutor(max_workers=4)

logger.info(f"✦ ATELIER v{VERSION} — inizializzazione in corso...")

# --- MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("masterface.png"):
            with open("masterface.png", "rb") as f:
                data = f.read()
            logger.info("✅ Master Face caricata.")
            return genai_types.Part.from_bytes(data=data, mime_type="image/png")
        logger.warning("⚠️ Master Face NON TROVATA.")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
        return None

MASTER_PART = get_face_part()

# VALERIA_BODY_STRONG e VALERIA_BODY_SAFE importate da C_shared100.py — non ridefinire qui.

# --- FILTRI ---
# Ogni filtro: label, emoji, descrizione scena, is_dual (2-in-1), varianti se dual
FILTERS = {
    "bikini_canvas": {
        "label": "🎨 Canvas Swimsuit",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "High-fashion editorial photograph. Professional studio or luxury exterior setting. "
            "Statuesque, confident pose. Technical focus on the garment as wearable art.\n\n"
            "**Outfit:**\n"
            "The subject wears a single-piece couture swimsuit whose fabric is a direct artistic transposition "
            "of the provided reference image — a canvas, painting, natural landscape, or artistic photograph. "
            "The entire surface of the garment reproduces the visual texture, color palette, tonal gradients "
            "and compositional elements of the reference as a high-resolution printed fabric. "
            "The swimsuit is elegant and sculptural: deep plunging neckline, "
            "metallic structural inserts at the waist and sides (gold or silver depending on color palette), "
            "clean architectural cut lines that follow and enhance the body silhouette. "
            "The garment is a complete one-piece — no separate parts, no strings, full coverage of the torso. "
            "Fabric finish: matte for organic/natural references, satin or metallic sheen for geometric or abstract ones.\n\n"
            "**Framing:**\n"
            "Editorial fashion, three-quarter or full body. Slight lateral angle to show garment volume. "
            "Setting: luxury beach club terrace, white concrete architecture, or neutral studio with dramatic directional light. "
            "Natural or cinematic lighting that enhances fabric texture and metallic inserts. "
            "Sharp subject, softly blurred background.\n"
        ),
    },
    "selfie_spiaggia": {
        "body_safe": True,
        "label": "🤳 Selfie Spiaggia",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Pieno Sole",
                "scene": (
                    "**Scene:**\n"
                    "True first-person selfie, dynamic and immersive. Camera perspective MUST be that of the subject taking the photo alone. "
                    "The phone is NOT visible, but the arm holding it MUST appear in the image, extended toward the camera with the hand suggesting the grip (like an arm-extended selfie). "
                    "Lateral selfie angle, subject lying on their side on granular sand, propped on elbow or hand, body slightly rotated toward camera. "
                    "The horizon and clear sea must be clearly visible in the background with depth effect. "
                    "Full body framing, showing the person entirely from feet to face so the swimwear is completely visible. "
                    "A colorful towel (no complex patterns) under the body. No chairs, deck chairs or foreign objects.\n\n"
                    "**Lighting:** Full midday sun, clear sky, bright natural light, sharp shadows.\n\n"
                    "**Expression:** Authentic, calm and relaxed facial expression, natural smile involving the eyes and small expression wrinkles.\n\n"
                    "**Technical:** 8K ultra-realistic, simulated 50mm focal length — face MUST NOT be distorted, elongated or deformed by perspective (no fish-eye effect). "
                    "f/2.8, ISO 200, 1/160s, creamy bokeh, glossy hyper-detailed finish, never waxy or plastic.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** visible phone, fish-eye lens, wide angle distortion, static, stiff, artificial lighting, body hair on arms legs chest.\n"
                ),
            },
            {
                "name": "🌅 Golden Hour",
                "scene": (
                    "**Scene:**\n"
                    "High-fashion beach editorial portrait at golden hour. "
                    "First-person perspective selfie — arm extended toward camera, hand suggesting grip, phone not visible. "
                    "Subject seated on granular sand on a colorful beach towel, body turned slightly toward camera, relaxed editorial pose. "
                    "Clear sea horizon visible in background. Full body editorial framing, swimwear fully visible.\n\n"
                    "**Lighting:** Golden hour, warm amber-gold directional light, long soft shadows, elegant rim light sculpting the silhouette.\n\n"
                    "**Expression:** Calm, confident, natural smile.\n\n"
                    "**Technical:** 8K editorial photography, 50mm equivalent, f/2.8, natural bokeh, "
                    "glossy high-fashion finish. No perspective distortion.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** visible phone, fish-eye distortion, wide angle, body hair, chest hair, arm hair, leg hair.\n"
                ),
            },
        ],
    },
    "letto": {
        "label": "🛌 Letto",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Giorno",
                "scene": (
                    "**Scene:**\n"
                    "Hyperrealistic full-body portrait of the subject lying on a bed in a relaxed pose: "
                    "head on pillow, body stretched diagonally on mattress, torso slightly rotated toward camera, "
                    "one hand resting beside the face, the other along the hip. Legs extended and naturally crossed, "
                    "emphasizing hip and torso line.\n\n"
                    "**Setting:** Bed with white, soft, slightly rumpled sheets. "
                    "Warm natural light entering from a large window (left side), creating golden reflections and soft shadows on skin and fabrics. "
                    "Neutral background, minimal bright room.\n\n"
                    "**Outfit:** Faithfully reproduce the exact garment from the reference photo provided: same model, same colors, same central decoration, "
                    "same fabric details, adapted to body proportions (D-cup bust, hourglass figure) without changing design or color.\n\n"
                    "**Style:** Soft but directional lights: warm highlights on body high points (shoulders, bust, abdomen, thighs), "
                    "soft shadows in sheet folds. Luminous and natural skin. Intimate, sophisticated, photographic atmosphere, zero vulgarity.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, standing pose, outdoor setting.\n"
                ),
            },
            {
                "name": "🌙 Notte",
                "scene": (
                    "**Scene:**\n"
                    "Hyperrealistic full-body portrait of the subject lying supine on a modern luxury bed, "
                    "completely resting on the mattress. Head on a white cylindrical pillow. "
                    "Arms raised above the head in a relaxed, elegant pose. Legs open toward the lower corners of the frame. "
                    "Full body framing.\n\n"
                    "**Setting:** Nocturnal interior: modern and refined bedroom, contemporary design, quality materials. "
                    "Soft diffused lighting with warm nocturnal ambient light, accent lamps creating an intimate, elegant and cinematic atmosphere. "
                    "Soft shadows, controlled contrast, natural and realistic skin rendering.\n\n"
                    "**Outfit:** Faithfully reproduce the exact garment from the reference photo provided: same model, same colors, same central decoration, "
                    "same fabric details, adapted to body proportions (D-cup bust, hourglass figure) without changing design or color.\n\n"
                    "**Technical:** f/2.8, ISO 200, 1/160s, 85mm, soft cinematic depth of field, natural bokeh, warm diffused light, "
                    "ultra-detailed glossy finish, neutral color calibration, ultra-realistic 8K.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, standing pose, outdoor setting, daylight.\n"
                ),
            },
        ],
    },
    "spiaggia_editoriale": {
        "body_safe": True,
        "label": "🌅 Spiaggia Editoriale",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "High-fashion editorial beach portrait at golden hour sunset. Exclusive luxury beach location — "
            "pristine white sand, crystal turquoise water, dramatic sky with warm orange and pink tones. "
            "The subject stands at the shoreline, waves gently lapping at their feet, "
            "body turned three-quarters toward camera with confident editorial posture.\n\n"
            "**Lighting:** Golden hour sunset, warm directional light from low sun, "
            "long golden shadows, glowing rim light sculpting the silhouette, "
            "soft fill from sky reflection on water.\n\n"
            "**Outfit:** High-end luxury swimwear or beach couture outfit "
            "faithfully extracted from the reference image provided.\n\n"
            "**Framing:** Full body editorial, 85mm perspective, shallow depth of field, "
            "ocean bokeh background. Cinematic color grade, rich warm tones.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, indoor setting.\n"
        ),
    },
    "beach_club": {
        "label": "🍹 Beach Club",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "Aperitivo moment at an exclusive Mediterranean beach club. "
            "Elegant lounge area with designer furniture, white linen, potted olive trees, "
            "infinity pool visible in background, sea horizon beyond. "
            "Late afternoon light — the golden hour before sunset, warm and cinematic. "
            "The subject is seated or semi-reclined on a luxury sun lounger or lounge chair, "
            "relaxed and confident, a cocktail glass nearby as a prop.\n\n"
            "**Lighting:** Warm late afternoon Mediterranean sun, soft golden directional light, "
            "subtle rim light from the sea reflection, elegant ambient fill.\n\n"
            "**Outfit:** Luxury resort wear or high-end swimwear with cover-up "
            "faithfully extracted from the reference image provided.\n\n"
            "**Framing:** Editorial fashion portrait, three-quarter body, slight low angle for elegance. "
            "Cinematic shallow depth of field, warm Mediterranean color grade.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, winter setting, urban setting.\n"
        ),
    },
    "yacht": {
        "body_safe": True,
        "label": "⛵ Yacht",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Pieno Sole",
                "scene": (
                    "**Scene:**\n"
                    "Luxury yacht editorial, full sun. The subject is on the main deck of a large private yacht, "
                    "lying or lounging on a padded sunbathing area (sundeck), surrounded by polished teak wood, "
                    "chrome fittings, and white fiberglass surfaces. Open sea in the background, horizon line visible. "
                    "Bright midday Mediterranean sun, deep blue sky, light sea spray caught in the air.\n\n"
                    "**Lighting:** Full midday sun, brilliant natural light, sharp shadows, warm golden tones. "
                    "Light reflecting off the sea surface creating subtle shimmer on skin.\n\n"
                    "**Pose:** Relaxed and confident — lying on the sundeck propped on one elbow, "
                    "or seated on the deck railing with the sea behind, editorial posture.\n\n"
                    "**Outfit:** Luxury resort wear or high-end swimwear "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Editorial fashion portrait, full body or three-quarter, "
                    "cinematic shallow depth of field, warm color grade, nautical luxury aesthetic.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, "
                    "indoor setting, urban setting, pool without sea context.\n"
                ),
            },
            {
                "name": "🌅 Tramonto",
                "scene": (
                    "**Scene:**\n"
                    "Luxury yacht editorial at golden hour sunset. The subject is standing on the deck of a large private yacht, "
                    "facing the horizon with the sun setting behind them over the open sea. "
                    "Polished teak deck, chrome details, white surfaces catching the warm orange-gold light. "
                    "The sea is painted in amber and rose tones, the sky layered with color.\n\n"
                    "**Lighting:** Dramatic golden hour — warm directional backlight from the setting sun "
                    "creating a luminous rim around the silhouette, long soft shadows on the deck, "
                    "reflected warm tones from the sea surface.\n\n"
                    "**Pose:** Standing upright, confident and elegant — one hand lightly resting on the railing, "
                    "body turned slightly toward the camera, gaze toward the horizon or the camera.\n\n"
                    "**Outfit:** Luxury resort wear or high-end swimwear "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Editorial fashion portrait, full body, low angle for grandeur, "
                    "cinematic golden color grade, sun flare permitted for atmosphere.\n\n"
                    "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, "
                    "indoor setting, urban setting, daytime harsh light.\n"
                ),
            },
        ],
    },
    "surf": {
        "body_safe": True,
        "label": "🏄 Surf",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "Dynamic action editorial on the ocean. The subject is mid-surf on a wave — "
            "standing on a surfboard, body engaged in the ride, arms out for balance, "
            "powerful ocean wave rising behind them. Spray and water droplets in the air. "
            "Raw natural energy, athletic and editorial simultaneously.\n\n"
            "**Lighting:** Bright natural ocean light, sun glinting off water surface, "
            "backlit spray creating luminous halo effect, dynamic and vivid.\n\n"
            "**Outfit:** Athletic surf-inspired swimwear or rash guard "
            "faithfully extracted from the reference image provided, adapted for aquatic movement.\n\n"
            "**Framing:** Dynamic low angle, wide enough to show wave and board context, "
            "subject sharp against motion-blurred water. 85mm equivalent, cinematic.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, static pose, indoor setting, beach without water.\n"
        ),
    },
    "riviera_60": {
        "label": "🎞️ Riviera '60",
        "is_dual": False,
        "scene": (
            "**⚠️ FACE IDENTITY LOCK — ABSOLUTE PRIORITY — DO NOT OVERRIDE:**\n"
            "**THE SUBJECT HAS A MALE FACE. 60-YEAR-OLD ITALIAN MAN. SILVER BEARD ~6cm. "
            "THIN OCTAGONAL TORTOISESHELL GLASSES — MANDATORY, ALWAYS VISIBLE. "
            "SHORT SILVER HAIR. THIS FACE MUST BE PRESERVED EXACTLY. "
            "DO NOT REPLACE WITH A FEMALE FACE. DO NOT GENERATE A GENERIC WOMAN. "
            "THE MALE FACE IS NON-NEGOTIABLE AND OVERRIDES ALL SCENE AESTHETICS.**\n\n"
            "**Scene:**\n"
            "Cinematic vintage editorial inspired by 1960s Côte d'Azur glamour. "
            "Location: iconic French or Italian Riviera — white and pastel architecture, "
            "harbor with classic wooden boats, palm trees, cafe terrace overlooking the sea. "
            "The subject exudes old Hollywood elegance meeting Mediterranean summer. "
            "The atmosphere is unhurried, warm, timeless — a moment stolen from a 1967 summer.\n\n"
            "**Outfit:** Vintage-inspired elegant swimwear or resort wear with retro 1960s aesthetic "
            "faithfully extracted from the reference image provided.\n\n"
            "**Lighting:** Warm afternoon Mediterranean sun, soft and slightly hazy, "
            "golden tones with a gentle overexposed quality typical of 1960s film photography.\n\n"
            "**Film aesthetic (MANDATORY):** Simulate authentic Kodachrome 64 / Polaroid Type 108 film stock. "
            "Slightly faded and desaturated colors — not Instagram-filtered, but genuinely aged photographic chemistry. "
            "Warm yellow-amber cast in shadows, soft cyan-green in highlights. "
            "Subtle but visible film grain throughout. Gentle vignette at corners. "
            "Slight halation around bright areas (windows, sky, water reflections). "
            "Tonal compression — no pure blacks, no pure whites, everything slightly lifted and warm. "
            "Color palette: Wes Anderson vintage meets aged Riviera postcard — dusty pinks, warm ivories, "
            "faded teals, sun-bleached blues. The image should feel like it was found in a 1968 photo album, "
            "not shot today with a retro filter.\n\n"
            "**Framing:** Classic editorial composition, medium to full body. Timeless, iconic, cinematic.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, "
            "modern architecture, digital look, cold tones, oversaturated colors, HDR, sharp clinical lighting, "
            "Instagram filter appearance, contemporary aesthetic.\n"
        ),
    },
    "pool_party": {
        "label": "🌊 Pool Party",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "Nocturnal luxury pool party. Infinity pool glowing turquoise against the night sky, "
            "city lights or ocean in the distance, string lights and torch lighting around the pool deck. "
            "The subject is at the pool edge — sitting on the rim, legs in the water, "
            "or standing on the wet pool deck, relaxed and confident. "
            "Festive but sophisticated atmosphere.\n\n"
            "**Lighting:** Dramatic nocturnal editorial — "
            "underwater pool glow illuminating from below, warm accent lights from above, "
            "deep blue night sky, specular highlights on wet skin and swimwear.\n\n"
            "**Outfit:** Luxury swimwear or metallic resort wear "
            "faithfully extracted from the reference image provided.\n\n"
            "**Framing:** Cinematic nocturnal editorial, full body or three-quarter, "
            "dramatic contrast, rich deep tones with luminous highlights.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, daylight, outdoor beach, desert setting.\n"
        ),
    },
    "underwater": {
        "body_safe": True,
        "label": "🤿 Underwater",
        "is_dual": False,
        "scene": (
            "**Scene:**\n"
            "Cinematic underwater fashion editorial. The subject is submerged in crystal-clear tropical water — "
            "turquoise and gold-lit from above by filtered sunlight. "
            "Surrounded by golden light rays, tropical fish, coral or floating fabric. "
            "The subject floats or poses gracefully underwater, "
            "hair and fabric moving in slow underwater motion.\n\n"
            "**Lighting:** Underwater caustic light — shimmering golden sun rays filtering through the water surface, "
            "warm golden and turquoise tones, luminous and ethereal atmosphere.\n\n"
            "**Outfit:** Luxury swimwear or flowing underwater-appropriate editorial garment "
            "faithfully extracted from the reference image provided.\n\n"
            "**Framing:** Cinematic underwater wide-to-medium shot, "
            "subject sharp against soft blue-gold water bokeh. "
            "Dreamy, ethereal, high-fashion.\n\n"
            "**NEGATIVE PROMPT — EXTRA:** body hair, chest hair, arm hair, leg hair, peli, dry setting, studio background, indoor.\n"
        ),
    },
    "shooting_editorial": {
        "label": "🎬 Shooting Editorial",
        "is_dual": False,
        "shooting": True,
        "scene": "",
    },

}

# --- STATO UTENTE ---
user_settings = defaultdict(lambda: {'ratio': '2:3', 'count': 1})
user_filter = {}       # uid → filter_key
pending_prompts = {}   # uid → {'full_p': str, 'img': bytes|None, 'is_dual': bool, 'variants': list|None}
last_prompt = {}       # uid → {'full_p': str, 'img': bytes|None}
# --- KEYBOARDS ---
def get_filter_keyboard():
    markup = InlineKeyboardMarkup()
    keys = list(FILTERS.keys())
    # 2 per riga
    for i in range(0, len(keys), 2):
        row_keys = keys[i:i+2]
        markup.row(*[InlineKeyboardButton(FILTERS[k]["label"], callback_data=f"flt_{k}") for k in row_keys])
    return markup

def get_formato_keyboard(uid):
    current = user_settings[uid]
    markup = InlineKeyboardMarkup()
    riga1 = ["2:3", "3:4", "4:5", "9:16"]
    riga2 = ["3:2", "4:3", "5:4", "16:9"]
    markup.row(*[InlineKeyboardButton(f"✅ {r}" if current['ratio'] == r else r, callback_data=f"ar_{r}") for r in riga1])
    markup.row(*[InlineKeyboardButton(f"✅ {r}" if current['ratio'] == r else r, callback_data=f"ar_{r}") for r in riga2])
    return markup

def get_count_keyboard(uid):
    current = user_settings[uid]
    markup = InlineKeyboardMarkup()
    btns = [InlineKeyboardButton(f"✅ {c}" if current['count'] == c else str(c), callback_data=f"n_{c}") for c in [1, 2, 3, 4]]
    markup.row(*btns)
    return markup

def get_confirm_keyboard():
    """Keyboard post-prompt: copia su Flow o torna home."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 Nuova foto",   callback_data="cancel_gen"),
        InlineKeyboardButton("🏠 Home",         callback_data="go_home")
    )
    return markup

# --- ANALISI OUTFIT (pipeline neutra come Architect) ---
def _to_jpeg(img_bytes: bytes) -> bytes:
    """Converte img_bytes in JPEG puro via PIL. Necessario perché Telegram può inviare
    immagini in formato WebP o PNG — l'API Gemini vision richiede JPEG o PNG esplicito.
    Ritorna i bytes JPEG oppure i bytes originali se la conversione fallisce."""
    try:
        buf = io.BytesIO(img_bytes)
        img = Image.open(buf).convert("RGB")
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=92)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"⚠️ _to_jpeg: conversione fallita ({e}), uso bytes originali")
        return img_bytes

def describe_outfit_from_image(img_bytes):
    """Analisi strutturata: sfondo/location separato da outfit, per mantenere entrambi nel prompt."""
    try:
        jpeg_bytes = _to_jpeg(img_bytes)
        logger.info(f"🔍 describe_outfit: {len(jpeg_bytes)} bytes JPEG → Gemini")
        img_part = genai_types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg")
        prompt = (
            "Analyze this image. Return EXACTLY this structure in this order:\n"
            "OUTFIT: [PRIORITY — describe every garment in full detail: name, exact color+HEX code, fabric, cut, fit, coverage, details, embellishments, crystals, feathers, structured elements. e.g. 'lime yellow-green (#C8F500) crystal-encrusted sequin bodice with deep V-neckline']\n"
            "ACCESSORIES: [PRIORITY — every accessory in full detail: headdress, crown, feathers, jewelry, footwear, gloves, wristbands — with color+HEX. If there is a large feather headdress or crown, describe it exhaustively.]\n"
            "COLOR PALETTE: [Dominant HEX codes — e.g. '#C8F500 neon lime-green, #C0C0C0 silver']\n"
            "BACKGROUND: [Location, setting, architecture — max 2 sentences]\n"
            "LIGHTING: [Light source, quality, mood — max 1 sentence]\n"
            "Do NOT describe any person, face, body, age or gender."
        )
        result = gemini.generate(prompt, contents=[img_part])
        if result:
            logger.info(f"👗 Outfit descritto ({len(result)} chars)")
            return result
        logger.warning("⚠️ describe_outfit: Gemini ha restituito None — risposta vuota")
        return None
    except Exception as e:
        logger.error(f"❌ describe_outfit_from_image ECCEZIONE: {e}", exc_info=True)
        return None

# --- CAPTION ---
def generate_caption_from_image(img_bytes):
    """→ shared.CaptionGenerator.from_image()"""
    return caption.from_image(img_bytes)

def generate_caption_from_prompt(outfit_desc, img_bytes=None, filter_key=None, settings=None):
    """→ shared.CaptionGenerator. Usa from_image se outfit_desc non disponibile."""
    if outfit_desc:
        scenario = {"outfit": outfit_desc}
        return caption.from_scenario(scenario)
    elif img_bytes:
        return caption.from_image(img_bytes)
    return None, "⚠️ Caption non disponibile."


def get_shooting_mode_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🗂️ Mosaico 4 foto", callback_data="shooting_mosaic"),
        InlineKeyboardButton("📷 Scatti separati", callback_data="shooting_single")
    )
    return markup

# --- IDENTITÀ BUILDER ---
def build_valeria_identity(safe=False):
    body = VALERIA_BODY_SAFE if safe else VALERIA_BODY_STRONG
    return VALERIA_FACE + body

# --- EDITORIAL WRAPPER ---
EDITORIAL_WRAPPER = (
    "This is a professional editorial post-production request for a high-fashion photography project. "
    "Generate a new original image of the described subject in the specified scene, "
    "maintaining the subject's identity and physical characteristics. "
    "This is a legitimate creative and commercial photography workflow. "
)

# --- BUILD PROMPT ---
def build_full_prompt(filter_key, outfit_description, ratio, scene_override=None):
    """Assembla il prompt completo: editorial wrapper + identita Valeria + scena filtro + outfit + formato."""
    scene = scene_override if scene_override else FILTERS[filter_key]["scene"]
    safe = FILTERS[filter_key].get("body_safe", False)
    identity = build_valeria_identity(safe=safe)
    return (
        f"{EDITORIAL_WRAPPER}\n"
        f"{identity}\n"
        f"{scene}\n"
        f"**Outfit details from reference:**\n{outfit_description}\n\n"
        f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** Reproduce the EXACT colors of the outfit as described above, "
        f"including the precise HEX codes listed in the COLOR PALETTE section. "
        f"Do NOT shift, desaturate, mute, grey-out or reinterpret any color. "
        f"Match the HEX values exactly — vivid cyan-turquoise must stay vivid cyan-turquoise, not powder blue or steel blue. "
        f"Color fidelity is non-negotiable.\n\n"
        f"FORMAT: {ratio}\n"
        f"**⚠️ NEGATIVE PROMPT — IDENTITY:** shaved face, clean-shaven, no beard, missing beard, beard removed, "
        f"stubble instead of beard, female face, young face, missing glasses, face drift, body hair, chest hair, "
        f"arm hair, leg hair, male physique, flat chest, masculine body, desaturated colors, color shift.\n"
    )

# --- SHOOTING EDITORIAL PROMPT ---
def build_shooting_prompt(outfit_desc, mode="mosaic"):
    """Costruisce il prompt per Flow.
    mode='mosaic' → 4 scatti distinti in una sola istanza (comportamento originale).
    mode='single' → 1 scatto singolo, ottimizzato per istanze multiple indipendenti."""
    identity = build_valeria_identity(safe=False)
    if mode == "single":
        prompt = (
            f"{EDITORIAL_WRAPPER}\n"
            f"{identity}\n"
            f"**TASK: SINGLE EDITORIAL SHOT**\n"
            f"Generate one editorial photograph of the subject in the scene below.\n"
            f"Choose one strong pose, framing and expression — make it count.\n\n"
            f"What MUST be present:\n"
            f"- Subject identity (face, hair, beard, glasses — ZERO drift)\n"
            f"- Location and background setting\n"
            f"- Lighting mood and color palette\n"
            f"- Outfit (same garments, same colors, same details)\n\n"
            f"**Reference image analysis:**\n{outfit_desc}\n\n"
            f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** Reproduce the EXACT colors of the outfit as described above, "
            f"including the precise HEX codes listed in the COLOR PALETTE section. "
            f"Do NOT shift, desaturate, mute, grey-out or reinterpret any color. "
            f"Match the HEX values exactly. Color fidelity is non-negotiable.\n\n"
            f"**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location and background described above MUST appear. "
            f"Never replace it with a studio or neutral background.\n\n"
            f"**Technical:** 8K, cinematic, photorealistic.\n"
            f"**NEGATIVE PROMPT:** studio background replacing original location, body hair, chest hair, "
        f"missing glasses, missing beard, shaved face, clean-shaven, beard removed, stubble instead of beard, "
        f"female face, face drift, desaturated colors, color shift.\n"
        )
    else:
        prompt = (
            f"{EDITORIAL_WRAPPER}\n"
            f"{identity}\n"
            f"**TASK: EDITORIAL SHOOTING — 4 DISTINCT SHOTS**\n"
            f"Generate exactly 4 editorial photographs of the same subject in the same scene.\n"
            f"Each of the 4 shots MUST be distinctly different from the others:\n"
            f"- Different pose (standing, seated, reclining, dynamic movement, etc.)\n"
            f"- Different framing (full body, three-quarter, close-up bust, wide angle)\n"
            f"- Different expression (confident, dreamy, fierce, playful)\n"
            f"- Different angle (frontal, profile, three-quarter, back view)\n\n"
            f"What MUST remain identical across all 4 shots:\n"
            f"- Subject identity (face, hair, beard, glasses — ZERO drift)\n"
            f"- Location and background setting\n"
            f"- Lighting mood and color palette\n"
            f"- Outfit (same garments, same colors, same details)\n\n"
            f"**Reference image analysis:**\n{outfit_desc}\n\n"
            f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** Reproduce the EXACT colors of the outfit as described above, "
            f"including the precise HEX codes listed in the COLOR PALETTE section. "
            f"Do NOT shift, desaturate, mute, grey-out or reinterpret any color. "
            f"Match the HEX values exactly. Color fidelity is non-negotiable.\n\n"
            f"**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location and background described above MUST appear "
            f"identically in ALL 4 shots. Never replace it with a studio, neutral background or different setting.\n\n"
            f"**Technical:** 8K, cinematic, photorealistic.\n"
            f"**NEGATIVE PROMPT:** duplicate poses, identical shots, studio background replacing original location, "
            f"wrong setting, body hair, chest hair, missing glasses, missing beard, shaved face, clean-shaven, "
            f"beard removed, stubble instead of beard, female face, face drift, desaturated colors, color shift.\n"
        )
    return prompt

# --- GENERAZIONE IMMAGINE ---

# --- COMANDI ---
@bot.message_handler(commands=['start', 'reset'])
def cmd_start(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name
    user_settings[uid] = {'ratio': '2:3', 'count': 1}
    user_filter.pop(uid, None)
    pending_prompts.pop(uid, None)
    last_prompt.pop(uid, None)
    logger.info(f"▶️ /start da {username} id={uid}")
    bot.send_message(m.chat.id,
        f"<b>✦ ATELIER v{VERSION}</b>\n\n"
        f"Invia una foto del costume o outfit da replicare.\n"
        f"Usa /help per i comandi.",
        reply_markup=get_filter_keyboard())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>✦ ATELIER v{VERSION} — Comandi</b>\n\n"
        f"/start · /reset — Menu principale\n"
        f"/caption — Genera caption da foto\n"
        f"/lastprompt — Mostra ultimo prompt\n"
        f"/settings — Impostazioni (ratio, count)\n"
        f"/info — Versione e informazioni\n"
        f"/help — Questo messaggio\n\n"
        f"<i>Invia una foto per iniziare.</i>"
    )

@bot.message_handler(commands=['info'])
def cmd_info(m):
    uid = m.from_user.id
    flt = user_filter.get(uid)
    flt_label = FILTERS[flt]["label"] if flt else "Nessuno"
    bot.send_message(m.chat.id,
        f"<b>✦ ATELIER v{VERSION}</b>\n\n"
        f"Filtro attivo: <b>{flt_label}</b>\n"
        f"Modello: <code>gemini-3-flash-preview</code>\n\n"
        f"<i>Output: prompt Flow-ready + caption. Nessuna generazione immagini diretta.</i>"
    )


# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Callback non autorizzato: uid={uid}")
        return
    username = call.from_user.username or call.from_user.first_name
    data = call.data

    # Filtro scelto
    if data.startswith("flt_"):
        filter_key = data[4:]
        if filter_key not in FILTERS:
            try: bot.answer_callback_query(call.id, "Filtro non trovato.")
            except Exception: pass
            return
        user_filter[uid] = filter_key
        label = FILTERS[filter_key]["label"]
        is_dual = FILTERS[filter_key]["is_dual"]
        logger.info(f"🎨 {username} (id={uid}) → filtro: {label}")
        try: bot.answer_callback_query(call.id, label)
        except Exception: pass
        dual_note = "\n<i>⚡ Filtro 2-in-1: genera 2 varianti automaticamente</i>" if is_dual else ""
        try:
            if filter_key == "shooting_editorial":
                bot.edit_message_text(
                    f"✅ Filtro: <b>{label}</b>\n\n🎬 Come vuoi generare gli scatti?",
                    cid, call.message.message_id,
                    reply_markup=get_shooting_mode_keyboard())
            else:
                bot.edit_message_text(
                    f"✅ Filtro: <b>{label}</b>{dual_note}\n\n📐 Scegli il formato:",
                    cid, call.message.message_id,
                    reply_markup=get_formato_keyboard(uid))
        except Exception: pass


    # Formato scelto
    elif data.startswith("ar_"):
        new_ratio = data[3:]
        user_settings[uid]['ratio'] = new_ratio
        logger.info(f"📐 {username} (id={uid}) → formato: {new_ratio}")
        try: bot.answer_callback_query(call.id, f"Formato: {new_ratio}")
        except Exception: pass
        flt = user_filter.get(uid)
        try:
            bot.edit_message_text(
                f"✅ Formato: <b>{new_ratio}</b>\n\n🔢 Quante foto?",
                cid, call.message.message_id,
                reply_markup=get_count_keyboard(uid))
        except Exception: pass

    # Numero foto scelto
    elif data.startswith("n_"):
        new_count = int(data[2:])
        user_settings[uid]['count'] = new_count
        flt = user_filter.get(uid)
        flt_label = FILTERS[flt]["label"] if flt else "?"
        logger.info(f"🔢 {username} (id={uid}) → quantità: {new_count}")
        try: bot.answer_callback_query(call.id, f"Quantità: {new_count}")
        except Exception: pass
        # Loop "nuovo filtro stessa foto" — riusa outfit già analizzato
        reuse = pending_prompts.get(uid, {}).get('reuse_outfit', False)
        if reuse:
            saved = last_prompt.get(uid)
            if not saved:
                try: bot.edit_message_text("⚠️ Outfit non trovato. Invia una nuova foto.", cid, call.message.message_id)
                except Exception: pass
                return
            # Ricostruisce prompt con nuovo filtro e outfit salvato
            outfit_desc = saved.get('outfit_desc', '')
            if not outfit_desc:
                try: bot.edit_message_text("⚠️ Outfit non trovato. Invia una nuova foto.", cid, call.message.message_id)
                except Exception: pass
                return
            settings = user_settings[uid]
            flt_obj = FILTERS[flt]
            is_dual = flt_obj["is_dual"]
            if is_dual:
                variant_list = []
                for v in flt_obj["variants"]:
                    full_p = build_full_prompt(flt, outfit_desc, settings['ratio'], scene_override=v["scene"])
                    variant_list.append({'name': v["name"], 'full_p': full_p})
                pending_prompts[uid] = {'is_dual': True, 'variants': variant_list, 'count': 2, 'outfit_desc': outfit_desc}
            else:
                full_p = build_full_prompt(flt, outfit_desc, settings['ratio'])
                pending_prompts[uid] = {'is_dual': False, 'full_p': full_p, 'count': new_count, 'outfit_desc': outfit_desc}
            try:
                bot.edit_message_text(
                    f"✅ Filtro: <b>{flt_label}</b> | Formato: <b>{settings['ratio']}</b> | Foto: <b>{new_count}</b>\n\n"
                    f"♻️ Riuso outfit precedente. Procedere?",
                    cid, call.message.message_id,
                    reply_markup=get_confirm_keyboard())
            except Exception: pass
        else:
            try:
                bot.edit_message_text(
                    f"✅ Filtro: <b>{flt_label}</b> | Formato: <b>{user_settings[uid]['ratio']}</b> | Foto: <b>{new_count}</b>\n\n"
                    f"📸 Invia la foto del costume/outfit di riferimento.",
                    cid, call.message.message_id)
            except Exception: pass

    # Home
    elif data == "go_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        pending_prompts.pop(uid, None)
        user_filter.pop(uid, None)
        bot.send_message(cid,
            f"<b>✦ ATELIER v{VERSION}</b>\n\nScegli il filtro:",
            reply_markup=get_filter_keyboard())

    # Nuova foto
    elif data == "cancel_gen":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        pending_prompts.pop(uid, None)
        bot.send_message(cid, "📸 Invia una nuova foto di riferimento.")

    # Shooting mode scelto
    elif data in ("shooting_mosaic", "shooting_single"):
        mode = "mosaic" if data == "shooting_mosaic" else "single"
        user_settings[uid]['shooting_mode'] = mode
        mode_label = "🗂️ Mosaico 4 foto" if mode == "mosaic" else "📷 Scatti separati"
        logger.info(f"🎬 {username} (id={uid}) → shooting mode: {mode}")
        try: bot.answer_callback_query(call.id, mode_label)
        except Exception: pass
        try:
            bot.edit_message_text(
                f"{mode_label}\n\n"
                f"📸 Invia la foto di riferimento per lo shooting.",
                cid, call.message.message_id)
        except Exception: pass

    elif data == "shooting_menu":
        # Torna al menu iniziale completo
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_settings[uid] = {'ratio': '2:3', 'count': 1}
        user_filter.pop(uid, None)
        pending_prompts.pop(uid, None)
        last_prompt.pop(uid, None)
        logger.info(f"🏠 {username} (id={uid}) → shooting_menu (reset)")
        bot.send_message(cid,
            f"<b>✦ ATELIER v{VERSION}</b>\n\nBenvenuta in atelier. Scegli il filtro:",
            reply_markup=get_filter_keyboard())

    elif data == "shooting_new":
        # Nuovo shooting — stesso filtro, nuova foto, scelta modalità diretta
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_filter[uid] = "shooting_editorial"
        logger.info(f"📸 {username} (id={uid}) → shooting_new")
        bot.send_message(cid,
            f"🎬 <b>Shooting Editorial</b>\n\n🎬 Come vuoi generare gli scatti?",
            reply_markup=get_shooting_mode_keyboard())


    elif data == "cabina_newprompt":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        bot.send_message(cid, "📸 Invia una nuova foto di riferimento.")

    # --- LOOP ---
    elif data == "loop_same":
        # Stessa foto, stesso filtro — riusa last_prompt
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        saved = last_prompt.get(uid)
        if not saved:
            bot.send_message(cid, "⚠️ Sessione scaduta. Invia una nuova foto.")
            return
        flt = user_filter.get(uid)
        flt_label = FILTERS[flt]["label"] if flt else "?"
        logger.info(f"🔄 {username} (id={uid}) → loop same | filtro: {flt_label}")
        if saved.get('is_dual'):
            pdata = {'is_dual': True, 'variants': saved['variants'], 'outfit_desc': saved.get('outfit_desc', '')}
            _run_dual(cid, uid, username, pdata)
        else:
            pdata = {'full_p': saved['full_p'], 'count': user_settings[uid]['count'], 'is_dual': False, 'outfit_desc': saved.get('outfit_desc', '')}
            _run_standard(cid, uid, username, pdata)

    elif data == "loop_new_filter":
        # Nuovo filtro, stessa foto — mostra selezione filtro
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        logger.info(f"🆕 {username} (id={uid}) → loop new filter")
        # Salva outfit description per riuso — sarà nel last_prompt
        bot.send_message(cid, "🎨 Scegli il nuovo filtro:", reply_markup=get_filter_keyboard())
        # Segnala che dopo la selezione filtro deve chiedere conferma senza nuova foto
        user_filter[uid] = None  # reset filtro, outfit già in last_prompt
        pending_prompts[uid] = {'reuse_outfit': True}

    elif data == "loop_new_photo":
        # Nuova foto, stesso filtro
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        flt = user_filter.get(uid)
        flt_label = FILTERS[flt]["label"] if flt else "?"
        logger.info(f"📸 {username} (id={uid}) → loop new photo | filtro: {flt_label}")
        bot.send_message(cid, f"📸 Stesso filtro <b>{flt_label}</b>. Invia la nuova foto.")

    elif data == "loop_reset":
        # Nuova foto, nuovo filtro — reset completo
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_filter.pop(uid, None)
        pending_prompts.pop(uid, None)
        logger.info(f"📸 {username} (id={uid}) → loop reset")
        bot.send_message(cid, "🎨 Scegli il filtro:", reply_markup=get_filter_keyboard())


# --- LOOP KEYBOARD ---
def get_loop_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔄 Stessa foto, stesso filtro", callback_data="loop_same"),
        InlineKeyboardButton("📸 Nuova foto, stesso filtro", callback_data="loop_new_photo"),
    )
    markup.row(
        InlineKeyboardButton("🆕 Nuovo filtro, stessa foto", callback_data="loop_new_filter"),
        InlineKeyboardButton("🔀 Nuova foto, nuovo filtro", callback_data="loop_reset"),
    )
    return markup

# --- GENERAZIONE STANDARD (N foto) ---
# --- HANDLER FOTO ---


@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    cid = m.chat.id
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid} username={m.from_user.username}")
        return
    username = m.from_user.username or m.from_user.first_name

    # Download foto
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)
        logger.info(f"🖼️ Foto da {username} (id={uid}), {len(img_data)} bytes")
    except Exception as e:
        logger.error(f"❌ Errore download foto: {e}", exc_info=True)
        bot.reply_to(m, "❌ Errore nel scaricare la foto. Riprova.")
        return

    # Verifica filtro selezionato
    filter_key = user_filter.get(uid)
    if not filter_key:
        bot.reply_to(m, "⚠️ Nessun filtro selezionato. Usa /start per sceglierlo.")
        return

    # Analisi outfit neutra
    wait_msg = bot.reply_to(m, "⧖ <b>Analisi in corso...</b>")
    outfit_desc = describe_outfit_from_image(img_data)
    try: bot.delete_message(cid, wait_msg.message_id)
    except Exception: pass

    if not outfit_desc:
        # Fallback: descrizione generica
        logger.warning(f"⚠️ Analisi outfit fallita per {username} — uso fallback")
        bot.send_message(cid, "⚠️ <i>Analisi outfit non disponibile, procedo con il testo della didascalia.</i>")

    settings = user_settings[uid]
    flt = FILTERS[filter_key]
    is_dual = flt["is_dual"]

    # --- SHOOTING EDITORIAL: genera prompt per Flow, non immagine ---
    if flt.get("shooting"):
        mode = settings.get('shooting_mode', 'mosaic')
        mode_label = "🗂️ Mosaico 4 foto" if mode == "mosaic" else "📷 Scatti separati"
        full_p = build_shooting_prompt(outfit_desc or "Fashion editorial outfit and setting.", mode)
        last_prompt[uid] = {'full_p': full_p, 'outfit_desc': outfit_desc}

        # --- Genera caption dalla scena ---
        wait_cap = bot.send_message(cid, "✦ <b>Caption...</b>")
        caption_text, cap_err = generate_caption_from_prompt(outfit_desc, img_bytes=img_data)
        try: bot.delete_message(cid, wait_cap.message_id)
        except Exception: pass

        # --- Invia prompt ---
        header = f"🎬 <b>Shooting Editorial</b> | {mode_label}\n\n"
        CHUNK = 3800
        if len(full_p) <= CHUNK:
            bot.send_message(cid,
                f"{header}<code>{html.escape(full_p)}</code>\n\n"
                f"💡 <b>Copia questo prompt su Flow</b>",
                parse_mode="HTML")
        else:
            chunks = [full_p[i:i+CHUNK] for i in range(0, len(full_p), CHUNK)]
            bot.send_message(cid, f"{header}<code>{html.escape(chunks[0])}</code>", parse_mode="HTML")
            for idx, chunk in enumerate(chunks[1:], 2):
                bot.send_message(cid, f"<i>({idx}/{len(chunks)})</i>\n<code>{html.escape(chunk)}</code>", parse_mode="HTML")
            bot.send_message(cid, "💡 <b>Copia questo prompt su Flow</b>", parse_mode="HTML")

        # --- Invia caption in messaggio separato ---
        if caption_text:
            bot.send_message(cid, caption_text, parse_mode=None)
        elif cap_err:
            bot.send_message(cid, f"⚠️ Caption non disponibile: {cap_err}")

        # --- Loop buttons shooting ---
        shooting_loop = InlineKeyboardMarkup()
        shooting_loop.row(
            InlineKeyboardButton("🏠 Menu iniziale", callback_data="shooting_menu"),
            InlineKeyboardButton("📸 Nuovo shooting", callback_data="shooting_new")
        )
        bot.send_message(cid, "Cosa vuoi fare adesso?", reply_markup=shooting_loop)
        return

    if is_dual:
        # Costruisce 2 varianti
        variant_list = []
        for v in flt["variants"]:
            full_p = build_full_prompt(filter_key, outfit_desc, settings['ratio'], scene_override=v["scene"])
            variant_list.append({'name': v["name"], 'full_p': full_p})
        pending_prompts[uid] = {
            'is_dual': True,
            'variants': variant_list,
            'count': 2,
            'outfit_desc': outfit_desc,
        }
        # Salva subito in last_prompt — disponibile anche se generazione fallisce
        last_prompt[uid] = {'is_dual': True, 'variants': variant_list, 'outfit_desc': outfit_desc}
        # Mostra preview prompt dual
        header = (
            f"✅ Filtro: <b>{flt['label']}</b>\n"
            f"⚡ 2 varianti: {' + '.join(v['name'] for v in flt['variants'])}\n\n"
        )
        CHUNK = 3800
        for v in variant_list:
            v_text = f"<b>{v['name']}:</b>\n<code>{html.escape(v['full_p'])}</code>"
            if len(v['full_p']) <= CHUNK:
                bot.send_message(cid, v_text, parse_mode="HTML")
            else:
                chunks = [v['full_p'][i:i+CHUNK] for i in range(0, len(v['full_p']), CHUNK)]
                bot.send_message(cid, f"<b>{v['name']}:</b>\n<code>{html.escape(chunks[0])}</code>", parse_mode="HTML")
                for idx, chunk in enumerate(chunks[1:], 2):
                    bot.send_message(cid, f"<i>({idx}/{len(chunks)})</i>\n<code>{html.escape(chunk)}</code>", parse_mode="HTML")
        sample_p = variant_list[0]['full_p'] if variant_list else ''
        confirm_text = f"{header}Procedere?"
        # --- Caption dal prompt ---
        wait_cap = bot.send_message(cid, "✦ <b>Caption...</b>")
        caption_text, cap_err = generate_caption_from_prompt(outfit_desc, img_bytes=img_data)
        try: bot.delete_message(cid, wait_cap.message_id)
        except Exception: pass
        if caption_text:
            bot.send_message(cid, caption_text, parse_mode=None)
        bot.send_message(cid, confirm_text, reply_markup=get_confirm_keyboard())
    else:
        # Costruisce prompt singolo
        full_p = build_full_prompt(filter_key, outfit_desc, settings['ratio'])
        pending_prompts[uid] = {
            'is_dual': False,
            'full_p': full_p,
            'count': settings['count'],
            'outfit_desc': outfit_desc,
        }
        # Salva subito in last_prompt — disponibile anche se generazione fallisce
        last_prompt[uid] = {'full_p': full_p, 'outfit_desc': outfit_desc}
        header = (
            f"✅ Filtro: <b>{flt['label']}</b> | "
            f"📐 <b>{settings['ratio']}</b> | "
            f"🔢 <b>{settings['count']} foto</b>\n\n"
        )
        # Preview prompt (chunked se lungo)
        CHUNK = 3800
        if len(full_p) <= CHUNK:
            bot.send_message(cid,
                f"{header}<code>{html.escape(full_p)}</code>")
        else:
            chunks = [full_p[i:i+CHUNK] for i in range(0, len(full_p), CHUNK)]
            bot.send_message(cid, f"{header}<code>{html.escape(chunks[0])}</code>")
            for idx, chunk in enumerate(chunks[1:], 2):
                bot.send_message(cid, f"<i>(continua {idx}/{len(chunks)})</i>\n<code>{html.escape(chunk)}</code>")
        # --- Caption dal prompt ---
        wait_cap = bot.send_message(cid, "✦ <b>Caption...</b>")
        caption_text, cap_err = generate_caption_from_prompt(outfit_desc, img_bytes=img_data)
        try: bot.delete_message(cid, wait_cap.message_id)
        except Exception: pass
        if caption_text:
            bot.send_message(cid, caption_text, parse_mode=None)
        bot.send_message(cid, "Procedere?", reply_markup=get_confirm_keyboard())

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text and m.text.startswith('/'):
        return
    uid = m.from_user.id
    bot.reply_to(m, "📸 Invia una foto del costume o outfit da replicare.\nUsa /start per scegliere il filtro.")

# --- SERVER ---
if __name__ == "__main__":
    logger.info(f"✦ Avvio ATELIER v{VERSION}")
    server.start()
    bot.infinity_polling()

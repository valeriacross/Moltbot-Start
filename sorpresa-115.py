import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "1.1.5"

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
    "**MANDATORY BODY — NOT A MALE BODY — OVERRIDE ALL DEFAULTS:**\n"
    "Feminine hourglass proportions, 180cm, 85kg. FULL D-CUP BUST — prominent, natural, clearly visible. "
    "Wide rounded hips, defined waist, full thighs. THIS BODY IS FEMININE. DO NOT GENERATE A MALE PHYSIQUE.\n"
    "Completely hairless body — NO body hair on ALL surfaces. Smooth porcelain skin. "
    "PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous from face → neck → shoulders → chest → arms.\n\n"
    "**Rendering physics:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200, 1/160s, natural bokeh.\n\n"
    "**Watermark:** 'feat. Valeria Cross 👠' — elegant champagne cursive, very small, bottom center, 90% opacity.\n\n"
    "**NEGATIVE PROMPT — FACE:** young face, female face, missing wrinkles, blurred skin, distorted glasses, missing beard, dark hair, face drift.\n"
    "**NEGATIVE PROMPT — HAIR:** long hair, feminine hairstyle, bun, ponytail, black hair, blonde hair, brown hair, curly hair, body hair, chest hair.\n"
    "**NEGATIVE PROMPT — BODY:** male flat chest, masculine frame, blurry hands, extra fingers, mismatched skin tone, body hair.\n"
    "**NEGATIVE PROMPT — SAFETY:** JSON output, text output, captions, metadata. IMAGE GENERATION ONLY. NO JSON LEAKAGE.\n"
)

# --- VARIABILI CASUALI ---
VARIABILI = {
    "sfondo": [
        "white seamless studio", "urban rooftop at night", "venetian palazzo interior",
        "tropical beach at sunset", "misty forest at dawn", "luxury hotel lobby",
        "ancient roman ruins", "tokyo neon street", "alpine meadow", "industrial loft",
        "moroccan riad courtyard", "parisian café terrace", "snowy mountain peak",
        "art deco theatre stage", "botanical garden greenhouse",
        "italian outdoor market, fruit stalls, colorful umbrellas, cobblestone piazza",
        "narrow italian vicolo, laundry hanging, warm stone walls",
        "crowded beach, beach umbrellas, summer chaos",
        "sidewalk café terrace, street life, people passing by",
        "moonlit beach at night, bioluminescent waves, full moon reflection on water, seashells on sand",
        "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
        "giant piano keys, oversized surreal prop, sheet music scattered, rose petals, candles",
        "wooden boat filled with flowers on a calm lake, aerial view",
        "desert at golden hour, sand dunes, warm haze, minimalist horizon",
        "swing hanging from a giant flower, floating above clouds, dark sky",
        "parisian outdoor café, pastel fringed umbrellas mint and pink and lilac, rose-covered stone walls, rattan bistro chairs, marble tables",
        "georgian townhouse marble steps, white ionic columns, cherry blossom trees in full bloom, mixed floral arrangements flanking entrance",
    ],
    "cielo": [
        "clear blue sky", "dramatic storm clouds", "golden hour sunset",
        "starry night sky", "overcast diffused light", "pink and purple dusk",
        "fog and mist", "bright midday sun", "moonlit night", "aurora borealis",
        "warm sunrise", "soft cloudy morning", "deep blue twilight",
        "blazing orange sunset", "pale winter light"
    ],
    "posa": [
        "standing tall, hand on hip", "seated elegantly, legs crossed",
        "walking confidently toward camera", "three-quarter back view, glancing over shoulder",
        "leaning against a wall, arms crossed", "sitting on a chair, relaxed",
        "mid-stride, dynamic movement", "arms raised, dramatic pose",
        "sitting on steps, elbows on knees", "spinning, fabric in motion",
        "profile view, chin up", "looking down, contemplative",
        "jumping, frozen mid-air", "standing at window, looking out",
        "reclining on a chaise, propped on elbow",
        "sitting casually on a low wall or ledge, one leg up, relaxed candid",
        "leaning on a market stall, arms resting, caught mid-conversation",
        "mid-walk, slightly turned, candid street photography moment",
        "seated on oversized surface, legs to one side, high slit visible, one arm propped",
        "carrying a tray or prop, one leg raised, playful diner pose"
    ],
    "espressione": [
        "confident smirk", "serene and calm", "intense direct gaze",
        "mysterious half-smile", "joyful laugh", "pensive and introspective",
        "fierce and bold", "soft and dreamy", "amused and playful",
        "stoic and powerful", "cold and distant", "surprised and wide-eyed",
        "proud and regal", "warm and inviting", "sensual and knowing"
    ],
    "outfit_top": [
        "structured blazer in deep burgundy, open neckline", "sheer silk blouse with ruffles, deep V",
        "leather biker jacket, open chest", "elegant off-shoulder fitted top",
        "sequined crop top", "silk wrap top with plunging neckline",
        "tailored white shirt open at collar, knotted at waist", "velvet bustier corset",
        "backless halter neck top", "draped one-shoulder top",
        "lace-up corset top in satin", "strapless structured bodice",
        "one-shoulder crop top with long sleeve", "floral bustier with thin spaghetti straps and ruffle trim",
        "tiered ruffle organza top, dramatic volume", "retro waitress dress with white frilled apron"
    ],
    "outfit_bottom": [
        "mini skirt in faux leather", "micro mini skirt in sequins",
        "structured pencil skirt in black, above knee", "sequined mini skirt",
        "asymmetric wrap mini skirt", "pleated skirt at knee length in silk",
        "high-waisted a-line skirt, above knee", "sheer layered tulle mini skirt",
        "fitted wrap skirt with deep side slit, above knee", "bodycon mini dress",
        "flared mini skirt in satin", "tailored mini skirt in tweed",
        "ruffled mini skirt in organza", "pleated tennis skirt in white",
        "floor-length mermaid skirt with thigh-high slit, satin",
        "chunky knit crochet maxi skirt with high front slit"
    ],
    "scarpe": [
        "stiletto ankle boots in patent leather", "strappy gold heeled sandals",
        "classic pumps in red", "knee-high suede boots",
        "embellished mule heels", "pointed-toe kitten heels",
        "metallic heeled sandals", "block-heel mules in nude",
        "espadrille wedges", "crystal-embellished heels",
        "strappy stiletto sandals in silver", "peep-toe pumps in nude",
        "satin heeled mules", "ankle-strap heeled sandals",
        "platform heels in black patent"
    ],
    "colore": [
        "monochromatic all-black", "vibrant electric blue tones",
        "soft pastel palette", "earthy terracotta and ochre",
        "bold red and gold", "cool grey and silver",
        "warm ivory and cream", "emerald green and jewel tones",
        "dusty rose and blush", "neon pop art palette",
        "deep navy and midnight blue", "warm amber and cognac",
        "stark white and ice", "rich purple and plum",
        "copper and bronze metallic"
    ],
    "accessori": [
        "oversized sunglasses and gold chain necklace",
        "wide-brim felt hat and leather gloves",
        "statement pearl earrings and silk scarf",
        "chunky silver cuff bracelet",
        "designer handbag in crocodile print",
        "layered gold necklaces",
        "dramatic feather boa",
        "structured fascinator hat",
        "vintage brooch on lapel",
        "long opera gloves",
        "stacked bangles and rings",
        "geometric earrings and minimalist watch",
        "fur stole draped over shoulders",
        "headband with embellishment",
        "no accessories — clean minimal look"
    ],
    "stile": [
        "high fashion editorial Vogue", "street style documentary",
        "vintage 1960s glamour", "cyberpunk futuristic",
        "romantic Victorian", "minimalist architectural",
        "maximalist baroque", "sportswear luxury",
        "dark gothic editorial", "tropical resort wear",
        "Parisian chic", "Japanese avant-garde",
        "American preppy", "bohemian festival",
        "retro 1980s power dressing",
        "candid street photography, authentic daily life, shallow depth of field, people blurred in background",
        "authentic italian summer lifestyle, documentary realism, no posing",
        "surrealist oversized prop photography, impossible scale, dreamlike",
        "total monochrome editorial, head-to-toe single color, maximum impact"
    ],
    "luce": [
        "dramatic chiaroscuro side lighting", "soft diffused natural light",
        "harsh direct sunlight with deep shadows", "warm golden hour backlight",
        "cool blue moonlight", "studio softbox portrait lighting",
        "neon sign ambient glow", "candlelight warm flicker",
        "mixed daylight and artificial", "hard rim lighting from behind",
        "flat bright fashion photography light", "moody low-key lighting",
        "dappled light through leaves", "reflected light from water",
        "soft window light",
        "harsh italian summer midday sun, hard shadows, warm golden skin glow, squinting light"
    ],
    "punto_di_ripresa": [
        "85mm portrait, eye level", "wide angle 24mm full body",
        "high angle looking down", "low angle looking up",
        "close-up on face and shoulders", "from behind, three-quarter",
        "bird's eye view from above", "dutch angle tilt",
        "telephoto compressed 200mm", "mid-shot waist up",
        "full body wide shot", "over-shoulder perspective",
        "side profile full body", "environmental portrait, subject in context",
        "tight editorial crop at three-quarter length"
    ],
    "pattern": [
        "none — solid color",
        "classic polka dots, large white dots on dark fabric",
        "coordinated total polka dot look, top and bottom matching",
        "thin pinstripes in contrasting color",
        "bold horizontal stripes, nautical",
        "floral print, large blooms, tropical",
        "small floral ditsy print with lace trim details",
        "animal print — leopard",
        "animal print — zebra",
        "tartan plaid in earthy tones",
        "abstract geometric print",
        "paisley in jewel tones",
        "tie-dye swirl, boho",
        "houndstooth black and white",
        "chunky crochet knit texture, handmade artisan look",
        "lightning bolt metallic print on silver fabric",
        "multicolor pastel fur patchwork, fluffy blocks of color",
        "monogram luxury pattern, all-over print"
    ],
    "stile_artistico": [
        "none — photorealistic",
        "🎨 Van Gogh — swirling impasto brushstrokes, vivid expressionist color, post-impressionist turbulence",
        "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism",
        "🌿 Klimt — gold leaf ornamentation, Art Nouveau arabesque patterns, Byzantine opulence",
        "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles",
        "💃 Toulouse-Lautrec — Belle Époque poster art, cabaret atmosphere, flat ink outlines",
        "🌊 Hokusai — Japanese woodblock print, ukiyo-e flat color, bold ink contours",
        "🖤 Aubrey Beardsley — Art Nouveau black ink illustration, decadent Victorian line art",
        "🌹 Mucha — Art Nouveau decorative poster, floral halo, soft pastel lithograph",
        "💥 Roy Lichtenstein — pop art Ben-Day dots, bold comic book outlines, primary colors",
        "🌑 Caravaggio — tenebrism chiaroscuro, dramatic candlelight, baroque realism",
        "🎭 DIRECTOR'S CUT — cinematic anamorphic lens flare, film grain 35mm, movie still color grading, letterbox aspect"
    ],
    "filtro_fx": [
        "none — pure photorealistic render"
    ]
}

VARIABILI_LABELS = {
    "sfondo": "🏛️ Sfondo",
    "cielo": "🌤️ Cielo",
    "posa": "🧍 Posa",
    "espressione": "😏 Espressione",
    "outfit_top": "👚 Top",
    "outfit_bottom": "👗 Bottom",
    "scarpe": "👠 Scarpe",
    "colore": "🎨 Colore",
    "accessori": "💍 Accessori",
    "stile": "✨ Stile",
    "luce": "💡 Luce",
    "punto_di_ripresa": "📷 Inquadratura",
    "filtro_fx": "✨ Filtro FX",
    "pattern": "🔵 Pattern",
    "stile_artistico": "🎨 Stile Artistico"
}

# --- TAG COMPATIBILITÀ ---

# Sfondi indoor: il cielo non è visibile → va neutralizzato
SFONDI_INDOOR = {
    "luxury hotel lobby", "venetian palazzo interior", "industrial loft",
    "art deco theatre stage", "botanical garden greenhouse",
    "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
    "giant piano keys, oversized surreal prop, sheet music scattered, rose petals, candles",
    "moroccan riad courtyard",
}

# Sfondi surreali/impossibili: luce realistica fotografica non è coerente
SFONDI_SURREALI = {
    "swing hanging from a giant flower, floating above clouds, dark sky",
    "giant piano keys, oversized surreal prop, sheet music scattered, rose petals, candles",
    "wooden boat filled with flowers on a calm lake, aerial view",
}

# Luci compatibili con sfondi surreali (atmosferiche, non fotografiche)
LUCI_SURREALI_OK = {
    "candlelight warm flicker", "cool blue moonlight", "neon sign ambient glow",
    "dramatic chiaroscuro side lighting", "moody low-key lighting",
    "soft diffused natural light", "dappled light through leaves",
    "reflected light from water",
}

# Luci fotografiche da bloccare con surreale
LUCI_FOTOGRAFICHE = {
    "harsh italian summer midday sun, hard shadows, warm golden skin glow, squinting light",
    "flat bright fashion photography light",
    "studio softbox portrait lighting",
    "harsh direct sunlight with deep shadows",
    "mixed daylight and artificial",
}

# Pattern con palette cromatica propria forte → colore generico si annulla
PATTERN_CON_COLORE_PROPRIO = {
    "animal print — leopard",
    "animal print — zebra",
    "houndstooth black and white",
    "tartan plaid in earthy tones",
    "tie-dye swirl, boho",
    "multicolor pastel fur patchwork, fluffy blocks of color",
    "paisley in jewel tones",
    "floral print, large blooms, tropical",
    "small floral ditsy print with lace trim details",
    "abstract geometric print",
    "lightning bolt metallic print on silver fabric",
    "monogram luxury pattern, all-over print",
    "coordinated total polka dot look, top and bottom matching",
    "classic polka dots, large white dots on dark fabric",
    "bold horizontal stripes, nautical",
    "thin pinstripes in contrasting color",
    "chunky crochet knit texture, handmade artisan look",
}

# Palette colore da bloccare se pattern ha colori propri (troppo generiche o contraddittorie)
COLORI_INCOMPATIBILI_CON_PATTERN = {
    "monochromatic all-black",
    "stark white and ice",
    "warm ivory and cream",
    "soft pastel palette",
    "neon pop art palette",
}

# Stile "total monochrome" incompatibile con qualsiasi pattern colorato
STILE_MONOCHROME = "total monochrome editorial, head-to-toe single color, maximum impact"

# FX che richiedono punto di ripresa specifico per funzionare bene
FX_PUNTO_RIPRESA_FORZATO = {
    "🪆 Action Figure — collectible fashion action figure in blister packaging, plastic toy aesthetic, retail product photography":
        "wide angle 24mm full body",
    "👯 Art Doll Exhibition — high-end fashion art doll, porcelain bisque finish, glass eyes, collector doll display, museum exhibition":
        "85mm portrait, eye level",
    "☁️ Cloud Sculpture — body sculpted entirely from dense cumulus clouds, whipped cream cloud texture, sky installation art":
        "wide angle 24mm full body",
}

# Correzione caption /start: 14 variabili (era rimasto "12" nel testo)
_START_VAR_COUNT = "14"

# --- TAG FORMATO ---
# Mappa sfondo → aspect ratio ottimale (parametro API reale)
SFONDI_ORIZZONTALI = {
    "desert at golden hour, sand dunes, warm haze, minimalist horizon",
    "alpine meadow",
    "snowy mountain peak",
    "moonlit beach at night, bioluminescent waves, full moon reflection on water, seashells on sand",
    "tropical beach at sunset",
    "crowded beach, beach umbrellas, summer chaos",
    "wooden boat filled with flowers on a calm lake, aerial view",
    "misty forest at dawn",
}

SFONDI_QUADRATI = {
    "white seamless studio",
    "moroccan riad courtyard",
    "botanical garden greenhouse",
    "industrial loft",
}

SFONDI_SURREALI_AUTO = {
    "swing hanging from a giant flower, floating above clouds, dark sky",
    "giant piano keys, oversized surreal prop, sheet music scattered, rose petals, candles",
}

# Punti di ripresa che forzano formato indipendentemente dallo sfondo
RIPRESA_ORIZZONTALE = {
    "bird's eye view from above",
    "wide angle 24mm full body",
    "telephoto compressed 200mm",
}
RIPRESA_QUADRATA = {
    "close-up on face and shoulders",
}

# FX che suggeriscono formato specifico
FX_FORMATO = {
    "🪆 Action Figure — collectible fashion action figure in blister packaging, plastic toy aesthetic, retail product photography": "3:4",
    "👯 Art Doll Exhibition — high-end fashion art doll, porcelain bisque finish, glass eyes, collector doll display, museum exhibition": "3:4",
    "🌌 Galaxy Couture — cosmic galaxy backdrop, nebula colors, star field, deep space atmosphere, Milky Way swirls, cosmic dust": "9:16",
    "☁️ Cloud Sculpture — body sculpted entirely from dense cumulus clouds, whipped cream cloud texture, sky installation art": "2:3",
}

# --- ASSE 11: STILE ARTISTICO OVERRIDES ---
# Per ogni stile artistico: parametri da forzare o filtrare per coerenza visiva.
# 'sfondo_ok': solo questi sfondi sono compatibili (se non None)
# 'sfondo_escludi': sfondi da escludere
# 'colore_ok': palette compatibili (se non None, sceglie solo tra queste)
# 'pattern': forza a questo valore
# 'accessori_escludi': accessori che rompono l'atmosfera
# 'punto_di_ripresa_ok': inquadrature compatibili

STILE_ARTISTICO_OVERRIDES = {
    "🎨 Van Gogh — swirling impasto brushstrokes, vivid expressionist color, post-impressionist turbulence": {
        "colore_ok": [
            "vibrant electric blue tones", "bold red and gold", "earthy terracotta and ochre",
            "emerald green and jewel tones", "rich purple and plum", "warm amber and cognac",
        ],
        "pattern": "none — solid color",
        "sfondo_escludi": {
            "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
            "tokyo neon street", "urban rooftop at night",
        },
    },
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism": {
        "colore_ok": [
            "soft pastel palette", "cool grey and silver", "warm ivory and cream",
            "stark white and ice", "deep navy and midnight blue",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio", "desert at golden hour, sand dunes, warm haze, minimalist horizon",
            "misty forest at dawn", "snowy mountain peak", "alpine meadow",
            "swing hanging from a giant flower, floating above clouds, dark sky",
        ],
    },
    "🌿 Klimt — gold leaf ornamentation, Art Nouveau arabesque patterns, Byzantine opulence": {
        "colore_ok": [
            "bold red and gold", "copper and bronze metallic", "rich purple and plum",
            "emerald green and jewel tones", "warm amber and cognac",
        ],
        "pattern": "none — solid color",
        "sfondo_escludi": {
            "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
            "tokyo neon street", "urban rooftop at night", "industrial loft",
        },
    },
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "bold red and gold",
            "vibrant electric blue tones",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio",
            "art deco theatre stage",
            "industrial loft",
        ],
        "punto_di_ripresa_ok": [
            "85mm portrait, eye level", "mid-shot waist up", "full body wide shot",
            "wide angle 24mm full body", "tight editorial crop at three-quarter length",
        ],
    },
    "💃 Toulouse-Lautrec — Belle Époque poster art, cabaret atmosphere, flat ink outlines": {
        "colore_ok": [
            "dusty rose and blush", "warm ivory and cream", "earthy terracotta and ochre",
            "rich purple and plum", "warm amber and cognac",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "art deco theatre stage", "parisian café terrace",
            "parisian outdoor café, pastel fringed umbrellas mint and pink and lilac, rose-covered stone walls, rattan bistro chairs, marble tables",
            "venetian palazzo interior",
        ],
    },
    "🌊 Hokusai — Japanese woodblock print, ukiyo-e flat color, bold ink contours": {
        "colore_ok": [
            "deep navy and midnight blue", "stark white and ice", "bold red and gold",
            "cool grey and silver",
        ],
        "pattern": "none — solid color",
        "sfondo_escludi": {
            "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
            "urban rooftop at night", "industrial loft",
        },
    },
    "🖤 Aubrey Beardsley — Art Nouveau black ink illustration, decadent Victorian line art": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "rich purple and plum",
            "deep navy and midnight blue",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio", "venetian palazzo interior", "art deco theatre stage",
            "botanical garden greenhouse",
        ],
    },
    "🌹 Mucha — Art Nouveau decorative poster, floral halo, soft pastel lithograph": {
        "colore_ok": [
            "soft pastel palette", "dusty rose and blush", "warm ivory and cream",
            "emerald green and jewel tones",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio", "botanical garden greenhouse",
            "parisian outdoor café, pastel fringed umbrellas mint and pink and lilac, rose-covered stone walls, rattan bistro chairs, marble tables",
            "georgian townhouse marble steps, white ionic columns, cherry blossom trees in full bloom, mixed floral arrangements flanking entrance",
        ],
    },
    "💥 Roy Lichtenstein — pop art Ben-Day dots, bold comic book outlines, primary colors": {
        "colore_ok": [
            "bold red and gold", "vibrant electric blue tones", "stark white and ice",
            "neon pop art palette",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio", "urban rooftop at night",
            "retro american diner, checkered floor, neon signs, mint green booths, pendant lamps",
        ],
    },
    "🌑 Caravaggio — tenebrism chiaroscuro, dramatic candlelight, baroque realism": {
        "colore_ok": [
            "monochromatic all-black", "earthy terracotta and ochre", "warm amber and cognac",
            "bold red and gold", "deep navy and midnight blue",
        ],
        "pattern": "none — solid color",
        "sfondo_ok": [
            "white seamless studio", "venetian palazzo interior", "ancient roman ruins",
            "art deco theatre stage",
            "giant piano keys, oversized surreal prop, sheet music scattered, rose petals, candles",
        ],
    },
    "🎭 DIRECTOR'S CUT — cinematic anamorphic lens flare, film grain 35mm, movie still color grading, letterbox aspect": {
        "colore_ok": None,  # tutti i colori compatibili con il cinema
        "pattern": None,    # pattern ammessi
        "sfondo_escludi": set(),  # nessuna esclusione
    },
}

# FX che hanno un loro sfondo implicito → lo sfondo estratto va neutralizzato
FX_SFONDO_PROPRIO = {
    "🌌 Galaxy Couture — cosmic galaxy backdrop, nebula colors, star field, deep space atmosphere, Milky Way swirls, cosmic dust",
    "☁️ Cloud Sculpture — body sculpted entirely from dense cumulus clouds, whipped cream cloud texture, sky installation art",
    "🪆 Action Figure — collectible fashion action figure in blister packaging, plastic toy aesthetic, retail product photography",
    "👯 Art Doll Exhibition — high-end fashion art doll, porcelain bisque finish, glass eyes, collector doll display, museum exhibition",
    "🎐 Stained Glass — stained glass window aesthetic, lead came outlines, jewel-tone glass panels, cathedral light, mosaic fragmentation",
}
FX_SFONDO_SOSTITUTO = "white seamless studio"

def get_formato(combo):
    """Determina l'aspect ratio ottimale in base alla combinazione estratta.
    Priorità: FX > punto_di_ripresa > sfondo > default 2:3
    Nota: 1:1 riservato ai mosaici, non usato per immagini singole."""
    fx = combo.get('filtro_fx', '')
    pdp = combo.get('punto_di_ripresa', '')
    sfondo = combo.get('sfondo', '')

    # 1. FX con formato specifico
    if fx in FX_FORMATO:
        return FX_FORMATO[fx]

    # 2. Punto di ripresa dominante
    if pdp in RIPRESA_ORIZZONTALE:
        return "16:9"
    if pdp in RIPRESA_QUADRATA:
        return "4:5"

    # 3. Sfondo surreale senza gravità → Auto (Gemini sceglie)
    if sfondo in SFONDI_SURREALI_AUTO:
        return "auto"

    # 4. Sfondo orizzontale
    if sfondo in SFONDI_ORIZZONTALI:
        return random.choice(["16:9", "3:2"])

    # 5. Sfondo quadrato/neutro → 4:5 (non 1:1, riservato mosaici)
    if sfondo in SFONDI_QUADRATI:
        return "4:5"

    # 6. Default: verticale portrait
    return "2:3"


def estrai_combinazione():
    """Estrae una opzione casuale per ogni variabile.
    Applica cascata di compatibilità su 11 assi:
    1. FX attivo → azzera stile_artistico
    2. stile_artistico attivo → azzera stile fashion
    3. Pattern con palette propria → neutralizza colore incompatibile
    4. Pattern attivo → blocca stile total-monochrome
    5. Sfondo indoor → neutralizza cielo
    6. Sfondo surreale → sostituisce luce fotografica con luce atmosferica
    7. Certi FX → forzano punto di ripresa ottimale
    8. Stile_artistico attivo → neutralizza luce fotografica
    9. Calcola formato ottimale
    10. FX con sfondo proprio → neutralizza sfondo terrestre
    11. Stile_artistico attivo → forza coerenza sfondo, colore, pattern
    """
    combo = {k: random.choice(v) for k, v in VARIABILI.items()}

    # 1. FX attivo → azzera stile_artistico
    if combo['filtro_fx'] != 'none — pure photorealistic render':
        combo['stile_artistico'] = 'none — photorealistic'

    # 2. stile_artistico attivo → azzera stile fashion
    if not combo['stile_artistico'].startswith('none'):
        combo['stile'] = 'none — see artistic style'

    # 3. Pattern con palette propria forte → neutralizza colore se incompatibile
    if combo['pattern'] in PATTERN_CON_COLORE_PROPRIO:
        if combo['colore'] in COLORI_INCOMPATIBILI_CON_PATTERN:
            # Scegli una palette neutra/complementare al pattern
            palette_neutre = [c for c in VARIABILI['colore'] if c not in COLORI_INCOMPATIBILI_CON_PATTERN]
            combo['colore'] = random.choice(palette_neutre)

    # 4. Pattern attivo → blocca stile total-monochrome
    if combo['pattern'] not in ('none — solid color',) and combo['stile'] == STILE_MONOCHROME:
        stili_ok = [s for s in VARIABILI['stile'] if s != STILE_MONOCHROME]
        combo['stile'] = random.choice(stili_ok)

    # 5. Sfondo indoor → neutralizza cielo (non visibile)
    if combo['sfondo'] in SFONDI_INDOOR:
        combo['cielo'] = 'none — indoor scene'

    # 6. Sfondo surreale → sostituisce luce fotografica con luce atmosferica
    if combo['sfondo'] in SFONDI_SURREALI:
        if combo['luce'] in LUCI_FOTOGRAFICHE:
            combo['luce'] = random.choice(list(LUCI_SURREALI_OK))

    # 7. Stile artistico attivo → neutralizza luce fotografica (senza senso in quadri/illustrazioni)
    if not combo['stile_artistico'].startswith('none'):
        if combo['luce'] in LUCI_FOTOGRAFICHE:
            combo['luce'] = random.choice(list(LUCI_SURREALI_OK))

    # 8. Certi FX forzano punto di ripresa ottimale
    if combo['filtro_fx'] in FX_PUNTO_RIPRESA_FORZATO:
        combo['punto_di_ripresa'] = FX_PUNTO_RIPRESA_FORZATO[combo['filtro_fx']]

    # 10. FX con sfondo proprio → neutralizza sfondo terrestre
    if combo['filtro_fx'] in FX_SFONDO_PROPRIO:
        combo['sfondo'] = FX_SFONDO_SOSTITUTO
        combo['cielo'] = 'none — indoor scene'

    # 11. Stile artistico attivo → forza coerenza sfondo, colore, pattern
    if not combo['stile_artistico'].startswith('none'):
        overrides = STILE_ARTISTICO_OVERRIDES.get(combo['stile_artistico'])
        if overrides:
            # Pattern: forza a solid color se specificato
            if 'pattern' in overrides and overrides['pattern'] is not None:
                combo['pattern'] = overrides['pattern']
            # Colore: scegli solo tra palette compatibili
            if overrides.get('colore_ok'):
                if combo['colore'] not in overrides['colore_ok']:
                    combo['colore'] = random.choice(overrides['colore_ok'])
            # Sfondo: se c'è sfondo_ok, scegli solo tra quelli
            if overrides.get('sfondo_ok'):
                if combo['sfondo'] not in overrides['sfondo_ok']:
                    combo['sfondo'] = random.choice(list(overrides['sfondo_ok']))
            # Sfondo: escludi sfondi esplicitamente incompatibili
            elif overrides.get('sfondo_escludi'):
                if combo['sfondo'] in overrides['sfondo_escludi']:
                    sfondi_ok = [s for s in VARIABILI['sfondo'] if s not in overrides['sfondo_escludi']]
                    combo['sfondo'] = random.choice(sfondi_ok)
            # Punto di ripresa: limita se specificato
            if overrides.get('punto_di_ripresa_ok'):
                if combo['punto_di_ripresa'] not in overrides['punto_di_ripresa_ok']:
                    combo['punto_di_ripresa'] = random.choice(overrides['punto_di_ripresa_ok'])

    # 9. Calcola formato ottimale in base alla combo finale (dopo asse 11)
    combo['_formato'] = get_formato(combo)

    return combo

def _cielo_str(combo):
    """Restituisce la stringa cielo solo se non neutralizzata."""
    return "" if combo['cielo'].startswith('none') else f", {combo['cielo']}"

def build_prompt(combo):
    """Costruisce il prompt completo da una combinazione."""
    scene = (
        f"**Scene:** {combo['sfondo']}{_cielo_str(combo)}.\n"
        f"**Pose:** {combo['posa']}.\n"
        f"**Expression:** {combo['espressione']}.\n"
        f"**Outfit:** {combo['outfit_top']} with {combo['outfit_bottom']}, {combo['scarpe']}.\n"
        + (f"**Pattern:** {combo['pattern']}.\n" if not combo['pattern'].startswith('none') else "")
        + f"**Color palette:** {combo['colore']}.\n"
        f"**Accessories:** {combo['accessori']}.\n"
        + (f"**Style:** {combo['stile']}.\n" if not combo['stile'].startswith('none') else "")
        + f"**Lighting:** {combo['luce']}.\n"
        f"**Shot:** {combo['punto_di_ripresa']}.\n"
        + (f"**FX Style:** {combo['filtro_fx']}.\n" if combo['filtro_fx'] != "none — pure photorealistic render" else "")
        + (f"**Artistic Style:** {combo['stile_artistico']}.\n" if not combo['stile_artistico'].startswith("none") else "")
    )
    return VALERIA_IDENTITY + "\n" + scene

def build_generic_prompt(combo):
    """Prompt generico senza identità Valeria — da condividere con i followers."""
    return (
        "Ultra-photorealistic 8K high-fashion editorial photography.\n\n"
        f"**Scene:** {combo['sfondo']}{_cielo_str(combo)}.\n"
        f"**Pose:** {combo['posa']}.\n"
        f"**Expression:** {combo['espressione']}.\n"
        f"**Outfit:** {combo['outfit_top']} with {combo['outfit_bottom']}, {combo['scarpe']}.\n"
        + (f"**Pattern:** {combo['pattern']}.\n" if not combo['pattern'].startswith('none') else "")
        + f"**Color palette:** {combo['colore']}.\n"
        f"**Accessories:** {combo['accessori']}.\n"
        + (f"**Style:** {combo['stile']}.\n" if not combo['stile'].startswith('none') else "")
        + f"**Lighting:** {combo['luce']}.\n"
        f"**Shot:** {combo['punto_di_ripresa']}.\n"
        + (f"**FX Style:** {combo['filtro_fx']}.\n" if combo['filtro_fx'] != "none — pure photorealistic render" else "")
        + (f"**Artistic Style:** {combo['stile_artistico']}.\n" if not combo['stile_artistico'].startswith("none") else "")
        + "\n"
        + "Subsurface Scattering, Global Illumination, Ambient Occlusion. "
        "85mm, f/2.8, ISO 200, natural bokeh."
    )

def build_threads_caption(combo):
    """Mini caption Threads: 4 parole chiave brevi + emoji, copiabile separatamente."""
    tokens = []

    # Pattern: solo la parola chiave (leopard, zebra, stripes…)
    if not combo['pattern'].startswith('none'):
        raw = combo['pattern'].split('—')[-1].strip()
        token = raw.split()[0].rstrip(',').lower()
        tokens.append(token)

    # Sfondo: prima parola significativa (no articoli)
    skip_words = {'a', 'an', 'the', 'at', 'in', 'on', 'with', 'and', 'of', 'from'}
    sfondo_words = [w.rstrip(',') for w in combo['sfondo'].split() if w.lower() not in skip_words]
    if sfondo_words:
        tokens.append(sfondo_words[0].lower())

    # FX: prima parola dopo l'emoji e il —
    if combo['filtro_fx'] != "none — pure photorealistic render":
        parts = combo['filtro_fx'].split('—')
        if len(parts) > 1:
            fx_word = parts[1].strip().split()[0].rstrip(',').lower()
            tokens.append(fx_word)

    # Stile artistico: nome artista/stile (prima parola non-emoji)
    if not combo['stile_artistico'].startswith('none'):
        for word in combo['stile_artistico'].split():
            if word[0].isalpha():
                tokens.append(word.lower())
                break

    # Fallback: colore → prima parola; posa → prima parola
    extras = [
        combo['colore'].split()[0].lower(),
        combo['espressione'].split()[0].lower(),
        combo['outfit_top'].split()[0].lower(),
    ]
    for e in extras:
        if len(tokens) >= 4:
            break
        if e and e not in tokens:
            tokens.append(e)

    tokens = tokens[:4]

    # Emoji più rappresentativa
    if combo['filtro_fx'] != "none — pure photorealistic render":
        first_char = combo['filtro_fx'][0]
        emoji = first_char if ord(first_char) > 127 else "✨"
    elif not combo['stile_artistico'].startswith('none'):
        first_char = combo['stile_artistico'][0]
        emoji = first_char if ord(first_char) > 127 else "🎨"
    elif not combo['pattern'].startswith('none'):
        emoji = "🔵"
    else:
        emoji = "👠"

    return " ".join(tokens) + f" {emoji}"

def format_combinazione(combo):
    """Formatta la combinazione estratta per la visualizzazione."""
    lines = []
    for k, label in VARIABILI_LABELS.items():
        lines.append(f"{label}: <b>{combo[k]}</b>")
    # Mostra formato calcolato
    fmt = combo.get('_formato', '2:3')
    lines.append(f"📐 Formato: <b>{fmt}</b>")
    return "\n".join(lines)

# --- GENERAZIONE ---
def execute_generation(full_prompt, formato="2:3"):
    try:
        contents = [full_prompt]
        if MASTER_PART:
            contents.append(MASTER_PART)
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")

        def _call():
            logger.info(f"   📤 Prompt a Gemini ({len(full_prompt)} chars) | formato={formato}")
            img_cfg = genai_types.ImageConfig(image_size="2K")
            if formato and formato != "auto":
                img_cfg = genai_types.ImageConfig(image_size="2K", aspect_ratio=formato)
            return client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=img_cfg,
                    safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in
                                     ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH",
                                      "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
                )
            )

        for attempt in range(2):
            with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_call)
                try:
                    response = future.result(timeout=120)
                    break
                except _cf.TimeoutError:
                    if attempt == 0:
                        logger.warning("⚠️ Timeout (120s) — retry tra 15s")
                        time.sleep(15)
                    else:
                        logger.error("❌ Timeout anche al retry")
                        return None, "⏱️ Timeout: Gemini non ha risposto dopo 2 tentativi. Riprova."
        else:
            return None, "⏱️ Timeout: Gemini non ha risposto. Riprova tra qualche minuto."

        if not response.candidates:
            return None, "❌ Nessun risultato dall'API. Riprova."

        candidate = response.candidates[0]
        if candidate.finish_reason != "STOP":
            return None, f"🛡️ Generazione bloccata.\nMotivo: <b>{candidate.finish_reason}</b>"

        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None

        return None, "❌ Nessuna immagine nella risposta. Riprova."

    except Exception as e:
        logger.error(f"❌ Errore execute_generation: {e}", exc_info=True)
        return None, f"❌ Errore interno:\n<code>{html.escape(str(e))}</code>"

# --- BOT ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎲 Tira i dadi!", callback_data="tira"))
    return markup

def get_confirm_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Conferma — Genera!", callback_data="conferma"),
        InlineKeyboardButton("🎲 Ritira i dadi", callback_data="tira")
    )
    return markup

def get_retry_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Nuova sorpresa", callback_data="tira"),
        InlineKeyboardButton("🔁 Riprova questa", callback_data="riprova")
    )
    return markup

# --- /start ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"🎲 /start da {username} (id={uid})")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎲 Tira i dadi!", callback_data="tira"))
    bot.send_message(message.chat.id,
        f"<b>🎲 SORPRESA v{VERSION}</b>\n\n"
        f"Ogni volta che premi il pulsante, il bot estrae casualmente <b>{_START_VAR_COUNT} variabili</b> "
        f"e genera un'immagine unica di Valeria Cross.\n\n"
        f"Non vedrai mai la stessa combinazione due volte.",
        reply_markup=markup)

# --- /info ---
@bot.message_handler(commands=['info'])
def handle_info(message):
    lines = [f"<b>🎲 SORPRESA v{VERSION}</b>\n\n<b>Variabili disponibili:</b>"]
    for k, label in VARIABILI_LABELS.items():
        lines.append(f"{label}: <b>{len(VARIABILI[k])}</b> opzioni")
    total = 1
    for v in VARIABILI.values():
        total *= len(v)
    lines.append(f"\n<b>Combinazioni possibili: {total:,}</b>")
    bot.send_message(message.chat.id, "\n".join(lines))

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
        # Estrae nuova combinazione e mostra per conferma
        combo = estrai_combinazione()
        last_combo[uid] = combo
        combo_text = format_combinazione(combo)
        bot.send_message(cid,
            f"🎲 <b>Combinazione estratta:</b>\n\n{combo_text}\n\n"
            f"Vuoi generare questa combinazione?",
            reply_markup=get_confirm_keyboard())
        logger.info(f"🎲 {username} (id={uid}) — combinazione estratta")

    elif call.data == "conferma":
        # Genera con la combo salvata
        combo = last_combo.get(uid)
        if not combo:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        combo_text = format_combinazione(combo)
        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            t = time.time()
            full_p = build_prompt(combo)
            fmt = combo.get('_formato', '2:3')
            last_prompt[uid] = full_p
            img, err = execute_generation(full_p, formato=fmt)
            elapsed = round(time.time() - t, 1)
            if img:
                try:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="sorpresa.jpg",
                        caption=f"✅ {elapsed}s | {fmt}")
                    generic = build_generic_prompt(combo)
                    threads = build_threads_caption(combo)
                    bot.send_message(cid,
                        f"📋 <b>Prompt generico:</b>\n\n<code>{html.escape(generic)}</code>")
                    bot.send_message(cid,
                        f"🧵 <b>Caption Threads:</b>\n<code>{html.escape(threads)}</code>",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — generata in {elapsed}s | formato={fmt}")
                except Exception as e:
                    logger.error(f"❌ Errore invio: {e}")
                    bot.send_message(cid, f"❌ Generata ma errore nell'invio.\n<code>{html.escape(str(e))}</code>")
            else:
                bot.send_message(cid, f"❌ <b>Generazione fallita</b> ({elapsed}s)\n{err}",
                    reply_markup=get_retry_keyboard())
                logger.warning(f"❌ {username} (id={uid}) — fallita ({elapsed}s): {err}")

        executor.submit(run)

    elif call.data == "riprova":
        # Riprova la stessa combo senza rimostrare
        combo = last_combo.get(uid)
        if not combo:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        bot.send_message(cid, "🔁 Riprovo la stessa combinazione...\n⏳ Generazione in corso...")

        def run_retry():
            t = time.time()
            full_p = build_prompt(combo)
            fmt = combo.get('_formato', '2:3')
            last_prompt[uid] = full_p
            img, err = execute_generation(full_p, formato=fmt)
            elapsed = round(time.time() - t, 1)
            if img:
                try:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="sorpresa.jpg",
                        caption=f"✅ Retry — {elapsed}s | {fmt}")
                    generic = build_generic_prompt(combo)
                    threads = build_threads_caption(combo)
                    bot.send_message(cid,
                        f"📋 <b>Prompt generico:</b>\n\n<code>{html.escape(generic)}</code>")
                    bot.send_message(cid,
                        f"🧵 <b>Caption Threads:</b>\n<code>{html.escape(threads)}</code>",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — retry in {elapsed}s | formato={fmt}")
                except Exception as e:
                    bot.send_message(cid, f"❌ Errore invio.\n<code>{html.escape(str(e))}</code>")
            else:
                bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                    reply_markup=get_retry_keyboard())

        executor.submit(run_retry)

# --- /lastprompt ---
@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🔍 /lastprompt da {username} (id={uid})")
    prompt = last_prompt.get(uid)
    if not prompt:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt inviato all'API</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

# --- STATO ---
last_combo = {}
last_prompt = {}

# --- FLASK ---
app = flask.Flask(__name__)

@app.route('/')
def health():
    return f"sorpresa v{VERSION} ok", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- MAIN ---
if __name__ == '__main__':
    logger.info(f"🎲 SORPRESA v{VERSION} — avvio")
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask health check attivo su porta 10000")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)

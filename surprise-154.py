import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "1.5.4"

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
    "**MANDATORY BODY — THIS IS NOT A MALE BODY — ABSOLUTE OVERRIDE:**\n"
    "**FULL D-CUP BUST — large, prominent, natural, clearly visible through any outfit. THIS IS THE MOST IMPORTANT BODY RULE.**\n"
    "**Feminine hourglass silhouette: 180cm, 85kg. Defined waist, wide rounded hips, full thighs, soft belly. "
    "DO NOT GENERATE A FLAT CHEST. DO NOT GENERATE A MALE PHYSIQUE. THE BUST MUST BE VISIBLE AND PROMINENT.**\n"
    "Completely hairless body — NO body hair anywhere. Smooth porcelain skin. "
    "PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous from face → neck → shoulders → chest → arms.\n\n"
    "**Rendering physics:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200, 1/160s, natural bokeh.\n\n"
    "**Watermark:** 'feat. Valeria Cross 👠' — elegant champagne cursive, very small, bottom center, 90% opacity.\n\n"
    "**NEGATIVE PROMPT — FACE:** young face, female face, missing wrinkles, blurred skin, distorted glasses, missing beard, dark hair, face drift.\n"
    "**NEGATIVE PROMPT — HAIR:** long hair, feminine hairstyle, bun, ponytail, black hair, blonde hair, brown hair, curly hair, body hair, chest hair.\n"
    "**NEGATIVE PROMPT — BODY:** male flat chest, masculine frame, blurry hands, extra fingers, mismatched skin tone, body hair.\n"
    "**NEGATIVE PROMPT — SAFETY:** JSON output, text output, captions, metadata. IMAGE GENERATION ONLY. NO JSON LEAKAGE.\n"
)

# --- SYSTEM PROMPT PER GENERAZIONE SCENARIO ---
LOCATION_POOL = [
    # Europa
    "Eiffel Tower gardens, Paris, golden hour",
    "Colosseum steps, Rome, warm afternoon light",
    "Amalfi Coast cliffside terrace, Positano",
    "Santorini blue dome church, Oia village",
    "Venice Grand Canal, gondola dock, misty morning",
    "Barcelona Gothic Quarter rooftop, sunset",
    "Athens Acropolis surroundings, classical columns",
    "Capri island marina, azure water, luxury boats",
    "Monaco harbour, yacht deck, Mediterranean sun",
    "Milan Galleria Vittorio Emanuele, grand arcade",
    "London Notting Hill, pastel townhouses, spring",
    "Paris Palais Royal gardens, stone arcades",
    "Dubrovnik city walls, Adriatic sea view",
    "Lisbon Alfama viewpoint, terracotta rooftops",
    "Prague Charles Bridge, misty dawn",
    "Vienna Schönbrunn Palace gardens, baroque fountain",
    "Amsterdam Jordaan canal, narrow bridges, tulips",
    "Mykonos whitewashed windmills, cobblestone alley",
    "Côte d'Azur beach, sun loungers, parasols",
    "Tuscany cypress hill road, golden wheat fields",
    "Cinque Terre colourful harbour, fishing boats",
    "Lake Como villa terrace, mountain backdrop",
    "Seville Alcázar palace courtyard, orange trees",
    "Istanbul Bosphorus waterfront, evening glow",
    "Swiss Alps snowy peak, clear blue sky, chalet",
    # Americhe
    "New York Fifth Avenue, art deco building facade",
    "Miami South Beach, Art Deco strip, pastel hotels",
    "Beverly Hills Rodeo Drive, palm trees, sunlight",
    "Rio de Janeiro Copacabana beachfront promenade",
    "New York MoMA sculpture garden, white walls",
    "Chicago Millennium Park, Cloud Gate reflection",
    "Buenos Aires Recoleta neighbourhood, French architecture",
    "Cartagena colonial walled city, bougainvillea walls",
    "Tulum beachfront cenote, turquoise water, jungle",
    "Havana Malecón seafront, vintage pastel buildings",
    # Asia
    "Tokyo Shinjuku neon district, night rain reflections",
    "Kyoto bamboo grove, Arashiyama, soft morning light",
    "Bali rice terraces, Ubud, emerald green, mist",
    "Singapore Marina Bay Sands infinity pool at dusk",
    "Shanghai Bund waterfront, Art Deco skyline",
    "Hong Kong Victoria Peak, city lights below",
    "Maldives overwater villa, turquoise lagoon, sunset",
    "Rajasthan palace courtyard, Jaipur, pink stone",
    "Angkor Wat temple, Cambodia, golden sunrise",
    "Seoul Bukchon Hanok village, traditional rooftops",
    # Africa e Medio Oriente
    "Marrakech Majorelle garden, cobalt blue walls",
    "Dubai desert dunes at sunset, luxury camp",
    "Cape Town V&A Waterfront, Table Mountain backdrop",
    "Sahara desert salt flats, vast horizon, blue sky",
    "Seychelles granite boulders, palm-fringed beach",
    # Oceania
    "Sydney Opera House forecourt, harbour at dusk",
    "Bora Bora overwater bungalow, Mount Otemanu",
    # Luxury venues
    "Grand hotel ballroom, crystal chandeliers, marble floor",
    "Rooftop infinity pool, city skyline at night",
    "Luxury yacht deck, open sea, horizon",
    "High-end fashion atelier, white walls, dress forms",
    "Opera house foyer, grand staircase, red carpet",
    "Art gallery white cube, contemporary sculpture",
    "Private villa poolside, Mediterranean garden",
    "Penthouse terrace, panoramic city view, night",
    "Horse racing paddock, manicured lawn, summer",
    "Cannes Croisette promenade, film festival banners",
]

OUTFIT_POOL = [
    # Mini dress / abiti corti
    "silver sequined Balmain mini dress, structured shoulders, bare legs",
    "black Versace micro mini dress, plunging V neckline, gold Medusa details",
    "white broderie anglaise Zimmermann mini dress, off-shoulder, thigh exposed",
    "hot pink Alexandre Vauthier strapless mini dress, ruched bodycon",
    "red Valentino ruffled mini dress, deep sweetheart neckline, bare shoulders",
    "feathered Valentino Haute Couture mini dress, stilettos, bare legs",
    "floral Dolce & Gabbana silk mini dress, spaghetti straps, cleavage",
    "cobalt blue Hervé Léger bandage mini dress, wrap neckline",
    # Abiti da sera con scollatura / slit
    "floor-length black Versace gown, plunging neckline to waist, gold chain belt",
    "emerald green Elie Saab gown, sheer lace bodice, deep cleavage, thigh slit",
    "red Marchesa strapless evening gown, sweetheart neckline, floral embroidery",
    "midnight blue Armani Privé draped gown, one shoulder, side slit to hip",
    "gold lamé Versace dress, deep V plunge, wrap skirt with high slit",
    "silver Galvan London halter gown, open back, barely-there neckline",
    # Beachwear / resort
    "Victoria's Secret gold metallic string bikini, bare midriff",
    "white one-piece swimsuit, open back, high cut legs, gold hardware",
    "coral La Perla triangle bikini, sarong barely tied at hip, espadrilles",
    "leopard print Norma Kamali barely-there bikini, cat-eye sunglasses",
    "red Baywatch-style high-cut one-piece, vintage inspired",
    "black Eres high-waist bikini, sheer mesh cover-up, oversized hat",
    # Estivi / leggerezza / gambe scoperte
    "white crochet Missoni beach dress, micro hemline, tan skin visible",
    "pastel yellow broderie Faithfull the Brand sundress, mini length, bare shoulders",
    "turquoise off-shoulder Agua Bendita mini dress, ruffle hem, sandals",
    "floral wrap mini dress, deep V neckline, bare legs, espadrille wedges",
    "pink satin slip mini dress, thin straps, cowl neckline, thigh exposed",
    "lemon yellow strapless Jacquemus mini dress, extreme mini, tan legs",
    "sheer white Saint Laurent blouse, barely buttoned, micro denim shorts",
    # Bodysuit / cut-out
    "black latex Alaïa bodycon dress, waist cut-out details, bare midriff",
    "Thierry Mugler metal underwire corset bodysuit, micro skirt, heels",
    "black Mugler cut-out spiral bodycon dress, bare waist and hips",
    "Victoria's Secret Angel rhinestone bodysuit, wings, bare legs",
    "white Nensi Dojaka asymmetric micro dress, sheer panels, cut-outs",
    # Avant-garde / sculptural
    "Iris van Herpen 3D-printed sculptural mini dress, bare arms and legs",
    "geometric Versace pop art micro dress, neon colors, plunging neckline",
    "black latex Alaïa total look, zip details, body-hugging from bust to thigh",
]

STYLE_POOL = [
    "Helmut Newton, glamorous monochrome editorial",
    "Guy Bourdin, saturated surrealist fashion photography",
    "Richard Avedon, dynamic high-fashion movement",
    "Irving Penn, clean studio portraiture, timeless elegance",
    "Peter Lindbergh, cinematic naturalistic beauty",
    "Herb Ritts, sculptural black and white photography",
    "Annie Leibovitz, narrative cinematic portraiture",
    "Mario Testino, vibrant glossy fashion photography",
    "Paolo Roversi, painterly soft-focus romanticism",
    "David LaChapelle, hyperrealistic pop art surrealism",
    "Nick Knight, avant-garde digital fashion imagery",
    "Steven Meisel, sophisticated high-fashion editorial",
    "Juergen Teller, raw unfiltered fashion realism",
    "Tim Walker, fantastical whimsical fashion storytelling",
    "Miles Aldridge, cinematic hyper-saturated colour",
    "Solve Sundsbo, futuristic digital fashion photography",
    "Ellen von Unwerth, playful glamorous feminine energy",
    "Patrick Demarchelier, classic elegant fashion photography",
    "Bruce Weber, sun-drenched American lifestyle photography",
    "Nan Goldin, intimate documentary fashion realism",
]

SCENARIO_SYSTEM = """You are a creative director for a high-fashion AI image generation system.
Generate sky, pose and mood for a Valeria Cross fashion editorial. Keep each field SHORT (max 10 words).

IMPORTANT for pose: must be a REAL, PHYSICALLY POSSIBLE human pose — standing, walking, sitting, leaning, reclining. NO wings, NO floating, NO supernatural elements.

Return ONLY valid JSON with these exact keys, no other text:
{
  "sky": "lighting condition, time of day, atmosphere (max 8 words)",
  "pose": "realistic human fashion pose, no fantasy (max 8 words)",
  "mood": "atmosphere and feeling (max 6 words)"
}"""

def generate_scenario():
    try:
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=["Generate sky lighting, pose and mood for a high-fashion editorial shoot."],
            config=genai_types.GenerateContentConfig(
                system_instruction=SCENARIO_SYSTEM,
                temperature=1.4,
                max_output_tokens=500,
            )
        )
        import json, re, random
        text = response.text.strip()
        logger.info(f"📝 Scenario raw: {text[:300]}")
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            logger.error(f"❌ Nessun JSON trovato nella risposta: {text[:200]}")
            raise ValueError("No JSON in response")
        partial = json.loads(match.group(0))
        # Aggiunge location, outfit e style dai pool fissi
        partial['location'] = random.choice(LOCATION_POOL)
        partial['outfit'] = random.choice(OUTFIT_POOL)
        partial['style'] = random.choice(STYLE_POOL)
        # Fallback per campi mancanti
        if 'sky' not in partial: partial['sky'] = "golden hour, warm afternoon light"
        if 'pose' not in partial: partial['pose'] = "standing elegantly, hand on hip"
        if 'mood' not in partial: partial['mood'] = "sophisticated and confident"
        logger.info(f"✅ Scenario: {partial['location']} | {partial['outfit'][:40]}")
        return partial
    except Exception as e:
        logger.error(f"❌ Errore generate_scenario: {e}", exc_info=True)
        # Fallback completo con pool — funziona anche senza Gemini
        import random
        return {
            'location': random.choice(LOCATION_POOL),
            'sky': random.choice(["golden hour, warm light", "blue sky, midday sun", "dramatic dusk, purple haze", "overcast soft light, misty"]),
            'outfit': random.choice(OUTFIT_POOL),
            'style': random.choice(STYLE_POOL),
            'pose': random.choice(["standing confidently, hand on hip", "walking gracefully toward camera", "leaning against wall, arms crossed", "sitting elegantly, legs crossed"]),
            'mood': random.choice(["sophisticated and powerful", "playful and vibrant", "mysterious and alluring", "bold and avant-garde"]),
        }

# --- COSTRUISCE PROMPT IMMAGINE ---
# Parole che causano elementi fantasy indesiderati
FANTASY_WORDS = [
    "wing", "wings", "fairy", "floating", "weightless", "levitating", "levitation",
    "flying", "fly", "hovering", "hover", "angel", "angelic", "supernatural",
    "mythical", "mermaid", "dragon", "magical", "enchanted", "ethereal wings",
    "organza wings", "butterfly wings", "feather wings"
]

# --- STILI ARTISTICI (da Sorpresa) ---
ARTISTIC_STYLES = [
    None,  # nessuno stile — photorealistic (stessa probabilità degli altri)
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism",
    "🌀 Dalì — melting surrealist dreamscape, hyper-detailed hallucination, elongated figures, Spanish surrealism",
    "🏛️ De Chirico — metaphysical painting, long dramatic shadows, empty piazzas, classical architecture, eerie stillness",
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles",
    "🖌️ Banksy — urban stencil street art, black and white spray paint, sharp political irony, graffiti aesthetic",
]

STILE_ARTISTICO_OVERRIDES = {
    "🌂 Magritte — surrealist hyper-realism, dreamlike impossible juxtapositions, Belgian surrealism": {
        "colore_ok": [
            "soft pastel palette", "cool grey and silver", "warm ivory and cream",
            "stark white and ice", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "white seamless studio", "Santorini cliffside terrace at dusk",
            "Swiss Alps snowy peak, clear blue sky", "Maldives overwater villa at sunset",
            "Monaco seafront promenade, golden hour",
        ],
    },
    "🌀 Dalì — melting surrealist dreamscape, hyper-detailed hallucination, elongated figures, Spanish surrealism": {
        "colore_ok": [
            "earthy terracotta and ochre", "warm amber and cognac", "warm ivory and cream",
            "soft pastel palette", "bold red and gold", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "Sahara desert dunes at golden hour, vast horizon",
            "Cappadocia landscape, hot air balloons, golden light",
            "Patagonia plains, dramatic sky, endless horizon",
            "Atacama desert, surreal salt flats, blue sky",
        ],
    },
    "🏛️ De Chirico — metaphysical painting, long dramatic shadows, empty piazzas, classical architecture, eerie stillness": {
        "colore_ok": [
            "earthy terracotta and ochre", "warm amber and cognac", "warm ivory and cream",
            "cool grey and silver", "deep navy and midnight blue",
        ],
        "sfondo_ok": [
            "Rome Piazza Navona, dramatic afternoon shadows, empty square",
            "Athens Acropolis surroundings, classical columns, warm light",
            "Venice Piazza San Marco at dawn, empty, long shadows",
            "Milan Galleria Vittorio Emanuele, grand arcade, warm light",
        ],
    },
    "🔷 Mondrian — primary color geometric grid, De Stijl abstraction, flat bold rectangles": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "bold red and gold",
            "vibrant electric blue tones",
        ],
        "sfondo_ok": [
            "white seamless studio", "Amsterdam canal house facades, geometric architecture",
            "New York modern art museum interior, white walls",
            "Paris Centre Pompidou exterior, bold graphic architecture",
        ],
    },
    "🖌️ Banksy — urban stencil street art, black and white spray paint, sharp political irony, graffiti aesthetic": {
        "colore_ok": [
            "monochromatic all-black", "stark white and ice", "cool grey and silver",
            "bold red and gold",
        ],
        "sfondo_ok": [
            "London Shoreditch street art district, brick walls, daylight",
            "New York Brooklyn street, urban energy, graffiti walls",
            "Berlin East Side Gallery, painted wall, open sky",
            "Tokyo Shibuya crossing, neon lights, night",
        ],
    },
}

def sanitize_scenario(scenario):
    """Rimuove elementi fantasy da outfit e pose."""
    import re
    for field in ["outfit", "pose", "mood"]:
        val = scenario.get(field, "")
        for word in FANTASY_WORDS:
            val = re.sub(rf"\b{re.escape(word)}\b", "", val, flags=re.IGNORECASE)
        # Pulisce spazi multipli e virgole orfane
        val = re.sub(r",\s*,", ",", val)
        val = re.sub(r"\s+", " ", val).strip(" ,")
        scenario[field] = val
    return scenario

def build_prompt(scenario):
    scenario = sanitize_scenario(scenario)
    fmt = random.choice(["2:3", "16:9"])

    # Legge stile artistico già estratto in pick_scene
    artistic_style = scenario.get('artistic_style')

    # Location dal pool fisso — gli override artistici NON sovrascrivono
    location = scenario['location']

    style_block = f"VISUAL STYLE: {scenario['style']}\n\n"
    if artistic_style:
        style_block += f"ARTISTIC STYLE: {artistic_style}\n\n"

    prompt = (
        f"{VALERIA_IDENTITY}\n\n"
        f"⚠️ BODY OVERRIDE — HIGHEST PRIORITY: Subject has FULL PROMINENT D-CUP BUST, clearly visible. "
        f"Feminine hourglass body. DO NOT generate flat chest or male physique under any circumstance.\n\n"
        f"SCENE: {location}. {scenario['sky']}.\n\n"
        f"OUTFIT: {scenario['outfit']}\n\n"
        f"POSE: {scenario['pose']}. Body must follow realistic human anatomy and physics — weight supported, no impossible floating positions.\n\n"
        f"MOOD: {scenario['mood']}\n\n"
        + style_block +
        f"FORMAT: {fmt}\n\n"
        f"Ultra-detailed 8K cinematic photography. No text, no watermark except the mandatory one."
    )
    return prompt, fmt, artistic_style

# --- GENERA IMMAGINE (single step, come Vogue/Cabina) ---
def execute_generation(full_prompt, formato="2:3"):
    try:
        # masterface PRIMA del prompt — identico a Vogue e Cabina
        if MASTER_PART:
            contents = [MASTER_PART, full_prompt]
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")
            contents = [full_prompt]

        def _call():
            return client.models.generate_content(
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

        for _attempt in range(2):
            with _cf.ThreadPoolExecutor(max_workers=1) as _ex:
                future = _ex.submit(_call)
                try:
                    response = future.result(timeout=120)
                    break
                except _cf.TimeoutError:
                    if _attempt == 0:
                        logger.warning("⚠️ Timeout (120s) — retry tra 15s")
                        time.sleep(15)
                    else:
                        return None, "⏱️ Timeout dopo 2 tentativi."
        else:
            return None, "⏱️ Timeout dopo 2 tentativi."

        if not response.candidates:
            return None, "❌ Nessun candidato dall'API."
        candidate = response.candidates[0]
        finish_str = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
        if finish_str != "STOP":
            return None, f"🛡️ Bloccata: {finish_str}"
        for part in candidate.content.parts:
            if part.inline_data:
                return part.inline_data.data, None
        return None, "❌ Nessuna immagine nella risposta."

    except Exception as e:
        logger.error(f"❌ Eccezione execute_generation: {e}", exc_info=True)
        return None, f"❌ Errore interno: {html.escape(str(e))}"

# --- CAPTION DA SCENARIO ---
def generate_caption_from_scenario(scenario):
    """Genera caption social dalla descrizione testuale dello scenario.
    Stessa struttura di VogueBot — 4/5 emoji + frase max 10 parole."""
    try:
        desc = (
            f"Location: {scenario.get('location', '')}\n"
            f"Sky: {scenario.get('sky', '')}\n"
            f"Outfit: {scenario.get('outfit', '')}\n"
            f"Mood: {scenario.get('mood', '')}"
        )
        instr = (
            f"Based on this fashion editorial scene description, generate a social media caption.\n\n"
            f"DESCRIPTION:\n{desc}\n\n"
            "Rules:\n"
            "- Start with 4 or 5 emoji that match the style, setting, mood and fashion\n"
            "- Follow with a short phrase of maximum 10 words\n"
            "- The phrase must be eye-catching, evocative, and descriptive of the scene\n"
            "- Do NOT mention any person's gender, age, or physical appearance\n"
            "- Focus on: mood, style, location, colors, atmosphere, fashion\n"
            "- No hashtags, no punctuation at the end\n"
            "- Return ONLY the caption on a single line, nothing else\n"
            "Example: '🌊✨👙🌅 golden hour on the mediterranean coast'\n"
            "Example: '🖤🌹💃🎭 dark glamour at the theatre'"
        )
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[instr]
        )
        if response.text:
            return response.text.strip(), None
        return None, "⚠️ Nessuna caption generata."
    except Exception as e:
        logger.error(f"❌ Errore caption: {e}", exc_info=True)
        return None, f"❌ Errore: {html.escape(str(e))}"

# --- BOT ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
last_scenario = {}
last_prompt   = {}
user_prefs    = {}   # uid → {'artistic': True/False}

# --- KEYBOARDS ---
def get_artistic_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎨 Con stile artistico", callback_data="pref_artistic_yes"),
        InlineKeyboardButton("📷 Solo fotografico",    callback_data="pref_artistic_no")
    )
    return markup

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎲 Surprise me!", callback_data="tira"))
    return markup

def get_confirm_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Sì", callback_data="conferma"),
        InlineKeyboardButton("🏠 No", callback_data="no_home")
    )
    return markup

def get_retry_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Nuova scena", callback_data="tira"),
        InlineKeyboardButton("🔁 Riprova questa", callback_data="riprova")
    )
    return markup

# --- FORMAT SCENARIO ---
def format_scenario(s):
    artistic = s.get('artistic_style')
    if artistic:
        artist_short = artistic.split(' — ')[0]
        style_line = f"🎨 <b>Style:</b> {s['style']} + {artist_short}"
    else:
        style_line = f"🎨 <b>Style:</b> {s['style']}"
    return (
        f"📍 <b>Location:</b> {s['location']}\n"
        f"🌤 <b>Sky:</b> {s['sky']}\n"
        f"👗 <b>Outfit:</b> {s['outfit']}\n"
        + style_line + "\n"
        f"💃 <b>Pose:</b> {s['pose']}\n"
        f"✨ <b>Mood:</b> {s['mood']}"
    )

# --- /start ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    last_scenario.pop(uid, None)
    last_prompt.pop(uid, None)
    user_prefs.pop(uid, None)
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id, "✅ <b>Reset completo.</b> Tutte le sessioni cancellate.")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Vuoi includere lo stile di un grande artista?\n"
        f"(Magritte, Dalì, De Chirico, Mondrian, Banksy)",
        reply_markup=get_artistic_keyboard())

# --- /info ---
@bot.message_handler(commands=['info'])
def handle_info(message):
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Genera scenari completamente liberi tramite Gemini.\n"
        f"Formati: <b>2:3</b> o <b>16:9</b> (random)\n"
        f"Comandi: /start /info /lastprompt")

# --- /lastprompt ---
@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    prompt = last_prompt.get(uid)
    if not prompt:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un'immagine.")
        return
    chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
    for idx, chunk in enumerate(chunks):
        header = f"🔍 <b>Ultimo prompt</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
        bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data in [
    "pref_artistic_yes", "pref_artistic_no",
    "tira", "conferma", "no_home", "riprova"
])
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name

    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    # --- Scelta stile artistico ---
    if call.data in ("pref_artistic_yes", "pref_artistic_no"):
        user_prefs[uid] = {'artistic': call.data == "pref_artistic_yes"}
        label = "🎨 Con stile artistico" if user_prefs[uid]['artistic'] else "📷 Solo fotografico"
        logger.info(f"🎨 {username} (id={uid}) → {label}")
        bot.send_message(cid,
            f"✅ <b>{label}</b>\n\nPremi il pulsante per generare la scena!",
            reply_markup=get_main_keyboard())

    # --- Tira scena ---
    elif call.data == "tira":
        wait = bot.send_message(cid, "🎲 Gemini sta scegliendo la scena...")

        def pick_scene():
            scenario = generate_scenario()
            try: bot.delete_message(cid, wait.message_id)
            except Exception: pass
            if not scenario:
                bot.send_message(cid, "❌ Errore nella generazione della scena. Riprova.",
                    reply_markup=get_main_keyboard())
                return
            # Stile artistico: solo se l'utente lo ha scelto
            want_artistic = user_prefs.get(uid, {}).get('artistic', True)
            if want_artistic:
                artistic = random.choice(ARTISTIC_STYLES)
            else:
                artistic = None
            scenario['artistic_style'] = artistic
            last_scenario[uid] = scenario
            # Messaggio 1: scena senza header, senza Body
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            # Messaggio 2: vuoi generare?
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎲 {username} (id={uid}) — scena: {scenario['location']} | {scenario['style']}")

        executor.submit(pick_scene)

    # --- No → home ---
    elif call.data == "no_home":
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        user_prefs.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
            f"Vuoi includere lo stile di un grande artista?\n"
            f"(Magritte, Dalì, De Chirico, Mondrian, Banksy)",
            reply_markup=get_artistic_keyboard())

    # --- Conferma: genera ---
    elif call.data == "conferma":
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        full_p, fmt, style_label = build_prompt(scenario)
        last_prompt[uid] = full_p

        # Messaggio 3: caption (prima della generazione, basata sullo scenario)
        caption_text, _ = generate_caption_from_scenario(scenario)
        if caption_text:
            bot.send_message(cid, caption_text, parse_mode=None)

        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            try:
                t = time.time()
                img, err = execute_generation(full_p, formato=fmt)
                elapsed = round(time.time() - t, 1)
                if img:
                    sl = f" | {style_label.split(' — ')[0]}" if style_label else ""
                    # Messaggio 4: immagine
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ {elapsed}s | {fmt}{sl}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — {elapsed}s | {fmt} | {scenario['location']}")
                else:
                    bot.send_message(cid, f"❌ <b>Generazione fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")

        executor.submit(run)

    # --- Riprova ---
    elif call.data == "riprova":
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        full_p_retry, fmt_retry, style_retry = build_prompt(scenario)
        last_prompt[uid] = full_p_retry
        bot.send_message(cid, "🔁 Riprovo la stessa scena...\n⏳ Generazione in corso...")

        def run_retry():
            try:
                t = time.time()
                img, err = execute_generation(full_p_retry, formato=fmt_retry)
                elapsed = round(time.time() - t, 1)
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ Retry — {elapsed}s | {fmt_retry}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} retry (id={uid}) — {elapsed}s")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run_retry() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")

        executor.submit(run_retry)

# --- FLASK ---
app = flask.Flask(__name__)

@app.route('/')
def health():
    return f"surprise v{VERSION} ok", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- MAIN ---
if __name__ == '__main__':
    logger.info(f"🎲 SURPRISE v{VERSION} — avvio")
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask health check attivo su porta 10000")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)

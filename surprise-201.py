import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "2.0.1"

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
    "Portofino harbour, pastel facades, luxury yachts",
    "Taormina Greek Theatre terrace, Etna backdrop, Sicily",
    "Puglia trulli rooftops, Alberobello, warm stone, summer",
    "Rome Prati neighbourhood, Liberty-style architecture, morning light",
    "Naples waterfront Lungomare, Castel dell'Ovo, golden sunset",
    "Sardinia Costa Smeralda, turquoise cove, white sand",
    "Florence Oltrarno rooftop, Duomo dome, warm dusk",
    "Venice Rialto Bridge at dawn, empty canals, mist",
    "Lecce baroque piazza, golden limestone, afternoon light",
    "Ravello Villa Rufolo terrace, Amalfi coast panorama",
    "Portofino rocky cove, emerald water, sun",
    "Milan Navigli canal, evening aperitivo, warm lights",
    "Rome Gianicolo hill terrace, city panorama, golden hour",
    "Lisbon Belém Tower, Tagus river, warm afternoon",
    "Sintra Pena Palace gardens, romantic architecture",
    "Porto Ribeira waterfront, colourful azulejo facades",
    "Algarve sea arch, Ponta da Piedade, turquoise water",
    "Lisbon Miradouro da Graça, terracotta rooftops, sunset",
    "Cascais coastal promenade, Atlantic light, whitewashed walls",
    "Douro Valley wine terraces, river bend, golden light",
    "Évora Roman temple, ancient columns, warm stone",
    "Comporta rice fields and dunes, wild Atlantic coast",
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
    "silver sequined Balmain mini dress, structured shoulders, bare legs, silver stiletto heels",
    "black Versace micro mini dress, plunging V neckline, gold Medusa details, black strappy heels",
    "white broderie anglaise Zimmermann mini dress, off-shoulder, thigh exposed, white block heels",
    "hot pink Alexandre Vauthier strapless mini dress, ruched bodycon, nude pointed-toe pumps",
    "red Valentino ruffled mini dress, deep sweetheart neckline, bare shoulders, red satin heels",
    "feathered Valentino Haute Couture mini dress, stilettos, bare legs",
    "floral Dolce & Gabbana silk mini dress, spaghetti straps, cleavage, gold mule heels",
    "cobalt blue Hervé Léger bandage mini dress, wrap neckline, cobalt blue platform heels",
    # Abiti da sera con scollatura / slit
    "floor-length black Versace gown, plunging neckline to waist, gold chain belt, black satin pumps",
    "emerald green Elie Saab gown, sheer lace bodice, deep cleavage, thigh slit, gold strappy sandals",
    "red Marchesa strapless evening gown, sweetheart neckline, floral embroidery, red platform heels",
    "midnight blue Armani Privé draped gown, one shoulder, side slit to hip, silver stiletto sandals",
    "gold lamé Versace dress, deep V plunge, wrap skirt with high slit, gold metallic heels",
    "silver Galvan London halter gown, open back, barely-there neckline, silver strappy heels",
    # Beachwear / resort
    "Victoria's Secret gold metallic string bikini, bare midriff",
    "white one-piece swimsuit, open back, high cut legs, gold hardware",
    "coral La Perla triangle bikini, sarong barely tied at hip, espadrilles",
    "leopard print Norma Kamali barely-there bikini, cat-eye sunglasses",
    "red Baywatch-style high-cut one-piece, vintage inspired",
    "black Eres high-waist bikini, sheer mesh cover-up, oversized hat",
    # Estivi / leggerezza / gambe scoperte
    "white crochet Missoni beach dress, micro hemline, tan skin visible, flat leather sandals",
    "pastel yellow broderie Faithfull the Brand sundress, mini length, bare shoulders, tan wedge sandals",
    "turquoise off-shoulder Agua Bendita mini dress, ruffle hem, sandals",
    "floral wrap mini dress, deep V neckline, bare legs, espadrille wedges",
    "pink satin slip mini dress, thin straps, cowl neckline, thigh exposed, barely-there heeled sandals",
    "lemon yellow strapless Jacquemus mini dress, extreme mini, tan legs, nude pointed pumps",
    "sheer white Saint Laurent blouse, barely buttoned, micro denim shorts, white leather sneakers",
    # Bodysuit / cut-out
    "black latex Alaïa bodycon dress, waist cut-out details, bare midriff, black patent heels",
    "Thierry Mugler metal underwire corset bodysuit, micro skirt, heels",
    "black Mugler cut-out spiral bodycon dress, bare waist and hips, black stiletto boots",
    "Victoria's Secret Angel rhinestone bodysuit, wings, bare legs",
    "white Nensi Dojaka asymmetric micro dress, sheer panels, cut-outs, clear perspex heels",
    # Avant-garde / sculptural
    "Iris van Herpen 3D-printed sculptural mini dress, bare arms and legs, architectural platform heels",
    "geometric Versace pop art micro dress, neon colors, plunging neckline, white patent heels",
    "black latex Alaïa total look, zip details, body-hugging from bust to thigh, black stiletto ankle boots",
    # Mini dress aggiuntivi
    "champagne sequined Retrofête mini dress, plunging V neckline, strappy heels",
    "fuchsia Jacquemus Le Chiquito mini dress, asymmetric neckline, bare shoulders, fuchsia mule heels",
    "white broderie Chloé strapless mini dress, deep sweetheart, golden tan skin, tan leather sandals",
    "bronze metallic Saint Laurent mini shift dress, spaghetti straps, bare legs, bronze stiletto heels",
    "black Coperni cut-out mini dress, architectural waist opening, heels",
    "coral ruffled Self-Portrait mini dress, tiered hem, plunging back, nude strappy sandals",
    "red satin Rick Owens draped mini, thigh-high slit, one shoulder, black leather boots",
    # Abiti da sera aggiuntivi
    "ivory Valentino Haute Couture column gown, structured bust, deep V back, ivory satin pumps",
    "cobalt blue Safiyaa off-shoulder gown, thigh slit, draped skirt, silver strappy sandals",
    "black velvet Tom Ford gown, deep plunge neckline, long sleeves, slit, black satin heels",
    "rose gold sequined Naeem Khan floor gown, open back, high slit, rose gold heeled sandals",
    "nude illusion Zuhair Murad gown, crystal embroidery, sheer bodice, nude pointed-toe pumps",
    # Beachwear aggiuntivo
    "neon green triangle string bikini, micro bottoms, silver anklet",
    "snake-print Zimmermann bikini, ruched top, sarong wrap, wedge sandals",
    "white lace-up one-piece swimsuit, plunging neckline, gold rings",
    "black wet-look Dolce & Gabbana high-leg one-piece, gold logo hardware",
    "turquoise Eres bandeau bikini, sheer pareo, oversized straw hat",
    "magenta Missoni crochet bikini, cover-up shawl, espadrilles",
    # Estivi aggiuntivi
    "sheer printed Etro maxi dress, side slit, bare midriff, bohemian, flat leather sandals",
    "cobalt blue MSGM micro skirt, matching crop halter top, mule heels",
    "olive green Bottega Veneta slip dress, cowl neckline, bare back, tan leather mules",
    "orange tie-dye Dries Van Noten mini dress, deep V, statement earrings, cork wedge sandals",
    # Cut-out aggiuntivi
    "beige Mugler hourglass bodycon dress, waist cut-outs, sheer panels, nude stiletto heels",
    "black PVC Versace bodysuit, plunging neckline, micro skirt, thigh-highs",
    "silver Rabanne chainmail micro dress, bare shoulders and hips, silver stiletto sandals",
    "red Alaïa laser-cut bodycon dress, geometric openwork, bare skin visible, red patent pumps",
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

POSE_POOL = [
    "standing upright, one hand on hip, chin slightly lifted",
    "walking confidently toward camera, skirt in motion",
    "leaning against wall, arms crossed, one knee bent",
    "sitting on edge of surface, legs crossed at ankle, back straight",
    "reclining on side, propped on elbow, legs extended",
    "standing back to camera, glancing over shoulder",
    "seated on floor, knees drawn up, arms wrapped around legs",
    "leaning forward slightly, hands on thighs, direct gaze",
    "standing side profile, one arm extended along wall",
    "walking away, looking back, hair movement",
    "sitting on steps, elbows on knees, chin resting on hands",
    "standing with arms raised overhead, arched back",
    "leaning on railing, one elbow resting, gazing at horizon",
    "crouching low, knees apart, hands on ground between feet",
    "standing with legs wide apart, hands clasped behind back",
    "seated on chair, legs draped over armrest, relaxed",
    "lying on back, arms above head, legs slightly apart",
    "standing in doorway, one hand on frame, body turned",
    "spinning, skirt fanned out, captured mid-rotation",
    "seated cross-legged on floor, hands resting on knees",
    "standing with one leg forward, weight shifted to hip",
    "leaning back against surface, head tilted up, eyes closed",
    "kneeling on one knee, other leg extended, torso upright",
    "standing with hands in hair, elbows raised",
    "seated on staircase, turned sideways, arm on banister",
    "walking sideways along wall, fingertips trailing surface",
    "standing with one hand on chest, other at side, soft gaze",
    "lying face down, propped on forearms, legs bent upward",
    "standing with legs crossed at knee, arms loose at sides",
    "seated at edge of water, feet dangling in",
]

SKY_POOL = [
    "golden hour, warm amber light, long soft shadows",
    "blue sky, harsh midday sun, sharp shadows",
    "overcast soft light, diffused, no shadows, milky sky",
    "dramatic dusk, deep purple and orange horizon",
    "clear night, full moon, silver-blue ambient light",
    "sunrise, pale pink and gold, delicate warm haze",
    "stormy sky, dark clouds, electric pre-rain tension",
    "magic hour, last light, sky deep crimson and gold",
    "bright white studio light, clean and clinical",
    "neon city night, pink and blue reflections on wet pavement",
    "candlelight warm glow, intimate, flickering amber",
    "underwater light, caustic rays, turquoise shimmer",
    "foggy morning, diffused cool light, soft mist",
    "backlit silhouette, strong rim light, sun behind subject",
    "blue hour, twilight, deep blue sky, city lights emerging",
    "desert midday, bleached white light, stark and hot",
    "autumn afternoon, warm orange, low angle sun through leaves",
    "crystal clear winter light, cold blue tones, sharp and clean",
    "tropical noon, vivid saturated colors, intense shadows",
    "Venetian afternoon, warm reflected light off water",
    "opera house interior, dramatic warm spotlights",
    "penthouse night, city glow from below, skyline backdrop",
    "rainy evening, grey sky, reflections on wet street",
    "greenhouse light, soft diffused green-tinted natural light",
    "late afternoon Mediterranean, golden haze, warm and sleepy",
    "rooftop at sunset, sky gradient pink to violet",
    "early morning beach, cool light, long shadows on sand",
    "grand ballroom chandeliers, warm crystal light from above",
    "snowy exterior, pure white reflected light, cold blue shadows",
    "poolside afternoon, bright white reflections off water surface",
]

MOOD_POOL = [
    "sophisticated and untouchable",
    "playful and irreverent",
    "mysterious and alluring",
    "bold and confrontational",
    "dreamy and introspective",
    "fierce and dominant",
    "sensual and confident",
    "melancholic and distant",
    "euphoric and free",
    "cold and editorial",
    "warm and inviting",
    "dangerous and magnetic",
    "nostalgic and cinematic",
    "raw and unfiltered",
    "elegant and composed",
    "wild and untamed",
    "ironic and detached",
    "glamorous and excessive",
    "intimate and vulnerable",
    "powerful and statuesque",
    "surreal and otherworldly",
    "casual and effortless",
    "theatrical and exaggerated",
    "romantic and soft",
    "angular and geometric",
    "languid and bored",
    "sharp and precise",
    "luminous and ethereal",
    "heavy and brooding",
    "joyful and explosive",
]

SCENARIO_SYSTEM = """You are a creative director for a high-fashion AI image generation system.
You will receive a location. Your job is to choose ONE sky, ONE pose and ONE mood that are COHERENT with that location.

COHERENCE RULES — strictly enforced:
- Outdoor natural locations (beach, mountain, countryside, garden): use natural light skies (golden hour, sunrise, midday sun, blue hour, stormy, foggy). NEVER use ballroom, opera house, studio, neon city, candlelight or penthouse skies.
- Indoor luxury venues (ballroom, opera house, atelier, gallery): use interior lighting skies (chandeliers, spotlights, candlelight, studio). NEVER use beach, desert, tropical or snowy outdoor skies.
- Urban outdoor (city streets, rooftops, canals, promenades): use city-compatible skies (blue hour, neon night, rainy evening, golden hour, overcast). NEVER use underwater, ballroom or snowy mountain skies.
- Beach / water locations: use beach or water-compatible skies (tropical noon, beach morning, golden hour, backlit). NEVER use ballroom, snowy or studio skies.
- Pose must be physically possible in the chosen location — no crouching on a yacht deck in a gown unless it makes sense.

Return ONLY valid JSON with these exact keys, no other text:
{
  "sky": "chosen sky from the options that fits the location",
  "pose": "chosen pose that fits the location and outfit",
  "mood": "chosen mood"
}"""

def generate_scenario():
    import json, re, random
    # Estrae location e outfit dai pool fissi PRIMA di chiamare Gemini
    location = random.choice(LOCATION_POOL)
    outfit   = random.choice(OUTFIT_POOL)
    style    = random.choice(STYLE_POOL)
    try:
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[f"Location for this editorial shoot: {location}\n\nChoose a coherent sky, pose and mood for this specific location."],
            config=genai_types.GenerateContentConfig(
                system_instruction=SCENARIO_SYSTEM,
                temperature=1.2,
                max_output_tokens=500,
            )
        )
        text = response.text.strip()
        logger.info(f"📝 Scenario raw: {text[:300]}")
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            raise ValueError("No JSON in response")
        partial = json.loads(match.group(0))
        partial['location'] = location
        partial['outfit']   = outfit
        partial['style']    = style
        if 'sky' not in partial:  partial['sky']  = random.choice(SKY_POOL)
        if 'pose' not in partial: partial['pose'] = random.choice(POSE_POOL)
        if 'mood' not in partial: partial['mood'] = random.choice(MOOD_POOL)
        logger.info(f"✅ Scenario: {partial['location']} | {partial['outfit'][:40]}")
        return partial
    except Exception as e:
        logger.error(f"❌ Errore generate_scenario: {e}", exc_info=True)
        # Fallback completo dai pool fissi — zero dipendenza da Gemini
        return {
            'location': location,
            'sky':      random.choice(SKY_POOL),
            'outfit':   outfit,
            'style':    style,
            'pose':     random.choice(POSE_POOL),
            'mood':     random.choice(MOOD_POOL),
        }

# --- COSTRUISCE PROMPT IMMAGINE ---
# Parole che causano elementi fantasy indesiderati
FANTASY_WORDS = [
    "wing", "wings", "fairy", "floating", "weightless", "levitating", "levitation",
    "flying", "fly", "hovering", "hover", "angel", "angelic", "supernatural",
    "mythical", "mermaid", "dragon", "magical", "enchanted", "ethereal wings",
    "organza wings", "butterfly wings", "feather wings"
]

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
    location = scenario['location']
    style_block = f"VISUAL STYLE: {scenario['style']}\n\n"
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
    return prompt, fmt, None

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

# --- KEYBOARDS ---
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
    return (
        f"📍 <b>Location:</b> {s['location']}\n"
        f"🌤 <b>Sky:</b> {s['sky']}\n"
        f"👗 <b>Outfit:</b> {s['outfit']}\n"
        f"🎨 <b>Style:</b> {s['style']}\n"
        f"💃 <b>Pose:</b> {s['pose']}\n"
        f"✨ <b>Mood:</b> {s['mood']}\n"
        f"🏛 <b>Body:</b> Feminine hourglass, 180cm 85kg, D-cup bust, smooth skin"
    )

# --- /start ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    last_scenario.pop(uid, None)
    last_prompt.pop(uid, None)
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id, "✅ <b>Reset completo.</b> Tutte le sessioni cancellate.")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Premi il pulsante per generare una scena casuale!",
        reply_markup=get_main_keyboard())

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

    # --- Tira scena ---
    if call.data == "tira":
        wait = bot.send_message(cid, "🎲 Gemini sta scegliendo la scena...")

        def pick_scene():
            scenario = generate_scenario()
            try: bot.delete_message(cid, wait.message_id)
            except Exception: pass
            if not scenario:
                bot.send_message(cid, "❌ Errore nella generazione della scena. Riprova.",
                    reply_markup=get_main_keyboard())
                return
            last_scenario[uid] = scenario
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎲 {username} (id={uid}) — scena: {scenario['location']} | {scenario['style']}")

        executor.submit(pick_scene)

    # --- No → home ---
    elif call.data == "no_home":
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
            f"Premi il pulsante per generare una scena casuale!",
            reply_markup=get_main_keyboard())

    # --- Conferma: genera ---
    elif call.data == "conferma":
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta. Tira di nuovo.", reply_markup=get_main_keyboard())
            return
        full_p, fmt, style_label = build_prompt(scenario)
        last_prompt[uid] = full_p
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

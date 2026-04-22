import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "3.0.1"

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
    # ── ITALIA (30) ──────────────────────────────────────────
    "Rome Colosseum exterior, warm golden afternoon light, ancient stone",
    "Rome Piazza Navona, baroque fountains, cobblestones, evening glow",
    "Rome Palatine Hill terrace, panoramic view over Roman Forum, dusk",
    "Rome Via Appia Antica, ancient pines, crumbling aqueduct, golden hour",
    "Florence Piazzale Michelangelo, Duomo panorama, warm sunset",
    "Florence Uffizi Gallery courtyard, Renaissance archways, morning light",
    "Florence Ponte Vecchio, Arno river reflection, golden dusk",
    "Venice Piazza San Marco at dawn, empty square, mist on water",
    "Venice Ca' d'Oro palazzo, Grand Canal, ornate Gothic facade",
    "Venice Burano island, vivid painted houses, canal reflections",
    "Milan Duomo Cathedral rooftop terraces, city panorama, blue sky",
    "Milan Castello Sforzesco courtyard, Renaissance towers, afternoon",
    "Milan Brera neighbourhood, cobblestones, ivy-covered walls, spring",
    "Amalfi Coast hairpin road, turquoise sea below, cliffside villages",
    "Positano terrace, bougainvillea walls, tiered white houses, sea",
    "Ravello Villa Cimbrone infinity terrace, Tyrrhenian sea panorama",
    "Matera Sassi ancient cave city, tufa stone, dramatic canyon light",
    "Alberobello trulli district, conical white rooftops, warm stone",
    "Ostuni white city, whitewashed alleyways, olive groves beyond",
    "Lecce baroque cathedral square, golden limestone, afternoon light",
    "Syracuse Ortigia island, Greek temple columns, harbour at dusk",
    "Taormina Teatro Antico, Etna silhouette, Ionian sea below",
    "Agrigento Valley of Temples, Doric columns, almond blossoms",
    "Cinque Terre Vernazza harbour, colourful tower, cliffside terraces",
    "Portofino lighthouse point, emerald cove, pastel village below",
    "Lake Como Villa del Balbianello terraced gardens, mountain backdrop",
    "Lake Garda Sirmione castle, clear water, medieval towers",
    "Dolomites Tre Cime di Lavaredo, dramatic rock spires, clear sky",
    "Turin Mole Antonelliana, river Po panorama, Alpine horizon",
    "Bologna Due Torri medieval towers, terracotta rooftops, arcades",
    # ── PORTOGALLO (20) ──────────────────────────────────────
    "Lisbon Belém Tower, Tagus river mouth, warm afternoon light",
    "Lisbon Alfama viewpoint Portas do Sol, terracotta rooftops, sunset",
    "Lisbon Miradouro da Graça, fado atmosphere, golden dusk",
    "Lisbon São Jorge Castle ramparts, city panorama, blue sky",
    "Lisbon Jerónimos Monastery cloister, Manueline stone arches",
    "Sintra Pena Palace ramparts, coloured towers, forested hills",
    "Sintra Quinta da Regaleira, mystical well, moss-covered stonework",
    "Sintra Moorish Castle walls, eucalyptus forest, Atlantic horizon",
    "Cascais fishing harbour, whitewashed walls, Atlantic light",
    "Óbidos medieval walled village, cobblestones, bougainvillea",
    "Évora Roman temple columns, warm stone, Alentejo plains beyond",
    "Évora Chapel of Bones, candlelight, dramatic interior",
    "Porto Ribeira waterfront, azulejo facades, Douro river at dusk",
    "Porto Dom Luís I iron bridge, double-decker, city at golden hour",
    "Porto São Bento railway station, azulejo tile murals, morning light",
    "Douro Valley terraced vineyards, river bend, harvest golden light",
    "Alentejo cork oak plains, golden wheat, vast horizon, blue sky",
    "Algarve Ponta da Piedade sea arches, turquoise water, boat below",
    "Comporta whitewashed beach shack, wild dunes, Atlantic light",
    "Monsaraz hilltop village, Alqueva lake reflection, pink dusk",
    # ── SPIAGGE SPECIFICHE (10) ──────────────────────────────
    "Spiaggia dei Conigli, Lampedusa, crystalline turquoise water, white sand",  # IT
    "Cala Goloritzé, Sardinia, dramatic limestone arch, emerald cove",             # IT
    "Scala dei Turchi, Sicily, white marlstone cliff steps, azure sea",            # IT
    "Praia da Marinha, Algarve, ochre rock formations, secret cove",              # PT
    "Praia do Camilo, Lagos, golden cliffs, turquoise inlet, wooden steps",       # PT
    "Whitehaven Beach, Whitsundays, Australia, pure silica white sand, aerial view",
    "Baia do Sancho, Fernando de Noronha, Brazil, lush cliff descent, turquoise",
    "Navagio Shipwreck Beach, Zakynthos, Greece, rusted wreck, white pebbles",
    "Pink Sands Beach, Harbour Island, Bahamas, blush pink sand, calm water",
    "Anse Source d'Argent, La Digue, Seychelles, granite boulders, pink sand",
    # ── SITI STORICI E ICONICI MONDIALI (50) ─────────────────
    "Petra Treasury facade, Jordan, rose-red sandstone, dawn light",
    "Petra Siq narrow canyon, Jordan, towering rock walls, filtered light",
    "Giza Pyramids, Egypt, desert plateau, dramatic sky, camel silhouette",
    "Great Sphinx of Giza, Egypt, limestone face, warm sunset backlight",
    "Karnak Temple columns, Luxor, Egypt, massive hieroglyph-carved pillars",
    "Abu Simbel temple facade, Egypt, colossal statues, Nubian sunrise",
    "Great Wall of China, Mutianyu section, forested mountains, misty morning",
    "Great Wall of China, Jinshanling, autumn foliage, golden light",
    "Forbidden City, Beijing, vermillion gates, imperial courtyard",
    "Terracotta Army pits, Xi'an, China, rows of warrior figures, amber light",
    "Machu Picchu citadel, Peru, Andean peaks above clouds, sunrise",
    "Chichen Itza El Castillo pyramid, Mexico, equinox light, shadow serpent",
    "Teotihuacan Pyramid of the Sun, Mexico, ancient avenue, blue sky",
    "Grand Canyon South Rim, Arizona, layered red rock, golden hour",
    "Antelope Canyon slot canyon, Arizona, light beams, swirling sandstone",
    "Monument Valley buttes, Arizona, red mesa silhouettes, sunset",
    "Niagara Falls Horseshoe, Canada, rainbow mist, thundering water",
    "Iguazu Falls panorama, Argentina/Brazil border, jungle mist, cascades",
    "Angel Falls, Venezuela, world's highest, jungle canyon, mist",
    "Taj Mahal at sunrise, Agra, India, reflection pool, pink sky",
    "Taj Mahal western gate, Agra, India, symmetrical archway, warm stone",
    "Hampi boulder landscape, Karnataka, India, ancient ruins, golden dusk",
    "Angkor Wat main causeway, Cambodia, lotus pond reflection, sunrise",
    "Angkor Thom Bayon temple, Cambodia, stone faces, jungle canopy",
    "Bagan temple plain, Myanmar, hot air balloons at dawn, misty pagodas",
    "Borobudur stupa terraces, Java, Indonesia, volcanic backdrop, sunrise",
    "Halong Bay limestone karsts, Vietnam, emerald water, fishing boats mist",
    "Santorini Oia village, white cubic houses, caldera, Aegean sunset",
    "Parthenon Acropolis, Athens, marble columns, city below, golden hour",
    "Delphi Oracle sanctuary, Greece, mountain valley, ancient columns",
    "Meteora monasteries, Greece, rock pinnacles, Byzantine churches, dawn",
    "Cappadocia Göreme valley, Turkey, hot air balloons, fairy chimneys",
    "Pamukkale travertine terraces, Turkey, white mineral pools, sunset",
    "Ephesus Library of Celsus, Turkey, Roman facade, warm stone",
    "Alhambra Nasrid Palaces courtyard, Granada, Moorish arches, reflection",
    "Sagrada Família nave interior, Barcelona, stained glass light forest",
    "Mont Saint-Michel, Normandy, tidal island monastery, low tide sand",
    "Versailles Hall of Mirrors, France, golden chandeliers, garden axis",
    "Colosseum interior arena, Rome, underground hypogeum, dramatic light",
    "Pompeii Via dell'Abbondanza, Italy, ancient street, Vesuvius beyond",
    "Stonehenge, Wiltshire, megalithic circle, dawn mist, rising sun",
    "Edinburgh Castle esplanade, Scotland, dramatic rock, city below",
    "Neuschwanstein Castle, Bavaria, fairytale towers, alpine forest, clouds",
    "Prague Old Town Square, astronomical clock, Gothic spires, dusk",
    "Dubrovnik Old City walls, Adriatic panorama, red rooftops, sunset",
    "Mostar Stari Most bridge, Bosnia, arched stone, Neretva river, summer",
    "Chefchaouen blue medina, Morocco, cobalt alleyways, terracotta pots",
    "Djemaa el-Fna square, Marrakech, lanterns, Atlas mountains horizon",
    "Victoria Falls, Zimbabwe/Zambia, smoke that thunders, rainbow mist",
    "Sossusvlei red dunes, Namib desert, Dead Vlei white clay, clear sky",
    "Easter Island Ahu Tongariki, Chile, moai row, ocean sunrise",
]

OUTFIT_POOL = [
    # ── MINI DRESS (12) ──────────────────────────────────────
    "electric cobalt sequined Balmain mini dress, plunging V neckline, structured shoulders, cobalt strappy heels, gold ear cuffs",
    "burnt orange Alexandre Vauthier strapless bodycon mini, ruched bust, high slit, nude pointed pumps, gold bangles",
    "deep forest green Versace micro mini, plunging neckline, gold Medusa hardware, black strappy sandals, statement gold hoops",
    "dusty rose Zimmermann broderie anglaise off-shoulder mini, tiered hem, blush wedge sandals, pearl drop earrings",
    "hot magenta Valentino ruffled mini dress, sweetheart neckline, bare shoulders, fuchsia satin heels, diamond tennis bracelet",
    "ice blue Hervé Léger bandage mini, wrap neckline, body-sculpting seams, powder blue platform heels, crystal ear studs",
    "acid yellow Jacquemus asymmetric micro mini, single draped strap, bare shoulders, nude pointed mules, gold chain necklace",
    "deep burgundy Self-Portrait lace mini, plunging back, long sleeves, wine-red strappy heels, pearl choker",
    "bright coral Retrofête sequined mini, plunging V, spaghetti straps, coral stiletto sandals, gold stacking rings",
    "steel grey Coperni cut-out mini, architectural cutaways at waist, perspex block heels, silver ear climbers",
    "terracotta Chloé broderie strapless mini, frayed hem, raw edges, tan leather block heels, hammered gold cuffs",
    "electric violet Rick Owens draped mini, asymmetric one-shoulder, thigh slit, violet pointed pumps, silver cuff",
    # ── ABITI DA SERA / GOWN (12) ────────────────────────────
    "midnight black Versace floor gown, plunging neckline to navel, gold safety-pin chain belt, black satin stilettos, diamond drop earrings",
    "vivid emerald Elie Saab gown, sheer crystal-embroidered bodice, deep cleavage, thigh slit, gold gladiator heels, no other jewellery",
    "flame red Marchesa strapless gown, 3D floral appliqué bodice, cathedral skirt, red satin platform heels, garnet earrings",
    "royal blue Armani Privé draped column gown, one shoulder, hip-high slit, silver stiletto sandals, sapphire ear studs",
    "champagne gold Naeem Khan fully-sequined floor gown, open back, high slit, nude strappy sandals, stacked gold bangles",
    "oyster white Zuhair Murad illusion gown, crystal-scattered sheer panels, structured bodice, ivory pumps, pearl drop earrings",
    "deep teal Safiyaa off-shoulder draped gown, side slit, fluid skirt, silver ankle-strap heels, aquamarine cocktail ring",
    "blush pink Valentino Haute Couture column gown, deep V back, architectural bow at hip, blush satin pumps, rose gold cuff",
    "onyx black Tom Ford velvet gown, ultra-deep plunge, long sleeves, thigh slit, black patent pumps, single chandelier earring",
    "burnt sienna Galvan halter gown, open back, waterfall skirt, bronze strappy heels, amber resin earrings",
    "electric blue lamé Versace wrap gown, deep V plunge, wrap skirt with high slit, metallic blue heels, no necklace",
    "ivory Saint Laurent tuxedo gown, sharp lapels, dramatic train, white stiletto pumps, pearl studs, black satin gloves",
    # ── BEACHWEAR / RESORT (14) ──────────────────────────────
    "crimson La Perla triangle string bikini, minimal coverage, red cord ties, gold anklet, oversized black sunglasses",
    "electric turquoise Eres bandeau bikini, high-cut bottoms, sheer turquoise pareo tied low, tan espadrille wedges",
    "sand beige Norma Kamali barely-there string bikini, ruched bottoms, woven sun hat, gold body chain",
    "sunshine yellow Zimmermann triangle bikini, ruched top, broderie sarong wrap, white platform sandals, gold hoops",
    "deep coral Missoni crochet bikini, fringe hem bottoms, matching crochet cover-up, tan flat sandals, shell earrings",
    "ivory white one-piece Alaïa swimsuit, deep V front, cut-out waist, high cut legs, white slide sandals, gold cuff",
    "forest green La Perla high-leg one-piece, structured bust, low back, gold hardware rings, tan leather slides",
    "black Dolce & Gabbana push-up bikini, gold logo charm at hip, black lace sarong, gold stiletto sandals, bold hoops",
    "neon pink Agent Provocateur barely-there micro bikini, pink rhinestone trim, matching pareo, pink flat sandals",
    "pale lavender Valentino one-piece, plunging halter neck, tie-side, lavender slides, amethyst bracelet",
    "bronze metallic Melissa Odabash string bikini, wide-brim bronze hat, tan leather thong sandals, layered gold chains",
    "cobalt blue Hunza G crinkle bikini, ruched top, matching crinkle shorts, cobalt espadrilles, silver anklet",
    "cherry red high-cut vintage one-piece, padded structured bust, retro silhouette, red wedge sandals, red cat-eye sunglasses",
    "sage green Seafolly bandeau bikini, tie-waist high-rise bottoms, sage linen shirt open, flat leather sandals",
    # ── ESTIVI / LEGGEREZZA (7) ──────────────────────────────
    "deep saffron Etro printed silk slip maxi dress, plunging cowl neck, thigh slit, gold flat sandals, layered gold chains",
    "powder blue Faithfull the Brand broderie sundress, mini length, puff sleeves, white block heels, pearl studs",
    "moss green Bottega Veneta intrecciato-detail slip dress, cowl back, bare shoulders, tan leather mules, gold cuff",
    "faded denim Jacquemus micro skirt, matching bandeau crop, silver buckle mules, silver ear climbers",
    "warm terracotta Dries Van Noten printed midi wrap dress, deep V, flutter sleeves, tan heeled sandals, ceramic hoops",
    "cream sheer Saint Laurent blouse barely buttoned, high-waist black micro shorts, black pointed boots, pearl necklace",
    "hot tangerine Agua Bendita off-shoulder ruffle mini, smocked bodice, cork wedge sandals, gold layered chains",
    # ── BODYSUIT / CUT-OUT / AVANT-GARDE (5) ─────────────────
    "liquid silver Rabanne chainmail micro dress, plunging V, bare hips, silver stiletto sandals, no jewellery",
    "matte black Mugler hourglass cut-out bodycon dress, spiral waist openings, sheer body panels, black stiletto boots",
    "deep violet Alaïa laser-cut bodycon, geometric openwork revealing skin, violet patent heels, single silver cuff",
    "rose gold Thierry Mugler metal underwire corset, structured boning, micro skirt, rose gold heels, chandelier earrings",
    "electric lime Iris van Herpen 3D-printed sculptural mini, bare arms, architectural platform heels, no jewellery",
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
last_scenario  = {}
last_prompt    = {}
manual_state   = {}  # uid → {'location':..., 'outfit':..., 'sky':..., 'pose':..., 'mood':..., 'style':...}

# --- PAGINAZIONE MANUALE ---
PAGE_SIZE = 5

def get_page(pool, page):
    start = page * PAGE_SIZE
    return pool[start:start + PAGE_SIZE]

def total_pages(pool):
    return (len(pool) + PAGE_SIZE - 1) // PAGE_SIZE

# --- KEYBOARDS ---
def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Automatico", callback_data="mode_auto"),
        InlineKeyboardButton("🎛️ Manuale", callback_data="mode_manual")
    )
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

def get_pool_keyboard(pool, page, prefix, title, state, done_steps):
    """Tastiera paginata generica per qualsiasi pool."""
    markup = InlineKeyboardMarkup()
    items = get_page(pool, page)
    for i, item in enumerate(items):
        idx = page * PAGE_SIZE + i
        short = item[:55] + "…" if len(item) > 55 else item
        markup.add(InlineKeyboardButton(short, callback_data=f"{prefix}{idx}"))
    # Navigazione
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"pg_{prefix}{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages(pool)}", callback_data="noop"))
    if page < total_pages(pool) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"pg_{prefix}{page+1}"))
    if nav:
        markup.row(*nav)
    return markup

MANUAL_STEPS = [
    ("location", "📍 Scegli la <b>Location</b>:", LOCATION_POOL, "loc_"),
    ("outfit",   "👗 Scegli l'<b>Outfit</b>:",    OUTFIT_POOL,   "out_"),
    ("sky",      "🌤 Scegli lo <b>Sky / Lighting</b>:", SKY_POOL, "sky_"),
    ("pose",     "💃 Scegli la <b>Pose</b>:",      POSE_POOL,     "pos_"),
    ("mood",     "✨ Scegli il <b>Mood</b>:",       MOOD_POOL,     "moo_"),
    ("style",    "📷 Scegli lo <b>Stile fotografico</b>:", STYLE_POOL, "sty_"),
]

def send_manual_step(cid, uid, step_index):
    key, title, pool, prefix = MANUAL_STEPS[step_index]
    markup = get_pool_keyboard(pool, 0, prefix, title, manual_state.get(uid, {}), step_index)
    bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")

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
    manual_state.pop(uid, None)
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id, "✅ <b>Reset completo.</b>")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Come vuoi generare la scena?",
        reply_markup=get_main_keyboard())

# --- /info ---
@bot.message_handler(commands=['info'])
def handle_info(message):
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Genera scenari editoriali.\n"
        f"<b>Automatico:</b> tutto random con coerenza location\n"
        f"<b>Manuale:</b> scegli ogni elemento dai pool\n"
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
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name
    data = call.data

    try: bot.answer_callback_query(call.id)
    except Exception: pass

    # noop (label pagina)
    if data == "noop":
        return

    # --- Scelta modalità ---
    if data == "mode_auto":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        wait = bot.send_message(cid, "🎲 Generazione scena automatica...")
        def pick_auto():
            scenario = generate_scenario()
            try: bot.delete_message(cid, wait.message_id)
            except Exception: pass
            if not scenario:
                bot.send_message(cid, "❌ Errore. Riprova.", reply_markup=get_main_keyboard())
                return
            last_scenario[uid] = scenario
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎲 AUTO {username} (id={uid}) — {scenario['location']}")
        executor.submit(pick_auto)

    elif data == "mode_manual":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state[uid] = {}
        send_manual_step(cid, uid, 0)

    # --- Navigazione pagine pool manuale ---
    elif data.startswith("pg_"):
        # formato: pg_<prefix><page>
        rest = data[3:]  # es. "loc_2"
        # trova il prefisso (4 chars)
        prefix = rest[:4]
        page = int(rest[4:])
        step = next((i for i, s in enumerate(MANUAL_STEPS) if s[3] == prefix), None)
        if step is None:
            return
        _, title, pool, _ = MANUAL_STEPS[step]
        markup = get_pool_keyboard(pool, page, prefix, title, manual_state.get(uid, {}), step)
        try:
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=markup)
        except Exception: pass

    # --- Scelta elemento manuale ---
    elif data[:4] in [s[3] for s in MANUAL_STEPS]:
        prefix = data[:4]
        idx = int(data[4:])
        step = next((i for i, s in enumerate(MANUAL_STEPS) if s[3] == prefix), None)
        if step is None:
            return
        key, title, pool, _ = MANUAL_STEPS[step]
        chosen = pool[idx]
        if uid not in manual_state:
            manual_state[uid] = {}
        manual_state[uid][key] = chosen
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        short = chosen[:60] + "…" if len(chosen) > 60 else chosen
        bot.send_message(cid, f"✅ <b>{title.split('<b>')[1].split('</b>')[0]}:</b> {short}", parse_mode="HTML")
        # Prossimo step o conferma
        next_step = step + 1
        if next_step < len(MANUAL_STEPS):
            send_manual_step(cid, uid, next_step)
        else:
            # Tutti scelti → costruisce scenario e mostra
            state = manual_state[uid]
            scenario = {
                'location': state['location'],
                'outfit':   state['outfit'],
                'sky':      state['sky'],
                'pose':     state['pose'],
                'mood':     state['mood'],
                'style':    state['style'],
            }
            last_scenario[uid] = scenario
            bot.send_message(cid, "🎛️ <b>Scena manuale:</b>", parse_mode="HTML")
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎛️ MANUAL {username} (id={uid}) — {scenario['location']}")

    # --- Tira (da retry keyboard) ---
    elif data == "tira":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())

    # --- No → home ---
    elif data == "no_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        manual_state.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())

    # --- Conferma: genera ---
    elif data == "conferma":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta.", reply_markup=get_main_keyboard())
            return
        full_p, fmt, _ = build_prompt(scenario)
        last_prompt[uid] = full_p
        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            try:
                t = time.time()
                img, err = execute_generation(full_p, formato=fmt)
                elapsed = round(time.time() - t, 1)
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ {elapsed}s | {fmt}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — {elapsed}s | {fmt}")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")
        executor.submit(run)

    # --- Riprova ---
    elif data == "riprova":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta.", reply_markup=get_main_keyboard())
            return
        full_p_retry, fmt_retry, _ = build_prompt(scenario)
        last_prompt[uid] = full_p_retry
        bot.send_message(cid, "🔁 Riprovo...\n⏳ Generazione in corso...")

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
                    logger.info(f"✅ retry {username} (id={uid}) — {elapsed}s")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run_retry(): {e}", exc_info=True)
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

import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "4.2.6"

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
    "**Hair:** Short silver Italian cut, slightly voluminous top, nape exposed.\n"
    "**⚠️ BEARD — MANDATORY — NON-NEGOTIABLE:** "
    "Full silver-grey beard approximately 6-7cm, perfectly groomed, dense and uniform, following the jawline. "
    "The beard MUST be clearly visible in EVERY shot. "
    "DO NOT shave it. DO NOT reduce it. DO NOT replace it with stubble. "
    "A clean-shaven face is a generation FAILURE. The beard is part of the identity lock.\n"
    "**⚠️ COEXISTENCE RULE — CRITICAL:** The silver-grey beard on the male face AND the feminine body are NOT a contradiction. "
    "They MUST coexist in the same image. Do NOT resolve this by removing the beard. "
    "Do NOT resolve this by masculinizing the body. Keep both exactly as described.\n\n"
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

# --- LOCATION POOL ---
LOCATION_POOL = [
    # ══ 🇮🇹 ITALIA (85) ══════════════════════════════════════
    # Abruzzo
    ("🇮🇹 · Abruzzo, Santo Stefano di Sessanio, Gran Sasso",  "Santo Stefano di Sessanio, Abruzzo, stone village, Gran Sasso backdrop"),
    ("🇮🇹 · Abruzzo, Scanno, lago e borgo medievale",         "Lago di Scanno, Abruzzo, heart-shaped lake, medieval village above, dawn mist"),
    ("🇮🇹 · Abruzzo, Castelluccio, piana fiorita",            "Castelluccio di Norcia, flowering plain, Monti Sibillini backdrop"),
    # Basilicata
    ("🇮🇹 · Basilicata, Matera, chiese rupestri",             "Matera cave churches, Sassi rupestri, dramatic canyon, candlelight golden hour"),
    ("🇮🇹 · Basilicata, Maratea, Cristo Redentore",           "Maratea, Cristo Redentore statue, Tyrrhenian sea panorama, dramatic cliff"),
    # Calabria
    ("🇮🇹 · Calabria, Capo Vaticano, costa degli Dei",        "Capo Vaticano, Calabria, Costa degli Dei, turquoise sea, white cliffs, dramatic coastline"),
    ("🇮🇹 · Calabria, Scilla, castello Ruffo",                "Scilla, Calabria, Ruffo Castle on rock, colourful fishermen quarter"),
    ("🇮🇹 · Calabria, Tropea, scoglio e spiaggia bianca",     "Tropea, Calabria, cliff church on rock, white sand below, turquoise sea"),
    # Campania
    ("🇮🇹 · Campania, Amalfi, strada costiera",               "Amalfi Coast hairpin road, turquoise sea below, cliffside villages"),
    ("🇮🇹 · Campania, Capri, Faraglioni",                     "Capri Faraglioni sea stacks, crystal clear Mediterranean water, golden afternoon"),
    ("🇮🇹 · Campania, Caserta, Reggia e fontane",             "Reggia di Caserta, Bourbon royal palace, grand waterfall fountain axis, Versailles of Italy"),
    ("🇮🇹 · Campania, Ischia, Castello Aragonese",            "Ischia Castello Aragonese, volcanic island fortress, sunset Tyrrhenian sea"),
    ("🇮🇹 · Campania, Napoli, Castel dell'Ovo",               "Naples waterfront Lungomare, Castel dell'Ovo, golden sunset, Vesuvius"),
    ("🇮🇹 · Campania, Paestum, templi greci",                 "Paestum, Greek temples, Doric columns, golden wheat field, Campania"),
    ("🇮🇹 · Campania, Pompei, Via dell'Abbondanza",           "Pompeii Via dell'Abbondanza, ancient street, Vesuvius beyond, warm stone"),
    ("🇮🇹 · Campania, Positano, terrazza e bouganville",      "Positano terrace, bougainvillea walls, tiered white houses, sea"),
    ("🇮🇹 · Campania, Procida, Marina Corricella",            "Procida Marina Corricella, pastel-coloured fishermen houses, harbour"),
    ("🇮🇹 · Campania, Ravello, Villa Cimbrone",               "Ravello Villa Cimbrone infinity terrace, Tyrrhenian sea panorama"),
    # Dolomiti
    ("🇮🇹 · Dolomiti, Alpe di Siusi, prato all'alba",         "Alpe di Siusi, Dolomites, alpine meadow at dawn, pink rock peaks"),
    ("🇮🇹 · Dolomiti, Cortina d'Ampezzo, paesaggio innevato", "Cortina d'Ampezzo, Dolomites, snow-covered alpine village, dramatic rock peaks, winter light"),
    ("🇮🇹 · Dolomiti, Lago di Braies, foresta di pini",       "Lago di Braies, Dolomites, emerald alpine lake, pine forest, reflection"),
    ("🇮🇹 · Dolomiti, Tre Cime di Lavaredo",                  "Dolomites Tre Cime di Lavaredo, dramatic rock spires, clear sky"),
    # Emilia-Romagna
    ("🇮🇹 · Emilia-Romagna, Bologna, Due Torri",              "Bologna Due Torri medieval towers, terracotta rooftops, arcades"),
    ("🇮🇹 · Emilia-Romagna, Ferrara, Castello Estense",       "Ferrara Castello Estense, moat reflection, Renaissance towers, dusk"),
    ("🇮🇹 · Emilia-Romagna, Ravenna, mosaici bizantini",      "Ravenna Byzantine mosaic interior, golden glittering vault, candlelight"),
    # Friuli
    ("🇮🇹 · Friuli, Trieste, Castello di Miramare",           "Castello di Miramare, Trieste, white castle on cliff, Gulf of Trieste, turquoise"),
    # Lazio
    ("🇮🇹 · Lazio, Civita di Bagnoregio, tufo e canyon",      "Civita di Bagnoregio, dying city, tufa rock, dramatic canyon, bridge approach"),
    ("🇮🇹 · Lazio, Roma, Castel Sant'Angelo",                 "Castel Sant'Angelo, Rome, Tiber river, Angels Bridge, golden dusk"),
    ("🇮🇹 · Lazio, Roma, Colosseo esterno",                   "Rome Colosseum exterior, warm golden afternoon light, ancient stone"),
    ("🇮🇹 · Lazio, Roma, Colle Palatino e Foro Romano",       "Rome Palatine Hill terrace, panoramic view over Roman Forum, dusk"),
    ("🇮🇹 · Lazio, Roma, Piazza di Spagna all'alba",          "Rome Piazza di Spagna, Spanish Steps, dawn light, azalea flowers"),
    ("🇮🇹 · Lazio, Roma, Piazza Navona",                      "Rome Piazza Navona, baroque fountains, cobblestones, evening glow"),
    ("🇮🇹 · Lazio, Roma, Via Appia e acquedotto",             "Rome Via Appia Antica, ancient pines, crumbling aqueduct, golden hour"),
    ("🇮🇹 · Lazio, Roma, Villa Borghese, terrazza tra i pini","Rome Villa Borghese terrace, umbrella pines, city panorama, golden hour"),
    ("🇮🇹 · Lazio, Tivoli, Villa d'Este e fontane",           "Villa d'Este, Tivoli, Renaissance garden, hundred fountains, cypress alleys"),
    # Liguria
    ("🇮🇹 · Liguria, Boccadasse, borgo e caletta",            "Boccadasse, Genova, pastel fishing village, small pebbly cove, colourful boats, afternoon"),
    ("🇮🇹 · Liguria, Cinque Terre, porto di Vernazza",        "Cinque Terre Vernazza harbour, colourful tower, cliffside terraces"),
    ("🇮🇹 · Liguria, Portofino, faro e insenatura",           "Portofino lighthouse point, emerald cove, pastel village below"),
    ("🇮🇹 · Liguria, Portofino, piazzetta e yacht",           "Portofino piazzetta, colourful facades, luxury yachts, summer Mediterranean"),
    # Lombardia
    ("🇮🇹 · Lombardia, Lago di Como, Villa Balbianello",      "Lake Como Villa del Balbianello terraced gardens, mountain backdrop"),
    ("🇮🇹 · Lombardia, Lago Maggiore, Isola Bella",           "Lake Maggiore Isola Bella, baroque terraced gardens, peacocks, blue water"),
    ("🇮🇹 · Lombardia, Milano, Galleria Vittorio Emanuele",   "Milan Galleria Vittorio Emanuele II, glass vault, mosaic floor, warm light"),
    ("🇮🇹 · Lombardia, Milano, Navigli al tramonto",          "Milan Navigli canals at sunset, colourful facades reflected in water, aperitivo atmosphere"),
    ("🇮🇹 · Lombardia, Milano, Terrazze del Duomo",           "Milan Duomo Cathedral rooftop terraces, city panorama, blue sky"),
    ("🇮🇹 · Lombardia, Milano, quartiere Brera",              "Milan Brera neighbourhood, cobblestones, ivy-covered walls, spring"),
    # Piemonte
    ("🇮🇹 · Piemonte, Langhe, vigneti nella nebbia",          "Langhe, Piedmont, autumn vineyard hills, morning mist, golden foliage"),
    ("🇮🇹 · Piemonte, Sacra di San Michele, abisso alpino",   "Sacra di San Michele, Piedmont, dramatic alpine abbey, gorge below, mist"),
    ("🇮🇹 · Piemonte, Torino, Mole Antonelliana",             "Turin Mole Antonelliana, river Po panorama, Alpine horizon"),
    ("🇮🇹 · Piemonte, Torino, Piazza Castello",               "Turin Piazza Castello, Palazzo Madama, baroque facade, golden hour"),
    # Puglia
    ("🇮🇹 · Puglia, Alberobello, trulli",                     "Alberobello trulli district, conical white rooftops, warm stone"),
    ("🇮🇹 · Puglia, Lecce, cattedrale barocca",               "Lecce baroque cathedral square, golden limestone, afternoon light"),
    ("🇮🇹 · Puglia, Locorotondo, centro storico bianco",      "Locorotondo, Puglia, circular white-washed village, narrow alleys, Valle d'Itria trulli below"),
    ("🇮🇹 · Puglia, Ostuni, città bianca",                    "Ostuni white city, whitewashed alleyways, olive groves beyond"),
    ("🇮🇹 · Puglia, Polignano a Mare, scogliera adriatica",   "Polignano a Mare, Adriatic cliff, turquoise sea below, dramatic rock"),
    # Sardegna
    ("🇮🇹 · Sardegna, Cagliari, bastione di San Remy",        "Cagliari, Bastione di Saint Remy, panoramic terrace, city rooftops, Sardinian sea beyond"),
    ("🇮🇹 · Sardegna, Cala Goloritzé, arco e caletta",        "Cala Goloritzé, Sardinia, dramatic limestone arch, emerald cove"),
    ("🇮🇹 · Sardegna, Costa Paradiso, rocce rosse",           "Costa Paradiso, Sardinia, dramatic red granite rocks, turquoise sea"),
    ("🇮🇹 · Sardegna, Costa Smeralda, baia turchese",         "Sardinia Costa Smeralda, turquoise cove, white sand, luxury yachts"),
    ("🇮🇹 · Sardegna, S'Archittu, arco marino",               "S'Archittu natural sea arch, Sardinia, limestone rock, emerald water"),
    # Sicilia
    ("🇮🇹 · Sicilia, Agrigento, Valle dei Templi",            "Agrigento Valley of Temples, Doric columns, almond blossoms"),
    ("🇮🇹 · Sicilia, Cave di Alcantara, basalto",             "Alcantara Gorge, Sicily, black basalt columns, crystal river, canyon"),
    ("🇮🇹 · Sicilia, Cefalù, Duomo normanno",                 "Cefalù Norman Cathedral, Sicilian beach, golden stone, turquoise sea"),
    ("🇮🇹 · Sicilia, Erice, castello normanno nella nebbia",  "Erice, Sicily, Norman castle above clouds, medieval stone, dramatic mist"),
    ("🇮🇹 · Sicilia, Lampedusa, Isola dei Conigli",           "Lampedusa Isola dei Conigli beach, crystalline turquoise water, white sand"),
    ("🇮🇹 · Sicilia, Noto, barocco siciliano",                "Noto baroque cathedral, golden limestone facade, Sicily, warm afternoon"),
    ("🇮🇹 · Sicilia, Pantelleria, dammusi e mare nero",       "Pantelleria island, traditional dammusi stone houses, black volcanic rock, dark sea, Mediterranean"),
    ("🇮🇹 · Sicilia, Scala dei Turchi, scogliera bianca",     "Scala dei Turchi, Sicily, white marlstone cliff steps, azure sea"),
    ("🇮🇹 · Sicilia, Siracusa, Ortigia, tempio greco",        "Syracuse Ortigia island, Greek temple columns, harbour at dusk"),
    ("🇮🇹 · Sicilia, Taormina, Teatro con Etna",              "Taormina Teatro Antico, Etna silhouette, Ionian sea below"),
    # Toscana
    ("🇮🇹 · Toscana, Capalbio, borgo medievale sul mare",     "Capalbio, Tuscany, medieval hilltop village, maremma coast visible beyond, golden sunset"),
    ("🇮🇹 · Toscana, Firenze, Cortile degli Uffizi",          "Florence Uffizi Gallery courtyard, Renaissance archways, morning light"),
    ("🇮🇹 · Toscana, Firenze, Giardino di Boboli",            "Boboli Gardens, Florence, baroque terraces, cypress alleys, afternoon"),
    ("🇮🇹 · Toscana, Firenze, Piazzale Michelangelo",         "Florence Piazzale Michelangelo, Duomo panorama, warm sunset"),
    ("🇮🇹 · Toscana, Firenze, Ponte Vecchio",                 "Florence Ponte Vecchio, Arno river reflection, golden dusk"),
    ("🇮🇹 · Toscana, Forte dei Marmi, spiaggia e Alpi Apuane","Forte dei Marmi, Tuscany, elegant beach, Apuan Alps backdrop, summer luxury"),
    ("🇮🇹 · Toscana, Lucca, mura rinascimentali",             "Lucca Renaissance city walls, medieval towers, tree-lined ramparts, Tuscany"),
    ("🇮🇹 · Toscana, Pisa, Piazza dei Miracoli",              "Pisa Piazza dei Miracoli, Leaning Tower, marble cathedral, green lawn"),
    ("🇮🇹 · Toscana, San Gimignano, torri medievali",         "San Gimignano medieval towers, Tuscany skyline, golden afternoon"),
    ("🇮🇹 · Toscana, Siena, Piazza del Campo",                "Siena Piazza del Campo, shell-shaped square, medieval tower, dusk"),
    ("🇮🇹 · Toscana, Val d'Orcia, cipressi nella nebbia",     "Val d'Orcia, Tuscany, cypress avenue, morning mist, rolling hills"),
    # Umbria
    ("🇮🇹 · Umbria, Assisi, Basilica di San Francesco",       "Assisi Basilica di San Francesco, pink stone, Umbrian valley panorama"),
    ("🇮🇹 · Umbria, Orvieto, Duomo sulla rupe",               "Orvieto Duomo, striped Gothic facade, tufa cliff edge, dramatic sky"),
    ("🇮🇹 · Umbria, Urbino, Palazzo Ducale",                  "Urbino Palazzo Ducale courtyard, Renaissance architecture, warm stone"),
    # Veneto
    ("🇮🇹 · Veneto, Lago di Garda, Sirmione",                 "Lake Garda Sirmione castle, clear water, medieval towers"),
    ("🇮🇹 · Veneto, Padova, Prato della Valle",               "Padova Prato della Valle, elliptical square, statues, canal, afternoon"),
    ("🇮🇹 · Veneto, Venezia, Burano, case colorate",          "Venice Burano island, vivid painted houses, canal reflections"),
    ("🇮🇹 · Veneto, Venezia, Ca' d'Oro, Canal Grande",        "Venice Ca' d'Oro palazzo, Grand Canal, ornate Gothic facade"),
    ("🇮🇹 · Veneto, Venezia, Piazza San Marco all'alba",      "Venice Piazza San Marco at dawn, empty square, mist on water"),
    ("🇮🇹 · Veneto, Venezia, Ponte di Rialto",                "Venice Rialto Bridge, Grand Canal below, market arches, morning light"),
    ("🇮🇹 · Veneto, Verona, Arena romana",                    "Verona Roman Arena, Piazza Bra, warm stone, golden evening light"),
    ("🇮🇹 · Veneto, Vicenza, Basilica Palladiana",            "Basilica Palladiana, Vicenza, Palladian arches, Piazza dei Signori, golden hour"),

    # ══ 🇵🇹 PORTOGALLO (28) ══════════════════════════════════
    # Azzorre — 2 voci
    ("🇵🇹 · Azzorre, Caldeira do Faial, cratere vulcanico",   "Caldeira do Faial, Azores, volcanic crater, wild vegetation, mist"),
    ("🇵🇹 · Azzorre, Sete Cidades, laghi gemelli",             "Sete Cidades, São Miguel, twin crater lakes, volcanic green rim"),
    # Madeira — 2 voci
    ("🇵🇹 · Madeira, Cabo Girão, scogliera vertiginosa",      "Madeira Cabo Girão, one of world highest sea cliffs, Atlantic panorama"),
    ("🇵🇹 · Madeira, Pico do Arieiro, nuvole sotto i piedi",  "Pico do Arieiro, Madeira, volcanic summit above clouds, dramatic sunrise"),
    # Lisbona
    ("🇵🇹 · Lisbona, Alfama, Portas do Sol",                  "Lisbon Alfama viewpoint Portas do Sol, terracotta rooftops, sunset"),
    ("🇵🇹 · Lisbona, Castello di São Jorge",                  "Lisbon São Jorge Castle ramparts, city panorama, blue sky"),
    ("🇵🇹 · Lisbona, Chiado, tram e azulejos",                "Lisbon Chiado neighbourhood, yellow tram, azulejo-tiled facades, morning"),
    ("🇵🇹 · Lisbona, Jerónimos, archi manueline",             "Lisbon Jerónimos Monastery cloister, Manueline stone arches"),
    ("🇵🇹 · Lisbona, Miradouro da Graça, crepuscolo",         "Lisbon Miradouro da Graça, fado atmosphere, golden dusk"),
    ("🇵🇹 · Lisbona, Torre di Belém",                         "Lisbon Belém Tower, Tagus river mouth, warm afternoon light"),
    # Porto
    ("🇵🇹 · Porto, Livraria Lello, scala Art Nouveau",        "Porto Livraria Lello bookshop, neo-Gothic staircase, stained glass ceiling"),
    ("🇵🇹 · Porto, Ponte Dom Luís, ora dorata",               "Porto Dom Luís I iron bridge, double-decker, city at golden hour"),
    ("🇵🇹 · Porto, Ribeira, azulejos e Douro",                "Porto Ribeira waterfront, azulejo facades, Douro river at dusk"),
    ("🇵🇹 · Porto, Stazione São Bento, murales",              "Porto São Bento railway station, azulejo tile murals, morning light"),
    ("🇵🇹 · Porto, Torre dei Clérigos",                       "Porto Clérigos Tower, baroque granite, rooftop city panorama, dusk"),
    # Sintra
    ("🇵🇹 · Sintra, Castello Moresco",                        "Sintra Moorish Castle walls, eucalyptus forest, Atlantic horizon"),
    ("🇵🇹 · Sintra, Palazzo della Pena",                      "Sintra Pena Palace ramparts, coloured towers, forested hills"),
    ("🇵🇹 · Sintra, Quinta da Regaleira, pozzo",              "Sintra Quinta da Regaleira, mystical well, moss-covered stonework"),
    # Algarve e Centro
    ("🇵🇹 · Algarve, archi di Ponta da Piedade",              "Algarve Ponta da Piedade sea arches, turquoise water, boat below"),
    ("🇵🇹 · Algarve, Lagos, Praia do Camilo",                 "Praia do Camilo, Lagos, golden cliffs, turquoise inlet, wooden steps"),
    ("🇵🇹 · Algarve, Praia da Marinha, formazioni rocciose",  "Praia da Marinha, Algarve, ochre rock formations, secret cove"),
    ("🇵🇹 · Comporta, dune selvagge, Atlantico",              "Comporta whitewashed beach shack, wild dunes, Atlantic light"),
    ("🇵🇹 · Évora, cappella delle Ossa",                      "Évora Chapel of Bones, candlelight, dramatic interior"),
    ("🇵🇹 · Évora, tempio romano, pianura alentejana",        "Évora Roman temple columns, warm stone, Alentejo plains beyond"),
    ("🇵🇹 · Nazaré, faro e onde gigantesche",                 "Nazaré lighthouse promontory, Portugal, massive Atlantic waves crashing below, dramatic stormy sky, red lighthouse on cliff edge"),
    ("🇵🇹 · Óbidos, borgo medievale e bouganville",           "Óbidos medieval walled village, cobblestones, bougainvillea"),
    ("🇵🇹 · Sagres, Fortezza, scogliere atlantiche",          "Sagres Fortress, Cabo de São Vicente, Atlantic cliffs, dramatic wind"),
    ("🇵🇹 · Valle del Douro, vigneti a terrazze",             "Douro Valley terraced vineyards, river bend, harvest golden light"),

    # ══ 🇫🇷 FRANCIA (12) ═════════════════════════════════════
    ("🇫🇷 · Francia, Alsazia, Colmar, canale e case a graticcio","Colmar, Alsace, Little Venice canal, half-timbered coloured houses, flower boxes"),
    ("🇫🇷 · Francia, Costa Azzurra, Cap Ferrat, villa",       "Cap Ferrat peninsula, French Riviera, Belle Époque villa, palm garden, sea"),
    ("🇫🇷 · Francia, Costa Azzurra, Èze, villaggio medievale","Èze medieval perched village, Côte d'Azur, stone alleyways, Mediterranean below"),
    ("🇫🇷 · Francia, Mont Saint-Michel, isola di marea",      "Mont Saint-Michel, Normandy, tidal island monastery, low tide sand"),
    ("🇫🇷 · Francia, Parigi, Le Marais, architettura storica","Le Marais district, Paris, 17th century mansions, cobblestones, warm stone"),
    ("🇫🇷 · Francia, Parigi, Louvre, piramide di vetro",      "Louvre Museum glass pyramid, Paris, classical courtyard, blue sky, morning"),
    ("🇫🇷 · Francia, Parigi, Montmartre, Sacré-Cœur",         "Sacré-Cœur Basilica, Montmartre, Paris, cobblestone steps, panoramic city view"),
    ("🇫🇷 · Francia, Parigi, Palais Royal, giardini",         "Palais Royal gardens, Paris, symmetrical arcades, Buren columns, dusk"),
    ("🇫🇷 · Francia, Parigi, Tour Eiffel, Champ de Mars",     "Eiffel Tower, Paris, Champ de Mars green lawn, golden afternoon light"),
    ("🇫🇷 · Francia, Provenza, Gordes, borgo in pietra",      "Gordes perched village, Provence, stone houses cascading down hill, golden sunset"),
    ("🇫🇷 · Francia, Provenza, Les Baux, Les Alpilles",       "Les Baux-de-Provence, limestone citadel ruins, arid landscape, dramatic sky"),
    ("🇫🇷 · Francia, Versailles, Galleria degli Specchi",     "Versailles Hall of Mirrors, France, golden chandeliers, garden axis"),

    # ══ 🇬🇧 REGNO UNITO (5) ══════════════════════════════════
    ("🇬🇧 · Inghilterra, Londra, Notting Hill, case colorate","Notting Hill, London, pastel-painted terraced houses, colourful facades, garden squares"),
    ("🇬🇧 · Inghilterra, Londra, Tower Bridge all'alba",      "Tower Bridge, London, dawn light on Thames, gothic towers, river mist"),
    ("🇬🇧 · Inghilterra, Stonehenge, nebbia all'alba",        "Stonehenge, Wiltshire, megalithic circle, dawn mist, rising sun"),
    ("🇬🇧 · Scozia, Castello di Edimburgo",                   "Edinburgh Castle esplanade, Scotland, dramatic rock, city below"),
    ("🇬🇧 · Scozia, Eilean Donan Castle, Highlands",          "Eilean Donan Castle, Scottish Highlands, loch reflection, misty mountains, dramatic sky"),

    # ══ 🇩🇪 GERMANIA (1) ═════════════════════════════════════
    ("🇩🇪 · Germania, Neuschwanstein, foresta alpina",        "Neuschwanstein Castle, Bavaria, fairytale towers, alpine forest, clouds"),

    # ══ 🇨🇿 REP. CECA (1) ════════════════════════════════════
    ("🇨🇿 · Rep. Ceca, Praga, orologio astronomico",          "Prague Old Town Square, astronomical clock, Gothic spires, dusk"),

    # ══ 🇪🇸 SPAGNA (2) ═══════════════════════════════════════
    ("🇪🇸 · Spagna, Alhambra, cortile moresco",               "Alhambra Nasrid Palaces courtyard, Granada, Moorish arches, reflection"),
    ("🇪🇸 · Spagna, Sagrada Família, navata di vetro",        "Sagrada Família nave interior, Barcelona, stained glass light forest"),

    # ══ 🇭🇷 CROAZIA (1) ══════════════════════════════════════
    ("🇭🇷 · Croazia, Dubrovnik, mura sull'Adriatico",         "Dubrovnik Old City walls, Adriatic panorama, red rooftops, sunset"),

    # ══ 🇬🇷 GRECIA (3) ═══════════════════════════════════════
    ("🇬🇷 · Grecia, Atene, Acropoli e Partenone",             "Parthenon Acropolis, Athens, marble columns, city below, golden hour"),
    ("🇬🇷 · Grecia, Meteore, monasteri sulle rocce",          "Meteora monasteries, Greece, rock pinnacles, Byzantine churches, dawn"),
    ("🇬🇷 · Grecia, Santorini Oia, caldera",                  "Santorini Oia village, white cubic houses, caldera, Aegean sunset"),

    # ══ 🇹🇷 TURCHIA (2) ══════════════════════════════════════
    ("🇹🇷 · Turchia, Cappadocia, camini delle fate",          "Cappadocia Göreme valley, Turkey, hot air balloons, fairy chimneys"),
    ("🇹🇷 · Turchia, Pamukkale, piscine di travertino",       "Pamukkale travertine terraces, Turkey, white mineral pools, sunset"),

    # ══ 🇲🇦 MAROCCO (2) ══════════════════════════════════════
    ("🇲🇦 · Marocco, Chefchaouen, medina blu",                "Chefchaouen blue medina, Morocco, cobalt alleyways, terracotta pots"),
    ("🇲🇦 · Marocco, Marrakech, Djemaa el-Fna",              "Djemaa el-Fna square, Marrakech, lanterns, Atlas mountains horizon"),

    # ══ 🇪🇬 EGITTO (3) ═══════════════════════════════════════
    ("🇪🇬 · Egitto, Abu Simbel, statue colossali",            "Abu Simbel temple facade, Egypt, colossal statues, Nubian sunrise"),
    ("🇪🇬 · Egitto, Piramidi di Giza",                        "Giza Pyramids, Egypt, desert plateau, dramatic sky, camel silhouette"),
    ("🇪🇬 · Egitto, Tempio di Karnak, colonne scolpite",      "Karnak Temple columns, Luxor, Egypt, massive hieroglyph-carved pillars"),

    # ══ 🇯🇴 GIORDANIA (2) ════════════════════════════════════
    ("🇯🇴 · Giordania, Petra, canyon del Siq",                "Petra Siq narrow canyon, Jordan, towering rock walls, filtered light"),
    ("🇯🇴 · Giordania, Petra, facciata del Tesoro",           "Petra Treasury facade, Jordan, rose-red sandstone, dawn light"),

    # ══ 🇳🇦 NAMIBIA (1) ══════════════════════════════════════
    ("🇳🇦 · Namibia, Sossusvlei, dune rosse",                 "Sossusvlei red dunes, Namib desert, Dead Vlei white clay, clear sky"),

    # ══ 🇿🇼 ZIMBABWE / ZAMBIA (1) ════════════════════════════
    ("🇿🇼 · Zimbabwe, Cascate Vittoria",                      "Victoria Falls, Zimbabwe/Zambia, smoke that thunders, rainbow mist"),

    # ══ 🇦🇪 EMIRATI ARABI (1) ════════════════════════════════
    ("🇦🇪 · Dubai, Burj Khalifa, skyline desertico",          "Burj Khalifa, Dubai, glass skyscraper at sunset, desert city skyline, golden light"),

    # ══ 🇿🇦 SUD AFRICA (1) ═══════════════════════════════════
    ("🇿🇦 · Sud Africa, Cape Town, Table Mountain",           "Table Mountain, Cape Town, flat-topped peak, city below, Atlantic Ocean panorama"),

    # ══ 🇧🇦 BOSNIA (1) ═══════════════════════════════════════
    ("🇧🇦 · Bosnia, Mostar, Stari Most sul Neretva",          "Mostar Stari Most bridge, Bosnia, arched stone, Neretva river, summer"),

    # ══ 🇮🇳 INDIA (4) ════════════════════════════════════════
    ("🇮🇳 · India, Hampi, rovine tra i massi",                "Hampi boulder landscape, Karnataka, India, ancient ruins, golden dusk"),
    ("🇮🇳 · India, Jaipur, Hawa Mahal",                      "Hawa Mahal, Jaipur, India, pink sandstone facade, honeycomb windows"),
    ("🇮🇳 · India, Taj Mahal, vasca riflettente",             "Taj Mahal at sunrise, Agra, India, reflection pool, pink sky"),
    ("🇮🇳 · India, Varanasi, Gange al tramonto",              "Varanasi, Ganges river, ritual ghats at sunset, candles floating, mist"),

    # ══ 🇳🇵 NEPAL (1) ════════════════════════════════════════
    ("🇳🇵 · Nepal, Himalaya, Everest base camp",              "Everest Base Camp, Nepal, Himalaya snow peaks, prayer flags, dramatic altitude"),

    # ══ 🇨🇳 CINA (3) ═════════════════════════════════════════
    ("🇨🇳 · Cina, Città Proibita, Pechino",                   "Forbidden City, Beijing, vermillion gates, imperial courtyard"),
    ("🇨🇳 · Cina, Esercito di Terracotta, Xi'an",             "Terracotta Army pits, Xi'an, China, rows of warrior figures, amber light"),
    ("🇨🇳 · Cina, Grande Muraglia, Jinshanling",              "Great Wall of China, Jinshanling, autumn foliage, golden light"),

    # ══ 🇭🇰 HONG KONG (1) ════════════════════════════════════
    ("🇭🇰 · Hong Kong, Victoria Peak, skyline notturno",      "Victoria Peak, Hong Kong, glittering night skyline, skyscrapers, harbour below"),

    # ══ 🇸🇬 SINGAPORE (1) ════════════════════════════════════
    ("🇸🇬 · Singapore, Marina Bay Sands, Gardens by the Bay", "Marina Bay Sands, Singapore, futuristic skyline, Gardens by the Bay supertrees, night"),

    # ══ 🇯🇵 GIAPPONE (3) ═════════════════════════════════════
    ("🇯🇵 · Giappone, Kyoto, bosco di bambù Arashiyama",      "Arashiyama bamboo grove, Kyoto, towering green culms, filtered light"),
    ("🇯🇵 · Giappone, Kyoto, torii di Fushimi Inari",         "Fushimi Inari shrine, Kyoto, endless red torii gates, misty forest path"),
    ("🇯🇵 · Giappone, Monte Fuji, fiori di ciliegio",         "Mount Fuji, Japan, cherry blossom foreground, Kawaguchiko lake reflection"),

    # ══ 🇹🇭 TAILANDIA (1) ════════════════════════════════════
    ("🇹🇭 · Tailandia, Maya Bay, scogliere carsiche",         "Maya Bay, Phi Phi Islands, Thailand, limestone cliffs, emerald water"),

    # ══ 🇻🇳 VIETNAM (1) ══════════════════════════════════════
    ("🇻🇳 · Vietnam, Baia di Halong, picchi carsici",         "Halong Bay limestone karsts, Vietnam, emerald water, fishing boats mist"),

    # ══ 🇰🇭 CAMBOGIA (2) ════════════════════════════════════
    ("🇰🇭 · Cambogia, Angkor Wat, stagno di loto",            "Angkor Wat main causeway, Cambodia, lotus pond reflection, sunrise"),
    ("🇰🇭 · Cambogia, Bayon, volti di pietra",                "Angkor Thom Bayon temple, Cambodia, stone faces, jungle canopy"),

    # ══ 🇲🇲 MYANMAR (1) ══════════════════════════════════════
    ("🇲🇲 · Myanmar, Bagan, pagode e mongolfiere",            "Bagan temple plain, Myanmar, hot air balloons at dawn, misty pagodas"),

    # ══ 🇵🇭 FILIPPINE (1) ════════════════════════════════════
    ("🇵🇭 · Filippine, El Nido, lagune carsiche",             "El Nido, Palawan, Philippines, limestone karst islands, turquoise lagoon"),

    # ══ 🇮🇩 INDONESIA (1) ════════════════════════════════════
    ("🇮🇩 · Indonesia, Bali, terrazze di riso Tegalalang",    "Tegalalang rice terraces, Bali, Indonesia, green stepped fields, palm trees, morning mist"),

    # ══ 🇲🇻 MALDIVE (1) ══════════════════════════════════════
    ("🇲🇻 · Maldive, bungalow sull'acqua, laguna",            "Maldives overwater bungalows, crystal clear turquoise lagoon, white sand, tropical sunset"),

    # ══ 🇸🇨 SEYCHELLES (1) ═══════════════════════════════════
    ("🇸🇨 · Seychelles, Anse Source d'Argent",                "Anse Source d'Argent, La Digue, Seychelles, granite boulders, pink sand"),

    # ══ 🇦🇺 AUSTRALIA (2) ════════════════════════════════════
    ("🇦🇺 · Australia, Uluru, tramonto nel deserto rosso",    "Uluru, Ayers Rock, Australia, monolithic red sandstone, desert sunset, ancient sacred site"),
    ("🇦🇺 · Australia, Whitsundays, Whitehaven Beach",        "Whitehaven Beach, Whitsundays, Australia, pure silica white sand"),

    # ══ 🇺🇸 USA (7) ══════════════════════════════════════════
    ("🇺🇸 · USA, Arizona, Antelope Canyon, raggi di luce",    "Antelope Canyon slot canyon, Arizona, light beams, swirling sandstone"),
    ("🇺🇸 · USA, Arizona, Grand Canyon, rocce rosse",         "Grand Canyon South Rim, Arizona, layered red rock, golden hour"),
    ("🇺🇸 · USA, Arizona, Monument Valley, mesa",             "Monument Valley buttes, Arizona, red mesa silhouettes, sunset"),
    ("🇺🇸 · USA, Louisiana, New Orleans, French Quarter",     "New Orleans French Quarter, wrought-iron balconies, jazz street, warm evening light"),
    ("🇺🇸 · USA, Florida, Miami, South Beach Art Déco",       "Miami South Beach, Ocean Drive, Art Deco pastel hotels, palm trees, turquoise sea"),
    ("🇺🇸 · USA, Nevada, Las Vegas, Strip di notte",          "Las Vegas Strip at night, neon signs, luxury hotel facades, dazzling light show"),
    ("🇺🇸 · USA, New York, Central Park, viale autunnale",    "New York Central Park, autumn tree-lined path, golden leaves, Manhattan skyline beyond"),
    ("🇺🇸 · USA, New York, Manhattan skyline notturno",       "Manhattan skyline at night, New York, glittering skyscrapers, Hudson river reflection"),
    ("🇺🇸 · USA, Niagara Falls, arcobaleno",                  "Niagara Falls Horseshoe, Canada, rainbow mist, thundering water"),

    # ══ 🇧🇷 BRASILE (3) ══════════════════════════════════════
    ("🇧🇷 · Brasile, Baia do Sancho, Fernando de Noronha",    "Baia do Sancho, Fernando de Noronha, Brazil, lush cliff, turquoise"),
    ("🇧🇷 · Brasile, Rio de Janeiro, Copacabana",             "Copacabana beach, Rio de Janeiro, iconic promenade, mosaic pavement, Atlantic"),
    ("🇧🇷 · Brasile, Rio de Janeiro, Pan di Zucchero",        "Sugarloaf Mountain, Rio de Janeiro, cable car, Guanabara Bay panorama, sunset"),

    # ══ 🇦🇷 ARGENTINA (1) ════════════════════════════════════
    ("🇦🇷 · Argentina, Cascate di Iguazú",                    "Iguazu Falls panorama, Argentina/Brazil border, jungle mist, cascades"),

    # ══ 🇨🇱 CILE (1) ═════════════════════════════════════════
    ("🇨🇱 · Cile, Isola di Pasqua, moai",                    "Easter Island Ahu Tongariki, Chile, moai row, ocean sunrise"),

    # ══ 🇵🇪 PERÙ (1) ═════════════════════════════════════════
    ("🇵🇪 · Perù, Machu Picchu, alba andina",                 "Machu Picchu citadel, Peru, Andean peaks above clouds, sunrise"),

    # ══ 🇲🇽 MESSICO (1) ══════════════════════════════════════
    ("🇲🇽 · Messico, Chichen Itza, El Castillo",              "Chichen Itza El Castillo pyramid, Mexico, equinox light, shadow serpent"),

    # ══ 🇺🇸 HAWAII (1) ═══════════════════════════════════════
    ("🇺🇸 · USA, Hawaii, Na Pali Coast, Kauai",               "Na Pali Coast, Kauai, Hawaii, dramatic green sea cliffs, turquoise Pacific, waterfalls"),

    # ══ 🇪🇨 GALÁPAGOS (1) ════════════════════════════════════
    ("🇪🇨 · Ecuador, Galápagos, Pinnacle Rock",               "Pinnacle Rock, Bartolomé Island, Galápagos, volcanic spire, turquoise bay, marine iguanas"),
]

# --- OUTFIT POOL (100) ---
# Ordinamento: Beachwear → Mini Dress → Futurista → Retrò '20 → Retrò '70 → Avanguardia/Scenografico → Costumi/Teatrali → Film Iconici
# All'interno di ogni sezione: alfabetico per stilista, poi colore
# Esclusi: abiti lunghi/maxi/midi, pantaloni, shorts, indumenti maschili, safety risk (lingerie, fishnet, barely-there, spray-on)
OUTFIT_POOL = [
    # (label, value_prompt)
    # Ordine: Tipo → Colore → Stilista
    # Label: "Colore — descrizione breve" — stilista rimosso dal label, presente solo nel prompt

    # ── BEACHWEAR ──────────────────────────────────────────────────────────────
    ("Bianco — one-piece con cut-out",            "ivory white Alaia one-piece, structured V front, sculpted waist, classic cut legs, white slide sandals, gold cuff"),
    ("Bianco — bandeau high-cut",                 "ivory white Eres sporty bandeau high-cut bikini, sculpted top, clean minimal lines, white wrap pareo, gold flat sandals, oversized sunglasses"),
    ("Rosso cremisi — triangle bikini",           "crimson La Perla triangle string bikini, red cord ties, gold anklet, oversized black sunglasses"),
    ("Rosso — one-piece con hardware oro",        "bold red Gottex structured underwire one-piece, high-cut legs, low back, gold ring hardware at hip, red wedge espadrilles, gold cuff"),
    ("Rosa caldo — one-piece con trim oro",       "hot pink Versace structured one-piece, gold Greek key trim, plunging neckline, gold stiletto sandals, statement gold hoops"),
    ("Rosa fucsia — halter bikini",               "electric fuchsia Gottex halter bikini, underwire top, high-waist bottoms, fuchsia slides, layered gold necklaces"),
    ("Corallo profondo — bikini crochet",         "deep coral Missoni crochet bikini, fringe hem bottoms, matching crochet cover-up, tan flat sandals, shell earrings"),
    ("Corallo tropicale — triangle print bikini", "tropical coral Zimmermann triangle print bikini, ruffled top, high-waist bottoms, matching pareo wrap, cork wedge sandals, gold ring earrings"),
    ("Arancio tangerine — ruffle off-shoulder",   "hot tangerine Agua Bendita off-shoulder ruffle mini swimwear, smocked bodice, cork wedge sandals, gold layered chains"),
    ("Metallico bronzo — string bikini",          "bronze metallic Melissa Odabash string bikini, wide-brim bronze hat, tan leather thong sandals, layered gold chains"),
    ("Turchese elettrico — bandeau bikini",       "electric turquoise Eres bandeau bikini, high-cut bottoms, sheer turquoise pareo tied low, tan espadrille wedges"),
    ("Turchese — halter one-piece",               "turquoise Melissa Odabash structured halter one-piece, ruched front panel, gold ring detail, metallic flat sandals"),
    ("Blu cobalto — crinkle bikini",              "cobalt blue Hunza G crinkle bikini, ruched bandeau top, matching high-rise briefs, cobalt espadrilles, silver anklet"),
    ("Verde foresta — sporty bandeau",            "forest green Eres sporty bandeau crop-top bikini, high-rise briefs, linen shirt open over shoulders, tan espadrilles"),
    ("Verde foresta — one-piece high-leg",        "forest green La Perla high-leg one-piece, structured bust, low back, gold hardware rings, tan leather slides"),
    ("Verde salvia — bandeau bikini",             "sage green Seafolly bandeau bikini, tie-waist high-rise bottoms, sage linen shirt open, flat leather sandals"),
    ("Viola elettrico — ruched bandeau",          "electric violet Vilebrequin ruched bandeau bikini, high-rise briefs, matching sarong wrap, violet flat sandals, gold anklet"),
    ("Lavanda — halter one-piece",                "pale lavender Valentino one-piece, plunging halter neck, tie-side, lavender slides, amethyst bracelet"),

    # ── MINI DRESS ─────────────────────────────────────────────────────────────
    ("Nero midnight — asymmetric micro",          "midnight black Nensi Dojaka asymmetric micro dress, structured panels, delicate straps, black perspex heels, no jewellery"),
    ("Bianco crema — tweed micro",                "cream and black Chanel tweed micro dress, structured skirt, gold chain trim, low-cut neckline, black cap-toe pumps, pearl bracelet"),
    ("Bianco avorio — lace-panel mini",           "ivory Christopher Kane lace-panel micro mini, semi-opaque geometric inserts, structured bodice, nude platform heels, pearl cluster earrings"),
    ("Rosso burgundy — lace mini",                "deep burgundy Self-Portrait lace mini, plunging back, long sleeves, wine-red strappy heels, pearl choker"),
    ("Rosso rubino — velvet mini",                "deep ruby Tom Ford velvet micro mini, plunging V neckline, long sleeves, ruby satin stilettos, single diamond drop earring"),
    ("Rosa magenta — ruffled mini",               "hot magenta Valentino ruffled mini dress, sweetheart neckline, bare shoulders, fuchsia satin heels, diamond tennis bracelet"),
    ("Rosa baby — crystal-trim micro",            "baby pink Miu Miu crystal-embellished micro mini, rhinestone-trimmed raw hem, cropped top, pink satin mules, crystal barrette"),
    ("Rosa dusty — broderie off-shoulder",        "dusty rose Zimmermann broderie anglaise off-shoulder mini, tiered hem, blush wedge sandals, pearl drop earrings"),
    ("Corallo — sequined mini",                   "bright coral Retrofete sequined mini, plunging V, spaghetti straps, coral stiletto sandals, gold stacking rings"),
    ("Terracotta — broderie strapless",           "terracotta Chloe broderie strapless mini, frayed hem, raw edges, tan leather block heels, hammered gold cuffs"),
    ("Arancio bruciato — strapless bodycon",      "burnt orange Alexandre Vauthier strapless bodycon mini, ruched bust, high slit, nude pointed pumps, gold bangles"),
    ("Ambra calda — slip micro",                  "warm amber Isabel Marant silk slip micro, bias-cut, thin spaghetti straps, open back, amber flat sandals, layered gold chains"),
    ("Giallo acido — asymmetric micro",           "acid yellow Jacquemus asymmetric micro mini, single draped strap, bare shoulders, nude pointed mules, gold chain necklace"),
    ("Verde giada — spiral seam mini",            "jade green Mugler spiral-seam bodycon mini, precision-cut curved seams, high neck, black stiletto ankle boots, no jewellery"),
    ("Verde foresta — micro mini",                "deep forest green Versace micro mini, plunging neckline, gold Medusa hardware, black strappy sandals, statement gold hoops"),
    ("Blu cobalto — sequined mini",               "electric cobalt sequined Balmain mini dress, plunging V neckline, structured shoulders, cobalt strappy heels, gold ear cuffs"),
    ("Blu navy — Bar micro",                      "navy midnight Dior Bar-inspired micro, structured nipped waist, flared mini skirt, navy pointed pumps, pearl choker, white gloves"),
    ("Blu teal — wrap mini",                      "electric teal Acne Studios asymmetric wrap mini, draped one-shoulder, thigh slit, teal patent heels, single chain earring"),
    ("Blu ghiaccio — bandage mini",               "ice blue Herve Leger bandage mini, wrap neckline, body-sculpting seams, powder blue platform heels, crystal ear studs"),
    ("Grigio acciaio — cut-out mini",             "steel grey Coperni cut-out mini, architectural cutaways at waist, perspex block heels, silver ear climbers"),
    ("Viola elettrico — draped one-shoulder",     "electric violet Rick Owens draped mini, asymmetric one-shoulder, thigh slit, violet pointed pumps, silver cuff"),
    ("Lilla polvere — structured mini",           "powder lilac Givenchy structured boxy mini, stiff sculpted silhouette, architectural seams, lilac pointed pumps, geometric silver earrings"),
    ("Lilla dusty — draped mini",                 "dusty lilac Nanushka draped satin mini, gathered at hip, one-shoulder asymmetric, lilac heeled mules, simple pearl stud"),
    ("Metallico oro — disc mini",                 "gold metallic disc-chain Paco Rabanne mini dress, linked metal discs, gold stiletto sandals, no other jewellery"),
    ("Metallico argento — crystal mesh",          "silver crystal-mesh Poster Girl micro mini, bodycon, all-over rhinestones, silver ankle-strap heels"),

    # ── ESTIVI ─────────────────────────────────────────────────────────────────
    ("Caramello — knit micro Bottega",             "caramel Bottega Veneta intrecciato knit micro dress, low scoop back, fitted, tan leather block heels, tortoiseshell cuff"),
    ("Blu polvere — broderie sundress",           "powder blue Faithfull broderie sundress, mini length, puff sleeves, white block heels, pearl studs"),
    ("Verde muschio — slip dress",                "moss green Bottega Veneta slip dress, cowl back, bare shoulders, tan leather mules, gold cuff"),
    ("Viola profondo — laser-cut bodycon",        "deep violet Alaia laser-cut bodycon, geometric laser-cut openwork, violet patent heels, single silver cuff"),

    # ── FUTURISTA / SCI-FI ─────────────────────────────────────────────────────
    ("Nero opaco — hourglass cut-out",            "matte black Mugler hourglass cut-out bodycon dress, spiral waist openings, structured panels, black stiletto boots"),
    ("Bianco gesso — vinyl circle micro",         "chalk white Courrèges vinyl circle-cut micro dress, geometric seaming, structured collar, white go-go boots, silver geometric earrings"),
    ("Bianco — abstract sculpture",               "white Comme des Garcons conceptual abstract sculptural dress, exaggerated architectural form, asymmetric padded volumes, flat white shoes"),
    ("Arancio neon — inflated cocoon",            "neon orange Balenciaga inflated cocoon silhouette mini dress, sculptural volume, matching orange boots, minimalist"),
    ("Arancio — laser-cut vinyl",                 "hot orange Versace laser-cut vinyl mini dress, geometric perforations, orange patent heels, chrome hoops"),
    ("Verde lime — 3D sculptural",                "electric lime Iris van Herpen 3D-printed sculptural mini, bare arms, architectural platform heels, no jewellery"),
    ("Verde chartreuse — Pleats Please",          "neon chartreuse Issey Miyake Pleats Please micro dress, accordion pleats, geometric origami folds, flat white sandals, single sculptural cuff"),
    ("Grigio colomba — pod micro",                "dove grey Rick Owens sculptural pod micro, asymmetric volume panel at hip, bare shoulders, white leather platform boots, no jewellery"),
    ("Metallico rame — liquid mesh",              "molten copper Paco Rabanne liquid chainmail mesh mini, plunging neckline, fluid drape, copper stiletto sandals, no jewellery"),
    ("Metallico iridescente — magnetic wave",     "iridescent Iris van Herpen magnetic-wave mini, undulating 3D-printed panels, perspex platform heels, single ear antennae"),
    ("Metallico reflective — space-age",          "reflective mylar Marques Almeida space-age mini dress, crinkled metallic surface, silver platform sneakers"),

    # ── RETRÒ ANNI '20 / ART DÉCO ──────────────────────────────────────────────
    ("Avorio — bias-cut satin Gatsby",            "ivory 1920s Gatsby-era bias-cut satin mini dress, cowl neckline, beaded shoulder straps, ivory heels, diamond headband"),
    ("Oro pallido — silk charmeuse",              "pale gold 1920s Vionnet-inspired silk charmeuse bias-cut mini, fluid drape, backless, gold sandals, long pearl necklace"),
    ("Oro champagne — flapper beaded",            "gold beaded Art Deco flapper dress, fringe hem, dropped waist, intricate beadwork, T-strap gold heels, long pearl rope, feather headband"),
    ("Champagne — Charleston sequined",           "champagne sequined 1920s Charleston dress, fringed hem, sleeveless, V back, champagne heels, rhinestone headpiece"),
    ("Blu midnight — drop-waist Art Déco",        "midnight blue Art Deco beaded drop-waist dress, geometric pattern, silver fringe, silver T-bar heels, feathered headpiece"),

    # ── RETRÒ ANNI '70 / GLAM ROCK / DISCO ────────────────────────────────────
    ("Oro liquido — studio disco halter",         "liquid gold Halston 1970s studio disco halter dress, fluid jersey, one shoulder, bare back, gold platforms, hoop earrings"),
    ("Arancio ruggine — crepe halter micro",      "rust orange Ossie Clark crepe halter micro, draped cowl neck, open back, platform wooden sandals, amber bead necklace"),
    ("Siena bruciato — satin halter disco",       "burnt sienna Biba 1970s satin deep-V halter disco mini, cowl front, bare back, platform sandals, long pendant earrings"),
    ("Grafica bianco/nero — op-art mini",         "black and white Biba op-art geometric micro mini, bold graphic print, high neck, white platform ankle boots, round white sunglasses"),
    ("Multicolor — graphic print anni 70",        "electric Pucci 1970s bold graphic-print mini dress, signature swirling pattern, platform wedges, oversized sunglasses"),

    # ── AVANGUARDIA / SCENOGRAFIA ──────────────────────────────────────────────
    ("Bianco — architectural micro Junya",         "white structured Junya Watanabe architectural micro dress, exaggerated collar, rigid geometric volumes, white platform boots, no jewellery"),
    ("Nero — armadillo structural mini",          "black Alexander McQueen structural mini, dramatic winged shoulders, armour-like silhouette, McQueen armadillo platform heels"),
    ("Nero — asymmetric draped micro",            "charcoal Ann Demeulemeester asymmetric draped micro, raw-edge hem, one bare shoulder, black strapped flat sandals, single cuff"),
    ("Nero — hourglass estremo",                  "pitch black Balenciaga extreme hourglass mini, exaggerated waist, structured skirt panel, black stiletto ankle boots, no jewellery"),
    ("Bianco — trompe l'oeil ottico",             "nude illusion Maison Margiela trompe l oeil micro, body-print optical illusion fabric, nude heels, minimalist"),
    ("Rosso bordeaux — draped angular",           "bordeaux Haider Ackermann angular draped micro, sharp asymmetric hem, bias-cut crepe, bare back, bordeaux stiletto mules, ear cuff"),
    ("Verde smeraldo — velvet embroidered",       "emerald Dries Van Noten velvet micro mini, dense floral embroidery, jewel-tone beading, deep V back, green velvet heels, stacked rings"),
    ("Blu indaco — patchwork micro",              "indigo patchwork Junya Watanabe denim micro mini, mixed texture panels, deconstructed seams, white platform boots, no jewellery"),
    ("Oro — cone bra corset",                     "gold satin Jean Paul Gaultier iconic cone bra corset mini dress, structured pointed bust, gold stilettos, theatrical makeup"),
    ("Metallico chrome — geometric",              "chrome geometric Gareth Pugh metallic sculptural mini dress, angular panels, architectural construction, chrome platform boots"),

    # ── COSTUMI / TEATRALI ─────────────────────────────────────────────────────
    ("Nero — feather-cape bodysuit",              "black Ashi Studio feathered dramatic cape bodysuit, cascading ostrich feathers, bare legs, black stilettos, no jewellery"),
    ("Bianco lino — sacerdotessa egizia",         "white linen Egyptian priestess fashion micro, precision pleated fabric, wide gold pectoral collar, gold arm cuffs, flat gold sandals, kohl eyes"),
    ("Bianco/oro — silk obi geisha",              "contemporary fashion geisha-inspired ivory and gold silk micro dress, wide sculptural obi sash waistband, structured collar, ivory wooden platform sandals, gold kanzashi"),
    ("Oro martellato — armatura amazzone",        "hammered gold Amazon warrior fashion editorial, sculptural bronze-effect armour breastplate, micro leather skirt, gold gladiator sandals to knee, laurel headpiece"),
    ("Rosso rubino — brocade odalisque",          "ruby red orientalist fashion micro, richly embroidered brocade bodice, layered silk skirt panels, jewelled belt, flat embroidered slippers, chandelier earrings"),
    ("Blu royal — tartan corset",                 "royal blue tartan Vivienne Westwood corseted mini, structured boning, asymmetric bustle, platform shoes, punk accessories"),
    ("Argento frost — valchiria metallica",       "silver frost Norse goddess editorial fashion, metallic scale-pattern micro dress, structured shoulder guards, silver thigh-high boots, hammered silver circlet"),
    ("Multicolor aurora — ombré silk",            "aurora borealis ombré silk micro dress, iridescent teal to violet gradient, sculptural collar, crystal platform heels"),

    # ── FILM ICONICI ───────────────────────────────────────────────────────────
    ("Nero — LBD Breakfast at Tiffany",           "iconic black Givenchy Breakfast at Tiffany LBD, sleeveless column mini silhouette, opera gloves, tiara, pearl necklace, upswept hair"),
    ("Nero — studded micro Mad Max",              "burnt metal Mad Max warrior fashion editorial, studded asymmetric micro leather dress, armoured shoulder detail, laced boots to knee, no jewellery"),
    ("Bianco — abito subway Monroe",              "white halter pleated Marilyn Monroe subway dress, billowing skirt, white stiletto heels, diamond drop earrings"),
    ("Bianco — structured tutu Black Swan",       "pure white Black Swan structured tutu bodysuit, fitted corseted bodice, sculpted tulle skirt, white satin pointe heels, feather crown headpiece"),
    ("Bianco gesso — wrap mini Basic Instinct",   "chalk white Basic Instinct-inspired structured wrap mini dress, sharp lapels, belted waist, white stiletto heels, no jewellery, icy gaze"),
    ("Bianco — strapless swimsuit La Dolce Vita", "white La Dolce Vita-inspired strapless structured swimsuit, sculpted bustier top, Anita Ekberg silhouette, white kitten heels, pearl drop earrings"),
    ("Rosso scarlatto — corseted Pretty Woman",   "scarlet red Pretty Woman strapless corseted mini dress, structured bodice, full mini skirt, red satin heels, long gloves, diamond drop earrings"),
    ("Rosa caldo — pink satin Gentlemen Blondes", "hot pink strapless satin micro from Gentlemen Prefer Blondes, structured sweetheart bust, pink satin gloves, diamond chandelier earrings, pink heels"),
    ("Oro bianco — linen micro Cleopatra",        "white gold pleated Cleopatra-inspired linen wrap micro, wide metallic collar, gold ankle cuffs, flat gold sandals, kohl eye makeup"),
    ("Giallo/nero — plaid micro Clueless",        "yellow and black plaid Clueless micro mini skirt set, matching cropped blazer open, white knee socks, white platform Mary Janes, tiny backpack"),
    ("Argento — space vinyl Barbarella",          "silver Barbarella-style space-age vinyl micro outfit, structured breastplate, thigh-high boots, futuristic accessories, dramatic hair"),
    ("Argento — crystal goblin queen Labyrinth",  "silver crystal Labyrinth goblin queen fashion editorial, structured crystal-studded mini bodice, dramatic silver cape collar, silver thigh-high boots, crystal crown"),
    ("Argento — machine-woman Metropolis",        "polished silver Metropolis-inspired fashion editorial bodysuit, riveted metal panels, structured breast plate, silver thigh-high boots, silver crown"),
    ("Chrome — space disco Zoolander",            "chrome silver Zoolander-inspired space disco micro dress, metallic sheen, structured shoulders, silver platform boots, dramatic silver eye makeup"),
]

STYLE_POOL = [
    # ordinamento: alfabetico A→Z per nome stile o fotografo
    ("Albert Watson · ritratto tagliente",           "Albert Watson, sharp precise portraiture, graphic contrast, technical mastery"),
    ("Annie Leibovitz · ritratto narrativo",         "Annie Leibovitz, narrative cinematic portraiture"),
    ("Art Déco · geometria e oro",                   "Art Deco style, geometric opulence, gold and black, symmetry, 1920s glamour"),
    ("Art Nouveau · decorativo liberty",             "Art Nouveau style, flowing organic lines, floral motifs, Mucha-inspired decorative frame, pastel and gold"),
    ("Arte tribale · etnico contemporaneo",          "tribal ethnic contemporary art style, bold geometric patterns, earth pigments, ritual aesthetics, raw power"),
    ("Azzurro pastello · estetica coreana",          "Korean pastel soft aesthetic, dreamy blue tones, clean minimalism, gentle light"),
    ("Bauhaus · geometria modernista",               "Bauhaus design aesthetic, geometric composition, primary colours, modernist grid, clean functional beauty"),
    ("Bruce Weber · lifestyle soleggiato",           "Bruce Weber, sun-drenched American lifestyle photography"),
    ("Chiaroscuro barocco · Caravaggio",             "Baroque chiaroscuro, Caravaggio dramatic light, deep shadow, single light source"),
    ("Cibachrome · saturazione anni 80",             "1980s Cibachrome process, hyper-saturated chemical colours, high contrast glossy"),
    ("Cyberpunk · neon e pioggia",                   "cyberpunk aesthetic, neon lights, rain-soaked streets, electric blue and pink"),
    ("David LaChapelle · pop art iperrealista",      "David LaChapelle, hyperrealistic pop art surrealism"),
    ("Ellen von Unwerth · glamour giocoso",          "Ellen von Unwerth, playful glamorous feminine energy"),
    ("Espressionismo tedesco · angoscia drammatica", "German Expressionist style, dramatic distortion, Munch-like colour, psychological tension, raw brushwork"),
    ("Film noir · bianco e nero cinematografico",    "Film noir style, high contrast black and white, venetian blind shadows, moody"),
    ("Folklore slavo · oro e velluto",               "Slavic folk art style, ornate gold embroidery, rich velvet, Byzantine icon influence, jewelled headdress"),
    ("Futurismo italiano · dinamismo",               "Italian Futurism, dynamic movement lines, speed, machine aesthetic, bold angles"),
    ("Guy Bourdin · surrealismo saturo",             "Guy Bourdin, saturated surrealist fashion photography"),
    ("Helmut Newton · glamour in bianco e nero",     "Helmut Newton, glamorous monochrome editorial"),
    ("Herb Ritts · scultura in bianco e nero",       "Herb Ritts, sculptural black and white photography"),
    ("Impressionismo · luce e colore",               "Impressionist painting style, loose brushwork, natural light, colour vibration"),
    ("Irving Penn · studio pulito e senza tempo",    "Irving Penn, clean studio portraiture, timeless elegance"),
    ("Iris van Herpen · digitale organico",          "Iris van Herpen digital editorial, organic-digital fusion, otherworldly forms"),
    ("Juergen Teller · realismo grezzo",             "Juergen Teller, raw unfiltered fashion realism"),
    ("Lo-fi analogico · grana e imperfezione",       "lo-fi analog photography, visible grain, light leaks, imperfection as beauty"),
    ("Mario Testino · glossy vibrante",              "Mario Testino, vibrant glossy fashion photography"),
    ("Miles Aldridge · iper-saturo cinematografico", "Miles Aldridge, cinematic hyper-saturated colour"),
    ("Miniatura persiana · ornato islamico",         "Persian miniature painting style, gold leaf, intricate Islamic geometric border, jewel-like colours"),
    ("Minimalismo estremo · bianco totale",          "extreme minimalism, pure white background, single subject, no distraction"),
    ("Nan Goldin · documentario intimo",             "Nan Goldin, intimate documentary fashion realism"),
    ("Nick Knight · avanguardia digitale",           "Nick Knight, avant-garde digital fashion imagery"),
    ("Paolo Roversi · morbidezza pittorica",         "Paolo Roversi, painterly soft-focus romanticism"),
    ("Patrick Demarchelier · eleganza classica",     "Patrick Demarchelier, classic elegant fashion photography"),
    ("Peter Lindbergh · cinema naturale",            "Peter Lindbergh, cinematic naturalistic beauty"),
    ("Pittura fiamminga · oro e dettaglio",          "Flemish painting style, meticulous detail, golden light, jewel and fabric texture"),
    ("Pittura orientale · Cina classica",            "classical Chinese ink painting style, mountain mist, silk textures, delicate brushwork, poetic atmosphere"),
    ("Pop Art · colore piatto e grafica",            "Pop Art style, flat bold colour, graphic outline, Warhol and Lichtenstein influence"),
    ("Preraffaellita · romanticismo medievale",      "Pre-Raphaelite painting style, medieval romanticism, Rossetti and Millais aesthetic, jewel colours, narrative"),
    ("Propaganda sovietica · poster costruttivista", "Soviet constructivist poster style, bold red and black, diagonal composition, heroic figure"),
    ("Richard Avedon · movimento dinamico",          "Richard Avedon, dynamic high-fashion movement"),
    ("Rinascimento italiano · pittura classica",     "Italian Renaissance painting style, Leonardo and Raphael composition, sfumato lighting, classical harmony"),
    ("Romanticismo · atmosfera Turner",              "Romantic painting style, Turner atmospheric landscape, sublime nature, dramatic sky"),
    ("Steven Meisel · editoriale sofisticato",       "Steven Meisel, sophisticated high-fashion editorial"),
    ("Surrealismo onirico · sogno Dalì-Magritte",    "Surrealist dreamscape style, Dalì and Magritte influence, impossible juxtapositions, hyper-real detail"),
    ("Tim Walker · fantasy bizzarro",                "Tim Walker, fantastical whimsical fashion storytelling"),
    ("Ukiyo-e giapponese · stampa woodblock",        "Japanese Ukiyo-e woodblock print style, flat colour, bold outlines, decorative patterns, Edo period aesthetics"),
    ("Vintage Kodachrome · caldo e granoso",         "vintage Kodachrome film, warm tones, fine grain, 1960s saturated palette"),
    ("Vogue Italia anni 90 · editoriale duro",       "Vogue Italia 1990s hard editorial, provocative, Steven Meisel era, raw beauty"),
    ("Wet plate collodio · dagherrotipo vittoriano", "wet collodion plate process, Victorian daguerreotype, silver tones, antique texture"),
    ("Wim Wenders · road movie malinconico",         "Wim Wenders road movie aesthetic, melancholic Americana, wide angle, lonely landscapes"),
]

POSE_POOL = [
    # ── IN PIEDI — frontale ────────────────────────────────────────────────────
    ("🧍 In piedi · mano sul fianco",           "standing upright, one hand on hip, chin slightly lifted"),
    ("🧍 In piedi · gambe incrociate",          "standing with legs crossed at knee, arms loose at sides"),
    ("🧍 In piedi · postura larga",             "standing with legs wide apart, hands clasped behind back"),
    ("🧍 In piedi · gamba avanzata",            "standing with one leg forward, weight shifted to hip"),
    ("🧍 In piedi · mano sul petto",            "standing with one hand on chest, other at side, soft gaze"),
    ("🧍 In piedi · braccia alzate",            "standing with arms raised overhead, arched back"),
    ("🧍 In piedi · mani tra i capelli",        "standing with hands in hair, elbows raised"),
    ("🧍 In piedi · profilo laterale",          "standing side profile, one arm extended along wall"),
    ("🧍 In piedi · schiena alla camera",       "standing back to camera, glancing over shoulder"),
    ("🧍 In piedi · sulla porta",               "standing in doorway, one hand on frame, body turned"),
    # ── IN PIEDI — in movimento ────────────────────────────────────────────────
    ("🚶 Cammina verso la camera",              "walking confidently toward camera, skirt in motion"),
    ("🚶 Cammina e si volta",                   "walking away, looking back, hair movement"),
    ("🚶 Cammina di lato lungo il muro",        "walking sideways along wall, fingertips trailing surface"),
    ("💃 Gira su se stessa",                    "spinning, skirt fanned out, captured mid-rotation"),
    ("💃 Saltello · gambe in aria",             "jumping lightly, legs bent upward behind, carefree movement"),
    ("💃 Passo di danza · braccio alzato",      "dance step, one arm raised elegantly, weight on one leg"),
    # ── IN PIEDI — appoggiate ──────────────────────────────────────────────────
    ("🧗 Appoggiata al muro · ginocchio piegato","leaning against wall, arms crossed, one knee bent"),
    ("🧗 Appoggiata al muro · sporge in avanti","leaning forward slightly, hands on thighs, direct gaze"),
    ("🧗 Appoggiata · testa reclinata all'indietro","leaning back against surface, head tilted up, eyes closed"),
    ("🧗 Appoggiata al corrimano · orizzonte",  "leaning on railing, one elbow resting, gazing at horizon"),
    ("🧗 Appoggiata allo stipite · gambe incrociate","leaning on door frame, ankles crossed, arms folded"),
    ("🧗 Mano sulla parete · corpo girato",     "one hand flat on wall, body turned away, gaze sideways"),
    # ── SEDUTA ─────────────────────────────────────────────────────────────────
    ("🪑 Seduta · gambe incrociate",            "sitting on edge of surface, legs crossed at ankle, back straight"),
    ("🪑 Seduta su sedia · gambe sul bracciolo","seated on chair, legs draped over armrest, relaxed"),
    ("🪑 Seduta sulle scale · gomiti sulle ginocchia","sitting on steps, elbows on knees, chin resting on hands"),
    ("🪑 Seduta sulle scale · fianco al corrimano","seated on staircase, turned sideways, arm on banister"),
    ("🪑 Seduta sul bordo dell'acqua",          "seated at edge of water, feet dangling in"),
    ("🪑 Seduta in terra · gambe piegate",      "seated on floor, knees drawn up, arms wrapped around legs"),
    ("🪑 Seduta a gambe incrociate · terra",    "seated cross-legged on floor, hands resting on knees"),
    ("🪑 In ginocchio · gamba estesa",          "kneeling on one knee, other leg extended, torso upright"),
    ("🪑 Inginocchiata di lato · peso su un fianco",   "kneeling sideways, weight shifted onto one hip, one leg extended to the side, torso upright, elegant fashion pose"),
    # ── DISTESA ────────────────────────────────────────────────────────────────
    ("😴 Distesa di lato · gomito a terra",     "reclining on side, propped on elbow, legs extended"),
    ("😴 Distesa · braccia sopra la testa",     "lying on back, arms above head, legs slightly apart"),
    ("😴 Pancia a terra · gambe piegate",       "lying face down, propped on forearms, legs bent upward"),
    ("😴 Distesa in acqua · galleggiante",      "floating on water surface, arms extended, serene"),
    ("😴 Distesa sull'erba · mano sul viso",    "lying on grass, one hand under cheek, relaxed, natural"),
    # ── SPECIALI ───────────────────────────────────────────────────────────────
    ("✨ Di schiena · abito in primo piano",    "back to camera, dress detail in focus, hair over shoulder"),
    ("✨ Silhouette controluce",                "strong backlight silhouette, dramatic outline, no face detail"),
    ("✨ Mezza figura · sguardo diretto",       "half-body shot, direct intense gaze into camera"),
    ("✨ Figura intera · sguardo lontano",      "full body, gaze into distance, contemplative and distant"),
    ("✨ Figura intera · occhi chiusi",         "full body, eyes closed, serene expression, head slightly tilted"),
    ("✨ Dettaglio abito · figura tagliata",    "close crop on outfit detail, partial body, strong graphic"),
    ("✨ Posa teatrale · braccio proteso",      "theatrical pose, one arm extended dramatically toward camera"),
    ("✨ Mani in primo piano · corpo sfocato",  "hands in foreground sharp, body softly blurred behind"),
    ("✨ Riflesso nello specchio",              "mirror reflection pose, subject and reflection both visible"),
    ("✨ Ombra sul muro · corpo fuori campo",   "dramatic shadow cast on wall, body partially out of frame"),
    ("✨ In controluce · alone luminoso",       "backlit halo around figure, contre-jour, ethereal glow"),
    ("✨ Posa scultorea · statica e potente",   "statuesque still pose, monumental and commanding presence"),
    ("✨ Posa glamour anni 50 · pin-up",        "1950s glamour pin-up pose, playful, classic Hollywood"),
    ("✨ In punta di piedi · braccia aperte",   "standing on tiptoe, arms open wide, balletic and light"),
]

SKY_POOL = [
    # ── NOTTE ──────────────────────────────────────────────────────────────────
    ("🌑 Notte senza luna · buio totale",        "moonless night, total darkness, only artificial lights, deep shadows"),
    ("🌕 Notte · luna piena, luce argentata",    "clear night, full moon, silver-blue ambient light, sharp shadows"),
    ("🌃 Notte urbana · neon e asfalto bagnato", "neon city night, pink and blue reflections on wet pavement"),
    ("🏙 Notte panoramica · skyline luminoso",   "penthouse night, city glow from below, skyline backdrop"),
    ("🕯 Notte · candele e luce tremolante",     "candlelight warm glow, intimate, flickering amber"),
    ("🎭 Notte · faretti teatrali",              "theatrical spotlights, dramatic stage lighting, dark background"),
    # ── ALBA ───────────────────────────────────────────────────────────────────
    ("🌅 Alba · rosa pallido e oro",             "sunrise, pale pink and gold, delicate warm haze"),
    ("🌫 Alba nebbiosa · nebbia fresca",         "foggy morning, diffused cool light, soft mist"),
    ("❄️ Alba invernale · toni blu freddi",      "crystal clear winter light, cold blue tones, sharp and clean"),
    ("🌊 Alba marina · luce radente sull'acqua", "early morning beach, cool light, long shadows on sand"),
    # ── ORA BLU ────────────────────────────────────────────────────────────────
    ("🔵 Ora blu · crepuscolo profondo",         "blue hour, twilight, deep blue sky, city lights emerging"),
    ("🌧 Sera piovosa · riflessi sul selciato",  "rainy evening, grey sky, reflections on wet street"),
    # ── MATTINA ────────────────────────────────────────────────────────────────
    ("🌤 Mattina mediterranea · luce dorata",    "mediterranean morning, warm golden diffused light, clear sky"),
    ("🌿 Mattina in serra · verde diffuso",      "greenhouse light, soft diffused green-tinted natural light"),
    ("🏔 Mattina alpina · aria cristallina",     "mountain morning, crystal clear air, cool alpine light, blue sky"),
    # ── MEZZOGIORNO ────────────────────────────────────────────────────────────
    ("☀️ Mezzogiorno · sole duro, ombre nette",  "blue sky, harsh midday sun, sharp shadows"),
    ("🏜 Mezzogiorno desertico · luce bianca",   "desert midday, bleached white light, stark and hot"),
    ("🌺 Mezzogiorno tropicale · saturo vivido", "tropical noon, vivid saturated colors, intense shadows"),
    ("🏊 Mezzogiorno a bordo piscina",           "poolside afternoon, bright white reflections off water surface"),
    # ── POMERIGGIO ─────────────────────────────────────────────────────────────
    ("🍂 Pomeriggio autunnale · arancio basso",  "autumn afternoon, warm orange, low angle sun through leaves"),
    ("🇮🇹 Pomeriggio veneziano · luce sull'acqua","Venetian afternoon, warm reflected light off water"),
    ("🌊 Pomeriggio mediterraneo · afa dorata",  "late afternoon Mediterranean, golden haze, warm and sleepy"),
    ("🌧 Pomeriggio coperto · luce diffusa",     "overcast soft light, diffused, no shadows, milky sky"),
    ("🌨 Pomeriggio innevato · freddo blu",      "snowy exterior, pure white reflected light, cold blue shadows"),
    # ── ORA MAGICA / TRAMONTO ──────────────────────────────────────────────────
    ("✨ Ora d'oro · ambra calda e ombre lunghe","golden hour, warm amber light, long soft shadows"),
    ("🌇 Ora magica · cremisi e oro",            "magic hour, last light, sky deep crimson and gold"),
    ("🌆 Tramonto · crepuscolo viola arancio",   "dramatic dusk, deep purple and orange horizon"),
    ("🏙 Tramonto sul terrazzo · rosa viola",    "rooftop at sunset, sky gradient pink to violet"),
    ("⛈ Temporale · nuvole scure pre-pioggia",  "stormy sky, dark clouds, electric pre-rain tension"),
    ("🌊 Controluce · sole radente forte",       "backlit silhouette, strong rim light, sun behind subject"),
    # ── INTERNI ────────────────────────────────────────────────────────────────
    ("🏛 Studio · luce bianca clinica",          "bright white studio light, clean and clinical"),
    ("💫 Sala da ballo · lampadari di cristallo","grand ballroom chandeliers, warm crystal light from above"),
    ("🎭 Teatro dell'opera · faretti caldi",     "opera house interior, dramatic warm spotlights"),
    ("🌊 Subacqueo · raggi caustici",            "underwater light, caustic rays, turquoise shimmer"),
    ("🌿 Atelier · luce naturale laterale",      "atelier north light, soft lateral daylight, neutral tones"),
    ("🕌 Interno medievale · torce e pietra",    "medieval interior, torch light, warm amber on stone walls"),
    ("🏠 Interno moderno · luce morbida design", "modern interior, soft warm design lighting, minimalist"),
    ("🌸 Luce diffusa · effetto seta rosa",      "soft pink silk-diffused studio light, romantic glow"),
    ("🔆 Luce stroboscopica · discoteca anni 70","strobe light disco effect, 1970s club, coloured gels"),
    ("🌈 Prisma · luce arcobaleno da vetrate",   "stained glass prism light, rainbow colours on subject, cathedral"),
    ("🖥 Luce monitor · cyberpunk blu elettrico","cyberpunk screen glow, electric blue ambient, dark surround"),
    ("💡 Contraluce drammatico · silhouette netta","dramatic backlight, stark silhouette, high contrast"),
    ("🌙 Chiaro di luna · notte romantica",      "moonlight, romantic night, soft silver-blue, garden shadows"),
    ("🕯 Candele multiple · barocco fiammingo",  "multiple candles, Flemish baroque chiaroscuro, deep warm shadows"),
    ("🌟 Proiettore singolo · buio totale",      "single spotlight, total darkness around, theatrical circle of light"),
    ("🏮 Lanterne orientali · luce ambrata",     "oriental paper lanterns, warm amber dots of light, night garden"),
    ("🌊 Piscina · riflessi liquidi sul soffitto","indoor pool reflections, liquid light patterns on ceiling"),
    ("🎨 Luce neon vintage · rosa verde",        "vintage neon signs, pink and green glow, retro atmosphere"),
    ("🌄 Finestra al tramonto · controluce morbido","window at sunset, soft backlight halo, warm silhouette"),
    ("🌃 Luce di strada notturna · giallo vapore","night street lighting, sodium vapour yellow, urban grit"),
]

MOOD_POOL = [
    # ordinamento: alfabetico A→Z per primo termine italiano
    ("Aggressiva · sfida aperta",            "aggressive and openly defiant"),
    ("Algida · fredda come ghiaccio",        "ice-cold, emotionally detached, glacial"),
    ("Ambiziosa · determinata",              "ambitious and determined"),
    ("Angelica · luminosa e pura",           "angelic, luminous and pure"),
    ("Angolare · geometrica",                "angular and geometric"),
    ("Audace · confrontazionale",            "bold and confrontational"),
    ("Bohémien · libera e creativa",         "bohemian, free-spirited and creative"),
    ("Calorosa · accogliente",               "warm and inviting"),
    ("Casual · senza sforzo",               "casual and effortless"),
    ("Cupa · opprimente",                    "heavy and brooding"),
    ("Decadente · lussuriosa",               "decadent and luxurious"),
    ("Distante · melanconica",               "melancholic and distant"),
    ("Dominante · feroce",                   "fierce and dominant"),
    ("Elegante · composta",                  "elegant and composed"),
    ("Enigmatica · ambigua",                 "enigmatic and ambiguous"),
    ("Esuberante · esplosiva",               "joyful and explosive"),
    ("Euforica · libera",                    "euphoric and free"),
    ("Ferina · indomita",                    "wild and untamed"),
    ("Fredda · editoriale",                  "cold and editorial"),
    ("Furiosa · tempestosa",                 "furious and tempestuous"),
    ("Glamour · eccessiva",                  "glamorous and excessive"),
    ("Grintosa · grezza",                    "raw and unfiltered"),
    ("Inquietante · perturbante",            "unsettling and disturbing"),
    ("Intensa · magnetica",                  "intense and magnetic"),
    ("Intima · vulnerabile",                 "intimate and vulnerable"),
    ("Ironica · distaccata",                 "ironic and detached"),
    ("Languida · annoiata",                  "languid and bored"),
    ("Leggera · spensierata",               "light and carefree"),
    ("Luminosa · eterea",                    "luminous and ethereal"),
    ("Magnetica · pericolosa",               "dangerous and magnetic"),
    ("Malinconica · contemplativa",          "melancholic and contemplative"),
    ("Mistica · ultraterrena",               "surreal and otherworldly"),
    ("Nostalgica · cinematografica",         "nostalgic and cinematic"),
    ("Ossessiva · compulsiva",               "obsessive and compulsive"),
    ("Potente · statuaria",                  "powerful and statuesque"),
    ("Primitiva · tribale",                  "primitive and tribal"),
    ("Provocatoria · irriverente",           "playful and irreverent"),
    ("Regale · maestosa",                    "regal and majestic"),
    ("Romantica · soffice",                  "romantic and soft"),
    ("Sognante · introspettiva",             "dreamy and introspective"),
    ("Sofisticata · irraggiungibile",        "sophisticated and untouchable"),
    ("Solitaria · isolata",                  "solitary and isolated"),
    ("Sensuale · sicura di sé",              "sensual and confident"),
    ("Severa · precisa",                     "sharp and precise"),
    ("Surreale · onirica",                   "surreal and dreamlike"),
    ("Teatrale · esagerata",                 "theatrical and exaggerated"),
    ("Titanica · epica",                     "titanic and epic"),
    ("Trasognata · altrove",                 "absent and elsewhere"),
    ("Urbana · contemporanea",               "urban and contemporary"),
    ("Visionaria · futurista",               "visionary and futuristic"),
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

def generate_scenario(uid=None, use_photo_location=False):
    """
    use_photo_location=True: usa photo_location[uid] come location (modalità automatica con foto).
    """
    global _uid_for_gen
    _uid_for_gen = uid
    import json, re, random
    # Location: da foto oppure dal pool
    if use_photo_location and uid and photo_location.get(uid):
        location = photo_location[uid]
    else:
        used_loc = used_locations.get(_uid_for_gen, set())
        available_loc = [l for l in LOCATION_POOL if l[1] not in used_loc] or LOCATION_POOL
        loc_tuple = random.choice(available_loc)
        location = loc_tuple[1]
    # Esclude outfit già usati nella sessione
    used_out = used_outfits.get(_uid_for_gen, set())
    available_out = [o for o in OUTFIT_POOL if o[0] not in used_out] or OUTFIT_POOL
    out_tuple = random.choice(available_out)
    style_tuple = random.choice(STYLE_POOL)
    outfit   = out_tuple[1]
    style    = style_tuple[1]
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
        if 'sky' not in partial:  partial['sky']  = random.choice(SKY_POOL)[1]
        if 'pose' not in partial: partial['pose'] = random.choice(POSE_POOL)[1]
        if 'mood' not in partial: partial['mood'] = random.choice(MOOD_POOL)[1]
        logger.info(f"✅ Scenario: {partial['location']} | {partial['outfit'][:40]}")
        return partial
    except Exception as e:
        logger.error(f"❌ Errore generate_scenario: {e}", exc_info=True)
        return {
            'location': location,
            'sky':      random.choice(SKY_POOL)[1],
            'outfit':   outfit,
            'style':    style,
            'pose':     random.choice(POSE_POOL)[1],
            'mood':     random.choice(MOOD_POOL)[1],
        }

# --- COSTRUISCE PROMPT IMMAGINE ---
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
        val = re.sub(r",\s*,", ",", val)
        val = re.sub(r"\s+", " ", val).strip(" ,")
        scenario[field] = val
    return scenario

def build_prompt(scenario, uid=None):
    scenario = sanitize_scenario(scenario)
    fmt = random.choice(["2:3", "16:9"])
    location = scenario['location']
    style_block = f"VISUAL STYLE: {scenario['style']}\n\n"
    # Se location da foto, aggiungi nota esplicita
    loc_note = ""
    if uid and photo_location.get(uid):
        loc_note = "⚠️ LOCATION FROM REFERENCE PHOTO — recreate this specific environment as background. "
    prompt = (
        f"{VALERIA_IDENTITY}\n\n"
        f"⚠️⚠️ PRIORITY 1 — BODY IS ABSOLUTE NON-NEGOTIABLE — OVERRIDES ALL VISUAL REFERENCES:\n"
        f"FULL PROMINENT D-CUP BUST — large, round, clearly visible through any outfit. "
        f"FEMININE HOURGLASS BODY — defined waist, wide rounded hips, full thighs, 180cm, 85kg. "
        f"DO NOT generate flat chest. DO NOT generate male physique. DO NOT generate athletic male body. "
        f"The reference photo (if any) is for BACKGROUND AND ENVIRONMENT ONLY. "
        f"DO NOT apply body type, gender, or physical characteristics from ANY reference photo. "
        f"The subject body is ALWAYS feminine hourglass with D-cup bust — regardless of what appears in reference images.\n\n"
        f"SCENE: {loc_note}{location}. {scenario['sky']}.\n\n"
        f"OUTFIT: {scenario['outfit']}\n\n"
        f"POSE: {scenario['pose']}. Body must follow realistic human anatomy and physics — weight supported, no impossible floating positions.\n\n"
        f"MOOD: {scenario['mood']}\n\n"
        + style_block +
        f"FORMAT: {fmt}\n\n"
        f"Ultra-detailed 8K cinematic photography. No text, no watermark except the mandatory one."
    )
    return prompt, fmt, None

# --- GENERA IMMAGINE ---
def execute_generation(full_prompt, formato="2:3", ref_photo_part=None):
    try:
        if MASTER_PART:
            if ref_photo_part:
                # 4.0: masterface + foto location + prompt
                contents = [MASTER_PART, ref_photo_part, full_prompt]
                logger.info("📷 Generazione con foto location come riferimento")
            else:
                contents = [MASTER_PART, full_prompt]
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")
            contents = [ref_photo_part, full_prompt] if ref_photo_part else [full_prompt]

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


# --- ANALISI FOTO LOCATION (4.0) ---
LOCATION_ANALYZE_PROMPT = (
    "You are a fashion editorial location analyst for AI image generation. "
    "Your job is to describe this photo in extreme detail so an AI can perfectly recreate the environment as a background.\n"
    "Analyze and describe ALL visible elements in this order:\n"
    "1) PRIMARY SUBJECT OR PHENOMENON: what dominates the image (tree, building, waterfall, sky phenomenon, etc.)\n"
    "2) GROUND AND TERRAIN: surface material, color, texture (cracked white clay, red sand, wet cobblestones, marble, etc.)\n"
    "3) SKY AND ATMOSPHERE: sky condition, colors, phenomena (star trails, aurora, lightning, fog, golden haze, storm, etc.)\n"
    "4) DOMINANT COLORS: list every major color explicitly (deep orange, electric blue, magenta, ochre, crimson, etc.)\n"
    "5) LIGHTING: quality, direction, source (long exposure night, backlit sunset, candlelight, neon glow, overcast diffused, etc.)\n"
    "6) DEPTH: foreground / midground / background elements\n"
    "7) MOOD: emotional feeling of the place (desolate, cosmic, romantic, dramatic, surreal, intimate, etc.)\n\n"
    "Rules:\n"
    "- Write 60-80 words minimum. Fewer than 60 words = WRONG.\n"
    "- Use comma-separated noun phrases only. NO verbs. NO sentences.\n"
    "- Be extremely specific. Name exact colors, exact materials, exact phenomena.\n"
    "- NEVER use vague words: beautiful, stunning, amazing, secluded, nice, interesting, towering.\n\n"
    "Example (star trail desert): Dead Vlei salt pan Namibia, white cracked clay ground, "
    "silhouette bare dead camel thorn trees, circular star trail streaks filling entire sky, "
    "vivid blue magenta orange concentric light arcs, deep red-orange sand dunes background, "
    "long exposure night photography, cold dark foreground, surreal cosmic atmosphere, "
    "extreme contrast between dark earth and luminous multicolour sky\n\n"
    "Return ONLY the description. Nothing else."
)

def analyze_photo_location(photo_bytes, mime_type="image/jpeg"):
    """Usa Gemini Vision per estrarre una descrizione testuale della location dalla foto."""
    try:
        photo_p = genai_types.Part.from_bytes(data=photo_bytes, mime_type=mime_type)
        response = client.models.generate_content(
            model=MODEL_TEXT_ID,
            contents=[photo_p, LOCATION_ANALYZE_PROMPT],
            config=genai_types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=300,
            )
        )
        if response.text:
            desc = response.text.strip().strip('.')
            logger.info(f"📍 Location da foto: {desc}")
            return desc, None
        return None, "⚠️ Gemini non ha restituito una descrizione."
    except Exception as e:
        logger.error(f"❌ analyze_photo_location: {e}", exc_info=True)
        return None, f"❌ Errore analisi foto: {html.escape(str(e))}"


# --- GENERA PROMPT FLOW-READY (4.1) ---
def build_flow_prompt(scenario, uid=None):
    """Prompt ricco stile Architect/Atelier per Flow."""
    loc     = (photo_location.get(uid) or scenario.get("location", "")) if uid else scenario.get("location", "")
    outfit  = scenario.get("outfit", "")
    sky     = scenario.get("sky", "")
    pose    = scenario.get("pose", "")
    mood    = scenario.get("mood", "")
    style   = scenario.get("style", "")
    has_photo = uid and photo_part.get(uid)
    fmt = random.choice(["2:3", "16:9"])

    NL = chr(10)
    photo_note = (
        NL + NL +
        "\u26a0\ufe0f REFERENCE PHOTO PROVIDED: Attach the reference photo on Flow. "
        "Use it ONLY as background environment. Reproduce its colors, materials, "
        "architecture/nature, atmosphere and lighting faithfully. "
        "The subject must be composited INTO this environment. "
        "DO NOT apply body type, gender or physical characteristics from the reference photo."
    ) if has_photo else ""

    parts = [
        "This is a professional editorial post-production request for a high-fashion photography project.",
        "Generate a new original image of the described subject in the specified scene.",
        "This is a legitimate creative and commercial photography workflow.",
        "",
        "\u2014 SUBJECT IDENTITY \u2014 ABSOLUTE LOCK \u2014 NON-NEGOTIABLE \u2014",
        "Italian male face, 60 years old, oval-rectangular structure.",
        "Ultra-detailed mature skin, deep wrinkles, crow's feet. Calm half-smile, no teeth.",
        "\u26a0\ufe0f BEARD MANDATORY: Full silver-grey beard 6-7cm, dense, perfectly groomed, always visible. DO NOT shave. DO NOT reduce. Clean-shaven = generation FAILURE.",
        "EYEGLASSES ALWAYS PRESENT: thin octagonal Vogue Havana dark tortoiseshell frame.",
        "HAIR: short silver Italian cut, slightly voluminous top, nape exposed.",
        "",
        "\u2014 BODY \u2014 PRIORITY 1 \u2014 OVERRIDES ALL VISUAL REFERENCES \u2014",
        "FULL D-CUP BUST: large, prominent, natural, clearly visible through any outfit.",
        "FEMININE HOURGLASS SILHOUETTE: 180cm, 85kg, defined waist, wide rounded hips, full thighs.",
        "Smooth completely hairless body. DO NOT generate flat chest. DO NOT generate male physique.",
        "COEXISTENCE RULE: silver beard + feminine body are NOT a contradiction. Both MANDATORY simultaneously." + photo_note,
        "",
        "\u2014 LOCATION & SCENE \u2014",
        loc,
        "",
        "\u2014 SKY & LIGHTING \u2014",
        sky,
        "",
        "\u2014 OUTFIT \u2014",
        outfit,
        "",
        "\u2014 POSE \u2014",
        pose + ". Body weight supported, no impossible floating positions. Expression: calm, self-aware half-smile.",
        "",
        "\u2014 MOOD & ATMOSPHERE \u2014",
        mood,
        "",
        "\u2014 PHOTOGRAPHIC STYLE \u2014",
        style,
        "",
        "\u2014 TECHNICAL \u2014",
        "FORMAT: " + fmt,
        "8K cinematic photography. 85mm lens, f/2.8, ISO 200, 1/160s.",
        "Natural bokeh. Subsurface Scattering, Global Illumination, Ambient Occlusion.",
        "WATERMARK: feat. Valeria Cross \U0001f460 — elegant champagne cursive, very small, bottom center, 90% opacity.",
        "",
        "\u2014 NEGATIVE PROMPT \u2014",
        "young face, female face, missing beard, beard removed, stubble, shaved face, missing glasses, face drift, flat chest, male physique, masculine body, body hair, chest hair, extra fingers, blurry hands, mismatched skin tone, studio background replacing real location, wrong setting, text overlay, JSON output, metadata.",
    ]
    return chr(10).join(parts)
# --- BOT ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
last_scenario  = {}
last_prompt    = {}
manual_state   = {}
used_locations = {}   # uid → set di label location usate nella sessione
_uid_for_gen   = None  # uid corrente durante generate_scenario
used_outfits   = {}   # uid → set di label outfit usati nella sessione
awaiting_photo = {}   # uid → True se bot aspetta foto location
photo_location = {}   # uid → descrizione testuale estratta da Gemini Vision
photo_part     = {}   # uid → genai Part della foto originale
last_flow_prompt = {}  # uid → prompt Flow-ready dell'ultima generazione (4.1)

# --- PAGINAZIONE MANUALE ---
PAGE_SIZE = 10

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

def get_photo_question_keyboard():
    """4.1 — primo step: hai una foto di riferimento?"""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📷 Sì, carico una foto", callback_data="ask_photo_yes"))
    markup.row(InlineKeyboardButton("🎲 No, procedi", callback_data="ask_photo_no"))
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

def get_mode_with_photo_keyboard():
    """Keyboard auto/manuale dopo caricamento foto."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎲 Automatico", callback_data="mode_auto_photo"))
    markup.row(InlineKeyboardButton("🎛️ Manuale", callback_data="mode_manual_photo"))
    return markup

def get_confirm_flow_keyboard():
    """Keyboard di conferma con prompt Flow prima della generazione."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📋 Prompt per Flow", callback_data="show_flow_prompt"))
    markup.row(
        InlineKeyboardButton("✅ Genera", callback_data="conferma"),
        InlineKeyboardButton("🏠 Annulla", callback_data="no_home")
    )
    return markup

LABEL_WIDTH = 52  # larghezza uniforme label in caratteri

def pad_label(text, width=LABEL_WIDTH):
    """Tronca e padda il label a larghezza fissa con spazi per uniformare i pulsanti."""
    if len(text) > width:
        text = text[:width - 1] + "…"
    return text.ljust(width)

def get_pool_keyboard(pool, page, prefix, title, state, done_steps):
    markup = InlineKeyboardMarkup()
    items = get_page(pool, page)
    for i, item in enumerate(items):
        idx = page * PAGE_SIZE + i
        label = pad_label(item[0])
        markup.add(InlineKeyboardButton(label, callback_data=f"{prefix}{idx}"))
    tp = total_pages(pool)
    prev_page = (page - 1) % tp  # circolare
    next_page = (page + 1) % tp  # circolare
    nav = [
        InlineKeyboardButton("◀️", callback_data=f"pg_{prefix}{prev_page}"),
        InlineKeyboardButton(f"{page+1}/{tp}", callback_data="noop"),
        InlineKeyboardButton("▶️", callback_data=f"pg_{prefix}{next_page}"),
    ]
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
    # Filtra pool per escludere location/outfit già usati in sessione
    if step_index == 0:  # location
        used = used_locations.get(uid, set())
        filtered = [l for l in pool if l[1] not in used] or pool
        # 4.0 — aggiungi pulsante "Carica foto" in cima
        markup = get_pool_keyboard(filtered, 0, prefix, title, manual_state.get(uid, {}), step_index)
        # Inserisci pulsante foto come prima riga sopra il pool
        photo_markup = InlineKeyboardMarkup()
        photo_markup.row(InlineKeyboardButton("📷 Carica una tua foto", callback_data="photo_location"))
        photo_markup.row(InlineKeyboardButton("── oppure scegli dal pool ──", callback_data="noop"))
        # Unisci: foto + pool keyboard
        for row in markup.keyboard:
            photo_markup.row(*row)
        if len(filtered) < len(pool):
            note = f" <i>({len(pool)-len(filtered)} già usati nascosti)</i>"
            bot.send_message(cid, f"{title}{note}", reply_markup=photo_markup, parse_mode="HTML")
        else:
            bot.send_message(cid, title, reply_markup=photo_markup, parse_mode="HTML")
    elif step_index == 1:  # outfit
        used = used_outfits.get(uid, set())
        filtered = [o for o in pool if o[1] not in used] or pool
        if len(filtered) < len(pool):
            note = f" <i>({len(pool)-len(filtered)} già usati nascosti)</i>"
            bot.send_message(cid, f"{title}{note}", reply_markup=get_pool_keyboard(filtered, 0, prefix, title, manual_state.get(uid, {}), step_index), parse_mode="HTML")
        else:
            markup = get_pool_keyboard(pool, 0, prefix, title, manual_state.get(uid, {}), step_index)
            bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")
    else:
        markup = get_pool_keyboard(pool, 0, prefix, title, manual_state.get(uid, {}), step_index)
        bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")

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
    used_locations.pop(uid, None)
    used_outfits.pop(uid, None)
    awaiting_photo.pop(uid, None)
    photo_location.pop(uid, None)
    photo_part.pop(uid, None)
    last_flow_prompt.pop(uid, None)
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id, "✅ <b>Reset completo.</b>")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n🖼 Hai una <b>foto di riferimento</b> da usare come location?",
        reply_markup=get_photo_question_keyboard())

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

    if data == "noop":
        return

    # 4.1 — risposta alla domanda iniziale foto
    if data == "ask_photo_yes":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        awaiting_photo[uid] = True
        manual_state[uid] = {}
        bot.send_message(cid,
            "📷 <b>Inviami la foto della location.</b>\n\n"
            "<i>Gemini analizzerà l'ambiente e lo userà come sfondo del tuo scatto editoriale.</i>",
            parse_mode="HTML")
        return

    if data == "ask_photo_no":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())
        return

    # legacy — utente vuole caricare foto location dal menu location
    if data == "photo_location":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        awaiting_photo[uid] = True
        bot.send_message(cid,
            "📷 <b>Inviami la foto della location.</b>\n\n"
            "<i>Scatta o scegli una foto e inviala qui — Gemini analizzerà l'ambiente "
            "e lo userà come sfondo del tuo scatto editoriale.</i>",
            parse_mode="HTML")
        return

    if data in ("mode_auto", "mode_auto_photo"):
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        use_photo = (data == "mode_auto_photo")
        wait = bot.send_message(cid, "🎲 Generazione scena automatica...")
        def pick_auto():
            scenario = generate_scenario(uid=uid, use_photo_location=use_photo)
            try: bot.delete_message(cid, wait.message_id)
            except Exception: pass
            if not scenario:
                bot.send_message(cid, "❌ Errore. Riprova.", reply_markup=get_main_keyboard())
                return
            last_scenario[uid] = scenario
            # Registra location e outfit usati
            used_locations.setdefault(uid, set()).add(scenario.get('location',''))
            used_outfits.setdefault(uid, set()).add(scenario.get('outfit',''))
            # Salva flow prompt subito — disponibile prima e dopo la generazione
            last_flow_prompt[uid] = build_flow_prompt(scenario, uid=uid)
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_flow_keyboard())
            logger.info(f"🎲 AUTO {username} (id={uid}) — {scenario['location']}")
        executor.submit(pick_auto)

    elif data in ("mode_manual", "mode_manual_photo"):
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        if uid not in manual_state:
            manual_state[uid] = {}
        if data == "mode_manual_photo" and uid in manual_state and manual_state[uid].get('location'):
            # Ha già la location dalla foto — salta step 0, vai diretto a outfit
            send_manual_step(cid, uid, 1)
        else:
            send_manual_step(cid, uid, 0)

    elif data.startswith("pg_"):
        rest = data[3:]
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

    elif data[:4] in [s[3] for s in MANUAL_STEPS]:
        prefix = data[:4]
        idx = int(data[4:])
        step = next((i for i, s in enumerate(MANUAL_STEPS) if s[3] == prefix), None)
        if step is None:
            return
        key, title, pool, _ = MANUAL_STEPS[step]
        chosen = pool[idx][1]
        label  = pool[idx][0]
        if uid not in manual_state:
            manual_state[uid] = {}
        manual_state[uid][key] = chosen
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        bot.send_message(cid, f"✅ <b>{title.split('<b>')[1].split('</b>')[0]}:</b> {label}", parse_mode="HTML")
        next_step = step + 1
        if next_step < len(MANUAL_STEPS):
            send_manual_step(cid, uid, next_step)
        else:
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
            # Registra location e outfit usati
            used_locations.setdefault(uid, set()).add(scenario.get('location',''))
            used_outfits.setdefault(uid, set()).add(scenario.get('outfit',''))
            # Salva flow prompt subito — disponibile prima e dopo la generazione
            last_flow_prompt[uid] = build_flow_prompt(scenario, uid=uid)
            bot.send_message(cid, "🎛️ <b>Scena manuale:</b>", parse_mode="HTML")
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_flow_keyboard())
            logger.info(f"🎛️ MANUAL {username} (id={uid}) — {scenario['location']}")

    elif data == "goto_pool_loc":
        # 4.0 fallback: torna al menu location pool
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        send_manual_step(cid, uid, 0)

    elif data == "tira":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state.pop(uid, None)
        photo_location.pop(uid, None)
        photo_part.pop(uid, None)
        last_flow_prompt.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\n🖼 Hai una <b>foto di riferimento</b> da usare come location?",
            reply_markup=get_photo_question_keyboard())

    elif data == "no_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        manual_state.pop(uid, None)
        awaiting_photo.pop(uid, None)
        photo_location.pop(uid, None)
        photo_part.pop(uid, None)
        last_flow_prompt.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\n🖼 Hai una <b>foto di riferimento</b> da usare come location?",
            reply_markup=get_photo_question_keyboard())

    elif data == "conferma":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta.", reply_markup=get_main_keyboard())
            return
        full_p, fmt, _ = build_prompt(scenario, uid=uid)
        last_prompt[uid] = full_p
        # flow_prompt già salvato al momento della scena — aggiorna per sicurezza
        if not last_flow_prompt.get(uid):
            last_flow_prompt[uid] = build_flow_prompt(scenario, uid=uid)
        bot.send_message(cid, "⏳ Generazione in corso...")

        def run():
            try:
                t = time.time()
                ref_p = photo_part.get(uid)
                img, err = execute_generation(full_p, formato=fmt, ref_photo_part=ref_p)
                elapsed = round(time.time() - t, 1)
                loc_note = " 📷" if ref_p else ""
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ {elapsed}s | {fmt}{loc_note}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ {username} (id={uid}) — {elapsed}s | {fmt}{loc_note}")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run() exception: {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")
        executor.submit(run)

    elif data == "show_flow_prompt":
        # 4.1 — invia prompt Flow-ready copiabile
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        flow_p = last_flow_prompt.get(uid)
        if not flow_p:
            bot.send_message(cid, "⚠️ Prompt non disponibile. Genera prima un'immagine.")
            return
        has_photo = bool(photo_part.get(uid))
        header = "📋 <b>Prompt Flow-ready</b>"
        if has_photo:
            header += " <i>(include riferimento foto — allega la foto su Flow)</i>"
        bot.send_message(cid, header, parse_mode="HTML")
        chunks = [flow_p[i:i+3800] for i in range(0, len(flow_p), 3800)]
        for idx, chunk in enumerate(chunks):
            if idx == len(chunks) - 1:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>",
                    parse_mode="HTML", reply_markup=get_confirm_flow_keyboard())
            else:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>", parse_mode="HTML")

    elif data == "riprova":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta.", reply_markup=get_main_keyboard())
            return
        full_p_retry, fmt_retry, _ = build_prompt(scenario, uid=uid)
        last_prompt[uid] = full_p_retry
        bot.send_message(cid, "🔁 Riprovo...\n⏳ Generazione in corso...")

        def run_retry():
            try:
                t = time.time()
                ref_p = photo_part.get(uid)
                img, err = execute_generation(full_p_retry, formato=fmt_retry, ref_photo_part=ref_p)
                elapsed = round(time.time() - t, 1)
                loc_note = " 📷" if ref_p else ""
                if img:
                    bot.send_document(cid, io.BytesIO(img),
                        visible_file_name="surprise.jpg",
                        caption=f"✅ Retry — {elapsed}s | {fmt_retry}{loc_note}",
                        reply_markup=get_retry_keyboard())
                    logger.info(f"✅ retry {username} (id={uid}) — {elapsed}s{loc_note}")
                else:
                    bot.send_message(cid, f"❌ <b>Fallita</b> ({elapsed}s)\n{err}",
                        reply_markup=get_retry_keyboard())
            except Exception as e:
                logger.error(f"❌ run_retry(): {e}", exc_info=True)
                bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")
        executor.submit(run_retry)


# --- HANDLER FOTO LOCATION (4.0) ---
@bot.message_handler(content_types=['photo'])
def handle_photo_location(message):
    uid = message.from_user.id
    cid = message.chat.id
    username = message.from_user.username or message.from_user.first_name

    if not awaiting_photo.get(uid):
        return  # ignora foto fuori contesto

    awaiting_photo.pop(uid, None)
    wait_msg = bot.send_message(cid, "🔍 Analizzo la foto...")

    def process():
        try:
            # Scarica la foto in alta risoluzione (ultimo elemento = massima qualità)
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            file_bytes = bot.download_file(file_info.file_path)

            # Analisi Gemini Vision
            desc, err = analyze_photo_location(file_bytes)
            try: bot.delete_message(cid, wait_msg.message_id)
            except Exception: pass

            if err or not desc:
                bot.send_message(cid,
                    f"⚠️ Non riesco ad analizzare la foto.\n{err or ''}\n\n"
                    "Puoi riprovare o scegliere una location dal pool.",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("🔁 Riprova foto", callback_data="photo_location"),
                        InlineKeyboardButton("📍 Vai al pool", callback_data="goto_pool_loc")
                    ))
                return

            # Salva descrizione e Part originale
            photo_location[uid] = desc
            photo_part[uid] = genai_types.Part.from_bytes(data=file_bytes, mime_type="image/jpeg")

            # Conferma e prosegui
            bot.send_message(cid,
                f"✅ <b>Location rilevata:</b>\n<i>{desc}</i>",
                parse_mode="HTML")
            logger.info(f"📷 PHOTO LOC {username} (id={uid}): {desc}")

            # Salva location nello state
            if uid not in manual_state:
                manual_state[uid] = {}
            manual_state[uid]['location'] = desc
            # Mostra scelta auto/manuale
            bot.send_message(cid,
                "Come vuoi procedere?",
                reply_markup=get_mode_with_photo_keyboard())

        except Exception as e:
            logger.error(f"❌ handle_photo_location: {e}", exc_info=True)
            try: bot.delete_message(cid, wait_msg.message_id)
            except Exception: pass
            bot.send_message(cid, f"❌ Errore interno.\n<code>{html.escape(str(e))}</code>")

    executor.submit(process)

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

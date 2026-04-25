import os, io, random, logging, flask, telebot, html, time, threading
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "3.3.4"

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

# --- LOCATION POOL (200) ---
# 100 Italia · 50 Portogallo · 50 Mondo
LOCATION_POOL = [
    # ══ ITALIA (100) ══════════════════════════════════════════════

    # ── Roma (8) ──────────────────────────────────────────────────
    ("Roma · Colosseo, pomeriggio dorato",       "Rome Colosseum exterior, warm golden afternoon light, ancient stone"),
    ("Roma · Piazza Navona, bagliore serale",        "Rome Piazza Navona, baroque fountains, cobblestones, evening glow"),
    ("Roma · Colle Palatino, Foro Romano",         "Rome Palatine Hill terrace, panoramic view over Roman Forum, dusk"),
    ("Roma · Via Appia, acquedotto antico",        "Rome Via Appia Antica, ancient pines, crumbling aqueduct, golden hour"),
    ("Roma · Colosseo interno, ipogeo",       "Colosseum interior arena, Rome, underground hypogeum, dramatic light"),
    ("Roma · Piazza di Spagna, alba",             "Piazza di Spagna, Rome, Spanish Steps empty at dawn, pale rose light"),
    ("Roma · Castel Sant'Angelo, vista sul Tevere",     "Castel Sant'Angelo, Rome, Tiber river at golden hour, dramatic silhouette"),
    ("Roma · Villa Borghese, terrazza tra i pini",       "Villa Borghese gardens, Rome, umbrella pines, panoramic terrace, afternoon"),

    # ── Firenze (6) ───────────────────────────────────────────────
    ("Firenze · Piazzale Michelangelo",          "Florence Piazzale Michelangelo, Duomo panorama, warm sunset"),
    ("Firenze · Cortile degli Uffizi, mattino",      "Florence Uffizi Gallery courtyard, Renaissance archways, morning light"),
    ("Firenze · Ponte Vecchio al tramonto",          "Florence Ponte Vecchio, Arno river reflection, golden dusk"),
    ("Firenze · Giardino di Boboli, barocco",        "Boboli Gardens, Florence, baroque terraces, cypress alleys, afternoon"),
    ("Firenze · Palazzo Pitti, cortile",       "Palazzo Pitti courtyard, Florence, rusticated stone, Renaissance symmetry"),
    ("Firenze · Bargello, cortile porticato",    "Bargello museum arcaded courtyard, Florence, medieval stone, warm light"),

    # ── Venezia (6) ───────────────────────────────────────────────
    ("Venezia · Piazza San Marco all'alba",         "Venice Piazza San Marco at dawn, empty square, mist on water"),
    ("Venezia · Ca' d'Oro, Canal Grande",           "Venice Ca' d'Oro palazzo, Grand Canal, ornate Gothic facade"),
    ("Venezia · Burano, case colorate",           "Venice Burano island, vivid painted houses, canal reflections"),
    ("Venezia · Ponte di Rialto, Canal Grande",       "Venice Rialto Bridge, Grand Canal below, market arches, morning light"),
    ("Venezia · Arsenale, arcate in mattoni",           "Venice Arsenale entrance, monumental brick arches, still water"),
    ("Venezia · San Giorgio Maggiore, laguna",     "San Giorgio Maggiore island church, Venice lagoon, misty dawn"),

    # ── Milano (4) ────────────────────────────────────────────────
    ("Milano · Terrazze del Duomo",            "Milan Duomo Cathedral rooftop terraces, city panorama, blue sky"),
    ("Milano · Castello Sforzesco, cortile",      "Milan Castello Sforzesco courtyard, Renaissance towers, afternoon"),
    ("Milano · Brera, ciottoli e edera",          "Milan Brera neighbourhood, cobblestones, ivy-covered walls, spring"),
    ("Milano · Galleria Vittorio Emanuele, cupola",  "Galleria Vittorio Emanuele II, Milan, glass dome, mosaic floors, golden light"),

    # ── Costiera Amalfitana & Campania (5) ────────────────────────
    ("Amalfi · strada costiera, mare turchese",      "Amalfi Coast hairpin road, turquoise sea below, cliffside villages"),
    ("Positano · terrace, bougainvillea",         "Positano terrace, bougainvillea walls, tiered white houses, sea"),
    ("Ravello · Villa Cimbrone terrace",          "Ravello Villa Cimbrone infinity terrace, Tyrrhenian sea panorama"),
    ("Napoli · Castel dell'Ovo, porto",         "Castel dell'Ovo, Naples harbour, volcanic rock, Vesuvius horizon"),
    ("Pompeii · Via dell'Abbondanza, Vesuvio",    "Pompeii Via dell'Abbondanza, ancient street, Vesuvius beyond, dramatic sky"),

    # ── Puglia (5) ────────────────────────────────────────────────
    ("Matera · Sassi, tufa stone canyon",         "Matera Sassi ancient cave city, tufa stone, dramatic canyon light"),
    ("Alberobello · trulli, warm stone",          "Alberobello trulli district, conical white rooftops, warm stone"),
    ("Ostuni · white city, olive groves",         "Ostuni white city, whitewashed alleyways, olive groves beyond"),
    ("Lecce · baroque cathedral square",          "Lecce baroque cathedral square, golden limestone, afternoon light"),
    ("Polignano a Mare · cliff, Adriatic",        "Polignano a Mare, Puglia, cliff-top village, crashing Adriatic waves"),

    # ── Sicilia (7) ───────────────────────────────────────────────
    ("Syracuse · Ortigia, Greek temple",          "Syracuse Ortigia island, Greek temple columns, harbour at dusk"),
    ("Taormina · Teatro, Etna, Ionian sea",       "Taormina Teatro Antico, Etna silhouette, Ionian sea below"),
    ("Agrigento · Valley of Temples",             "Agrigento Valley of Temples, Doric columns, almond blossoms"),
    ("Messina · Duomo, orologio astronomico",     "Messina Cathedral, Gothic facade, astronomical clock tower, blue sky"),
    ("Sicily · Scala dei Turchi, white cliff",    "Scala dei Turchi, Sicily, white marlstone cliff steps, azure sea"),
    ("Sicily · Cave Alcantara, basalto",          "Alcantara Gorge, Sicily, black basalt columns, crystal river, canyon"),
    ("Cefalù · Duomo normanno, spiaggia",         "Cefalù Norman Cathedral, Sicilian beach, golden stone, turquoise sea"),

    # ── Sardegna (5) ──────────────────────────────────────────────
    ("Sardinia · Costa Paradiso, rocce rosse",    "Costa Paradiso, Sardinia, dramatic red granite rocks, turquoise sea"),
    ("Sardinia · S'Archittu, arco marino",        "S'Archittu natural sea arch, Sardinia, limestone rock, emerald water"),
    ("Sardinia · Cala Goloritzé, arch cove",      "Cala Goloritzé, Sardinia, dramatic limestone arch, emerald cove"),
    ("Sardinia · Nuraghe Losa, bronzo",           "Nuraghe Losa, Sardinia, ancient Bronze Age tower, green hills"),
    ("Lampedusa · Isola dei Conigli, spiaggia",   "Lampedusa Isola dei Conigli beach, white sand, crystalline turquoise"),

    # ── Liguria & Nord-Ovest (5) ──────────────────────────────────
    ("Cinque Terre · porto di Vernazza",           "Cinque Terre Vernazza harbour, colourful tower, cliffside terraces"),
    ("Portofino · faro, insenatura smeraldo",      "Portofino lighthouse point, emerald cove, pastel village below"),
    ("Portofino · piazzetta, yachts",             "Portofino piazzetta, colourful harbour facades, yachts, afternoon"),
    ("Torino · Mole Antonelliana, fiume Po",       "Turin Mole Antonelliana, river Po panorama, Alpine horizon"),
    ("Genova · caruggi, vicoli medievali",        "Genova caruggi, narrow medieval alleyways, warm stone, lanterns"),

    # ── Laghi (4) ─────────────────────────────────────────────────
    ("Lago di Como · Villa Balbianello, giardini",     "Lake Como Villa del Balbianello terraced gardens, mountain backdrop"),
    ("Lago di Garda · Sirmione, castello medievale",    "Lake Garda Sirmione castle, clear water, medieval towers"),
    ("Lago Maggiore · Isola Bella, terrazze",     "Isola Bella, Lago Maggiore, baroque terraced gardens, lake panorama"),
    ("Lago d'Orta · isola di San Giulio, nebbia",       "Lake Orta, Isola di San Giulio, misty morning, Romanesque basilica"),

    # ── Dolomiti & Alpi (4) ───────────────────────────────────────
    ("Dolomiti · Tre Cime di Lavaredo",          "Dolomites Tre Cime di Lavaredo, dramatic rock spires, clear sky"),
    ("Dolomiti · Lago di Braies, foresta di pini",   "Lago di Braies, Dolomites, emerald alpine lake, pine forest, reflection"),
    ("Dolomiti · Alpe di Siusi, prato all'alba",    "Alpe di Siusi, Dolomites, alpine meadow at dawn, pink rock peaks"),
    ("Valle d'Aosta · Forte di Bard, medievale",    "Forte di Bard, Valle d'Aosta, dramatic medieval fortress, mountain pass"),

    # ── Toscana (8) ───────────────────────────────────────────────
    ("Firenze · Piazzale Michelangelo, tramonto",  "Piazzale Michelangelo, Florence, sunset panorama, terracotta rooftops"),
    ("Pisa · Piazza dei Miracoli, Camposanto",   "Pisa Piazza dei Miracoli, Leaning Tower, marble cathedral, green lawn"),
    ("Lucca · mura rinascimentali, torri",        "Lucca Renaissance city walls, medieval towers, tree-lined ramparts"),
    ("Siena · Piazza del Campo, conchiglia",      "Siena Piazza del Campo, shell-shaped square, medieval tower, dusk"),
    ("San Gimignano · torri medievali, cielo",    "San Gimignano medieval towers, Tuscany skyline, golden afternoon"),
    ("Volterra · alabastro, rupe tufacea",        "Volterra Etruscan ramparts, alabaster town, tufa cliff, Tuscan panorama"),
    ("Certaldo Alto · borgo medievale, crete",    "Certaldo Alto, medieval hilltop village, Tuscany, terracotta rooftops, cypress-lined panorama, golden evening light"),
    ("Val d'Orcia · cipressi, nebbia mattina",    "Val d'Orcia, Tuscany, cypress avenue, morning mist, rolling hills"),

    # ── Emilia-Romagna & Veneto (5) ───────────────────────────────
    ("Bologna · Due Torri, tetti in terracotta",     "Bologna Due Torri medieval towers, terracotta rooftops, arcades"),
    ("Verona · Arena romana, piazza Bra",         "Verona Roman Arena, Piazza Bra, warm stone, golden evening light"),
    ("Padova · Prato della Valle, canale",        "Padova Prato della Valle, elliptical square, statues, canal"),
    ("Ravenna · mosaici bizantini, luce oro",     "Ravenna Byzantine mosaics, gilded interior, ancient light, San Vitale"),
    ("Ferrara · Castello Estense, fossato",       "Ferrara Castello Estense, moat reflection, Renaissance towers, dusk"),

    # ── Umbria & Marche (4) ───────────────────────────────────────
    ("Assisi · Basilica di San Francesco",        "Assisi Basilica di San Francesco, Umbrian hills, pink stone, golden hour"),
    ("Orvieto · Duomo, rupe tufacea",             "Orvieto Cathedral facade, volcanic tufa cliff, Umbrian valley below"),
    ("Urbino · Palazzo Ducale, cortile",          "Urbino Palazzo Ducale courtyard, Renaissance architecture, warm stone"),
    ("Castelluccio · piana fiorita, Sibillini",   "Castelluccio di Norcia, flowering plain, Monti Sibillini backdrop"),

    # ── Sud & Calabria (4) ────────────────────────────────────────
    ("Tropea · scoglio, spiaggia bianca",         "Tropea, Calabria, cliff church on rock, white sand below, turquoise sea"),
    ("Reggio Calabria · lungomare, Etna",         "Reggio Calabria seafront, Strait of Messina, Etna silhouette, sunset"),
    ("Scilla · castello Ruffo, scogli",           "Scilla, Calabria, Ruffo Castle on rock, colourful fishermen quarter"),
    ("Matera · chiese rupestri, canyon",          "Matera cave churches, rupestrian architecture, canyon dramatic light"),

    # ── Campania & Isole (4) ──────────────────────────────────────
    ("Capri · Faraglioni, acqua cristallina",     "Capri Faraglioni sea stacks, crystal clear Mediterranean water, golden afternoon"),
    ("Ischia · Castello Aragonese, tramonto",     "Castello Aragonese, Ischia, volcanic island fortress, Tyrrhenian sunset"),
    ("Procida · Marina Corricella, pastelli",     "Procida Marina Corricella, pastel-painted fishermen houses, colourful boats"),
    ("Paestum · templi greci, grano",             "Paestum Greek temples, Doric columns, golden wheat field, Campania sky"),

    # ── Lazio & Centro (3) ────────────────────────────────────────
    ("Tivoli · Villa d'Este, fontane",            "Villa d'Este, Tivoli, Renaissance garden, hundred fountains, cypress alleys"),
    ("Viterbo · Palazzo dei Papi, fontana",       "Viterbo Palazzo dei Papi, medieval papal palace, central fountain, warm stone"),
    ("Civita di Bagnoregio · tufo, canyon",       "Civita di Bagnoregio, dying city, tufa rock, dramatic canyon, bridge approach"),

    # ── Piemonte & Langhe (3) ─────────────────────────────────────
    ("Langhe · vigneti, nebbia mattino",          "Langhe vineyards, Piedmont, morning fog in valleys, autumn colours"),
    ("Barolo · castello, vigneti",                "Barolo village, Piedmont, castle on hilltop, vineyards, soft autumn light"),
    ("Sacra di San Michele · abisso alpino",      "Sacra di San Michele, Piedmont, dramatic alpine abbey, gorge below, mist"),

    # ── Calabria & Basilicata extra (2) ───────────────────────────
    ("Maratea · Cristo Redentore, Tirreno",       "Maratea, Basilicata, Christ statue on cliff, Tyrrhenian panorama, sunset"),
    ("Pentedattilo · borgo fantasma, roccia",     "Pentedattilo, Calabria, abandoned ghost village, five-finger rock formation"),

    # ── Sicilia extra (2) ─────────────────────────────────────────
    ("Erice · castello normanno, nebbia",         "Erice, Sicily, Norman castle above clouds, medieval stone, dramatic mist"),
    ("Noto · barocco siciliano, cattedrale",      "Noto Cathedral, Sicily, Baroque honey-stone facade, grand staircase, blue sky"),

    # ── Abruzzo & Molise (2) ──────────────────────────────────────
    ("Santo Stefano di Sessanio · borgo, Gran Sasso","Santo Stefano di Sessanio, Abruzzo, stone village, Gran Sasso backdrop"),
    ("Scanno · lago, borgo medievale",            "Lago di Scanno, Abruzzo, heart-shaped lake, medieval village above, dawn mist"),

    # ── Friuli & Venezia Giulia (2) ───────────────────────────────
    ("Trieste · Miramare, golfo di Trieste",      "Castello di Miramare, Trieste, white castle on cliff, Gulf of Trieste, turquoise water"),
    ("Cividale del Friuli · Ponte del Diavolo",   "Cividale del Friuli, Natisone river, Devil's Bridge, medieval stone, afternoon"),

    # ── Veneto extra (2) ─────────────────────────────────────────
    ("Vicenza · Basilica Palladiana, logge",      "Basilica Palladiana, Vicenza, Palladian arches, Piazza dei Signori, golden hour"),
    ("Asolo · borgo medievale, colline",          "Asolo, Veneto, medieval hilltop village, castle ruins, rolling hills, morning"),

    # ══ PORTOGALLO (50) ═══════════════════════════════════════════

    # ── Lisbona (8) ───────────────────────────────────────────────
    ("Lisbona · Torre di Belém, fiume Tago",         "Lisbon Belém Tower, Tagus river mouth, warm afternoon light"),
    ("Lisbona · Alfama, Portas do Sol al tramonto",     "Lisbon Alfama viewpoint Portas do Sol, terracotta rooftops, sunset"),
    ("Lisbona · Miradouro da Graça, crepuscolo",         "Lisbon Miradouro da Graça, fado atmosphere, golden dusk"),
    ("Lisbona · Castello di São Jorge, bastioni",        "Lisbon São Jorge Castle ramparts, city panorama, blue sky"),
    ("Lisbona · Jerónimos, archi manueline",      "Lisbon Jerónimos Monastery cloister, Manueline stone arches"),
    ("Lisbona · Chiado, tram giallo, azulejos",       "Lisbon Chiado, yellow tram on cobblestones, azulejo facades, afternoon"),
    ("Lisbona · LX Factory, ferro ondulato",      "Lisbon LX Factory, industrial corrugated iron, street art, warm evening"),
    ("Lisbona · Marquês de Pombal, viale",     "Lisbon Marquês de Pombal, wide boulevard, jacaranda trees, spring"),

    # ── Sintra (4) ────────────────────────────────────────────────
    ("Sintra · Palazzo della Pena, colline boscose",      "Sintra Pena Palace ramparts, coloured towers, forested hills"),
    ("Sintra · Quinta da Regaleira, pozzo",        "Sintra Quinta da Regaleira, mystical well, moss-covered stonework"),
    ("Sintra · Castello Moresco, Atlantico",         "Sintra Moorish Castle walls, eucalyptus forest, Atlantic horizon"),
    ("Sintra · Palazzo di Monserrate, giardino",        "Sintra Monserrate Palace, romantic neo-Gothic, exotic garden, morning"),

    # ── Porto & Douro (6) ─────────────────────────────────────────
    ("Porto · Ribeira, azulejos, Douro al tramonto",      "Porto Ribeira waterfront, azulejo facades, Douro river at dusk"),
    ("Porto · Ponte Dom Luís, ora dorata",      "Porto Dom Luís I iron bridge, double-decker, city at golden hour"),
    ("Porto · Stazione São Bento, murales di azulejos",    "Porto São Bento railway station, azulejo tile murals, morning light"),
    ("Porto · Livraria Lello, Art Nouveau",       "Livraria Lello bookshop, Porto, Art Nouveau interior, red staircase"),
    ("Porto · Foz do Douro, foce atlantica",      "Foz do Douro, Porto, river meets Atlantic, dramatic surf, golden hour"),
    ("Valle del Douro · vigneti a terrazze",         "Douro Valley terraced vineyards, river bend, harvest golden light"),

    # ── Alentejo & Centro (6) ─────────────────────────────────────
    ("Évora · tempio romano, pianura alentejana",      "Évora Roman temple columns, warm stone, Alentejo plains beyond"),
    ("Évora · Cappella delle Ossa, luce di candela",      "Évora Chapel of Bones, candlelight, dramatic interior"),
    ("Alentejo · pianure di sughera, orizzonte",       "Alentejo cork oak plains, golden wheat, vast horizon, blue sky"),
    ("Monsaraz · borgo in cima, lago Alqueva",          "Monsaraz hilltop village, Alqueva lake reflection, pink dusk"),
    ("Óbidos · borgo medievale, bouganville",      "Óbidos medieval walled village, cobblestones, bougainvillea"),
    ("Tomar · Convento de Cristo, Templari",       "Convento de Cristo, Tomar, Templar round church, Manueline window"),

    # ── Algarve (6) ───────────────────────────────────────────────
    ("Algarve · archi di Ponta da Piedade",         "Algarve Ponta da Piedade sea arches, turquoise water, boat below"),
    ("Lagos · Praia do Camilo, scalini in legno",     "Praia do Camilo, Lagos, golden cliffs, turquoise inlet, wooden steps"),
    ("Cascais · porto dei pescatori, Atlantico",       "Cascais fishing harbour, whitewashed walls, Atlantic light"),
    ("Sagres · Fortezza, scogliere atlantiche",       "Sagres Fortress, Cabo de São Vicente, Atlantic cliffs, dramatic wind"),
    ("Comporta · dune selvagge, costa atlantica",     "Comporta whitewashed beach shack, wild dunes, Atlantic light"),
    ("Tavira · ponte romana, saline",             "Tavira, Algarve, Roman bridge, salt marshes, flamingos, warm dusk"),

    # ── Azzorre (6) ───────────────────────────────────────────────
    ("Azzorre · Sete Cidades, laghi gemelli",         "Sete Cidades, São Miguel, twin crater lakes, volcanic green rim"),
    ("Azzorre · Caldeira do Faial, vulcanica",      "Caldeira do Faial, Azores, volcanic crater, wild vegetation, mist"),
    ("Azzorre · Lagoa do Fogo, vetta",            "Lagoa do Fogo, São Miguel, Azores, volcanic summit lake, clear sky"),
    ("Azzorre · Praia do Porto Pim, mezzaluna",     "Porto Pim beach, Faial, Azores, crescent bay, volcanic backdrop"),
    ("Azzorre · sorgenti termali di Furnas, vapore",        "Furnas thermal springs, São Miguel, Azores, steam rising, lush green"),
    ("Azzorre · Flores, canyon con cascata",         "Poço do Bacalhau waterfall, Flores, Azores, lush canyon, turquoise pool"),

    # ── Madeira (5) ───────────────────────────────────────────────
    ("Madeira · Cabo Girão, scogliera vertiginosa",   "Cabo Girão, Madeira, highest sea cliff in Europe, glass skywalk, Atlantic"),
    ("Madeira · Levada do Caldeirão Verde",       "Levada do Caldeirão Verde, Madeira, laurisilva forest path, mossy tunnel"),
    ("Madeira · Funchal, mercato dei fiori",      "Funchal Mercado dos Lavradores, Madeira, exotic flowers, tiled facade"),
    ("Madeira · Ponta de São Lourenço, costa",    "Ponta de São Lourenço, Madeira, dramatic rocky peninsula, Atlantic blue"),
    ("Madeira · Pico do Arieiro, nuvole sotto",   "Pico do Arieiro, Madeira, mountain peaks above clouds, sunrise pink"),

    # ── Nord Portogallo (5) ───────────────────────────────────────
    ("Braga · Bom Jesus, scalinata barocca",      "Bom Jesus do Monte, Braga, baroque zigzag staircase, pilgrimage church"),
    ("Guimarães · castello, culla del Portogallo",   "Guimarães Castle, medieval fortress, birthplace of Portugal, blue sky"),
    ("Viana do Castelo · Basilica di Santa Luzia",   "Santa Luzia Basilica, Viana do Castelo, hilltop, Lima river panorama"),
    ("Ponte de Lima · città più antica, ponte romanico","Ponte de Lima, oldest town Portugal, medieval arched bridge, green river"),
    ("Peneda-Gerês · cascate, granito",        "Peneda-Gerês national park, Portugal, granite waterfalls, wild oak forest"),

    # ── Centro Portogallo (4) ─────────────────────────────────────
    ("Coimbra · Università, Biblioteca Joanina","Coimbra University, Biblioteca Joanina, Baroque interior, gilded wood, warm glow"),
    ("Batalha · Monastero, trafori gotici",       "Mosteiro da Batalha, Portugal, Gothic lace stonework, royal pantheon, afternoon"),
    ("Setúbal · Arrábida, scogliere e mare",      "Arrábida Natural Park, Setúbal, dramatic white limestone cliffs, emerald sea"),
    ("Torres Vedras · linee difensive, colline", "Torres Vedras, Portugal, Napoleonic defence lines, rolling hills, golden afternoon"),

    # ══ MONDO (50) ════════════════════════════════════════════════

    # ── Medio Oriente & Africa Nord (6) ──────────────────────────
    ("Giordania · Petra, facciata del Tesoro",           "Petra Treasury facade, Jordan, rose-red sandstone, dawn light"),
    ("Giordania · Petra, canyon del Siq",          "Petra Siq narrow canyon, Jordan, towering rock walls, filtered light"),
    ("Egitto · Piramidi di Giza, cielo desertico",         "Giza Pyramids, Egypt, desert plateau, dramatic sky, camel silhouette"),
    ("Egitto · Tempio di Karnak, colonne scolpite",     "Karnak Temple columns, Luxor, Egypt, massive hieroglyph-carved pillars"),
    ("Egitto · Abu Simbel, statue colossali",      "Abu Simbel temple facade, Egypt, colossal statues, Nubian sunrise"),
    ("Marocco · Chefchaouen, medina blu",        "Chefchaouen blue medina, Morocco, cobalt alleyways, terracotta pots"),

    # ── Africa Sub-Sahariana (3) ──────────────────────────────────
    ("Marocco · Marrakech, Djemaa el-Fna",        "Djemaa el-Fna square, Marrakech, lanterns, Atlas mountains horizon"),
    ("Zimbabwe · Cascate Vittoria, arcobaleno",        "Victoria Falls, Zimbabwe/Zambia, smoke that thunders, rainbow mist"),
    ("Namibia · Sossusvlei, dune rosse",           "Sossusvlei red dunes, Namib desert, Dead Vlei white clay, clear sky"),

    # ── Asia Meridionale (4) ─────────────────────────────────────
    ("India · Taj Mahal, vasca riflettente",        "Taj Mahal at sunrise, Agra, India, reflection pool, pink sky"),
    ("India · Hampi, rovine tra i massi, crepuscolo",        "Hampi boulder landscape, Karnataka, India, ancient ruins, golden dusk"),
    ("India · Jaipur, Hawa Mahal, facciata",        "Hawa Mahal, Jaipur, India, honeycomb sandstone facade, blue sky"),
    ("India · Varanasi, Gange al tramonto",        "Varanasi ghats, Ganges river, India, golden sunset, rituals, smoke"),

    # ── Asia Sud-Est (5) ─────────────────────────────────────────
    ("Cambogia · Angkor Wat, stagno di loto",         "Angkor Wat main causeway, Cambodia, lotus pond reflection, sunrise"),
    ("Cambogia · Bayon, volti di pietra, giungla",     "Angkor Thom Bayon temple, Cambodia, stone faces, jungle canopy"),
    ("Myanmar · Bagan, pagode e mongolfiere",         "Bagan temple plain, Myanmar, hot air balloons at dawn, misty pagodas"),
    ("Vietnam · Baia di Halong, picchi carsici",         "Halong Bay limestone karsts, Vietnam, emerald water, fishing boats mist"),
    ("Giava · Borobudur, sfondo vulcanico",       "Borobudur stupa terraces, Java, Indonesia, volcanic backdrop, sunrise"),

    # ── Asia Orientale & Giappone (6) ────────────────────────────
    ("Cina · Grande Muraglia, Jinshanling autunnale",    "Great Wall of China, Jinshanling, autumn foliage, golden light"),
    ("Cina · Città Proibita, portale vermiglio",   "Forbidden City, Beijing, vermillion gates, imperial courtyard"),
    ("Cina · Esercito di Terracotta, Xi'an",            "Terracotta Army pits, Xi'an, China, rows of warrior figures, amber"),
    ("Giappone · Kyoto, torii di Fushimi Inari",        "Fushimi Inari shrine, Kyoto, endless red torii gates, misty forest path"),
    ("Giappone · Kyoto, bosco di bambù Arashiyama",    "Arashiyama bamboo grove, Kyoto, towering green culms, filtered light"),
    ("Giappone · Monte Fuji, fiori di ciliegio",       "Mount Fuji, Japan, cherry blossom foreground, Kawaguchiko lake reflection"),

    # ── Grecia & Turchia (5) ─────────────────────────────────────
    ("Grecia · Santorini Oia, vista sulla caldera",      "Santorini Oia village, white cubic houses, caldera, Aegean sunset"),
    ("Grecia · Acropoli, colonne del Partenone",     "Parthenon Acropolis, Athens, marble columns, city below, golden hour"),
    ("Grecia · Meteore, monasteri sulle rocce",        "Meteora monasteries, Greece, rock pinnacles, Byzantine churches, dawn"),
    ("Turchia · Cappadocia, camini delle fate",       "Cappadocia Göreme valley, Turkey, hot air balloons, fairy chimneys"),
    ("Turchia · Pamukkale, piscine di travertino",      "Pamukkale travertine terraces, Turkey, white mineral pools, sunset"),

    # ── Europa Occidentale & Nord (6) ────────────────────────────
    ("Spagna · Alhambra, cortile moresco",       "Alhambra Nasrid Palaces courtyard, Granada, Moorish arches, reflection"),
    ("Spagna · Sagrada Família, navata di vetro",       "Sagrada Família nave interior, Barcelona, stained glass light forest"),
    ("Francia · Mont Saint-Michel, isola di marea",    "Mont Saint-Michel, Normandy, tidal island monastery, low tide sand"),
    ("Francia · Versailles, Galleria degli Specchi",      "Versailles Hall of Mirrors, France, golden chandeliers, garden axis"),
    ("Germania · Neuschwanstein, foresta alpina",   "Neuschwanstein Castle, Bavaria, fairytale towers, alpine forest"),
    ("Scozia · Castello di Edimburgo, roccia",         "Edinburgh Castle esplanade, Scotland, dramatic rock, city below"),

    # ── Europa Centrale & Est (3) ─────────────────────────────────
    ("Rep. Ceca · Praga, orologio astronomico",        "Prague Old Town Square, astronomical clock, Gothic spires, dusk"),
    ("Croazia · mura di Dubrovnik, Adriatico",       "Dubrovnik Old City walls, Adriatic panorama, red rooftops, sunset"),
    ("Inghilterra · Stonehenge, nebbia all'alba",                "Stonehenge, Wiltshire, megalithic circle, dawn mist, rising sun"),

    # ── Americhe (5) ─────────────────────────────────────────────
    ("Arizona · Antelope Canyon, raggi di luce",    "Antelope Canyon slot canyon, Arizona, light beams, swirling sandstone"),
    ("Arizona · Monument Valley, mesas rosse",      "Monument Valley buttes, Arizona, red mesa silhouettes, sunset"),
    ("Perù · Machu Picchu, alba andina",       "Machu Picchu citadel, Peru, Andean peaks above clouds, sunrise"),
    ("Messico · Chichen Itza, El Castillo",        "Chichen Itza El Castillo pyramid, Mexico, equinox light, shadow serpent"),
    ("Brasile · Baia do Sancho, discesa dalla scogliera",    "Baia do Sancho, Fernando de Noronha, Brazil, lush cliff, turquoise"),

    # ── Oceania & Isole (4) ───────────────────────────────────────
    ("Seychelles · Anse Source d'Argent",         "Anse Source d'Argent, La Digue, Seychelles, granite boulders, pink sand"),
    ("Whitsundays · Whitehaven, sabbia di silice",     "Whitehaven Beach, Whitsundays, Australia, pure silica white sand"),
    ("Bahamas · Pink Sands, spiaggia rosata",         "Pink Sands Beach, Harbour Island, Bahamas, blush pink sand, calm water"),
    ("Cile · Isola di Pasqua, fila di moai",           "Easter Island Ahu Tongariki, Chile, moai row, ocean sunrise"),

    # ── Spiagge Iconiche Extra (3) ────────────────────────────────
    ("Zante · Navagio, spiaggia del naufragio",      "Navagio Shipwreck Beach, Zakynthos, Greece, rusted wreck, white pebbles"),
    ("Algarve · Praia da Marinha, arco roccioso",     "Praia da Marinha, Algarve, ochre rock formations, secret cove"),
    ("Maldive · bungalow sull'acqua, laguna",     "Maldives overwater bungalow, crystal lagoon, turquoise infinity, sunset"),
]

# --- OUTFIT POOL (100) ---
# Zero abiti lunghi / maxi / midi / pantaloni / indumenti maschili / look casual banali
OUTFIT_POOL = [
    # ── MINI DRESS (20) ───────────────────────────────────────────
    ("Balmain · sequined mini · electric cobalt",        "electric cobalt sequined Balmain mini dress, plunging V neckline, structured shoulders, cobalt strappy heels, gold ear cuffs"),
    ("Vauthier · strapless bodycon · burnt orange",      "burnt orange Alexandre Vauthier strapless bodycon mini, ruched bust, high slit, nude pointed pumps, gold bangles"),
    ("Versace · micro mini · deep forest green",         "deep forest green Versace micro mini, plunging neckline, gold Medusa hardware, black strappy sandals, statement gold hoops"),
    ("Zimmermann · broderie off-shoulder · dusty rose",  "dusty rose Zimmermann broderie anglaise off-shoulder mini, tiered hem, blush wedge sandals, pearl drop earrings"),
    ("Valentino · ruffled mini · hot magenta",           "hot magenta Valentino ruffled mini dress, sweetheart neckline, bare shoulders, fuchsia satin heels, diamond tennis bracelet"),
    ("Hervé Léger · bandage mini · ice blue",            "ice blue Hervé Léger bandage mini, wrap neckline, body-sculpting seams, powder blue platform heels, crystal ear studs"),
    ("Jacquemus · asymmetric micro · acid yellow",       "acid yellow Jacquemus asymmetric micro mini, single draped strap, bare shoulders, nude pointed mules, gold chain necklace"),
    ("Self-Portrait · lace mini · deep burgundy",        "deep burgundy Self-Portrait lace mini, plunging back, long sleeves, wine-red strappy heels, pearl choker"),
    ("Retrofête · sequined mini · bright coral",         "bright coral Retrofête sequined mini, plunging V, spaghetti straps, coral stiletto sandals, gold stacking rings"),
    ("Coperni · cut-out mini · steel grey",              "steel grey Coperni cut-out mini, architectural cutaways at waist, perspex block heels, silver ear climbers"),
    ("Chloé · broderie strapless · terracotta",          "terracotta Chloé broderie strapless mini, frayed hem, raw edges, tan leather block heels, hammered gold cuffs"),
    ("Rick Owens · draped one-shoulder · electric violet","electric violet Rick Owens draped mini, asymmetric one-shoulder, thigh slit, violet pointed pumps, silver cuff"),
    ("Dolce & Gabbana · lace corseted mini · noir",      "noir Dolce & Gabbana lace-corseted mini, structured boning, deep neckline, black satin pumps, jet drop earrings"),
    ("Versace · safety-pin micro · silver chrome",       "chrome silver Versace safety-pin micro dress, exposed midriff slashes, bare legs, silver platform sandals, choker chain"),
    ("Saint Laurent · vinyl mini · midnight black",      "midnight black Saint Laurent patent vinyl mini, structured collar, patent belt, black stiletto ankle boots, no jewellery"),
    ("Givenchy · asymmetric petal mini · ivory",         "ivory Givenchy asymmetric petal mini, sculptural draped hem, bare shoulders, ivory satin pumps, delicate gold chain"),
    ("Mugler · latex spiralled mini · deep red",         "deep red Mugler latex spiralled mini, hourglass spiral seaming, bare back cutout, red pointed ankle boots, bold chandelier earrings"),
    ("Dior · micro tweed mini · cobalt blue",            "cobalt blue micro tweed Dior mini, gold button trim, structured bust, nude strappy sandals, pearl and gold CC choker"),
    ("Nensi Dojaka · lingerie micro mini · black sheer", "black sheer Nensi Dojaka lingerie micro mini, spaghetti straps, barely-there panels, black stilettos, single diamond ear stud"),
    ("Poster Girl · cut-out structured mini · fuchsia",  "fuchsia Poster Girl cut-out structured mini, exaggerated hip panels, bare midriff window, fuchsia platform boots, oversized hoops"),

    # ── BEACHWEAR (20) ───────────────────────────────────────────
    ("La Perla · triangle string bikini · crimson",      "crimson La Perla triangle string bikini, minimal coverage, red cord ties, gold anklet, oversized black sunglasses"),
    ("Eres · bandeau high-cut bikini · electric turquoise","electric turquoise Eres bandeau bikini, high-cut bottoms, sheer turquoise pareo tied low, tan espadrille wedges"),
    ("Norma Kamali · barely-there bikini · sand beige",  "sand beige Norma Kamali barely-there string bikini, ruched bottoms, woven sun hat, gold body chain"),
    ("Zimmermann · triangle bikini · sunshine yellow",   "sunshine yellow Zimmermann triangle bikini, ruched top, broderie sarong wrap, white platform sandals, gold hoops"),
    ("Missoni · crochet bikini · deep coral",            "deep coral Missoni crochet bikini, fringe hem bottoms, matching crochet cover-up, tan flat sandals, shell earrings"),
    ("Alaïa · cut-out one-piece · ivory white",          "ivory white one-piece Alaïa swimsuit, deep V front, cut-out waist, high cut legs, white slide sandals, gold cuff"),
    ("La Perla · high-leg one-piece · forest green",     "forest green La Perla high-leg one-piece, structured bust, low back, gold hardware rings, tan leather slides"),
    ("Dolce & Gabbana · push-up bikini · black",         "black Dolce & Gabbana push-up bikini, gold logo charm at hip, black lace sarong, gold stiletto sandals, bold hoops"),
    ("Agent Provocateur · micro bikini · neon pink",     "neon pink Agent Provocateur barely-there micro bikini, pink rhinestone trim, matching pareo, pink flat sandals"),
    ("Valentino · halter one-piece · pale lavender",     "pale lavender Valentino one-piece, plunging halter neck, tie-side, lavender slides, amethyst bracelet"),
    ("Odabash · string bikini · bronze metallic",        "bronze metallic Melissa Odabash string bikini, wide-brim bronze hat, tan leather thong sandals, layered gold chains"),
    ("Hunza G · crinkle bikini · cobalt blue",           "cobalt blue Hunza G crinkle bikini, ruched top, matching crinkle shorts, cobalt espadrilles, silver anklet"),
    ("Vintage · high-cut one-piece · cherry red",        "cherry red high-cut vintage one-piece, padded structured bust, retro silhouette, red wedge sandals, red cat-eye sunglasses"),
    ("Seafolly · bandeau bikini · sage green",           "sage green Seafolly bandeau bikini, tie-waist high-rise bottoms, sage linen shirt open, flat leather sandals"),
    ("Versace · baroque print bikini · gold black",      "gold and black Versace baroque print bikini, baroque medallion pattern, gold hardware, platform sandals, sunglasses"),
    ("Zimmermann · printed ruffle bikini · tropical",    "Zimmermann tropical print ruffle bikini, frilled bust, high-waist bottoms, straw bag, gold sandals, printed sarong"),
    ("Eres · one-piece deep plunge · navy",              "navy deep-plunge Eres one-piece, minimal silhouette, open back, gold ring detail, navy slides, clean look"),
    ("La Perla · fishnet overlay bikini · black",        "black La Perla fishnet-overlay bikini, structured push-up cups, sheer net over bottoms, black platform mules, statement cuff"),
    ("Agua Bendita · floral cut-out one-piece · fuchsia","fuchsia floral Agua Bendita cut-out one-piece, hand-embroidered flowers, strategic openings, cork wedges, flower earrings"),
    ("Camilla · embellished kaftan bikini · jewel",      "jewel-toned Camilla embellished kaftan over triangle bikini, crystal trim, gold sandals, layered necklaces, headscarf"),

    # ── ESTIVI (6) ───────────────────────────────────────────────
    ("Faithfull · broderie sundress · powder blue",      "powder blue Faithfull the Brand broderie sundress, mini length, puff sleeves, white block heels, pearl studs"),
    ("Bottega Veneta · slip dress · moss green",         "moss green Bottega Veneta intrecciato-detail slip dress, cowl back, bare shoulders, tan leather mules, gold cuff"),
    ("Jacquemus · micro skirt set · faded denim",        "faded denim Jacquemus micro skirt, matching bandeau crop, silver buckle mules, silver ear climbers"),
    ("Agua Bendita · off-shoulder ruffle · hot tangerine","hot tangerine Agua Bendita off-shoulder ruffle mini, smocked bodice, cork wedge sandals, gold layered chains"),
    ("Zimmermann · linen strapless mini · butter yellow","butter yellow Zimmermann linen strapless mini, scalloped hem, woven espadrille wedges, tortoiseshell sunglasses"),
    ("Saloni · wrap mini · bold floral print",           "bold floral Saloni wrap mini, deep V neckline, bare shoulders, nude pointed heels, gold hoop earrings"),

    # ── BODYSUIT / AVANT-GARDE (8) ───────────────────────────────
    ("Rabanne · chainmail micro dress · liquid silver",   "liquid silver Rabanne chainmail micro dress, plunging V, bare hips, silver stiletto sandals, no jewellery"),
    ("Mugler · hourglass cut-out · matte black",          "matte black Mugler hourglass cut-out bodycon dress, spiral waist openings, sheer body panels, black stiletto boots"),
    ("Alaïa · laser-cut bodycon · deep violet",           "deep violet Alaïa laser-cut bodycon, geometric openwork revealing skin, violet patent heels, single silver cuff"),
    ("Thierry Mugler · metal corset · rose gold",         "rose gold Thierry Mugler metal underwire corset, structured boning, micro skirt, rose gold heels, chandelier earrings"),
    ("Iris van Herpen · 3D sculptural mini · electric lime","electric lime Iris van Herpen 3D-printed sculptural mini, bare arms, architectural platform heels, no jewellery"),
    ("Rabanne · gold disc mini · molten gold",            "molten gold Rabanne interlocking disc mini, bare shoulders, structured hips, gold platform sandals, ear stacks"),
    ("Alaïa · knit bodycon · camel nude",                 "camel nude Alaïa knit bodycon mini, precision seaming, second-skin fit, nude platform heels, single gold cuff"),
    ("Jean Paul Gaultier · cone bra corset · black white","black and white Jean Paul Gaultier conical bra corset mini, structured stiffened bust cones, bustier bodice, fishnet body stockings, patent heels"),

    # ── FUTURISTA / SCI-FI (8) ───────────────────────────────────
    ("Courrèges · vinyl micro · chrome white",            "chrome white Courrèges vinyl micro dress, circular cut-outs, structured collar, white go-go ankle boots, geometric silver earrings"),
    ("Mugler · latex corseted mini · electric red",       "electric red latex Mugler corseted mini, structured cone bust, bare midriff panel, red vinyl thigh-high boots, no jewellery"),
    ("Balenciaga · inflated sculptural mini · cobalt",    "cobalt Balenciaga inflated sculptural mini, oversized puffer silhouette, bare legs, chunky white platform boots, visor sunglasses"),
    ("Iris van Herpen · magnetic wave · iridescent",      "iridescent Iris van Herpen magnetic-wave mini, undulating 3D-printed panels, perspex platform heels, single ear antennae"),
    ("Paco Rabanne · chrome ring-mail mini · liquid metal","liquid metal Paco Rabanne interlocked chrome ring-mail mini, sculptural hip flare, matching chrome ankle boots, futurist visor"),
    ("Anrealage · light-reactive mini · white to colour", "Anrealage UV-reactive micro mini, transforms white to vivid colour in sunlight, architectural fold origami, flat white boots"),
    ("Thom Browne · neoprene cape-mini · gunmetal grey",  "gunmetal grey Thom Browne neoprene structured cape mini, exaggerated padded shoulders, leather platform brogues, visor spectacles"),
    ("Y-3 · technical bodysuit · all black",              "all-black Y-3 technical bodysuit, mesh inserts, moulded panels, structured shoulders, black platform trainers, reflective visor"),

    # ── RETRÒ ANNI '20 / ART DÉCO (6) ────────────────────────────
    ("Flapper · beaded fringe mini · champagne gold",     "champagne gold beaded flapper mini, layered fringe hem, deep V back, T-strap gold heels, long pearl rope, feather headband"),
    ("Art Déco · sequined blouson mini · jet black",      "jet black sequined Art Déco blouson mini, geometric pattern, dropped waist, black T-strap heels, marcasite cuff, cigarette holder"),
    ("Vionnet · bias satin mini · pale ivory",            "pale ivory bias-cut satin mini, draped cowl neck, asymmetric hem, ivory kitten heels, long jade necklace, elbow gloves"),
    ("Poiret · harem-inspired tunic mini · deep sapphire","deep sapphire Poiret-inspired draped tunic mini, kimono sleeves folded up, wide obi belt, platform sandals with ankle strap, headband"),
    ("Lanvin · art deco embroidered mini · midnight teal","midnight teal Jeanne Lanvin 1920s embroidered mini, geometric beaded motifs, dropped waist, T-strap bronze heels, jade and pearl cuff"),
    ("Madeleine Vionnet · handkerchief hem mini · blush", "blush Madeleine Vionnet handkerchief-hem mini, bias-cut draped points, bare décolleté, nude satin kitten heels, long crystal tassel earrings"),

    # ── RETRÒ ANNI '70 / GLAM ROCK / DISCO (6) ───────────────────
    ("Halston · disco halter mini · liquid gold",         "liquid gold Halston-style disco halter mini, bare midriff cut, wrap skirt flared, platform gold sandals, hoop earrings to shoulders"),
    ("Glam Rock · vinyl hot pants set · neon electric",   "neon electric Glam Rock vinyl hot pants and matching bandeau, studded belt, platform ankle boots with chrome buckles, oversized tinted lenses"),
    ("Ossie Clark · chiffon plunge mini · flame orange",  "flame orange Ossie Clark-style chiffon plunge mini, draped neckline, split sleeves, wooden platform heels, amber resin bangles"),
    ("Biba · velvet micro mini · aubergine",              "deep aubergine Biba velvet micro mini, wide floppy sleeves, low neckline, tan platform boots, oversized floppy hat"),
    ("Bill Gibb · printed jersey mini · psychedelic",     "psychedelic swirl Bill Gibb jersey mini, bold 70s print, long bell sleeves cropped, platform sandals, wide leather belt, floppy hat"),
    ("Zandra Rhodes · printed silk jersey mini · coral",  "coral Zandra Rhodes hand-printed silk jersey micro mini, zigzag hem, safety-pin accents, platform wedge sandals, long beaded earrings"),

    # ── AVANGUARDIA (6) ──────────────────────────────────────────
    ("CDG · deconstructed asymmetric · raw ecru",         "raw ecru Comme des Garçons deconstructed mini, asymmetric unfinished hem, padded hip protrusion, flat black derby shoes, no jewellery"),
    ("Margiela · inside-out bustier mini · chalk white",  "chalk white Margiela inside-out bustier mini, exposed boning and seams, bare back, white strappy platform sandals, single oversized brooch"),
    ("Rei Kawakubo · void silhouette mini · deep black",  "deep black Rei Kawakubo void-architecture mini, sculptural hollow back structure, flat black sneakers, no accessories"),
    ("Hussein Chalayan · remote-control hem mini · grey", "grey Hussein Chalayan engineered mini, mechanically retractable hem panels, structured bodice, bare legs, flat architectural shoes"),
    ("Walter Van Beirendonck · graphic pop mini · multi", "multicolour Walter Van Beirendonck graphic bodycon mini, bold cartoon motifs, oversized collar, platform boots with character faces"),
    ("Ann Demeulemeester · asymmetric wrap mini · blk wht","black and white Ann Demeulemeester asymmetric wrap mini, raw edges, leather wrap belt, flat lace-up boots, single long feather earring"),

    # ── COSTUMI / FILM ICONICI (10) ──────────────────────────────
    ("Cleopatra · gold ceremonial mini · beaten gold",    "beaten gold Egyptian ceremonial mini, pleated collar, wide jewelled arm cuffs, black kohl eyes, flat golden sandals with straps to knee"),
    ("Metropolis · machine-woman bodysuit · polished silver","polished silver Fritz Lang Metropolis-inspired bodysuit, riveted metal panels, structured breast plate, silver thigh-high boots, silver crown headpiece"),
    ("Moulin Rouge · showgirl corset micro · scarlet red","scarlet red showgirl corset micro, boned structured bodice, fringe hem, feather boa, scarlet red stiletto heels, chandelier earrings"),
    ("Barbarella · space-age vinyl micro · white",        "white space-age Barbarella vinyl micro, futuristic structured shoulders, thigh-high white boots, oversized round tinted goggles"),
    ("Catwoman · latex catsuit · gloss black",            "gloss black latex Catwoman catsuit, precise zip, moulded bust, stiletto black ankle boots, cat-ear headband, long black gloves"),
    ("Queen of Hearts · corset micro · vivid red",        "vivid red Queen of Hearts corset micro, structural boning, heart cutout, black ruffle under-skirt, red platform heels, heart crown headpiece"),
    ("Tron Legacy · bodysuit · black neon blue",          "black Tron Legacy bodysuit, glowing neon electric blue circuit lines, structured shoulders, illuminated platform boots"),
    ("Kill Bill · asymmetric micro · chrome yellow",      "chrome yellow Kill Bill-inspired asymmetric mini, clean graphic design, bare one shoulder, yellow pumps, single samurai pin brooch"),
    ("Marie Antoinette · corseted micro · powder blue",   "powder blue Marie Antoinette corseted structured micro, panniers scaled to mini, lace trim, platform heels, powdered wig fascinator"),
    ("Cabaret · sequined performer set · noir",           "noir Liza Minnelli Cabaret-style sequined bodysuit with attached micro skirt, fishnet stockings, black bowler hat, stiletto heels"),

    # ── CABARET / BURLESQUE (5) ──────────────────────────────────
    ("Burlesque · corset micro · midnight blue feathers", "midnight blue burlesque corset micro, structured boning, chandelier crystal trim, blue marabou feather boa, fishnet stockings, blue platform heels"),
    ("Dita von Teese · satin corset micro · red noir",    "burgundy satin burlesque corset, structured steel boning, micro skirt, black seamed stockings, red stiletto heels, long black gloves"),
    ("Crazy Horse · rhinestone bodysuit · nude black",    "nude illusion Crazy Horse rhinestone bodysuit, strategic crystal placement, micro fringe skirt attached, platform heels, dramatic eyelashes"),
    ("Follies Bergère · headdress micro · gold plumes",   "gold showgirl corset micro, massive gold plume headdress, crystal-beaded boning, nude fishnet, gold platform heels"),
    ("Lido · feather cape micro · white crystal",         "white crystal Lido showgirl micro with enormous white ostrich-feather cape, structured crystal bodice, long white gloves, white platform heels"),

    # ── HAUTE COUTURE SCENOGRAFICA (5) ────────────────────────────
    ("Schiaparelli · surrealist corset mini · shocking pink","shocking pink Schiaparelli surrealist corset mini, trompe-l'oeil rib cage embroidery, structured conical bust, platform heels, jewelled lobster brooch"),
    ("Alexander McQueen · armoured corset · bone ivory",  "bone ivory Alexander McQueen sculpted armoured corset mini, skeletal moulded bodice, structured hip plates, ivory platform heels, no jewellery"),
    ("Christian Lacroix · puffball mini · polychrome",    "polychrome Christian Lacroix puffball mini, enormous gathered silk skirt, structured bodice, stiletto heels, dramatic floral hat"),
    ("Versace · safety-pin couture · nude gold",          "nude and gold Versace safety-pin couture mini, dozens of interlocking gold safety pins, deep plunge, gold platform sandals, gold ear cuffs"),
    ("Thierry Mugler · robotic couture · chrome black",   "chrome and matte black Thierry Mugler robotic couture mini, exoskeleton shoulder wings, structured breastplate bodice, black patent stiletto heels"),
]

STYLE_POOL = [
    # ── FOTOGRAFI CLASSICI (20) ───────────────────────────────────
    ("Helmut Newton · glamorous B&W",        "Helmut Newton, glamorous monochrome editorial"),
    ("Guy Bourdin · saturated surrealist",   "Guy Bourdin, saturated surrealist fashion photography"),
    ("Richard Avedon · dynamic movement",    "Richard Avedon, dynamic high-fashion movement"),
    ("Irving Penn · clean studio",           "Irving Penn, clean studio portraiture, timeless elegance"),
    ("Peter Lindbergh · cinematic",          "Peter Lindbergh, cinematic naturalistic beauty"),
    ("Herb Ritts · sculptural B&W",          "Herb Ritts, sculptural black and white photography"),
    ("Annie Leibovitz · narrative cinema",   "Annie Leibovitz, narrative cinematic portraiture"),
    ("Mario Testino · vibrant glossy",       "Mario Testino, vibrant glossy fashion photography"),
    ("Paolo Roversi · painterly soft",       "Paolo Roversi, painterly soft-focus romanticism"),
    ("David LaChapelle · pop art hyper",     "David LaChapelle, hyperrealistic pop art surrealism"),
    ("Nick Knight · avant-garde digital",    "Nick Knight, avant-garde digital fashion imagery"),
    ("Steven Meisel · sophisticated",        "Steven Meisel, sophisticated high-fashion editorial"),
    ("Juergen Teller · raw unfiltered",      "Juergen Teller, raw unfiltered fashion realism"),
    ("Tim Walker · fantastical whimsical",   "Tim Walker, fantastical whimsical fashion storytelling"),
    ("Miles Aldridge · hyper-saturated",     "Miles Aldridge, cinematic hyper-saturated colour"),
    ("Solve Sundsbo · futuristic digital",   "Solve Sundsbo, futuristic digital fashion photography"),
    ("Ellen von Unwerth · playful glamour",  "Ellen von Unwerth, playful glamorous feminine energy"),
    ("Demarchelier · classic elegant",       "Patrick Demarchelier, classic elegant fashion photography"),
    ("Bruce Weber · sun-drenched lifestyle", "Bruce Weber, sun-drenched American lifestyle photography"),
    ("Nan Goldin · intimate documentary",    "Nan Goldin, intimate documentary fashion realism"),
    # ── STILI PITTORICI & STORICI (10) ────────────────────────────
    ("Rinascimentale · luce da Vermeer",     "Renaissance Old Masters painting style, Vermeer-like golden sidelight, draped fabrics, oil-on-canvas texture, sfumato background"),
    ("Orientale classico · seta e lacca",    "classical Oriental painting style, lacquered background, silk textures, calligraphy ink wash, lantern light, misty atmosphere"),
    ("Giapponese · woodblock ukiyo-e",       "Japanese ukiyo-e woodblock print aesthetic, flat bold outlines, graphic colour planes, sakura blossoms, washi paper texture"),
    ("Tribale · etnico, ocra e terra",       "tribal ethnic photographic style, warm ochre earth tones, geometric patterns, natural textures, dramatic sky, raw documentary"),
    ("Pictorialist · seppia, sfumato",       "Pictorialist fine-art photography 1910s, sepia tones, soft-focus painterly haze, velvet bokeh, romantic blur"),
    ("Neon Noir · pioggia, contrasto",       "neon noir photography, rain-slicked streets, vivid pink and blue neon reflections, extreme contrast, deep shadows"),
    ("Daguerreotype · argento monocromo",    "daguerreotype early photography style, silver-toned monochrome, metallic sheen texture, static formal pose, vignette edges"),
    ("Hyperrealism · pittura a olio",        "hyperrealist oil painting aesthetic, hyper-detailed impasto brushwork, visible paint texture, museum-quality rendering"),
    ("Infrared · bianchi bruciati",          "infrared photography, blown-out whites on foliage, jet-black skies, surreal tonal reversal, dreamlike high-contrast"),
    ("Tableau Vivant · dipinto seicentesco", "Tableau Vivant, seventeenth-century Old Master painting composition, theatrical chiaroscuro, dramatic drapery, candlelight sfumato"),
]

POSE_POOL = [
    ("Standing · hand on hip",               "standing upright, one hand on hip, chin slightly lifted"),
    ("Walking · toward camera",              "walking confidently toward camera, skirt in motion"),
    ("Leaning · wall, knee bent",            "leaning against wall, arms crossed, one knee bent"),
    ("Sitting · legs crossed, upright",      "sitting on edge of surface, legs crossed at ankle, back straight"),
    ("Reclining · on side, elbow",           "reclining on side, propped on elbow, legs extended"),
    ("Back to camera · over shoulder",       "standing back to camera, glancing over shoulder"),
    ("Floor · knees drawn up",               "seated on floor, knees drawn up, arms wrapped around legs"),
    ("Leaning forward · hands on thighs",    "leaning forward slightly, hands on thighs, direct gaze"),
    ("Side profile · arm on wall",           "standing side profile, one arm extended along wall"),
    ("Walking away · looking back",          "walking away, looking back, hair movement"),
    ("Steps · elbows on knees",              "sitting on steps, elbows on knees, chin resting on hands"),
    ("Arms raised · arched back",            "standing with arms raised overhead, arched back"),
    ("Railing · gazing at horizon",          "leaning on railing, one elbow resting, gazing at horizon"),
    ("Crouching · hands on ground",          "crouching low, knees apart, hands on ground between feet"),
    ("Wide stance · hands behind back",      "standing with legs wide apart, hands clasped behind back"),
    ("Chair · legs over armrest",            "seated on chair, legs draped over armrest, relaxed"),
    ("Lying · arms above head",              "lying on back, arms above head, legs slightly apart"),
    ("Doorway · hand on frame",              "standing in doorway, one hand on frame, body turned"),
    ("Spinning · skirt fanned out",          "spinning, skirt fanned out, captured mid-rotation"),
    ("Cross-legged · floor",                "seated cross-legged on floor, hands resting on knees"),
    ("One leg forward · hip shifted",        "standing with one leg forward, weight shifted to hip"),
    ("Leaning back · head tilted up",        "leaning back against surface, head tilted up, eyes closed"),
    ("Kneeling · one knee extended",         "kneeling on one knee, other leg extended, torso upright"),
    ("Hands in hair · elbows raised",        "standing with hands in hair, elbows raised"),
    ("Staircase · arm on banister",          "seated on staircase, turned sideways, arm on banister"),
    ("Walking sideways · trailing wall",     "walking sideways along wall, fingertips trailing surface"),
    ("Hand on chest · soft gaze",            "standing with one hand on chest, other at side, soft gaze"),
    ("Face down · legs bent up",             "lying face down, propped on forearms, legs bent upward"),
    ("Legs crossed · arms loose",            "standing with legs crossed at knee, arms loose at sides"),
    ("Water edge · feet dangling",           "seated at edge of water, feet dangling in"),
]

SKY_POOL = [
    ("Golden hour · warm amber",             "golden hour, warm amber light, long soft shadows"),
    ("Midday · harsh sun, sharp shadows",    "blue sky, harsh midday sun, sharp shadows"),
    ("Overcast · soft diffused light",       "overcast soft light, diffused, no shadows, milky sky"),
    ("Dusk · deep purple orange horizon",    "dramatic dusk, deep purple and orange horizon"),
    ("Night · full moon, silver-blue",       "clear night, full moon, silver-blue ambient light"),
    ("Sunrise · pale pink and gold",         "sunrise, pale pink and gold, delicate warm haze"),
    ("Stormy · dark clouds, pre-rain",       "stormy sky, dark clouds, electric pre-rain tension"),
    ("Magic hour · crimson and gold",        "magic hour, last light, sky deep crimson and gold"),
    ("Studio · bright white clinical",       "bright white studio light, clean and clinical"),
    ("Neon city night · wet pavement",       "neon city night, pink and blue reflections on wet pavement"),
    ("Candlelight · flickering amber",       "candlelight warm glow, intimate, flickering amber"),
    ("Underwater · caustic rays",            "underwater light, caustic rays, turquoise shimmer"),
    ("Foggy morning · cool mist",            "foggy morning, diffused cool light, soft mist"),
    ("Backlit · strong rim light",           "backlit silhouette, strong rim light, sun behind subject"),
    ("Blue hour · city lights emerging",     "blue hour, twilight, deep blue sky, city lights emerging"),
    ("Desert midday · bleached white",       "desert midday, bleached white light, stark and hot"),
    ("Autumn afternoon · low orange sun",    "autumn afternoon, warm orange, low angle sun through leaves"),
    ("Winter light · cold blue tones",       "crystal clear winter light, cold blue tones, sharp and clean"),
    ("Tropical noon · vivid saturated",      "tropical noon, vivid saturated colors, intense shadows"),
    ("Venetian afternoon · light off water", "Venetian afternoon, warm reflected light off water"),
    ("Opera house · warm spotlights",        "opera house interior, dramatic warm spotlights"),
    ("Penthouse night · city glow",          "penthouse night, city glow from below, skyline backdrop"),
    ("Rainy evening · wet street",           "rainy evening, grey sky, reflections on wet street"),
    ("Greenhouse · green diffused light",    "greenhouse light, soft diffused green-tinted natural light"),
    ("Mediterranean afternoon · golden",     "late afternoon Mediterranean, golden haze, warm and sleepy"),
    ("Rooftop sunset · pink to violet",      "rooftop at sunset, sky gradient pink to violet"),
    ("Beach morning · cool early light",     "early morning beach, cool light, long shadows on sand"),
    ("Ballroom · crystal chandeliers",       "grand ballroom chandeliers, warm crystal light from above"),
    ("Snow · white reflected, cold blue",    "snowy exterior, pure white reflected light, cold blue shadows"),
    ("Poolside · white reflections",         "poolside afternoon, bright white reflections off water surface"),
]

MOOD_POOL = [
    ("Sophisticated · untouchable",          "sophisticated and untouchable"),
    ("Playful · irreverent",                 "playful and irreverent"),
    ("Mysterious · alluring",               "mysterious and alluring"),
    ("Bold · confrontational",               "bold and confrontational"),
    ("Dreamy · introspective",               "dreamy and introspective"),
    ("Fierce · dominant",                    "fierce and dominant"),
    ("Sensual · confident",                  "sensual and confident"),
    ("Melancholic · distant",                "melancholic and distant"),
    ("Euphoric · free",                      "euphoric and free"),
    ("Cold · editorial",                     "cold and editorial"),
    ("Warm · inviting",                      "warm and inviting"),
    ("Dangerous · magnetic",                 "dangerous and magnetic"),
    ("Nostalgic · cinematic",                "nostalgic and cinematic"),
    ("Raw · unfiltered",                     "raw and unfiltered"),
    ("Elegant · composed",                   "elegant and composed"),
    ("Wild · untamed",                       "wild and untamed"),
    ("Ironic · detached",                    "ironic and detached"),
    ("Glamorous · excessive",                "glamorous and excessive"),
    ("Intimate · vulnerable",                "intimate and vulnerable"),
    ("Powerful · statuesque",                "powerful and statuesque"),
    ("Surreal · otherworldly",               "surreal and otherworldly"),
    ("Casual · effortless",                  "casual and effortless"),
    ("Theatrical · exaggerated",             "theatrical and exaggerated"),
    ("Romantic · soft",                      "romantic and soft"),
    ("Angular · geometric",                  "angular and geometric"),
    ("Languid · bored",                      "languid and bored"),
    ("Sharp · precise",                      "sharp and precise"),
    ("Luminous · ethereal",                  "luminous and ethereal"),
    ("Heavy · brooding",                     "heavy and brooding"),
    ("Joyful · explosive",                   "joyful and explosive"),
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
    loc_tuple   = random.choice(LOCATION_POOL)
    out_tuple   = random.choice(OUTFIT_POOL)
    style_tuple = random.choice(STYLE_POOL)
    location = loc_tuple[1]
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

# --- GENERA IMMAGINE ---
def execute_generation(full_prompt, formato="2:3"):
    try:
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
# threaded=False: i callback vengono processati uno alla volta (serializzati).
# Questo elimina alla radice le race condition che causano i messaggi duplicati.
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=False)

# --- STATO ---
last_scenario  = {}
last_prompt    = {}
manual_state   = {}

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
        InlineKeyboardButton("🔁 Riprova", callback_data="riprova"),
        InlineKeyboardButton("🎲 Nuovo", callback_data="tira")
    )
    return markup

# --- MANUAL STEPS ---
MANUAL_STEPS = [
    {"key": "location", "label": "📍 Location",         "pool": LOCATION_POOL},
    {"key": "outfit",   "label": "👗 Outfit",            "pool": OUTFIT_POOL},
    {"key": "sky",      "label": "🌤 Sky / Lighting",    "pool": SKY_POOL},
    {"key": "pose",     "label": "💃 Pose",              "pool": POSE_POOL},
    {"key": "mood",     "label": "✨ Mood",              "pool": MOOD_POOL},
    {"key": "style",    "label": "📷 Stile fotografico", "pool": STYLE_POOL},
]

def send_manual_step(cid, uid, step_idx, page=0):
    step = MANUAL_STEPS[step_idx]
    pool = step["pool"]
    label = step["label"]
    items = get_page(pool, page)
    tp = total_pages(pool)
    markup = InlineKeyboardMarkup()
    for item in items:
        name, _ = item
        markup.add(InlineKeyboardButton(name, callback_data=f"manual_{step_idx}_{pool.index(item)}"))
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"page_{step_idx}_{page-1}"))
    nav_row.append(InlineKeyboardButton(f"{page+1}/{tp}", callback_data="noop"))
    if page < tp - 1:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"page_{step_idx}_{page+1}"))
    if nav_row:
        markup.row(*nav_row)
    bot.send_message(cid,
        f"<b>Passo {step_idx+1}/6 — {label}</b>",
        reply_markup=markup, parse_mode="HTML")

def format_scenario(scenario):
    lines = []
    labels = {
        'location': '📍 Location',
        'outfit':   '👗 Outfit',
        'sky':      '🌤 Sky',
        'pose':     '💃 Pose',
        'mood':     '✨ Mood',
        'style':    '📷 Stile',
    }
    for k, lbl in labels.items():
        val = scenario.get(k, '—')
        lines.append(f"<b>{lbl}:</b> {val}")
    return "\n".join(lines)

# --- HANDLERS ---
@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    uid = message.from_user.id
    manual_state.pop(uid, None)
    last_scenario.pop(uid, None)
    last_prompt.pop(uid, None)
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
        reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    username = call.from_user.username or str(uid)
    data = call.data

    bot.answer_callback_query(call.id)

    try:
        # --- noop ---
        if data == "noop":
            return

        # --- Scelta modalità ---
        elif data == "mode_auto":
            try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            except Exception: pass
            manual_state.pop(uid, None)
            bot.send_message(cid, "⏳ Genero scenario...")
            scenario = generate_scenario()
            last_scenario[uid] = scenario
            bot.send_message(cid, "🎲 <b>Scena automatica:</b>", parse_mode="HTML")
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎲 AUTO {username} (id={uid}) — {scenario['location']}")

        elif data == "mode_manual":
            try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            except Exception: pass
            manual_state[uid] = {}
            send_manual_step(cid, uid, 0)

        # --- Paginazione ---
        elif data.startswith("page_"):
            _, step_str, page_str = data.split("_")
            step = int(step_str)
            page = int(page_str)
            try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            except Exception: pass
            # Rimuove tutte le pagine di questo step dal registro per permettere la navigazione
            send_manual_step(cid, uid, step, page)

        # --- Selezione manuale ---
        elif data.startswith("manual_"):
            parts = data.split("_")
            step = int(parts[1])
            idx  = int(parts[2])
            step_def = MANUAL_STEPS[step]
            pool = step_def["pool"]
            title = step_def["label"]
            item = pool[idx]
            label, value = item
            if uid not in manual_state:
                manual_state[uid] = {}
            manual_state[uid][step_def["key"]] = value
            try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
            except Exception: pass
            bot.send_message(cid, f"✅ <b>{title}:</b> {label}", parse_mode="HTML")
            next_step = step + 1
            if next_step < len(MANUAL_STEPS):
                # Pulisce il registro del prossimo step (nel caso fosse già stato visitato)
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

    except Exception as e:
        logger.error(f"❌ handle_callback exception: {e}", exc_info=True)

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
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask health check attivo su porta 10000")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)

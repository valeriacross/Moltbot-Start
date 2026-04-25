import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "3.7.0"

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

# --- LOCATION POOL ---
LOCATION_POOL = [
    # ══ 🇮🇹 ITALIA ══════════════════════════════════════════
    # Abruzzo
    ("🇮🇹 · Abruzzo, Santo Stefano di Sessanio, Gran Sasso",  "Santo Stefano di Sessanio, Abruzzo, stone village, Gran Sasso backdrop"),
    ("🇮🇹 · Abruzzo, Scanno, lago e borgo medievale",         "Lago di Scanno, Abruzzo, heart-shaped lake, medieval village above, dawn mist"),
    ("🇮🇹 · Abruzzo, Castelluccio, piana fiorita",            "Castelluccio di Norcia, flowering plain, Monti Sibillini backdrop"),
    # Calabria
    ("🇮🇹 · Calabria, Scilla, castello Ruffo",                "Scilla, Calabria, Ruffo Castle on rock, colourful fishermen quarter"),
    ("🇮🇹 · Calabria, Tropea, scoglio e spiaggia bianca",     "Tropea, Calabria, cliff church on rock, white sand below, turquoise sea"),
    ("🇮🇹 · Calabria, Reggio Calabria, lungomare",            "Reggio Calabria lungomare, strait of Messina, Etna silhouette at dusk"),
    ("🇮🇹 · Calabria, Pentedattilo, borgo fantasma",          "Pentedattilo, Calabria, abandoned ghost village, five-finger rock, dramatic"),
    # Campania
    ("🇮🇹 · Campania, Amalfi, strada costiera",               "Amalfi Coast hairpin road, turquoise sea below, cliffside villages"),
    ("🇮🇹 · Campania, Capri, Faraglioni",                     "Capri Faraglioni sea stacks, crystal clear Mediterranean water, golden afternoon"),
    ("🇮🇹 · Campania, Ischia, Castello Aragonese",            "Ischia Castello Aragonese, volcanic island fortress, sunset Tyrrhenian sea"),
    ("🇮🇹 · Campania, Napoli, Castel dell'Ovo",               "Naples waterfront Lungomare, Castel dell'Ovo, golden sunset, Vesuvius"),
    ("🇮🇹 · Campania, Paestum, templi greci",                 "Paestum, Greek temples, Doric columns, golden wheat field, Campania"),
    ("🇮🇹 · Campania, Pompei, Via dell'Abbondanza",           "Pompeii Via dell'Abbondanza, ancient street, Vesuvius beyond, warm stone"),
    ("🇮🇹 · Campania, Positano, terrazza e bouganville",      "Positano terrace, bougainvillea walls, tiered white houses, sea"),
    ("🇮🇹 · Campania, Procida, Marina Corricella",            "Procida Marina Corricella, pastel-coloured fishermen houses, harbour"),
    ("🇮🇹 · Campania, Ravello, Villa Cimbrone",               "Ravello Villa Cimbrone infinity terrace, Tyrrhenian sea panorama"),
    # Emilia-Romagna
    ("🇮🇹 · Emilia-Romagna, Bologna, Due Torri",              "Bologna Due Torri medieval towers, terracotta rooftops, arcades"),
    ("🇮🇹 · Emilia-Romagna, Ferrara, Castello Estense",       "Ferrara Castello Estense, moat reflection, Renaissance towers, dusk"),
    ("🇮🇹 · Emilia-Romagna, Ravenna, mosaici bizantini",      "Ravenna Byzantine mosaic interior, golden glittering vault, candlelight"),
    # Friuli-Venezia Giulia
    ("🇮🇹 · Friuli, Cividale del Friuli, Ponte del Diavolo",  "Cividale del Friuli, Natisone river, Devil's Bridge, medieval stone, afternoon"),
    ("🇮🇹 · Friuli, Trieste, Castello di Miramare",           "Castello di Miramare, Trieste, white castle on cliff, Gulf of Trieste, turquoise"),
    # Lazio
    ("🇮🇹 · Lazio, Roma, Castel Sant'Angelo",                 "Castel Sant'Angelo, Rome, Tiber river, Angels Bridge, golden dusk"),
    ("🇮🇹 · Lazio, Roma, Colosseo esterno",                   "Rome Colosseum exterior, warm golden afternoon light, ancient stone"),
    ("🇮🇹 · Lazio, Roma, Colosseo interno e ipogeo",          "Colosseum interior arena, Rome, underground hypogeum, dramatic light"),
    ("🇮🇹 · Lazio, Roma, Colle Palatino e Foro Romano",       "Rome Palatine Hill terrace, panoramic view over Roman Forum, dusk"),
    ("🇮🇹 · Lazio, Roma, Piazza di Spagna all'alba",          "Rome Piazza di Spagna, Spanish Steps, dawn light, azalea flowers"),
    ("🇮🇹 · Lazio, Roma, Piazza Navona",                      "Rome Piazza Navona, baroque fountains, cobblestones, evening glow"),
    ("🇮🇹 · Lazio, Roma, Via Appia e acquedotto",             "Rome Via Appia Antica, ancient pines, crumbling aqueduct, golden hour"),
    ("🇮🇹 · Lazio, Roma, Villa Borghese, terrazza tra i pini","Rome Villa Borghese terrace, umbrella pines, city panorama, golden hour"),
    ("🇮🇹 · Lazio, Civita di Bagnoregio, tufo e canyon",      "Civita di Bagnoregio, dying city, tufa rock, dramatic canyon, bridge approach"),
    ("🇮🇹 · Lazio, Tivoli, Villa d'Este e fontane",           "Villa d'Este, Tivoli, Renaissance garden, hundred fountains, cypress alleys"),
    ("🇮🇹 · Lazio, Viterbo, Palazzo dei Papi",                "Viterbo Palazzo dei Papi, medieval papal palace, central fountain, warm stone"),
    # Liguria
    ("🇮🇹 · Liguria, Cinque Terre, porto di Vernazza",        "Cinque Terre Vernazza harbour, colourful tower, cliffside terraces"),
    ("🇮🇹 · Liguria, Genova, caruggi medievali",              "Genova caruggi, narrow medieval alleyways, warm stone, lanterns"),
    ("🇮🇹 · Liguria, Portofino, faro e insenatura",           "Portofino lighthouse point, emerald cove, pastel village below"),
    ("🇮🇹 · Liguria, Portofino, piazzetta e yacht",           "Portofino piazzetta, colourful facades, luxury yachts, summer Mediterranean"),
    # Lombardia
    ("🇮🇹 · Lombardia, Lago di Como, Villa Balbianello",      "Lake Como Villa del Balbianello terraced gardens, mountain backdrop"),
    ("🇮🇹 · Lombardia, Lago Maggiore, Isola Bella",           "Lake Maggiore Isola Bella, baroque terraced gardens, peacocks, blue water"),
    ("🇮🇹 · Lombardia, Lago d'Orta, isola di San Giulio",     "Lago d'Orta, Isola di San Giulio, misty morning, Romanesque basilica"),
    ("🇮🇹 · Lombardia, Milano, Castello Sforzesco",           "Milan Castello Sforzesco courtyard, Renaissance towers, afternoon"),
    ("🇮🇹 · Lombardia, Milano, Galleria Vittorio Emanuele",   "Milan Galleria Vittorio Emanuele II, glass vault, mosaic floor, warm light"),
    ("🇮🇹 · Lombardia, Milano, Terrazze del Duomo",           "Milan Duomo Cathedral rooftop terraces, city panorama, blue sky"),
    ("🇮🇹 · Lombardia, Milano, quartiere Brera",              "Milan Brera neighbourhood, cobblestones, ivy-covered walls, spring"),
    # Piemonte
    ("🇮🇹 · Piemonte, Barolo, castello e vigneti",            "Barolo village, Piedmont, castle on hilltop, vineyards, soft autumn light"),
    ("🇮🇹 · Piemonte, Langhe, vigneti nella nebbia",          "Langhe, Piedmont, autumn vineyard hills, morning mist, golden foliage"),
    ("🇮🇹 · Piemonte, Sacra di San Michele, abisso alpino",   "Sacra di San Michele, Piedmont, dramatic alpine abbey, gorge below, mist"),
    ("🇮🇹 · Piemonte, Torino, Mole Antonelliana",             "Turin Mole Antonelliana, river Po panorama, Alpine horizon"),
    ("🇮🇹 · Piemonte, Torino, Piazza Castello",               "Turin Piazza Castello, Palazzo Madama, baroque facade, golden hour"),
    # Puglia
    ("🇮🇹 · Puglia, Alberobello, trulli",                     "Alberobello trulli district, conical white rooftops, warm stone"),
    ("🇮🇹 · Puglia, Lecce, cattedrale barocca",               "Lecce baroque cathedral square, golden limestone, afternoon light"),
    ("🇮🇹 · Puglia, Ostuni, città bianca",                    "Ostuni white city, whitewashed alleyways, olive groves beyond"),
    ("🇮🇹 · Puglia, Polignano a Mare, scogliera adriatica",   "Polignano a Mare, Adriatic cliff, turquoise sea below, dramatic rock"),
    # Sardegna
    ("🇮🇹 · Sardegna, Cala Goloritzé, arco e caletta",        "Cala Goloritzé, Sardinia, dramatic limestone arch, emerald cove"),
    ("🇮🇹 · Sardegna, Costa Paradiso, rocce rosse",           "Costa Paradiso, Sardinia, dramatic red granite rocks, turquoise sea"),
    ("🇮🇹 · Sardegna, Costa Smeralda, baia turchese",         "Sardinia Costa Smeralda, turquoise cove, white sand, luxury yachts"),
    ("🇮🇹 · Sardegna, Nuraghe Losa, età del bronzo",          "Nuraghe Losa, Sardinia, ancient Bronze Age tower, green hills"),
    ("🇮🇹 · Sardegna, S'Archittu, arco marino",               "S'Archittu natural sea arch, Sardinia, limestone rock, emerald water"),
    # Sicilia
    ("🇮🇹 · Sicilia, Agrigento, Valle dei Templi",            "Agrigento Valley of Temples, Doric columns, almond blossoms"),
    ("🇮🇹 · Sicilia, Cave di Alcantara, basalto",             "Alcantara Gorge, Sicily, black basalt columns, crystal river, canyon"),
    ("🇮🇹 · Sicilia, Cefalù, Duomo normanno",                 "Cefalù Norman Cathedral, Sicilian beach, golden stone, turquoise sea"),
    ("🇮🇹 · Sicilia, Erice, castello normanno nella nebbia",  "Erice, Sicily, Norman castle above clouds, medieval stone, dramatic mist"),
    ("🇮🇹 · Sicilia, Lampedusa, Isola dei Conigli",           "Lampedusa Isola dei Conigli beach, crystalline turquoise water, white sand"),
    ("🇮🇹 · Sicilia, Messina, Duomo e orologio astronomico",  "Messina Cathedral, Gothic facade, astronomical clock tower, Sicily, blue sky"),
    ("🇮🇹 · Sicilia, Noto, barocco siciliano",                "Noto baroque cathedral, golden limestone facade, Sicily, warm afternoon"),
    ("🇮🇹 · Sicilia, Scala dei Turchi, scogliera bianca",     "Scala dei Turchi, Sicily, white marlstone cliff steps, azure sea"),
    ("🇮🇹 · Sicilia, Siracusa, Ortigia, tempio greco",        "Syracuse Ortigia island, Greek temple columns, harbour at dusk"),
    ("🇮🇹 · Sicilia, Taormina, Teatro con Etna",              "Taormina Teatro Antico, Etna silhouette, Ionian sea below"),
    # Toscana
    ("🇮🇹 · Toscana, Certaldo Alto, borgo medievale",         "Certaldo Alto, medieval hilltop village, Tuscany, terracotta rooftops, cypress"),
    ("🇮🇹 · Toscana, Firenze, Cortile degli Uffizi",          "Florence Uffizi Gallery courtyard, Renaissance archways, morning light"),
    ("🇮🇹 · Toscana, Firenze, Giardino di Boboli",            "Boboli Gardens, Florence, baroque terraces, cypress alleys, afternoon"),
    ("🇮🇹 · Toscana, Firenze, Piazzale Michelangelo",         "Florence Piazzale Michelangelo, Duomo panorama, warm sunset"),
    ("🇮🇹 · Toscana, Firenze, Ponte Vecchio",                 "Florence Ponte Vecchio, Arno river reflection, golden dusk"),
    ("🇮🇹 · Toscana, Lucca, mura rinascimentali",             "Lucca Renaissance city walls, medieval towers, tree-lined ramparts, Tuscany"),
    ("🇮🇹 · Toscana, Pisa, Piazza dei Miracoli",              "Pisa Piazza dei Miracoli, Leaning Tower, marble cathedral, green lawn"),
    ("🇮🇹 · Toscana, San Gimignano, torri medievali",         "San Gimignano medieval towers, Tuscany skyline, golden afternoon"),
    ("🇮🇹 · Toscana, Siena, Piazza del Campo",                "Siena Piazza del Campo, shell-shaped square, medieval tower, dusk"),
    ("🇮🇹 · Toscana, Val d'Orcia, cipressi nella nebbia",     "Val d'Orcia, Tuscany, cypress avenue, morning mist, rolling hills"),
    ("🇮🇹 · Toscana, Volterra, rupe tufacea",                 "Volterra Etruscan ramparts, alabaster town, tufa cliff, Tuscan panorama"),
    # Umbria
    ("🇮🇹 · Umbria, Assisi, Basilica di San Francesco",       "Assisi Basilica di San Francesco, pink stone, Umbrian valley panorama"),
    ("🇮🇹 · Umbria, Orvieto, Duomo sulla rupe",               "Orvieto Duomo, striped Gothic facade, tufa cliff edge, dramatic sky"),
    ("🇮🇹 · Umbria, Perugia, Fontana Maggiore",               "Perugia Piazza IV Novembre, Gothic Fontana Maggiore, hilltop city, dusk"),
    ("🇮🇹 · Umbria, Urbino, Palazzo Ducale",                  "Urbino Palazzo Ducale courtyard, Renaissance architecture, warm stone"),
    # Valle d'Aosta e Dolomiti
    ("🇮🇹 · Valle d'Aosta, Forte di Bard",                    "Forte di Bard, Valle d'Aosta, dramatic medieval fortress, mountain pass"),
    ("🇮🇹 · Dolomiti, Alpe di Siusi, prato all'alba",         "Alpe di Siusi, Dolomites, alpine meadow at dawn, pink rock peaks"),
    ("🇮🇹 · Dolomiti, Lago di Braies, foresta di pini",       "Lago di Braies, Dolomites, emerald alpine lake, pine forest, reflection"),
    ("🇮🇹 · Dolomiti, Tre Cime di Lavaredo",                  "Dolomites Tre Cime di Lavaredo, dramatic rock spires, clear sky"),
    # Veneto
    ("🇮🇹 · Veneto, Asolo, borgo medievale",                  "Asolo, Veneto, medieval hilltop village, castle ruins, rolling hills, morning"),
    ("🇮🇹 · Veneto, Lago di Garda, Sirmione",                 "Lake Garda Sirmione castle, clear water, medieval towers"),
    ("🇮🇹 · Veneto, Padova, Prato della Valle",               "Padova Prato della Valle, elliptical square, statues, canal, afternoon"),
    ("🇮🇹 · Veneto, Venezia, Arsenale",                       "Venice Arsenale entrance, monumental brick arches, still water"),
    ("🇮🇹 · Veneto, Venezia, Burano, case colorate",          "Venice Burano island, vivid painted houses, canal reflections"),
    ("🇮🇹 · Veneto, Venezia, Ca' d'Oro, Canal Grande",        "Venice Ca' d'Oro palazzo, Grand Canal, ornate Gothic facade"),
    ("🇮🇹 · Veneto, Venezia, Piazza San Marco all'alba",      "Venice Piazza San Marco at dawn, empty square, mist on water"),
    ("🇮🇹 · Veneto, Venezia, Ponte di Rialto",                "Venice Rialto Bridge, Grand Canal below, market arches, morning light"),
    ("🇮🇹 · Veneto, Venezia, San Giorgio Maggiore",           "San Giorgio Maggiore island church, Venice lagoon, misty dawn"),
    ("🇮🇹 · Veneto, Verona, Arena romana",                    "Verona Roman Arena, Piazza Bra, warm stone, golden evening light"),
    ("🇮🇹 · Veneto, Vicenza, Basilica Palladiana",            "Basilica Palladiana, Vicenza, Palladian arches, Piazza dei Signori, golden hour"),
    ("🇮🇹 · Maratea, Cristo Redentore, Tirreno",              "Maratea, Cristo Redentore statue, Tyrrhenian sea panorama, dramatic cliff"),
    ("🇮🇹 · Basilicata, Matera, chiese rupestri",             "Matera cave churches, Sassi rupestri, dramatic canyon, candlelight golden hour"),
    ("🇮🇹 · Marche, Urbino, Palazzo Ducale e logge",          "Urbino Palazzo Ducale, Renaissance ducal palace, hilltop city, warm stone afternoon"),
    # ══ 🇵🇹 PORTOGALLO ═══════════════════════════════════════
    # Azzorre
    ("🇵🇹 · Azzorre, Caldeira do Faial, cratere",             "Caldeira do Faial, Azores, volcanic crater, wild vegetation, mist"),
    ("🇵🇹 · Azzorre, Flores, cascata Poço do Bacalhau",       "Poço do Bacalhau waterfall, Flores, Azores, lush canyon, turquoise pool"),
    ("🇵🇹 · Azzorre, Lagoa do Fogo, vetta",                   "Lagoa do Fogo, São Miguel, Azores, volcanic summit lake, clear sky"),
    ("🇵🇹 · Azzorre, Porto Pim, baia a mezzaluna",            "Porto Pim beach, Faial, Azores, crescent bay, volcanic backdrop"),
    ("🇵🇹 · Azzorre, Sete Cidades, laghi gemelli",             "Sete Cidades, São Miguel, twin crater lakes, volcanic green rim"),
    ("🇵🇹 · Azzorre, sorgenti termali di Furnas",              "Furnas thermal springs, São Miguel, Azores, steam rising, lush green"),
    # Lisbona
    ("🇵🇹 · Lisbona, Alfama, Portas do Sol",                  "Lisbon Alfama viewpoint Portas do Sol, terracotta rooftops, sunset"),
    ("🇵🇹 · Lisbona, Castello di São Jorge",                  "Lisbon São Jorge Castle ramparts, city panorama, blue sky"),
    ("🇵🇹 · Lisbona, Chiado, tram e azulejos",                "Lisbon Chiado neighbourhood, yellow tram, azulejo-tiled facades, morning"),
    ("🇵🇹 · Lisbona, Jerónimos, archi manueline",             "Lisbon Jerónimos Monastery cloister, Manueline stone arches"),
    ("🇵🇹 · Lisbona, LX Factory, industriale chic",           "Lisbon LX Factory, repurposed industrial space, street art, Sunday market"),
    ("🇵🇹 · Lisbona, Miradouro da Graça, crepuscolo",         "Lisbon Miradouro da Graça, fado atmosphere, golden dusk"),
    ("🇵🇹 · Lisbona, Torre di Belém",                         "Lisbon Belém Tower, Tagus river mouth, warm afternoon light"),
    # Madeira
    ("🇵🇹 · Madeira, Cabo Girão, scogliera vertiginosa",      "Madeira Cabo Girão, one of world highest sea cliffs, Atlantic panorama"),
    ("🇵🇹 · Madeira, Funchal, mercato dei fiori",             "Funchal, Madeira, covered flower market, tropical colours, morning bustle"),
    ("🇵🇹 · Madeira, Levada do Caldeirão Verde",              "Levada do Caldeirão Verde, Madeira, lush laurisilva forest, misty path"),
    ("🇵🇹 · Madeira, Pico do Arieiro, nuvole sotto i piedi",  "Pico do Arieiro, Madeira, volcanic summit above clouds, dramatic sunrise"),
    ("🇵🇹 · Madeira, Ponta de São Lourenço, costa",           "Ponta de São Lourenço, Madeira, rugged volcanic coastline, Atlantic crashing"),
    # Norte e Centro
    ("🇵🇹 · Aveiro, canali e barche moliceiro",               "Aveiro canals, painted moliceiro boats, Art Nouveau facades, colourful"),
    ("🇵🇹 · Batalha, Monastero gotico",                       "Mosteiro da Batalha, Portugal, Gothic lace stonework, royal pantheon, afternoon"),
    ("🇵🇹 · Braga, Bom Jesus, scalinata barocca",             "Bom Jesus do Monte, Braga, baroque zigzag staircase, pilgrimage church"),
    ("🇵🇹 · Cascais, porto dei pescatori",                     "Cascais fishing harbour, whitewashed walls, Atlantic light"),
    ("🇵🇹 · Cascais, Boca do Inferno, scogliere",             "Cascais Boca do Inferno, dramatic sea cliffs, crashing Atlantic waves"),
    ("🇵🇹 · Coimbra, Università, Biblioteca Joanina",          "Coimbra University, Biblioteca Joanina, baroque gilded interior, warm glow"),
    ("🇵🇹 · Comporta, dune selvagge, Atlantico",              "Comporta whitewashed beach shack, wild dunes, Atlantic light"),
    ("🇵🇹 · Évora, cappella delle Ossa",                      "Évora Chapel of Bones, candlelight, dramatic interior"),
    ("🇵🇹 · Évora, tempio romano, pianura alentejana",         "Évora Roman temple columns, warm stone, Alentejo plains beyond"),
    ("🇵🇹 · Guimarães, castello medievale",                    "Guimarães medieval castle, birthplace of Portugal, granite walls, green hills"),
    ("🇵🇹 · Monsaraz, borgo in cima, lago Alqueva",            "Monsaraz hilltop village, Alqueva lake reflection, pink dusk"),
    ("🇵🇹 · Óbidos, borgo medievale e bouganville",            "Óbidos medieval walled village, cobblestones, bougainvillea"),
    ("🇵🇹 · Peneda-Gerês, cascate e granito",                  "Peneda-Gerês National Park, granite waterfall, oak forest, misty morning"),
    ("🇵🇹 · Ponte de Lima, ponte romanico",                    "Ponte de Lima, oldest town in Portugal, Roman bridge, Lima river, afternoon"),
    ("🇵🇹 · Porto, Livraria Lello, scala Art Nouveau",         "Porto Livraria Lello bookshop, neo-Gothic staircase, stained glass ceiling"),
    ("🇵🇹 · Porto, Ponte Dom Luís, ora dorata",                "Porto Dom Luís I iron bridge, double-decker, city at golden hour"),
    ("🇵🇹 · Porto, Ribeira, azulejos e Douro",                 "Porto Ribeira waterfront, azulejo facades, Douro river at dusk"),
    ("🇵🇹 · Porto, Stazione São Bento, murales",               "Porto São Bento railway station, azulejo tile murals, morning light"),
    ("🇵🇹 · Porto, Torre dei Clérigos",                        "Porto Clérigos Tower, baroque granite, rooftop city panorama, dusk"),
    ("🇵🇹 · Sagres, Fortezza, scogliere atlantiche",           "Sagres Fortress, Cabo de São Vicente, Atlantic cliffs, dramatic wind"),
    ("🇵🇹 · Setúbal, Arrábida, caletta smeraldo",              "Arrábida Natural Park, Setúbal, dramatic white limestone cliffs, emerald sea"),
    ("🇵🇹 · Sintra, Castello Moresco",                         "Sintra Moorish Castle walls, eucalyptus forest, Atlantic horizon"),
    ("🇵🇹 · Sintra, Palazzo della Pena",                       "Sintra Pena Palace ramparts, coloured towers, forested hills"),
    ("🇵🇹 · Sintra, Palazzo di Monserrate",                    "Sintra Monserrate Palace, romantic neo-Gothic, exotic garden, morning"),
    ("🇵🇹 · Sintra, Quinta da Regaleira, pozzo",               "Sintra Quinta da Regaleira, mystical well, moss-covered stonework"),
    ("🇵🇹 · Tavira, ponte romano e saline",                    "Tavira, Algarve, Roman bridge, salt marshes, flamingos, warm dusk"),
    ("🇵🇹 · Tomar, Convento de Cristo, Templari",              "Convento de Cristo, Tomar, Templar round church, Manueline window"),
    ("🇵🇹 · Valle del Douro, vigneti a terrazze",              "Douro Valley terraced vineyards, river bend, harvest golden light"),
    ("🇵🇹 · Viana do Castelo, Basilica di Santa Luzia",        "Santa Luzia Basilica, Viana do Castelo, hilltop, Lima river panorama"),
    # Algarve
    ("🇵🇹 · Algarve, archi di Ponta da Piedade",              "Algarve Ponta da Piedade sea arches, turquoise water, boat below"),
    ("🇵🇹 · Algarve, Lagos, Praia do Camilo",                  "Praia do Camilo, Lagos, golden cliffs, turquoise inlet, wooden steps"),
    ("🇵🇹 · Algarve, Praia da Marinha, formazioni rocciose",   "Praia da Marinha, Algarve, ochre rock formations, secret cove"),
    # ══ 🌍 EUROPA ════════════════════════════════════════════
    ("🇨🇿 · Rep. Ceca, Praga, orologio astronomico",           "Prague Old Town Square, astronomical clock, Gothic spires, dusk"),
    ("🇩🇪 · Germania, Neuschwanstein, foresta alpina",         "Neuschwanstein Castle, Bavaria, fairytale towers, alpine forest, clouds"),
    ("🇪🇸 · Spagna, Alhambra, cortile moresco",                "Alhambra Nasrid Palaces courtyard, Granada, Moorish arches, reflection"),
    ("🇪🇸 · Spagna, Sagrada Família, navata di vetro",         "Sagrada Família nave interior, Barcelona, stained glass light forest"),
    ("🇫🇷 · Francia, Mont Saint-Michel, isola di marea",       "Mont Saint-Michel, Normandy, tidal island monastery, low tide sand"),
    ("🇫🇷 · Francia, Versailles, Galleria degli Specchi",      "Versailles Hall of Mirrors, France, golden chandeliers, garden axis"),
    ("🇬🇧 · Inghilterra, Stonehenge, nebbia all'alba",         "Stonehenge, Wiltshire, megalithic circle, dawn mist, rising sun"),
    ("🇬🇷 · Grecia, Atene, Acropoli e Partenone",              "Parthenon Acropolis, Athens, marble columns, city below, golden hour"),
    ("🇬🇷 · Grecia, Meteore, monasteri sulle rocce",           "Meteora monasteries, Greece, rock pinnacles, Byzantine churches, dawn"),
    ("🇬🇷 · Grecia, Santorini Oia, caldera",                   "Santorini Oia village, white cubic houses, caldera, Aegean sunset"),
    ("🇭🇷 · Croazia, Dubrovnik, mura sull'Adriatico",          "Dubrovnik Old City walls, Adriatic panorama, red rooftops, sunset"),
    ("🇸🇨 · Scozia, Castello di Edimburgo",                    "Edinburgh Castle esplanade, Scotland, dramatic rock, city below"),
    ("🇹🇷 · Turchia, Cappadocia, camini delle fate",           "Cappadocia Göreme valley, Turkey, hot air balloons, fairy chimneys"),
    ("🇹🇷 · Turchia, Pamukkale, piscine di travertino",        "Pamukkale travertine terraces, Turkey, white mineral pools, sunset"),
    # ══ 🌍 AFRICA E MEDIO ORIENTE ════════════════════════════
    ("🇪🇬 · Egitto, Abu Simbel, statue colossali",             "Abu Simbel temple facade, Egypt, colossal statues, Nubian sunrise"),
    ("🇪🇬 · Egitto, Piramidi di Giza",                         "Giza Pyramids, Egypt, desert plateau, dramatic sky, camel silhouette"),
    ("🇪🇬 · Egitto, Tempio di Karnak, colonne scolpite",       "Karnak Temple columns, Luxor, Egypt, massive hieroglyph-carved pillars"),
    ("🇯🇴 · Giordania, Petra, canyon del Siq",                 "Petra Siq narrow canyon, Jordan, towering rock walls, filtered light"),
    ("🇯🇴 · Giordania, Petra, facciata del Tesoro",            "Petra Treasury facade, Jordan, rose-red sandstone, dawn light"),
    ("🇲🇦 · Marocco, Chefchaouen, medina blu",                 "Chefchaouen blue medina, Morocco, cobalt alleyways, terracotta pots"),
    ("🇲🇦 · Marocco, Marrakech, Djemaa el-Fna",               "Djemaa el-Fna square, Marrakech, lanterns, Atlas mountains horizon"),
    ("🇳🇦 · Namibia, Sossusvlei, dune rosse",                  "Sossusvlei red dunes, Namib desert, Dead Vlei white clay, clear sky"),
    ("🇿🇼 · Zimbabwe, Cascate Vittoria",                        "Victoria Falls, Zimbabwe/Zambia, smoke that thunders, rainbow mist"),
    # ══ 🌏 ASIA ══════════════════════════════════════════════
    ("🇨🇳 · Cina, Città Proibita, Pechino",                    "Forbidden City, Beijing, vermillion gates, imperial courtyard"),
    ("🇨🇳 · Cina, Esercito di Terracotta, Xi'an",              "Terracotta Army pits, Xi'an, China, rows of warrior figures, amber light"),
    ("🇨🇳 · Cina, Grande Muraglia, Jinshanling",               "Great Wall of China, Jinshanling, autumn foliage, golden light"),
    ("🇮🇳 · India, Hampi, rovine tra i massi",                 "Hampi boulder landscape, Karnataka, India, ancient ruins, golden dusk"),
    ("🇮🇳 · India, Jaipur, Hawa Mahal",                        "Hawa Mahal, Jaipur, India, pink sandstone facade, honeycomb windows"),
    ("🇮🇳 · India, Taj Mahal, vasca riflettente",              "Taj Mahal at sunrise, Agra, India, reflection pool, pink sky"),
    ("🇮🇳 · India, Varanasi, Gange al tramonto",               "Varanasi, Ganges river, ritual ghats at sunset, candles floating, mist"),
    ("🇯🇵 · Giappone, Kyoto, bosco di bambù Arashiyama",       "Arashiyama bamboo grove, Kyoto, towering green culms, filtered light"),
    ("🇯🇵 · Giappone, Kyoto, torii di Fushimi Inari",          "Fushimi Inari shrine, Kyoto, endless red torii gates, misty forest path"),
    ("🇯🇵 · Giappone, Monte Fuji, fiori di ciliegio",          "Mount Fuji, Japan, cherry blossom foreground, Kawaguchiko lake reflection"),
    ("🇰🇭 · Cambogia, Angkor Wat, stagno di loto",             "Angkor Wat main causeway, Cambodia, lotus pond reflection, sunrise"),
    ("🇰🇭 · Cambogia, Bayon, volti di pietra",                 "Angkor Thom Bayon temple, Cambodia, stone faces, jungle canopy"),
    ("🇲🇲 · Myanmar, Bagan, pagode e mongolfiere",             "Bagan temple plain, Myanmar, hot air balloons at dawn, misty pagodas"),
    ("🇻🇳 · Vietnam, Baia di Halong, picchi carsici",          "Halong Bay limestone karsts, Vietnam, emerald water, fishing boats mist"),
    # ══ 🌎 AMERICHE ══════════════════════════════════════════
    ("🇦🇷 · Argentina, Cascate di Iguazú",                     "Iguazu Falls panorama, Argentina/Brazil border, jungle mist, cascades"),
    ("🇧🇷 · Brasile, Baia do Sancho, Fernando de Noronha",     "Baia do Sancho, Fernando de Noronha, Brazil, lush cliff, turquoise"),
    ("🇨🇱 · Cile, Isola di Pasqua, moai",                     "Easter Island Ahu Tongariki, Chile, moai row, ocean sunrise"),
    ("🇲🇽 · Messico, Chichen Itza, El Castillo",               "Chichen Itza El Castillo pyramid, Mexico, equinox light, shadow serpent"),
    ("🇵🇪 · Perù, Machu Picchu, alba andina",                  "Machu Picchu citadel, Peru, Andean peaks above clouds, sunrise"),
    ("🇺🇸 · USA, Arizona, Antelope Canyon",                    "Antelope Canyon slot canyon, Arizona, light beams, swirling sandstone"),
    ("🇺🇸 · USA, Arizona, Monument Valley",                    "Monument Valley buttes, Arizona, red mesa silhouettes, sunset"),
    ("🇺🇸 · USA, Arizona, Grand Canyon",                       "Grand Canyon South Rim, Arizona, layered red rock, golden hour"),
    ("🇺🇸 · USA, Niagara Falls, arcobaleno",                   "Niagara Falls Horseshoe, Canada, rainbow mist, thundering water"),
    # ══ 🌊 OCEANIA E SPIAGGE MONDIALI ════════════════════════
    ("🇦🇺 · Australia, Whitsundays, Whitehaven Beach",         "Whitehaven Beach, Whitsundays, Australia, pure silica white sand"),
    ("🇵🇭 · Filippine, El Nido, lagune carsiche",              "El Nido, Palawan, Philippines, limestone karst islands, turquoise lagoon"),
    ("🇸🇨 · Seychelles, Anse Source d'Argent",                 "Anse Source d'Argent, La Digue, Seychelles, granite boulders, pink sand"),
    ("🇹🇭 · Thailandia, Maya Bay, scogliere carsiche",         "Maya Bay, Phi Phi Islands, Thailand, limestone cliffs, emerald water"),
]

# --- OUTFIT POOL (100) ---
# Ordinamento: Beachwear → Mini Dress → Futurista → Retrò '20 → Retrò '70 → Avanguardia/Scenografico → Costumi/Teatrali → Film Iconici
# All'interno di ogni sezione: alfabetico per stilista, poi colore
# Esclusi: abiti lunghi/maxi/midi, pantaloni, shorts, indumenti maschili, safety risk (lingerie, fishnet, barely-there, spray-on)
OUTFIT_POOL = [
    # ── BEACHWEAR (13) ───────────────────────────────────────
    ("Alaia · cut-out one-piece · ivory white",          "ivory white one-piece Alaia swimsuit, deep V front, cut-out waist, high cut legs, white slide sandals, gold cuff"),
    ("Dolce Gabbana · push-up bikini · black",           "black Dolce Gabbana push-up bikini, gold logo charm at hip, black lace sarong, gold stiletto sandals, bold hoops"),
    ("Eres · bandeau high-cut bikini · electric turquoise","electric turquoise Eres bandeau bikini, high-cut bottoms, sheer turquoise pareo tied low, tan espadrille wedges"),
    ("Eres · sporty bandeau bikini · forest green",      "forest green Eres sporty bandeau crop-top bikini, high-rise briefs, linen shirt open over shoulders, tan espadrilles, tortoiseshell sunglasses"),
    ("Gottex · halter bikini · electric fuchsia",        "electric fuchsia Gottex halter bikini, underwire top, high-waist bottoms, fuchsia slides, layered gold necklaces"),
    ("Hunza G · crinkle bikini · cobalt blue",           "cobalt blue Hunza G crinkle bikini, ruched top, matching crinkle shorts, cobalt espadrilles, silver anklet"),
    ("La Perla · high-leg one-piece · forest green",     "forest green La Perla high-leg one-piece, structured bust, low back, gold hardware rings, tan leather slides"),
    ("La Perla · triangle string bikini · crimson",      "crimson La Perla triangle string bikini, minimal coverage, red cord ties, gold anklet, oversized black sunglasses"),
    ("Melissa Odabash · halter one-piece · turquoise",   "turquoise Melissa Odabash structured halter one-piece, ruched front panel, moderate coverage, gold ring detail, metallic flat sandals"),
    ("Missoni · crochet bikini · deep coral",            "deep coral Missoni crochet bikini, fringe hem bottoms, matching crochet cover-up, tan flat sandals, shell earrings"),
    ("Odabash · string bikini · bronze metallic",        "bronze metallic Melissa Odabash string bikini, wide-brim bronze hat, tan leather thong sandals, layered gold chains"),
    ("Seafolly · bandeau bikini · sage green",           "sage green Seafolly bandeau bikini, tie-waist high-rise bottoms, sage linen shirt open, flat leather sandals"),
    ("Valentino · halter one-piece · pale lavender",     "pale lavender Valentino one-piece, plunging halter neck, tie-side, lavender slides, amethyst bracelet"),
    ("Versace · structured one-piece · hot pink gold",   "hot pink Versace structured one-piece, gold Greek key trim, plunging neckline, gold stiletto sandals, statement gold hoops"),
    ("Vilebrequin · ruched bandeau · electric violet",   "electric violet Vilebrequin ruched bandeau bikini, high-rise briefs, matching sarong wrap, violet flat sandals, gold anklet"),
    ("Zimmermann · print one-piece · tropical coral",    "tropical coral Zimmermann printed plunge one-piece, side cut-out, ruched front panel, cork wedge sandals, gold ring earrings"),
    ("Eres · bandeau high-cut · ivory white",            "ivory white Eres sporty bandeau high-cut bikini, sculpted top, clean minimal lines, white wrap pareo, gold flat sandals, oversized sunglasses"),
    ("Gottex · underwire one-piece · bold red",          "bold red Gottex structured underwire one-piece, high cut legs, low back, gold ring hardware at hip, red wedge espadrilles, gold cuff"),
    # ── MINI DRESS (19) ──────────────────────────────────────
    ("Balmain · sequined mini · electric cobalt",        "electric cobalt sequined Balmain mini dress, plunging V neckline, structured shoulders, cobalt strappy heels, gold ear cuffs"),
    ("Chanel · tweed micro dress · cream black",         "cream and black Chanel tweed micro dress, structured skirt, gold chain trim, low-cut neckline, black cap-toe pumps, pearl bracelet"),
    ("Chloe · broderie strapless · terracotta",          "terracotta Chloe broderie strapless mini, frayed hem, raw edges, tan leather block heels, hammered gold cuffs"),
    ("Christopher Kane · lace-panel mini · ivory",       "ivory Christopher Kane lace-panel micro mini, sheer geometric inserts, structured bodice, nude platform heels, pearl cluster earrings"),
    ("Coperni · cut-out mini · steel grey",              "steel grey Coperni cut-out mini, architectural cutaways at waist, perspex block heels, silver ear climbers"),
    ("Givenchy · structured mini · powder lilac",        "powder lilac Givenchy structured boxy mini, stiff sculpted silhouette, architectural seams, lilac pointed pumps, geometric silver earrings"),
    ("Herve Leger · bandage mini · ice blue",            "ice blue Herve Leger bandage mini, wrap neckline, body-sculpting seams, powder blue platform heels, crystal ear studs"),
    ("Jacquemus · asymmetric micro · acid yellow",       "acid yellow Jacquemus asymmetric micro mini, single draped strap, bare shoulders, nude pointed mules, gold chain necklace"),
    ("Miu Miu · crystal-trim micro · baby pink",         "baby pink Miu Miu crystal-embellished micro mini, rhinestone-trimmed raw hem, cropped top, pink satin mules, crystal barrette"),
    ("Mugler · spiral seam mini · jade green",           "jade green Mugler spiral-seam bodycon mini, precision-cut curved seams, high neck, black stiletto ankle boots, no jewellery"),
    ("Nensi Dojaka · micro asymmetric · midnight black", "midnight black Nensi Dojaka asymmetric micro dress, sheer panels, delicate straps, black perspex heels, no jewellery"),
    ("Paco Rabanne · disc mini · gold metallic",         "gold metallic disc-chain Paco Rabanne mini dress, linked metal discs, gold stiletto sandals, no other jewellery"),
    ("Poster Girl · crystal mesh mini · silver",         "silver crystal-mesh Poster Girl micro mini, bodycon, all-over rhinestones, silver ankle-strap heels"),
    ("Retrofete · sequined mini · bright coral",         "bright coral Retrofete sequined mini, plunging V, spaghetti straps, coral stiletto sandals, gold stacking rings"),
    ("Rick Owens · draped one-shoulder · electric violet","electric violet Rick Owens draped mini, asymmetric one-shoulder, thigh slit, violet pointed pumps, silver cuff"),
    ("Self-Portrait · lace mini · deep burgundy",        "deep burgundy Self-Portrait lace mini, plunging back, long sleeves, wine-red strappy heels, pearl choker"),
    ("Tom Ford · velvet mini · deep ruby",               "deep ruby Tom Ford velvet micro mini, plunging V neckline, long sleeves, ruby satin stilettos, single diamond drop earring"),
    ("Valentino · ruffled mini · hot magenta",           "hot magenta Valentino ruffled mini dress, sweetheart neckline, bare shoulders, fuchsia satin heels, diamond tennis bracelet"),
    ("Vauthier · strapless bodycon · burnt orange",      "burnt orange Alexandre Vauthier strapless bodycon mini, ruched bust, high slit, nude pointed pumps, gold bangles"),
    ("Versace · micro mini · deep forest green",         "deep forest green Versace micro mini, plunging neckline, gold Medusa hardware, black strappy sandals, statement gold hoops"),
    ("Zimmermann · broderie off-shoulder · dusty rose",  "dusty rose Zimmermann broderie anglaise off-shoulder mini, tiered hem, blush wedge sandals, pearl drop earrings"),
    ("Acne Studios · asymmetric wrap mini · electric teal","electric teal Acne Studios asymmetric wrap mini, draped one-shoulder, thigh slit, teal patent heels, single chain earring"),
    ("Bottega Veneta · knit micro · caramel",            "caramel Bottega Veneta intrecciato knit micro dress, low scoop back, fitted, tan leather block heels, tortoiseshell cuff"),
    ("Dior · New Look micro · navy midnight",            "navy midnight Dior Bar-inspired micro, structured nipped waist, flared mini skirt, navy pointed pumps, pearl choker, white gloves"),
    ("Isabel Marant · slip micro · warm amber",          "warm amber Isabel Marant silk slip micro, bias-cut, thin spaghetti straps, plunging back, amber flat sandals, layered gold chains"),
    ("Nanushka · draped mini · dusty lilac",             "dusty lilac Nanushka draped satin mini, gathered at hip, one-shoulder asymmetric, lilac heeled mules, simple pearl stud"),
    # ── ESTIVI / LEGGEREZZA (4) ──────────────────────────────
    ("Agua Bendita · off-shoulder ruffle · hot tangerine","hot tangerine Agua Bendita off-shoulder ruffle mini, smocked bodice, cork wedge sandals, gold layered chains"),
    ("Alaia · laser-cut bodycon · deep violet",          "deep violet Alaia laser-cut bodycon, geometric openwork revealing skin, violet patent heels, single silver cuff"),
    ("Bottega Veneta · slip dress · moss green",         "moss green Bottega Veneta intrecciato-detail slip dress, cowl back, bare shoulders, tan leather mules, gold cuff"),
    ("Faithfull · broderie sundress · powder blue",      "powder blue Faithfull the Brand broderie sundress, mini length, puff sleeves, white block heels, pearl studs"),
    # ── FUTURISTA / SCI-FI (10) ──────────────────────────────
    ("Balenciaga · inflated cocoon · neon orange",       "neon orange Balenciaga inflated cocoon silhouette mini dress, sculptural volume, matching orange boots, minimalist"),
    ("Courrèges · vinyl circle micro · chalk white",     "chalk white Courrèges vinyl circle-cut micro dress, geometric seaming, structured collar, white go-go boots, silver geometric earrings"),
    ("Iris van Herpen · 3D sculptural · electric lime",  "electric lime Iris van Herpen 3D-printed sculptural mini, bare arms, architectural platform heels, no jewellery"),
    ("Iris van Herpen · magnetic wave · iridescent",     "iridescent Iris van Herpen magnetic-wave mini, undulating 3D-printed panels, perspex platform heels, single ear antennae"),
    ("Issey Miyake · Pleats Please · neon chartreuse",   "neon chartreuse Issey Miyake Pleats Please micro dress, accordion pleats, geometric origami folds, flat white sandals, single sculptural cuff"),
    ("Marques Almeida · space-age mini · reflective",    "reflective mylar Marques Almeida space-age mini dress, crinkled metallic surface, silver platform sneakers"),
    ("Mugler · hourglass cut-out · matte black",         "matte black Mugler hourglass cut-out bodycon dress, spiral waist openings, sheer body panels, black stiletto boots"),
    ("Paco Rabanne · liquid mesh · molten copper",       "molten copper Paco Rabanne liquid chainmail mesh mini, plunging neckline, fluid drape, copper stiletto sandals, no jewellery"),
    ("Rick Owens · pod micro · dove grey",               "dove grey Rick Owens sculptural pod micro, asymmetric volume panel at hip, bare shoulders, white leather platform boots, no jewellery"),
    ("Versace · laser-cut vinyl · hot orange",           "hot orange Versace laser-cut vinyl mini dress, geometric perforations, orange patent heels, chrome hoops"),
    # ── RETRÒ ANNI '20 / ART DÉCO (5) ───────────────────────
    ("1920s · Charleston · champagne sequined",          "champagne sequined 1920s Charleston dancing dress, fringed hem, sleeveless, V back, champagne heels, rhinestone headpiece"),
    ("Art Deco · flapper · gold beaded",                 "gold beaded Art Deco flapper dress, fringe hem, dropped waist, intricate beadwork, T-strap gold heels, long pearl rope, feather headband"),
    ("Art Nouveau · drop-waist · midnight blue",         "midnight blue Art Nouveau beaded drop-waist dress, geometric Art Deco pattern, silver fringe, silver T-bar heels, feathered headpiece"),
    ("Gatsby · bias-cut satin · ivory",                  "ivory 1920s Gatsby-era bias-cut satin mini dress, cowl neckline, sparkling beaded shoulder straps, ivory heels, diamond headband"),
    ("Vionnet · silk charmeuse · pale gold",             "pale gold 1920s Vionnet-inspired silk charmeuse bias-cut mini, fluid drape, backless, gold sandals, long pearl necklace"),
    # ── RETRÒ ANNI '70 / GLAM ROCK / DISCO (5) ───────────────
    ("Biba · op-art mini · black white graphic",         "black and white Biba op-art geometric micro mini, bold graphic print, high neck, white platform ankle boots, round white sunglasses"),
    ("Biba · satin deep-V · burnt sienna",               "burnt sienna Biba 1970s satin deep-V halter disco mini, cowl front, bare back, platform sandals, long pendant earrings"),
    ("Halston · studio disco · liquid gold",             "liquid gold Halston 1970s studio disco halter dress, fluid jersey, one shoulder, bare back, gold platforms, hoop earrings"),
    ("Ossie Clark · crepe halter micro · rust orange",   "rust orange Ossie Clark crepe halter micro, draped cowl neck, open back, platform wooden sandals, amber bead necklace"),
    ("Pucci · bold graphic print · electric",            "electric Emilio Pucci 1970s bold graphic-print mini dress, signature swirling pattern, platform wedges, oversized sunglasses"),
    # ── AVANGUARDIA / SCENOGRAFIA (10) ───────────────────────
    ("Alexander McQueen · armadillo mini · black",       "black Alexander McQueen structural mini, dramatic winged shoulders, armour-like silhouette, McQueen armadillo platform heels"),
    ("Ann Demeulemeester · asymmetric micro · charcoal", "charcoal Ann Demeulemeester asymmetric draped micro, raw-edge hem, one bare shoulder, black strapped flat sandals, single cuff"),
    ("Balenciaga · hourglass mini · pitch black",        "pitch black Balenciaga extreme hourglass mini, exaggerated waist, structured skirt panel, black stiletto ankle boots, no jewellery"),
    ("Comme des Garcons · abstract sculpture · white",   "white Comme des Garcons conceptual abstract sculptural dress, exaggerated architectural form, asymmetric padded volumes, flat white shoes"),
    ("Dries Van Noten · velvet embroidered mini · emerald","emerald Dries Van Noten velvet micro mini, dense floral embroidery, jewel-tone beading, deep V back, green velvet heels, stacked rings"),
    ("Gareth Pugh · geometric metallic · chrome",        "chrome geometric Gareth Pugh metallic sculptural mini dress, angular panels, architectural construction, chrome platform boots"),
    ("Haider Ackermann · draped angular · bordeaux",     "bordeaux Haider Ackermann angular draped micro, sharp asymmetric hem, bias-cut crepe, bare back, bordeaux stiletto mules, ear cuff"),
    ("Jean Paul Gaultier · cone bra · gold",             "gold satin Jean Paul Gaultier iconic cone bra corset mini dress, structured pointed bust, gold stilettos, theatrical makeup"),
    ("Junya Watanabe · patchwork micro · indigo mix",    "indigo patchwork Junya Watanabe denim micro mini, mixed texture panels, deconstructed seams, white platform boots, no jewellery"),
    ("Maison Margiela · trompe l'oeil · nude illusion",  "nude illusion Maison Margiela trompe l'oeil micro, body-print fabric simulating bare skin beneath sheer panel, nude heels, minimalist"),
    # ── COSTUMI / TEATRALI (8) ────────────────────────────────
    ("Amazzone · armatura bronzea · hammered gold",      "hammered gold Amazon warrior fashion editorial, sculptural bronze-effect armour breastplate, micro leather skirt, gold gladiator sandals to knee, laurel headpiece"),
    ("Ashi Studio · feather-cape bodysuit · black",      "black Ashi Studio feathered dramatic cape bodysuit, cascading ostrich feathers, bare legs, black stilettos, no jewellery"),
    ("Butterfly · ombré silk micro · aurora borealis",   "aurora borealis ombré silk micro dress, theatrical fashion costume, iridescent teal to violet gradient, sculptural winged collar, crystal platform heels"),
    ("Dea Egiziana · pleated micro · white linen",       "white linen Egyptian priestess fashion micro, precision pleated fabric, wide gold pectoral collar, gold arm cuffs, flat gold sandals, kohl eyes"),
    ("Geisha · silk obi mini · ivory gold",              "contemporary fashion geisha-inspired ivory and gold silk micro dress, wide sculptural obi sash waistband, structured collar, ivory wooden platform sandals, gold kanzashi"),
    ("Odalisque · brocade cropped · ruby red",           "ruby red orientalist fashion micro, richly embroidered brocade bodice, layered silk skirt panels, jewelled belt, flat embroidered slippers, chandelier earrings"),
    ("Valchiria · metallic micro · silver frost",        "silver frost Norse goddess editorial fashion, metallic scale-pattern micro dress, structured shoulder guards, silver thigh-high boots, hammered silver circlet"),
    ("Vivienne Westwood · tartan corset · royal blue",   "royal blue tartan Vivienne Westwood corseted mini, structured boning, asymmetric bustle, platform shoes, punk accessories"),
    # ── FILM ICONICI (10) ────────────────────────────────────
    ("Barbarella · space vinyl · silver",                "silver Barbarella-style space-age vinyl micro outfit, structured breastplate, thigh-high boots, futuristic accessories, dramatic hair"),
    ("Black Swan · structured tutu · pure white",        "pure white structured Black Swan tutu bodysuit, fitted corseted bodice, sculpted tulle skirt, white satin pointe heels, feather crown headpiece"),
    ("Breakfast at Tiffany · LBD Givenchy · black",      "iconic black Givenchy Breakfast at Tiffany LBD, sleeveless column mini silhouette, opera gloves, tiara, pearl necklace, upswept hair"),
    ("Clueless · plaid micro · yellow black",            "yellow and black plaid Clueless micro mini skirt set, matching cropped blazer open, white knee socks, white platform Mary Janes, tiny backpack"),
    ("Cleopatra · pleated linen · white gold",           "white gold pleated Cleopatra-inspired linen wrap micro, wide metallic collar, gold ankle cuffs, flat gold sandals, kohl eye makeup"),
    ("Gentlemen Prefer Blondes · pink satin · hot pink", "hot pink Monroe Gentlemen Prefer Blondes strapless satin micro dress, structured sweetheart bust, pink satin gloves, diamond chandelier earrings, pink heels"),
    ("La Dolce Vita · strapless swimsuit · white",       "white La Dolce Vita-inspired strapless structured swimsuit, sculpted bustier top, Anita Ekberg silhouette, white kitten heels, pearl drop earrings"),
    ("Labyrinth · goblin queen · silver crystal",        "silver crystal Labyrinth goblin queen fashion editorial, structured crystal-studded mini bodice, dramatic silver cape collar, silver thigh-high boots, crystal crown"),
    ("Mad Max · studded micro · burnt metal",            "burnt metal Mad Max warrior fashion editorial, studded asymmetric micro leather dress, armoured shoulder detail, laced boots to knee, no jewellery"),
    ("Monroe · subway white dress · white",              "white halter pleated Marilyn Monroe subway dress, billowing skirt, white stiletto heels, diamond drop earrings"),
    ("Basic Instinct · white wrap mini · chalk white",   "chalk white Basic Instinct-inspired structured wrap mini dress, sharp lapels, belted waist, white stiletto heels, no jewellery, icy gaze"),
    ("Metropolis · machine-woman · polished silver",     "polished silver Fritz Lang Metropolis-inspired fashion editorial bodysuit, riveted metal panels, structured breast plate, silver thigh-high boots, silver crown"),
    ("Pretty Woman · opera gown mini · scarlet red",     "scarlet red opera mini version of Pretty Woman strapless structured dress, corseted bodice, full mini skirt, red satin heels, long gloves, diamond drop earrings"),
    ("Zoolander · silver space disco · chrome",          "chrome silver Zoolander-inspired space disco micro dress, metallic sheen, structured shoulders, silver platform boots, dramatic silver eye makeup"),
]

STYLE_POOL = [
    ("Helmut Newton · glamour in bianco e nero",    "Helmut Newton, glamorous monochrome editorial"),
    ("Guy Bourdin · surrealismo saturo",             "Guy Bourdin, saturated surrealist fashion photography"),
    ("Richard Avedon · movimento dinamico",          "Richard Avedon, dynamic high-fashion movement"),
    ("Irving Penn · studio pulito e senza tempo",   "Irving Penn, clean studio portraiture, timeless elegance"),
    ("Peter Lindbergh · cinema naturale",            "Peter Lindbergh, cinematic naturalistic beauty"),
    ("Herb Ritts · scultura in bianco e nero",       "Herb Ritts, sculptural black and white photography"),
    ("Annie Leibovitz · ritratto narrativo",         "Annie Leibovitz, narrative cinematic portraiture"),
    ("Mario Testino · glossy vibrante",              "Mario Testino, vibrant glossy fashion photography"),
    ("Paolo Roversi · morbidezza pittorica",         "Paolo Roversi, painterly soft-focus romanticism"),
    ("David LaChapelle · pop art iperrealista",      "David LaChapelle, hyperrealistic pop art surrealism"),
    ("Nick Knight · avanguardia digitale",           "Nick Knight, avant-garde digital fashion imagery"),
    ("Steven Meisel · editoriale sofisticato",       "Steven Meisel, sophisticated high-fashion editorial"),
    ("Juergen Teller · realismo grezzo",             "Juergen Teller, raw unfiltered fashion realism"),
    ("Tim Walker · fantasy bizzarro",                "Tim Walker, fantastical whimsical fashion storytelling"),
    ("Miles Aldridge · iper-saturo cinematografico", "Miles Aldridge, cinematic hyper-saturated colour"),
    ("Ellen von Unwerth · glamour giocoso",          "Ellen von Unwerth, playful glamorous feminine energy"),
    ("Patrick Demarchelier · eleganza classica",     "Patrick Demarchelier, classic elegant fashion photography"),
    ("Bruce Weber · lifestyle soleggiato",           "Bruce Weber, sun-drenched American lifestyle photography"),
    ("Nan Goldin · documentario intimo",             "Nan Goldin, intimate documentary fashion realism"),
    ("Rinascimento italiano · pittura classica",     "Italian Renaissance painting style, Leonardo and Raphael composition, sfumato lighting, classical harmony"),
    ("Pittura orientale · Cina classica",            "classical Chinese ink painting style, mountain mist, silk textures, delicate brushwork, poetic atmosphere"),
    ("Ukiyo-e giapponese · stampa woodblock",        "Japanese Ukiyo-e woodblock print style, flat colour, bold outlines, decorative patterns, Edo period aesthetics"),
    ("Arte tribale · etnico contemporaneo",          "tribal ethnic contemporary art style, bold geometric patterns, earth pigments, ritual aesthetics, raw power"),
    ("Miniatura persiana · ornato islamico",         "Persian miniature painting style, gold leaf, intricate Islamic geometric border, jewel-like colours"),
    ("Art Nouveau · decorativo liberty",             "Art Nouveau style, flowing organic lines, floral motifs, Mucha-inspired decorative frame, pastel and gold"),
    ("Preraffaellita · romanticismo medievale",      "Pre-Raphaelite painting style, medieval romanticism, Rossetti and Millais aesthetic, jewel colours, narrative"),
    ("Espressionismo tedesco · angoscia drammatica", "German Expressionist style, dramatic distortion, Munch-like colour, psychological tension, raw brushwork"),
    ("Surrealismo onirico · sogno Dalì-Magritte",   "Surrealist dreamscape style, Dalì and Magritte influence, impossible juxtapositions, hyper-real detail"),
    ("Folklore slavo · oro e velluto",               "Slavic folk art style, ornate gold embroidery, rich velvet, Byzantine icon influence, jewelled headdress"),
    ("Bauhaus · geometria modernista",               "Bauhaus design aesthetic, geometric composition, primary colours, modernist grid, clean functional beauty"),
]

POSE_POOL = [
    ("Standing · hand on hip",              "standing upright, one hand on hip, chin slightly lifted"),
    ("Walking · toward camera",             "walking confidently toward camera, skirt in motion"),
    ("Leaning · wall, knee bent",           "leaning against wall, arms crossed, one knee bent"),
    ("Sitting · legs crossed, upright",     "sitting on edge of surface, legs crossed at ankle, back straight"),
    ("Reclining · on side, elbow",          "reclining on side, propped on elbow, legs extended"),
    ("Back to camera · over shoulder",      "standing back to camera, glancing over shoulder"),
    ("Floor · knees drawn up",              "seated on floor, knees drawn up, arms wrapped around legs"),
    ("Leaning forward · hands on thighs",   "leaning forward slightly, hands on thighs, direct gaze"),
    ("Side profile · arm on wall",          "standing side profile, one arm extended along wall"),
    ("Walking away · looking back",         "walking away, looking back, hair movement"),
    ("Steps · elbows on knees",             "sitting on steps, elbows on knees, chin resting on hands"),
    ("Arms raised · arched back",           "standing with arms raised overhead, arched back"),
    ("Railing · gazing at horizon",         "leaning on railing, one elbow resting, gazing at horizon"),
    ("Crouching · hands on ground",         "crouching low, knees apart, hands on ground between feet"),
    ("Wide stance · hands behind back",     "standing with legs wide apart, hands clasped behind back"),
    ("Chair · legs over armrest",           "seated on chair, legs draped over armrest, relaxed"),
    ("Lying · arms above head",             "lying on back, arms above head, legs slightly apart"),
    ("Doorway · hand on frame",             "standing in doorway, one hand on frame, body turned"),
    ("Spinning · skirt fanned out",         "spinning, skirt fanned out, captured mid-rotation"),
    ("Cross-legged · floor",               "seated cross-legged on floor, hands resting on knees"),
    ("One leg forward · hip shifted",       "standing with one leg forward, weight shifted to hip"),
    ("Leaning back · head tilted up",       "leaning back against surface, head tilted up, eyes closed"),
    ("Kneeling · one knee extended",        "kneeling on one knee, other leg extended, torso upright"),
    ("Hands in hair · elbows raised",       "standing with hands in hair, elbows raised"),
    ("Staircase · arm on banister",         "seated on staircase, turned sideways, arm on banister"),
    ("Walking sideways · trailing wall",    "walking sideways along wall, fingertips trailing surface"),
    ("Hand on chest · soft gaze",           "standing with one hand on chest, other at side, soft gaze"),
    ("Face down · legs bent up",            "lying face down, propped on forearms, legs bent upward"),
    ("Legs crossed · arms loose",           "standing with legs crossed at knee, arms loose at sides"),
    ("Water edge · feet dangling",          "seated at edge of water, feet dangling in"),
]

SKY_POOL = [
    ("Golden hour · warm amber",            "golden hour, warm amber light, long soft shadows"),
    ("Midday · harsh sun, sharp shadows",   "blue sky, harsh midday sun, sharp shadows"),
    ("Overcast · soft diffused light",      "overcast soft light, diffused, no shadows, milky sky"),
    ("Dusk · deep purple orange horizon",   "dramatic dusk, deep purple and orange horizon"),
    ("Night · full moon, silver-blue",      "clear night, full moon, silver-blue ambient light"),
    ("Sunrise · pale pink and gold",        "sunrise, pale pink and gold, delicate warm haze"),
    ("Stormy · dark clouds, pre-rain",      "stormy sky, dark clouds, electric pre-rain tension"),
    ("Magic hour · crimson and gold",       "magic hour, last light, sky deep crimson and gold"),
    ("Studio · bright white clinical",      "bright white studio light, clean and clinical"),
    ("Neon city night · wet pavement",      "neon city night, pink and blue reflections on wet pavement"),
    ("Candlelight · flickering amber",      "candlelight warm glow, intimate, flickering amber"),
    ("Underwater · caustic rays",           "underwater light, caustic rays, turquoise shimmer"),
    ("Foggy morning · cool mist",           "foggy morning, diffused cool light, soft mist"),
    ("Backlit · strong rim light",          "backlit silhouette, strong rim light, sun behind subject"),
    ("Blue hour · city lights emerging",    "blue hour, twilight, deep blue sky, city lights emerging"),
    ("Desert midday · bleached white",      "desert midday, bleached white light, stark and hot"),
    ("Autumn afternoon · low orange sun",   "autumn afternoon, warm orange, low angle sun through leaves"),
    ("Winter light · cold blue tones",      "crystal clear winter light, cold blue tones, sharp and clean"),
    ("Tropical noon · vivid saturated",     "tropical noon, vivid saturated colors, intense shadows"),
    ("Venetian afternoon · light off water","Venetian afternoon, warm reflected light off water"),
    ("Opera house · warm spotlights",       "opera house interior, dramatic warm spotlights"),
    ("Penthouse night · city glow",         "penthouse night, city glow from below, skyline backdrop"),
    ("Rainy evening · wet street",          "rainy evening, grey sky, reflections on wet street"),
    ("Greenhouse · green diffused light",   "greenhouse light, soft diffused green-tinted natural light"),
    ("Mediterranean afternoon · golden",    "late afternoon Mediterranean, golden haze, warm and sleepy"),
    ("Rooftop sunset · pink to violet",     "rooftop at sunset, sky gradient pink to violet"),
    ("Beach morning · cool early light",    "early morning beach, cool light, long shadows on sand"),
    ("Ballroom · crystal chandeliers",      "grand ballroom chandeliers, warm crystal light from above"),
    ("Snow · white reflected, cold blue",   "snowy exterior, pure white reflected light, cold blue shadows"),
    ("Poolside · white reflections",        "poolside afternoon, bright white reflections off water surface"),
]

MOOD_POOL = [
    ("Sophisticated · untouchable",         "sophisticated and untouchable"),
    ("Playful · irreverent",                "playful and irreverent"),
    ("Mysterious · alluring",               "mysterious and alluring"),
    ("Bold · confrontational",              "bold and confrontational"),
    ("Dreamy · introspective",              "dreamy and introspective"),
    ("Fierce · dominant",                   "fierce and dominant"),
    ("Sensual · confident",                 "sensual and confident"),
    ("Melancholic · distant",               "melancholic and distant"),
    ("Euphoric · free",                     "euphoric and free"),
    ("Cold · editorial",                    "cold and editorial"),
    ("Warm · inviting",                     "warm and inviting"),
    ("Dangerous · magnetic",                "dangerous and magnetic"),
    ("Nostalgic · cinematic",               "nostalgic and cinematic"),
    ("Raw · unfiltered",                    "raw and unfiltered"),
    ("Elegant · composed",                  "elegant and composed"),
    ("Wild · untamed",                      "wild and untamed"),
    ("Ironic · detached",                   "ironic and detached"),
    ("Glamorous · excessive",               "glamorous and excessive"),
    ("Intimate · vulnerable",               "intimate and vulnerable"),
    ("Powerful · statuesque",               "powerful and statuesque"),
    ("Surreal · otherworldly",              "surreal and otherworldly"),
    ("Casual · effortless",                 "casual and effortless"),
    ("Theatrical · exaggerated",            "theatrical and exaggerated"),
    ("Romantic · soft",                     "romantic and soft"),
    ("Angular · geometric",                 "angular and geometric"),
    ("Languid · bored",                     "languid and bored"),
    ("Sharp · precise",                     "sharp and precise"),
    ("Luminous · ethereal",                 "luminous and ethereal"),
    ("Heavy · brooding",                    "heavy and brooding"),
    ("Joyful · explosive",                  "joyful and explosive"),
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
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

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
        InlineKeyboardButton("🎲 Nuova scena", callback_data="tira"),
        InlineKeyboardButton("🔁 Riprova questa", callback_data="riprova")
    )
    return markup

def get_pool_keyboard(pool, page, prefix, title, state, done_steps):
    markup = InlineKeyboardMarkup()
    items = get_page(pool, page)
    for i, item in enumerate(items):
        idx = page * PAGE_SIZE + i
        label = item[0]
        markup.add(InlineKeyboardButton(label, callback_data=f"{prefix}{idx}"))
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
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
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

    if data == "noop":
        return

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
            bot.send_message(cid, "🎛️ <b>Scena manuale:</b>", parse_mode="HTML")
            bot.send_message(cid, format_scenario(scenario), parse_mode="HTML")
            caption_text, _ = generate_caption_from_scenario(scenario)
            if caption_text:
                bot.send_message(cid, caption_text, parse_mode=None)
            bot.send_message(cid, "Vuoi generare?", reply_markup=get_confirm_keyboard())
            logger.info(f"🎛️ MANUAL {username} (id={uid}) — {scenario['location']}")

    elif data == "tira":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())

    elif data == "no_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        manual_state.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())

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

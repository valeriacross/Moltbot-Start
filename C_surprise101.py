import os, io, random, logging, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK, VALERIA_NEGATIVE

# --- VERSIONE ---
VERSION = "1.0.1"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN   = os.environ.get("TELEGRAM_TOKEN_SORPRESA")

gemini  = GeminiClient()
caption = CaptionGenerator(gemini)
server  = HealthServer("SURPRISE", VERSION)

executor = ThreadPoolExecutor(max_workers=4)



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

    # ══ 🩱 BEACHWEAR (18) ══════════════════════════════════════════════════
    ("beachwear · bianco · one-piece cut-out",
     "white structured one-piece swimsuit, deep geometric side cut-outs exposing waist, high-leg hem, thin shoulder straps, minimal gold ring hardware, sleek editorial"),
    ("beachwear · bianco · bandeau high-cut",
     "white strapless bandeau bikini, flat structured chest band, ultra high-cut thong bottom elongating the leg, no hardware, pure minimal lines"),
    ("beachwear · rosso cremisi · triangle bikini",
     "deep crimson triangle bikini, thin string ties at neck and hips, minimal coverage, small gold ring detail at center, saturated red colour"),
    ("beachwear · rosso · one-piece hardware oro",
     "red one-piece swimsuit, exposed gold O-ring hardware at waist cinch and shoulder straps, plunging neckline, high-cut legs, bold contrast"),
    ("beachwear · rosa caldo · one-piece trim oro",
     "hot pink one-piece swimsuit with gold metallic trim along neckline edge and straps, structured boned bodice, high-cut silhouette, luxury resort aesthetic"),
    ("beachwear · rosa fucsia · halter bikini",
     "fuchsia pink halter-neck bikini, bold wide halter strap tied at nape, triangle top with padded cups, mid-rise bottoms, vivid saturated colour"),
    ("beachwear · corallo profondo · bikini crochet",
     "deep coral hand-crocheted bikini, open knotted weave texture throughout, triangle top with crochet string ties, hip-tied bottoms, artisanal crafted look"),
    ("beachwear · corallo tropicale · triangle print",
     "tropical coral triangle print bikini, bold botanical graphic repeat pattern, knotted string ties, high-cut bottoms, vibrant tropical colour"),
    ("beachwear · arancio tangerine · ruffle off-shoulder",
     "tangerine orange ruffle off-shoulder one-piece swimsuit, cascading tiered frill across bust and shoulders, gathered waist, high-leg cut, festive editorial"),
    ("beachwear · bronzo metallico · string bikini",
     "metallic bronze micro string bikini, reflective shimmering fabric, ultra-thin adjustable side strings, minimal triangle top, body-sculpting silhouette"),
    ("beachwear · turchese elettrico · bandeau bikini",
     "electric turquoise strapless bandeau bikini, wide structured flat band top, matching mid-rise bottoms, bold neon-bright saturated colour, high-impact editorial"),
    ("beachwear · turchese · halter one-piece",
     "turquoise halter-neck one-piece swimsuit, deep V-plunge neckline with gold halter ring, moderately high-cut legs, smooth fabric, poolside luxury"),
    ("beachwear · blu cobalto · crinkle bikini",
     "cobalt blue crinkle-texture bikini, gathered micro-crinkled fabric creating organic texture throughout, triangle top, ruched bottoms, tactile editorial look"),
    ("beachwear · verde foresta · sporty bandeau",
     "forest green sporty bandeau bikini set, wide flat strapless band top, moderate full-coverage bottoms, athletic clean silhouette, outdoor editorial"),
    ("beachwear · verde foresta · one-piece high-leg",
     "forest green high-leg one-piece swimsuit, scoop neckline, dramatically high-cut legs creating long leg illusion, minimal back coverage, editorial silhouette"),
    ("beachwear · verde salvia · bandeau bikini",
     "sage green bandeau bikini, soft matte fabric, thin removable straps, gently gathered front panel, mid-rise bottoms, understated natural aesthetic"),
    ("beachwear · viola elettrico · ruched bandeau",
     "electric violet ruched strapless bandeau bikini, densely gathered fabric creating rich texture across band and bottoms, bold intense purple colour"),
    ("beachwear · lavanda · halter one-piece",
     "lavender halter-neck one-piece, soft pastel fabric with sheen, crossed halter straps meeting at nape, moderate leg cut, delicate feminine silhouette"),

    # ══ 👗 MINI DRESS (25) ══════════════════════════════════════════════════
    ("mini dress · nero midnight · asymmetric micro",
     "midnight black asymmetric micro dress, single-shoulder neckline, diagonal hemline dramatically shorter on one side, bodycon stretch fabric, sharp editorial"),
    ("mini dress · bianco crema · tweed micro",
     "cream white tweed micro dress, woven boucle fabric with gold thread, collarless neckline, gilt chain trim at hem, structured boxy silhouette, Parisian chic"),
    ("mini dress · bianco avorio · lace-panel mini",
     "ivory white lace-panel mini dress, semi-sheer floral lace inserts at bodice and side panels, fitted silhouette, delicate scalloped hem, romantic editorial"),
    ("mini dress · rosso burgundy · lace mini",
     "deep burgundy allover floral lace mini dress, lace over skin-tone lining, fitted bodycon silhouette, long sleeves, scalloped edges, opulent evening look"),
    ("mini dress · rosso rubino · velvet mini",
     "deep ruby red velvet micro mini dress, plunging deep-V neckline, long fitted sleeves in stretch velvet, bodycon silhouette, rich saturated colour"),
    ("mini dress · rosa magenta · ruffled mini",
     "magenta pink ruffled mini dress, layered cascading frills at hem and along neckline, off-shoulder or sweetheart neckline, voluminous romantic silhouette"),
    ("mini dress · rosa baby · crystal-trim micro",
     "baby pink micro dress with rhinestone crystal trim lining neckline and hem, smooth stretch bodycon fabric, iridescent crystal embellishment, glamour editorial"),
    ("mini dress · rosa dusty · broderie off-shoulder",
     "dusty rose broderie anglaise off-shoulder mini dress, intricate eyelet embroidery throughout, elasticated off-shoulder neckline, tiered hem, feminine summer editorial"),
    ("mini dress · corallo · sequined mini",
     "bright coral fully sequined mini dress, plunging V neckline, thin spaghetti straps, allover sequin embellishment, short flared hem, high-energy editorial"),
    ("mini dress · terracotta · broderie strapless",
     "terracotta broderie anglaise strapless mini dress, intricate eyelet cutwork on structured bandeau bodice, gathered skirt, warm earthy tone, artisanal beauty"),
    ("mini dress · arancio bruciato · strapless bodycon",
     "burnt orange strapless bodycon mini dress, structured boned bustier top, smooth stretch fabric, pencil-tight silhouette, bold warm tone, sleek evening look"),
    ("mini dress · ambra calda · slip micro",
     "warm amber satin-effect slip micro dress, thin spaghetti straps, bias-cut fluid drape following body, minimal structure, Nineties-inspired sensual simplicity"),
    ("mini dress · giallo acido · asymmetric micro",
     "acid yellow asymmetric micro dress, single-shoulder design with diagonal draped bodice, ultra-short hemline, stretch jersey, high-visibility editorial"),
    ("mini dress · verde giada · spiral seam mini",
     "jade green bodycon mini dress with precision spiral-cut curved seams following body contours, high structured neckline, architectural tailoring, black stiletto ankle boots"),
    ("mini dress · verde foresta · micro mini",
     "forest green sleeveless micro mini dress, smooth bodycon silhouette, minimal clean detailing, bold deep saturated colour, striking simplicity"),
    ("mini dress · blu cobalto · sequined mini",
     "cobalt blue allover sequined mini dress, sleeveless with thin shoulder straps, fully embellished body, short flared hem, electric night editorial"),
    ("mini dress · blu navy · Bar micro",
     "navy blue structured micro dress with padded architectural shoulders, cinched waist, flared peplum mini skirt, sharp tailoring, powerful high-fashion silhouette"),
    ("mini dress · blu teal · wrap mini",
     "teal blue wrap mini dress, deep V-neckline wrap closure, sash tie at waist, fluid drape following curves, short flared hem, sensual editorial"),
    ("mini dress · blu ghiaccio · bandage mini",
     "ice blue bandage mini dress, horizontal stretch bandage strips sculpting silhouette, strapless or single-shoulder, figure-sculpting construction, cool editorial"),
    ("mini dress · grigio acciaio · cut-out mini",
     "steel grey cut-out mini dress, strategic geometric cut-outs at waist and side panels, bodycon silhouette, industrial-minimal aesthetic, sharp editorial"),
    ("mini dress · viola elettrico · draped one-shoulder",
     "electric violet draped one-shoulder mini dress, fluid gathered fabric falling from one shoulder, soft cascade at hip, lightweight jersey, bold colour"),
    ("mini dress · lilla polvere · structured mini",
     "powder lilac structured mini dress, architectural stiffened silhouette, clean precise lines, defined waist with boning, minimal ornamentation, sculptural beauty"),
    ("mini dress · lilla dusty · draped mini",
     "dusty lilac softly draped mini dress, cowl neckline with gathered fabric, relaxed bodycon silhouette, satin-effect material, romantic dreamy editorial"),
    ("mini dress · oro metallico · disc mini",
     "gold metallic chainmail disc mini dress, interlocking circular metal disc construction, fluid drape of linked gold discs, plunging neckline, gold stiletto sandals"),
    ("mini dress · argento metallico · crystal mesh",
     "silver metallic crystal mesh mini dress, fine mesh base fabric fully embellished with crystals and rhinestones, sparkling bodycon silhouette, maximum glamour"),

    # ══ ☀️ ESTIVI (4) ══════════════════════════════════════════════════════
    ("estivo · caramello · knit micro Bottega",
     "caramel beige woven leather-effect intrecciato knit micro dress, structured woven construction in fine leather strips, sleeveless, bodycon silhouette, luxury Italian craft"),
    ("estivo · blu polvere · broderie sundress",
     "powder blue broderie anglaise sundress, intricate eyelet embroidery throughout, sweetheart neckline, thin shoulder straps, softly flared mini skirt, summery editorial"),
    ("estivo · verde muschio · slip dress",
     "moss green satin-effect slip dress, thin spaghetti straps, bias-cut fluid drape following body curves, delicate V-neckline, minimal sensual editorial"),
    ("estivo · viola profondo · laser-cut bodycon",
     "deep violet laser-cut bodycon dress, precision geometric perforations creating semi-transparent floral pattern, fitted silhouette, technical fashion craft"),

    # ══ 🚀 FUTURISTA / SCI-FI (11) ═════════════════════════════════════════
    ("futurista · nero opaco · hourglass cut-out",
     "matte black hourglass bodycon dress with spiral waist cut-outs, structured curved panels sculpting an extreme silhouette, architectural fashion, black stiletto boots"),
    ("futurista · bianco gesso · vinyl circle micro",
     "chalk white vinyl circle-cut micro dress, geometric circular panelled construction in rigid PVC-effect white vinyl, futuristic space-age editorial"),
    ("futurista · bianco · abstract sculpture",
     "white abstract sculptural dress, three-dimensional architectural panels in rigid foam and resin, volumetric avant-garde silhouette, digital couture aesthetic"),
    ("futurista · arancio neon · inflated cocoon",
     "neon orange inflated puffer-cocoon dress, air-filled voluminous rounded silhouette, experimental architectural fashion, bold futuristic editorial"),
    ("futurista · arancio · laser-cut vinyl",
     "orange laser-cut vinyl mini dress, precision geometric perforations in rigid vinyl, structured futuristic silhouette, technical fashion craft editorial"),
    ("futurista · verde lime · 3D sculptural",
     "lime green three-dimensional sculptural dress, geometric shapes protruding from body surface, digital fabrication aesthetic, otherworldly high-fashion editorial"),
    ("futurista · verde chartreuse · Pleats Please",
     "chartreuse yellow-green micro-pleated dress, permanent heat-set pleats throughout creating accordion texture, lightweight fluid movement, vivid architectural fashion"),
    ("futurista · grigio colomba · pod micro",
     "dove grey pod micro dress, smooth sculptural moulded silhouette suggesting a protective pod form, minimal surface detail, space-age editorial"),
    ("futurista · rame metallico · liquid mesh",
     "molten copper liquid chainmail mesh mini dress, interlocking metal mesh rings in fluid drape, plunging neckline, copper stilettos, maximum metallic impact"),
    ("futurista · iridescente metallico · magnetic wave",
     "iridescent holographic metallic magnetic wave dress, shifting multi-colour surface, fluid wave-like structural form, otherworldly light-refracting editorial"),
    ("futurista · reflective metallico · space-age",
     "reflective mirror-silver space-age mini dress, highly polished reflective surface panels, geometric rigid construction, 1960s modernist couture reference"),

    # ══ 🪭 RETRÒ '20 (5) ════════════════════════════════════════════════════
    ("retrò '20 · avorio · bias-cut satin Gatsby",
     "ivory bias-cut satin slip dress, Great Gatsby-era inspiration, fluid diagonal drape, deep V-back with waterfall fabric, thin straps, Art Deco beaded belt at hip"),
    ("retrò '20 · oro pallido · silk charmeuse",
     "pale gold silk charmeuse 1920s-inspired dress, soft liquid drape, low cowl neckline, loose graceful silhouette, delicate satin sheen, vintage editorial"),
    ("retrò '20 · oro champagne · flapper beaded",
     "champagne gold beaded flapper dress, allover bead and fringe embellishment, drop-waist silhouette, V-neckline, heavily fringed hem swinging with movement"),
    ("retrò '20 · champagne · Charleston sequined",
     "champagne fully sequined Charleston dress, allover sequin embellishment, loose drop-waist silhouette, fringed hem designed for dance, Art Deco glamour"),
    ("retrò '20 · blu midnight · drop-waist Art Déco",
     "midnight blue drop-waist Art Deco dress, geometric beaded embroidery in gold and silver, low dropped waist, straight column silhouette, silk chiffon, 1920s opulence"),

    # ══ 🕺 RETRÒ '70 / DISCO (5) ════════════════════════════════════════════
    ("retrò '70 · oro liquido · studio disco halter",
     "liquid gold Studio 54 halter disco dress, deep plunging halter V-neckline, fluid gold lamé fabric, open back to waist, gold platform stilettos"),
    ("retrò '70 · arancio ruggine · crepe halter micro",
     "rust orange crepe halter micro dress, deep V halter neckline, fluid matte crepe fabric, open back, 1970s editorial glamour aesthetic"),
    ("retrò '70 · siena bruciato · satin halter disco",
     "burnt sienna satin halter disco dress, plunging halter V, high-sheen satin with fluid movement, open back to waist, 1970s nightclub glamour"),
    ("retrò '70 · grafica bianco/nero · op-art mini",
     "black and white graphic op-art mini dress, bold optical illusion concentric circle pattern, high-contrast geometric print, mod 1970s A-line silhouette"),
    ("retrò '70 · multicolor · graphic print anni 70",
     "multicolour graphic print 1970s mini dress, bold abstract repeat pattern, earthy orange-brown-yellow palette, slightly flared A-line silhouette, retro editorial"),

    # ══ ✂️ AVANGUARDIA (10) ══════════════════════════════════════════════════
    ("avanguardia · bianco · architectural micro Junya",
     "white architectural micro dress, deconstructed structured panels with unexpected volume at shoulders and hem, anti-fashion precision tailoring, conceptual editorial"),
    ("avanguardia · nero · armadillo structural mini",
     "black armadillo-inspired structural mini dress, rigid segmented panels resembling overlapping armour scales, savage beauty aesthetic, dark high-fashion editorial"),
    ("avanguardia · nero · asymmetric draped micro",
     "black asymmetric draped micro dress, single-shoulder with cascading fabric falling to one side, fluid jersey, minimal hardware, dramatic asymmetry"),
    ("avanguardia · nero · hourglass estremo",
     "pitch black extreme hourglass mini dress, exaggerated cinched waist with boning, structured flared panel skirt, power silhouette, dark architectural editorial"),
    ("avanguardia · bianco · trompe l'oeil ottico",
     "white optical trompe l'oeil mini dress, printed illusion of shadows folds and depth on flat fabric surface, conceptual art-fashion, photorealistic print"),
    ("avanguardia · rosso bordeaux · draped angular",
     "bordeaux red angular draped micro dress, sharp asymmetric hem, bias-cut crepe, open structured back, bordeaux stiletto mules, architectural editorial"),
    ("avanguardia · verde smeraldo · velvet embroidered",
     "emerald green velvet embroidered mini dress, richly embroidered surface with gold floral motif, structured fitted bodice, opulent dark glamour editorial"),
    ("avanguardia · blu indaco · patchwork micro",
     "indigo blue patchwork micro dress, assembled from varying fabric patches and textures, deconstructed artisanal aesthetic, conceptual fashion editorial"),
    ("avanguardia · oro · cone bra corset",
     "gold satin iconic conical corset mini dress, conical pointed bust cups with concentric satin stitching, boned corset waist, lace-up back, gold stilettos, theatrical makeup"),
    ("avanguardia · chrome metallico · geometric",
     "chrome metallic geometric mini dress, mirror-polished angular panels in structured geometric forms, hard-edge construction, futurist architectural editorial"),

    # ══ 🎭 COSTUMI / TEATRALI (8) ═══════════════════════════════════════════
    ("teatrale · nero · feather-cape bodysuit",
     "black dramatic feather-cape bodysuit, cascading black ostrich feathers forming sweeping cape silhouette, long legs, black stilettos, theatrical dark editorial"),
    ("teatrale · bianco lino · sacerdotessa egizia",
     "white linen Egyptian priestess column dress, straight minimal silhouette, wide pleated collar in gold and lapis, gold cuff bracelets, ceremonial editorial"),
    ("teatrale · bianco/oro · silk obi geisha",
     "white and gold silk dress with architectural obi-inspired structured sash, kimono-pattern brocade, wide sculptural waist, ceremonial elegance editorial"),
    ("teatrale · oro martellato · armatura amazzone",
     "hammered gold Amazon warrior armour-inspired dress, structured metallic breastplate bodice, short layered skirt with segmented panels, leather straps and gold sandals"),
    ("teatrale · rosso rubino · brocade odalisque",
     "ruby red Ottoman brocade odalisque dress, rich gold-patterned brocade fabric, plunging neckline, wide silhouette, gold belt and layered jewellery, opulent editorial"),
    ("teatrale · blu royal · tartan corset",
     "royal blue tartan corset-boned mini dress, structured boning at bodice, Highland tartan plaid fabric, punk-royal aesthetic, platform boots, dramatic editorial"),
    ("teatrale · argento frost · valchiria metallica",
     "frost silver metallic Valkyrie dress, structured chainmail-effect fabric, angular breastplate references, dramatic pointed shoulder details, silver warrior boots"),
    ("teatrale · multicolor aurora · ombré silk",
     "multicolour aurora borealis ombré silk dress, gradient shifting from deep violet through turquoise to pale gold, fluid silk in movement, ethereal supernatural editorial"),

    # ══ 🎬 FILM ICONICI (24) ════════════════════════════════════════════════
    ("film · nero · LBD Breakfast at Tiffany's",
     "black sleeveless column Little Black Dress, elegant minimal silhouette, elbow-length black gloves, triple strand pearl necklace, upswept hair with tiara, 1960s ultimate chic"),
    ("film · nero · studded micro Mad Max",
     "black studded leather micro dress, riveted metal studs throughout body, distressed leather panels, post-apocalyptic warrior editorial, chain hardware details"),
    ("film · bianco · abito subway Monroe",
     "white halter pleated dress with billowing full skirt, deep V halter neckline, ivory white fabric, skirt lifting dramatically in the wind, white stiletto heels, diamond earrings"),
    ("film · bianco · structured tutu Black Swan",
     "white structured ballet tutu dress, stiff multi-layered tulle skirt, fitted boned bodice, delicate feather embellishments at neckline, ballet pink pointe shoes"),
    ("film · bianco gesso · wrap mini Basic Instinct",
     "chalk white sharply tailored wrap mini dress, precise lapels, belted waist, power dressing minimal aesthetic, white stiletto heels, no jewellery, icy direct editorial"),
    ("film · bianco · strapless swimsuit La Dolce Vita",
     "white strapless one-piece swimsuit, structured boning, clean minimal cut, elegant 1960s Italian Riviera aesthetic, black stilettos, sunglasses, cinematic glamour"),
    ("film · rosso scarlatto · corseted Pretty Woman",
     "scarlet red corseted cocktail dress, structured boned sweetheart bodice, full flared short skirt, long red opera gloves, red satin stilettos, classic Hollywood glamour"),
    ("film · rosa caldo · pink satin Gentlemen Prefer Blondes",
     "hot pink satin strapless micro dress, structured boned bodice, dramatic large bow at back, diamond chandelier earrings, elbow gloves, platinum blonde editorial"),
    ("film · oro bianco · linen micro Cleopatra",
     "white and gold linen micro Cleopatra column dress, gold pleated trim at neckline and hem, wide Egyptian jewelled collar, gold cuff bracelets, elaborate gold headdress, kohl-lined eyes"),
    ("film · giallo/nero · plaid micro Clueless",
     "yellow and black tartan plaid collarless micro suit dress, boxy structured silhouette, matching plaid blazer-dress, white knee-high socks, platform Mary Janes, schoolgirl chic"),
    ("film · argento · space vinyl Barbarella",
     "silver space vinyl Barbarella mini dress, glossy PVC panels with geometric openings, futuristic 1960s camp sci-fi aesthetic, clear platform boots, bold eye makeup"),
    ("film · argento · crystal goblin queen Labyrinth",
     "silver crystal-encrusted goblin queen mini dress, dramatic structured puffed shoulders, embellished bodice with cascading crystal beading, flowing panel skirt"),
    ("film · argento · machine-woman Metropolis",
     "silver Art Deco machine-woman mini dress, sculpted metallic bodice with riveted geometric panels, stiffened architectural skirt, 1920s futurist expressionist aesthetic"),
    ("film · chrome · space disco Zoolander",
     "chrome mirror-effect space disco mini dress, highly reflective chrome fabric, structured geometric panels, camp high-fashion editorial humour, silver boots"),
    # +10 nuovi film
    ("film · verde · Shrek princess before sunset",
     "rich medieval green velvet princess dress adapted as structured mini, square neckline with gold trim, fitted boned bodice, layered skirt panels in jewel-green, gold crown"),
    ("film · rosso/oro · Jessica Rabbit sequin",
     "deep red fully sequined floor-length-inspired micro dress, extreme hourglass silhouette, one-shoulder, thigh-high side slit, red satin gloves, Old Hollywood maximalism"),
    ("film · azzurro · Cinderella ball gown micro",
     "icy blue structured ball gown silhouette adapted as micro dress, strapless boned bodice, dramatic voluminous tulle skirt cropped micro, crystal scattered throughout"),
    ("film · nero/rosso · kill bill bodysuit",
     "bright yellow tracksuit-inspired micro mini dress with black stripe, sleek bodycon silhouette, structured editorial version of action-hero aesthetic, black stiletto boots"),
    ("film · viola · Maleficent sorceress gown micro",
     "deep violet dramatic Maleficent-inspired mini dress, structured angular shoulder wings in black, dark purple silk bodice, horn-shaped headpiece, dark sorceress editorial"),
    ("film · argento/bianco · Trinity Matrix catsuit",
     "silver-white latex bodycon micro dress, liquid-like reflective surface, minimal seaming, strong futuristic silhouette, silver stiletto boots, Matrix aesthetic editorial"),
    ("film · rosa pastello · Barbie dream gown micro",
     "pastel pink structured dream-gown adapted as micro mini, strapless sweetheart bodice, layered tulle skirt cropped short, scattered rhinestones, pink platform heels"),
    ("film · oro/verde · Wicked Elphaba emerald",
     "emerald green structured witch-couture mini dress, architectural silhouette with dramatic pointed hem, black lace overlay, structured corseted bodice, sky-high heels"),
    ("film · bianco/argento · Black Swan white swan",
     "white swan feather-embellished strapless mini dress, hand-sewn white feathers at hem and shoulders, delicate crystal bodice, sheer tulle panels, pointe heel shoes"),
    ("film · oro · Moulin Rouge showgirl",
     "gold sequined showgirl Moulin Rouge micro costume dress, fully sequined bodycon, dramatic feather plume headdress in gold, sheer metallic tights, gold platform heels"),

    # ══ 🏛️ MET GALA (20) ════════════════════════════════════════════════════
    # 3 ispirati a Heidi Klum
    ("Met Gala · grigio marmo · statua velata",
     "grey marble-effect full-body sculptural gown, latex and spandex crafted to resemble carved stone, trompe l'oeil veiled fabric illusion over face and body, ancient Roman Vestal aesthetic, floral wreath headpiece, marble-painted skin"),
    ("Met Gala · arancio fiamma · catsuit body paint",
     "flaming orange full-body painted catsuit, airbrushed fire and flame body painting over skin-toned base, dramatic flame-tongue feather headdress, sculpted platform hooves, otherworldly creature editorial"),
    ("Met Gala · oro antico · dea vivente",
     "ancient gold living goddess bodysuit, intricate hand-painted gold leaf patterns covering body, structured gold breastplate, dramatic wing-spread behind shoulders, classical mythology editorial"),
    # 17 iconici Met Gala
    ("Met Gala · giallo canary · cape fur gown",
     "canary yellow structured couture cape gown, voluminous sculptural silhouette, dramatic fur-trimmed hem sweeping the floor, golden silk fabric, empress-level grand entrance"),
    ("Met Gala · rosa shocking · quad outfit change",
     "hot pink voluminous theatrical cape gown opening to reveal black column dress, camp maximalism, four-look concept, dramatic stage-entrance proportions, oversized silhouette"),
    ("Met Gala · nude/cristalli · naked dress",
     "illusion crystal-covered bodycon gown, 200,000 hand-applied crystals on sheer base, figure-sculpting silhouette, blinding reflective surface, maximum crystal maximalism"),
    ("Met Gala · bianco · dress film strips",
     "white tulle mini dress constructed from actual film strips, old Hollywood noir references, transparent film reel material creating layered skirt, cinematic couture editorial"),
    ("Met Gala · nero latex · Givenchy tech gown",
     "black latex Givenchy-inspired technical gown, futuristic latex fabric, cherry blossom embroidery in silver, puffed structured shoulders, rhinestone embellishments throughout"),
    ("Met Gala · sabbia · sand sculpture gown",
     "sand-coloured Balmain gown sculpted from actual sand and resin, organic granular surface texture, hourglass silhouette, earth-mineral editorial, sand-dusted accessories"),
    ("Met Gala · rosso · Vatican cape gown",
     "deep red Catholic-inspired cape gown, embroidered gold cross motifs, ecclesiastical column silhouette, dramatic floor-sweeping cape, gemstone headpiece, sacred fashion editorial"),
    ("Met Gala · bianco/oro · robotic armour dress",
     "white and gold robotic armour-inspired couture dress, structured metallic panels suggesting mecha aesthetics, gold filigree over white silk base, futuristic medievalism"),
    ("Met Gala · verde · punk tartan chaos",
     "green tartan punk couture gown, safety pins as structural detailing, tartan panels deconstructed and reassembled, mohawk headpiece, platform combat boots"),
    ("Met Gala · argento · mirror ball gown",
     "silver mirror-tile mosaic ball gown, thousands of tiny mirror fragments covering structured skirt, blinding reflective surface, strapless bodice, live disco ball editorial"),
    ("Met Gala · nero · dramatic feather column",
     "black dramatically plumed column gown, sweeping black Chanel-style feather plumes layered throughout, light airy construction, powerful impact, minimalist face"),
    ("Met Gala · viola/piume · extravagant fantasy",
     "deep violet fantasy gown, enormous structured ruffled tulle skirt with purple feathers, sculptural nipped waist, surreal baroque proportions, living couture editorial"),
    ("Met Gala · oro · Cleopatra procession gown",
     "gold lamé Cleopatra-inspired couture gown, structured pleated column silhouette, wide jewelled lapis collar, elaborate headdress with cobra detail, ancient luxury editorial"),
    ("Met Gala · bianco · origami structural gown",
     "white architectural origami paper-fold couture dress, rigid geometric pleated panels, mathematical precision construction, Japanese paper-art aesthetic, minimal accessories"),
    ("Met Gala · rosso · camp maximalism layered",
     "red camp maximalism layered gown, multiple skirt tiers in different red fabrics, exaggerated proportions, oversized bow, theatrical excess, fashion-as-spectacle editorial"),
    ("Met Gala · nero/bianco · op art illusion gown",
     "black and white op-art illusion gown, geometric optical print creating three-dimensional effect, figure-warping swirl pattern, graphic maximalism, bold editorial impact"),

    # ══ ✨ PRINCIPESSE & FATE (30) ══════════════════════════════════════════
    ("principessa · blu ghiaccio · signora del mare",
     "icy blue seashell-and-scale mini dress, iridescent fish-scale sequins covering structured bodice, pearl and shell embellishments, flowing chiffon tail-panels, sculpted-shoulder ocean goddess editorial"),
    ("principessa · rosa corallo · sirena tropicale",
     "coral pink tropical mermaid micro dress, graduated scale sequins from deep coral to pale blush, starfish and pearl accessories, sculpted shoulders, reef editorial"),
    ("principessa · oro · sovrana solare",
     "golden sun-queen micro dress, structured metallic sun-ray collar forming dramatic halo, gold lamé fitted bodice, solar disc headdress, celestial editorial"),
    ("principessa · azzurro baby · danzatrice stellare",
     "baby blue star-dancer micro dress, scattered star crystal embellishments throughout tulle, structured bodice with star-shaped cutouts, silver tiara, ethereal ballet editorial"),
    ("principessa · viola magico · strega buona",
     "deep purple good-witch couture micro dress, crescent moon and star embroidery in silver, structured pointed bodice, dramatic wide-brim hat with stars, twilight editorial"),
    ("principessa · verde foresta · guardiana bosco",
     "forest green nature-guardian micro dress, hand-embroidered leaves and vines covering bodice, layered botanical skirt panels, floral crown, woodland fairy editorial"),
    ("principessa · bianco neve · specchio magico",
     "snow white high-contrast micro dress, structured black bodice with white collar detail, vivid apple-red accents, gold-trimmed hem, fairytale editorial"),
    ("principessa · rosa shocking · ballerina ribelle",
     "shocking pink rebel ballerina micro tutu, ripped and deconstructed pink tulle layers, crystal-studded torn bodice, combat boots, punk fairy editorial"),
    ("principessa · ambra · lampada magica",
     "warm amber harem-inspired micro dress, sheer chiffon panels over structured gold bodice, midriff-baring design, jewelled belt and bangles, Middle Eastern fantasy editorial"),
    ("principessa · verde smeraldo · principessa draghi",
     "emerald green dragon-scale structured mini dress, embossed scale-pattern metallic fabric, shoulder armour in black, dragon-wing cape detail, fantasy power editorial"),
    ("principessa · bianco gelato · regina delle nevi",
     "ice-white Snow Queen micro dress, sheer crystal-studded overlay, structured bodice with snowflake motif, frosted ombre hem, crystal snowflake crown, frozen editorial"),
    ("principessa · rosa polvere · dea dei sogni",
     "powder pink dream-goddess micro dress, cloud-soft tulle layers, iridescent butterfly wings attached to back, scattered rose crystals, gold sandals, reverie editorial"),
    ("principessa · nero stellato · cacciatrice notturna",
     "black star-map micro dress, galaxie print on fitted bodycon, constellation crystal embroidery, crescent headpiece, silver arrow accessories, night-hunter editorial"),
    ("principessa · rosso rubino · cuori e magia",
     "ruby red hearts-and-magic micro dress, playing card suit embroidery throughout, structured sweetheart bodice, gold crown, fantastical royal editorial"),
    ("principessa · azzurro · guerriera dell'acqua",
     "azure blue water-warrior micro dress, liquid-effect pleated panels, water droplet crystal embellishments, structured bodice with wave motifs, navy blue editorial"),
    ("principessa · arancio · principessa del fuoco",
     "vivid orange fire-princess micro dress, flame-pattern embroidery in gold and red, structured bodice with ember crystals, flame-shaped headpiece, elemental editorial"),
    ("principessa · oro/bianco · angelo custode",
     "ivory and gold guardian angel micro dress, structured feather-wing bodice panels, delicate gold halo headpiece, trailing sheer chiffon, ethereal spiritual editorial"),
    ("principessa · multicolor arcobaleno · fata arcobaleno",
     "multicolour rainbow fairy micro dress, gradient ombre fabric shifting through all spectrum colours, iridescent butterfly wings, prismatic crystal tiara, joyful editorial"),
    ("principessa · verde lime · principessa lego",
     "lime green geometric Lego-inspired structured mini dress, block-structured angular panels resembling Lego bricks, pixel aesthetic construction, yellow block crown"),
    ("principessa · blu/giallo · costruttrice di mondi",
     "blue and yellow Lego master-builder mini dress, geometric block-structured panels, colour-blocked architecture, playful primary colours, iconic toy aesthetic editorial"),
    ("principessa · rosso · avventuriera Pixar",
     "bright red adventure-heroine mini dress, structured athletic bodice, dynamic angular panels suggesting movement, curly hair accessory, freckled editorial adventurer look"),
    ("principessa · verde scuro · ranger della foresta",
     "dark green forest ranger micro dress, structured utility-inspired bodice with bronze buckles, layered leaf panels, wooden crown, earthy Pixar-ranger editorial"),
    ("principessa · lavanda · creatrice di incantesimi",
     "lavender spell-crafter micro dress, scattered rune and star embroidery, structured boned bodice, pointed ceremonial hat, crystal wand accessory, magic editorial"),
    ("principessa · turchese · principessa delle bolle",
     "turquoise bubble-princess micro dress, three-dimensional bubble-shaped embellishments covering skirt, iridescent sphere details, structured strapless bodice, underwater editorial"),
    ("principessa · bianco/argento · specchio parlante",
     "white and silver talking-mirror micro dress, mirrored sequin mosaic bodice, reflective panels throughout, silver crown with mirror detail, enchanted editorial"),
    ("principessa · giallo dorato · principessa della luce",
     "golden yellow light-princess micro dress, sunburst crystal embroidery radiating from bodice, structured strapless silhouette, tall crystal crown, radiant editorial"),
    ("principessa · rosa intenso · cupcake queen",
     "hot pink cupcake queen micro dress, structured bodice with pastel frosting-inspired textures, layered candy-coloured tulle, sugar crystal embellishments, sweet fantasy editorial"),
    ("principessa · blu notte · guardiana degli astri",
     "deep midnight blue star-guardian micro dress, hand-embroidered constellation map throughout, fitted structured bodice, telescope-shaped sceptre accessory, astronomy editorial"),
    ("principessa · corallo/oro · principessa del tramonto",
     "coral and gold sunset princess micro dress, ombre gradient from deep coral to burnished gold, structured strapless bodice, sunset crystal embellishments, dusk editorial"),
    ("principessa · argento · cavalcatrice di comete",
     "silver comet-rider micro dress, metallic silver structured bodice with comet-tail train, iridescent stardust embellishments, chrome boots, speed-of-light editorial"),
    # extra
    ("principessa · oro/nero · guerriera delle stelle",
     "black and gold star-warrior micro dress, structured metallic breastplate bodice with star motifs, angular shoulder armour panels, gold constellation embroidery throughout, black platform boots, cosmic editorial"),
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

def generate_scenario(uid=None):
    """Genera scenario completamente locale — zero API."""
    used_loc = used_locations.get(uid, set())
    available_loc = [l for l in LOCATION_POOL if l[1] not in used_loc] or LOCATION_POOL
    loc_tuple = random.choice(available_loc)
    location = loc_tuple[1]
    used_out = used_outfits.get(uid, set())
    available_out = [o for o in OUTFIT_POOL if o[1] not in used_out] or OUTFIT_POOL
    out_tuple   = random.choice(available_out)
    style_tuple = random.choice(STYLE_POOL)
    sky_tuple   = random.choice(SKY_POOL)
    pose_tuple  = random.choice(POSE_POOL)
    mood_tuple  = random.choice(MOOD_POOL)
    scenario = {
        'location': location,
        'outfit':   out_tuple[1],
        'style':    style_tuple[1],
        'sky':      sky_tuple[1],
        'pose':     pose_tuple[1],
        'mood':     mood_tuple[1],
    }
    logger.info(f"🎲 Scenario locale: {location[:40]}")
    return scenario

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

def build_flow_prompt(scenario, uid=None):
    """Genera prompt dettagliato per Flow usando DNA da C_shared100.py."""
    loc    = scenario.get('location', '')
    outfit = scenario.get('outfit', '')
    sky    = scenario.get('sky', '')
    pose   = scenario.get('pose', '')
    mood   = scenario.get('mood', '')
    style  = scenario.get('style', '')

    prompt = (
        f"{VALERIA_FACE}"
        f"{VALERIA_BODY_STRONG}"
        f"LOCATION: {loc}\n\n"
        f"OUTFIT: {outfit}\n\n"
        f"LIGHTING / SKY: {sky}\n\n"
        f"POSE: {pose}\n\n"
        f"MOOD / ATMOSPHERE: {mood}\n\n"
        f"PHOTOGRAPHIC STYLE: {style}\n\n"
        f"TECHNICAL: 8K cinematic, 85mm lens, f/2.8, ISO 200, natural bokeh, "
        f"Subsurface Scattering, Global Illumination.\n"
        f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
        f"NEGATIVE: {VALERIA_NEGATIVE}"
    )
    return prompt

def build_prompt(scenario, uid=None):
    return build_flow_prompt(scenario, uid=uid), "2:3", None

def sanitize_scenario(scenario):
    return scenario

def generate_caption_from_scenario(scenario):
    """→ shared.CaptionGenerator.from_scenario()"""
    return caption.from_scenario(scenario)

# --- BOT ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- STATO ---
last_scenario  = {}
last_prompt    = {}
manual_state   = {}
used_locations = {}   # uid → set di label location usate nella sessione
_uid_for_gen   = None  # uid corrente durante generate_scenario
used_outfits   = {}   # uid → set di label outfit usati nella sessione
last_flow_prompt = {}  # uid → prompt Flow-ready

# --- DEDUP CALLBACK (fix step 1/6 duplicato) ---
# Telegram può recapitare lo stesso callback_query più volte se l'ack non arriva in tempo.
# _seen_callbacks memorizza i call.id già processati (stringa univoca per ogni pressione).
# _seen_callbacks_order tiene l'ordine di inserimento per pulizia FIFO (max 200 voci).
import collections
_seen_callbacks: set = set()
_seen_callbacks_order: collections.deque = collections.deque(maxlen=200)

def _is_duplicate_callback(call_id: str) -> bool:
    """Ritorna True se call_id è già stato processato (duplicato da Telegram).
    Mantiene un buffer FIFO di max 200 call_id per evitare crescita infinita del set.
    """
    if call_id in _seen_callbacks:
        logger.warning(f"⚠️ Callback duplicato ignorato: {call_id}")
        return True
    # Se il deque è pieno, rimuove il più vecchio dal set prima di aggiungere il nuovo
    if len(_seen_callbacks_order) == _seen_callbacks_order.maxlen:
        oldest = _seen_callbacks_order[0]
        _seen_callbacks.discard(oldest)
    _seen_callbacks.add(call_id)
    _seen_callbacks_order.append(call_id)
    return False

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
    markup.row(InlineKeyboardButton("🎲 Nuova scena", callback_data="tira"))
    return markup

def get_confirm_flow_keyboard():
    """Keyboard di conferma: un solo pulsante Flow + Home."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📋 Prompt Flow", callback_data="conferma"),
        InlineKeyboardButton("🏠 Home", callback_data="no_home")
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
        markup = get_pool_keyboard(filtered, 0, prefix, title, manual_state.get(uid, {}), step_index)
        if len(filtered) < len(pool):
            note = f" <i>({len(pool)-len(filtered)} già usati nascosti)</i>"
            bot.send_message(cid, f"{title}{note}", reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")
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
    import re as _re
    loc_display = s['location']
    if '{' in loc_display and '"subject"' in loc_display:
        values = _re.findall(r'"(?:subject|ground|sky|colors|lighting|depth|mood)"\s*:\s*"([^"]+)"', loc_display)
        loc_display = ", ".join(v.strip() for v in values if v.strip()) if values else loc_display[:120]
    return (
        f"📍 <b>Location:</b> {html.escape(loc_display)}\n"
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
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid} username={message.from_user.username}")
        return
    username = message.from_user.username or message.from_user.first_name
    last_scenario.pop(uid, None)
    last_prompt.pop(uid, None)
    manual_state.pop(uid, None)
    used_locations.pop(uid, None)
    used_outfits.pop(uid, None)
    last_flow_prompt.pop(uid, None)
    logger.info(f"🎲 /start da {username} (id={uid})")
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
        reply_markup=get_main_keyboard())

# --- /help ---
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION} — Comandi</b>\n\n"
        f"/start — Reset e menu principale\n"
        f"/lastprompt — Mostra ultimo prompt Flow\n"
        f"/info — Versione e informazioni\n"
        f"/help — Questo messaggio\n\n"
        f"<i>Scegli Automatico per uno scenario random,\n"
        f"Manuale per scegliere ogni elemento.</i>"
    )

# --- /info ---
@bot.message_handler(commands=['info'])
def handle_info(message):
    bot.send_message(message.chat.id,
        f"<b>🎲 SURPRISE v{VERSION}</b>\n\n"
        f"Genera scenari editoriali Valeria Cross.\n"
        f"Pool: 200 location · 100 outfit · 50 stili · 50 pose · 50 sky · 50 mood\n"
        f"Modello caption: <code>gemini-3-flash-preview</code>\n\n"
        f"<i>Output: label + caption + prompt Flow-ready.</i>"
    )

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
    if not is_allowed(uid):
        logger.warning(f"🚫 Callback non autorizzato: uid={uid}")
        return
    # Dedup: scarta callback già processati (retry Telegram)
    if _is_duplicate_callback(call.id):
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        return
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
            scenario = generate_scenario(uid=uid)
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
            bot.send_message(cid, "📋 Prompt Flow:", reply_markup=get_confirm_flow_keyboard())
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
            bot.send_message(cid, "📋 Prompt Flow:", reply_markup=get_confirm_flow_keyboard())
            logger.info(f"🎛️ MANUAL {username} (id={uid}) — {scenario['location']}")

    elif data == "tira":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state.pop(uid, None)
        last_flow_prompt.pop(uid, None)
        bot.send_message(cid,
            f"<b>🎲 SURPRISE v{VERSION}</b>\n\nCome vuoi generare la scena?",
            reply_markup=get_main_keyboard())

    elif data == "no_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        manual_state.pop(uid, None)
        last_flow_prompt.pop(uid, None)
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
        full_p, fmt, _ = build_prompt(scenario, uid=uid)
        last_prompt[uid] = full_p
        # flow_prompt già salvato al momento della scena — aggiorna per sicurezza
        if not last_flow_prompt.get(uid):
            last_flow_prompt[uid] = build_flow_prompt(scenario, uid=uid)
        flow_p = last_flow_prompt.get(uid) or build_flow_prompt(scenario, uid=uid)
        header = "📋 <b>Prompt Flow-ready</b>"
        bot.send_message(cid, header, parse_mode="HTML")
        chunks = [flow_p[i:i+3800] for i in range(0, len(flow_p), 3800)]
        for idx, chunk in enumerate(chunks):
            if idx == len(chunks) - 1:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>",
                    parse_mode="HTML", reply_markup=get_retry_keyboard())
            else:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>", parse_mode="HTML")
        logger.info(f"📋 FLOW PROMPT inviato a {username} (id={uid})")

    elif data == "riprova":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        scenario = last_scenario.get(uid)
        if not scenario:
            bot.send_message(cid, "⚠️ Sessione scaduta.", reply_markup=get_main_keyboard())
            return
        full_p_retry, fmt_retry, _ = build_prompt(scenario, uid=uid)
        last_prompt[uid] = full_p_retry
        flow_p = last_flow_prompt.get(uid) or build_flow_prompt(scenario, uid=uid)
        header = "📋 <b>Prompt Flow-ready</b> <i>(reinviato)</i>"
        bot.send_message(cid, header, parse_mode="HTML")
        chunks = [flow_p[i:i+3800] for i in range(0, len(flow_p), 3800)]
        for idx, chunk in enumerate(chunks):
            if idx == len(chunks) - 1:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>",
                    parse_mode="HTML", reply_markup=get_retry_keyboard())
            else:
                bot.send_message(cid, f"<code>{html.escape(chunk)}</code>", parse_mode="HTML")


# --- FLASK ---
# --- MAIN ---
if __name__ == '__main__':
    logger.info(f"🎲 SURPRISE v{VERSION} — avvio")
    server.start()
    bot.infinity_polling(timeout=30, long_polling_timeout=25)

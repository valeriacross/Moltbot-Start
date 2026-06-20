import os, io, random, logging, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed, analyze_scene, generate_mini_caption, generate_mini_prompt, SHARED_VERSION, SHARED_DATE
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK, VALERIA_NEGATIVE
from C_shared100 import VALERIA_DNA, EDITORIAL_WRAPPER, build_valeria_identity

# --- VERSIONE ---
# CHANGELOG 2.0.0 (20/06/2026): fix #8 — idx nel callback_data di location/outfit
# era risolto contro il pool completo invece del pool filtrato mostrato in
# tastiera, causando selezione silenziosamente errata dal secondo giro in
# sessione. Introdotto shown_pool per tracciare il pool esatto mostrato per
# uid+step; fix applicato sia alla selezione che al cambio pagina (pg_).
VERSION = "2.0.0"

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

    # ══ 🇮🇹 ITALIA ═════════════════════════════════════════
    ("🇮🇹 · Gran Sasso, borgo in pietra", "Santo Stefano di Sessanio, Abruzzo, ancient hilltop stone village, Gran Sasso mountain backdrop, narrow medieval alleyways, warm golden hour light"),
    ("🇮🇹 · Scanno, lago a cuore", "Lago di Scanno, Abruzzo, heart-shaped glacial lake visible from above, medieval village perched above water, early morning mist over surface"),
    ("🇮🇹 · Matera, sassi e chiese rupestri", "Matera, Basilicata, UNESCO cave city, ancient sassi carved into ravine, rupestrian churches, golden limestone glowing at sunset, dramatic canyon below"),
    ("🇮🇹 · Maratea, Cristo sul Tirreno", "Maratea, Basilicata, Cristo Redentore statue on Monte San Biagio, panoramic Tyrrhenian sea view, dramatic cliff coastline, white marble Christ figure"),
    ("🇮🇹 · Tropea, scogliera e spiaggia bianca", "Tropea, Calabria, hilltop town perched on sheer sandstone cliffs above white sandy beach, crystal turquoise Tyrrhenian sea, island church of Santa Maria dell'Isola"),
    ("🇮🇹 · Scilla, castello sul mare", "Scilla, Calabria, Ruffo Castle on rocky promontory, fishermen's quarter Chianalea, Strait of Messina, Etna visible across the water on clear days"),
    ("🇮🇹 · Pentedattilo, borgo fantasma", "Pentedattilo, Calabria, abandoned ghost village clinging to claw-shaped volcanic rock formation, crumbling medieval ruins, dramatic Aspromonte mountains"),
    ("🇮🇹 · Positano, bouganville e terrazze", "Positano, Amalfi Coast, stacked pastel houses cascading down cliffs to pebble beach, bougainvillea-draped terraces, turquoise bay, colorful fishing boats"),
    ("🇮🇹 · Ravello, Villa Cimbrone sul mare", "Villa Cimbrone, Ravello, Campania, Terrace of Infinity overlooking the Tyrrhenian sea, marble busts along balustrade, rose gardens, infinite horizon"),
    ("🇮🇹 · Capri, Faraglioni al tramonto", "Faraglioni rocks, Capri, Campania, three limestone sea stacks rising from electric blue water, golden sunset light, Marina Piccola below, yachts in foreground"),
    ("🇮🇹 · Paestum, templi greci nella luce", "Paestum, Campania, three exceptionally preserved Doric Greek temples, Temple of Neptune, amber evening light raking across ancient limestone columns"),
    ("🇮🇹 · Procida, Marina Corricella colorata", "Marina Corricella, Procida, Campania, densely stacked fishermen's houses in ochre yellow pink and terracotta, boats in small harbour, no cars, timeless atmosphere"),
    ("🇮🇹 · Dolomiti, Tre Cime di Lavaredo", "Tre Cime di Lavaredo, Dolomites, three iconic rocky pinnacles rising above alpine meadow, pink alpenglow at dawn, reflection in small mountain lake"),
    ("🇮🇹 · Dolomiti, Lago di Braies al mattino", "Lago di Braies, Dolomites, emerald green glacial lake, traditional red wooden rowing boat on mirror-calm water, pine forest, Seekofel peak reflected"),
    ("🇮🇹 · Dolomiti, Alpe di Siusi all'alba", "Alpe di Siusi, Dolomites, largest high-altitude alpine meadow in Europe, wildflowers, Sassolungo and Sassopiatto peaks glowing pink at sunrise"),
    ("🇮🇹 · Trieste, Castello di Miramare", "Castello di Miramare, Trieste, Friuli, white 19th century castle on rocky promontory above Adriatic sea, terraced gardens, turquoise water below"),
    ("🇮🇹 · Venezia, Piazza San Marco all'alba", "Piazza San Marco at dawn, Venice, Veneto, golden light on Byzantine basilica facade, empty square reflected in acqua alta, pigeons, campanile tower"),
    ("🇮🇹 · Venezia, Burano, case colorate", "Burano island, Venice lagoon, intensely coloured fishermen's houses in red yellow blue green, narrow canals, small bridges, lace curtains in windows"),
    ("🇮🇹 · Venezia, Canal Grande all'ora dorata", "Grand Canal, Venice, golden hour light on Renaissance and Gothic palaces, gondola in foreground, Rialto Bridge in background, warm amber reflections"),
    ("🇮🇹 · Venezia, San Giorgio Maggiore", "Basilica of San Giorgio Maggiore, Venice, Palladian church on its own island, viewed from Riva degli Schiavoni, campanile reflected in lagoon at dusk"),
    ("🇮🇹 · Verona, Arena romana", "Roman Arena, Verona, Veneto, remarkably preserved 1st century amphitheatre, pink marble exterior, surrounding piazza with outdoor cafes, evening lights"),
    ("🇮🇹 · Lago di Garda, Sirmione sul lago", "Sirmione, Lake Garda, Veneto, medieval Scaligero castle on narrow peninsula, turquoise glacial lake water, cypress trees, Lombardy Alps in background"),
    ("🇮🇹 · Roma, Colosseo al tramonto", "Colosseum exterior, Rome, Lazio, largest ancient amphitheatre ever built, warm amber travertine stone glowing at sunset, Via Sacra in foreground"),
    ("🇮🇹 · Roma, Foro Romano tra le colonne", "Roman Forum, Rome, Palatine Hill, ancient column ruins with Capitol Hill backdrop, umbrella pines, golden light raking across ancient stones"),
    ("🇮🇹 · Roma, Castel Sant'Angelo sul Tevere", "Castel Sant'Angelo, Rome, cylindrical mausoleum fortress on Tiber riverbank, Ponte Sant'Angelo with angel statues, soft blue hour light"),
    ("🇮🇹 · Roma, Piazza di Spagna all'alba", "Spanish Steps at dawn, Rome, empty travertine steps descending to Piazza di Spagna, Trinità dei Monti church above, Barcaccia fountain, first light"),
    ("🇮🇹 · Civita di Bagnoregio, isola nel cielo", "Civita di Bagnoregio, Lazio, medieval hill town on eroding volcanic tufa outcrop, accessible only by footbridge, floating above deep canyon, mist below"),
    ("🇮🇹 · Tivoli, Villa d'Este e le fontane", "Villa d'Este, Tivoli, Lazio, UNESCO Renaissance garden with hundreds of fountains, Avenue of Hundred Fountains, moss-covered nymphaea, water everywhere"),
    ("🇮🇹 · Assisi, Basilica nella nebbia", "Basilica of San Francesco, Assisi, Umbria, pink and white stone church complex on hill, morning fog filling valley below, Umbrian countryside panorama"),
    ("🇮🇹 · Orvieto, Duomo sulla rupe", "Orvieto Cathedral, Umbria, Gothic Duomo on volcanic tufa cliff, golden mosaic facade glittering in sunlight, dramatic sheer rock face below city"),
    ("🇮🇹 · Firenze, Ponte Vecchio sull'Arno", "Ponte Vecchio, Florence, Tuscany, medieval bridge lined with goldsmiths' shops over Arno river, warm sunrise light, Vasari Corridor above, reflections"),
    ("🇮🇹 · Firenze, Piazzale Michelangelo", "Piazzale Michelangelo, Florence, Tuscany, panoramic terrace overlooking entire city, Duomo dome, Palazzo Vecchio tower, Arno river, Tuscan hills beyond"),
    ("🇮🇹 · Toscana, Val d'Orcia con cipressi", "Val d'Orcia, Tuscany, UNESCO rolling hills with iconic cypress tree lines, winding white gravel road, morning fog in valley, medieval farmhouse silhouette"),
    ("🇮🇹 · Siena, Piazza del Campo", "Piazza del Campo, Siena, Tuscany, medieval shell-shaped piazza, terracotta brickwork, Torre del Mangia tower, surrounding Gothic palaces, warm evening light"),
    ("🇮🇹 · San Gimignano, torri medievali", "San Gimignano, Tuscany, medieval town with 14 surviving tower houses, Sangimignano skyline visible from vineyards, Vernaccia wine country surrounding"),
    ("🇮🇹 · Volterra, rupe tufacea e vento", "Volterra, Tuscany, windswept hilltop Etruscan-medieval city, dramatic eroding tufa cliffs Le Balze on edge of town, wide Tuscan plain panorama"),
    ("🇮🇹 · Cinque Terre, Vernazza", "Vernazza, Cinque Terre, Liguria, colourful harbour village on rocky clifftop, turquoise inlet, pastel tower houses, terraced vineyards above, fishing boats"),
    ("🇮🇹 · Portofino, faro e yacht", "Portofino, Liguria, exclusive fishing village around horseshoe bay, luxury yachts, pastel houses reflected in harbour water, hilltop lighthouse above"),
    ("🇮🇹 · Langhe, vigneti nella nebbia", "Langhe hills, Piedmont, sea of morning fog filling valleys between Barolo and Barbaresco wine hills, lone farmhouse on ridge, golden autumn vineyards"),
    ("🇮🇹 · Lago di Como, Villa Balbianello", "Villa del Balbianello, Lake Como, Lombardia, baroque villa on wooded promontory, stone loggia with columns, manicured gardens, misty alps reflected in lake"),
    ("🇮🇹 · Lago Maggiore, Isola Bella", "Isola Bella, Lake Maggiore, Lombardia, baroque palace and terraced gardens on island, ten-tiered garden with statues and exotic plants, Alps backdrop"),
    ("🇮🇹 · Milano, Galleria Vittorio Emanuele", "Galleria Vittorio Emanuele II, Milan, Lombardia, Europe's oldest shopping arcade, iron and glass octagonal dome, mosaic floor, warm golden interior light"),
    ("🇮🇹 · Milano, Terrazze del Duomo", "Milan Cathedral rooftop terraces, Lombardia, Gothic marble spires and pinnacles close up, city panorama below, Madonnina gold statue, blue sky"),
    ("🇮🇹 · Alberobello, trulli bianchi", "Alberobello, Puglia, UNESCO trulli district, hundreds of circular stone dwellings with conical limestone roofs, whitewashed walls, Mediterranean light"),
    ("🇮🇹 · Polignano a Mare, scogliera adriatica", "Polignano a Mare, Puglia, medieval town perched on white limestone cliffs above clear Adriatic sea, dramatic sea caves below, pebble cove access"),
    ("🇮🇹 · Ostuni, città bianca nella luce", "Ostuni, Puglia, La Città Bianca, labyrinth of whitewashed houses cascading down hillside, cathedral at summit, olive groves in surrounding Murge plain"),
    ("🇮🇹 · Sardegna, Costa Smeralda", "Costa Smeralda, Sardinia, impossibly clear turquoise water over white quartz sand, pink granite rocks, Mediterranean scrub, exclusive northern Sardinian coast"),
    ("🇮🇹 · Sardegna, Cala Goloritzé", "Cala Goloritzé, Sardinia, UNESCO natural monument, limestone arch and pinnacle above transparent emerald cove accessible only by boat or trek, wild coast"),
    ("🇮🇹 · Sicilia, Valle dei Templi", "Valley of the Temples, Agrigento, Sicily, exceptionally preserved Doric Greek temples on ridge, Temple of Concordia at sunset, almond blossom in spring"),
    ("🇮🇹 · Taormina, Teatro Greco con Etna", "Greek Theatre of Taormina, Sicily, ancient semicircular theatre with Etna volcano behind, snow-capped crater, Ionian sea below, perfect composition"),
    ("🇮🇹 · Scala dei Turchi, scogliera bianca", "Scala dei Turchi, Sicily, brilliant white marl rock staircase formation above blue Mediterranean sea, layered natural limestone terraces, sea erosion"),
    ("🇮🇹 · Cefalù, Duomo normanno e mare", "Cefalù, Sicily, Norman cathedral with twin towers backed by steep La Rocca cliff, old town terracotta rooftops, turquoise Tyrrhenian bay below"),
    ("🇮🇹 · Siracusa, Ortigia al tramonto", "Ortigia island, Syracuse, Sicily, baroque piazza with Greek temple columns embedded in cathedral facade, honey-coloured limestone, Ionian sea glittering"),
    ("🇮🇹 · Emilia-Romagna, Ravenna mosaici", "Ravenna, Emilia-Romagna, UNESCO Byzantine mosaics in Mausoleo di Galla Placidia, deep blue and gold starfield ceiling, glittering tesserae, sacred interior"),
    ("🇮🇹 · Piemonte, Sacra di San Michele", "Sacra di San Michele, Piedmont, Romanesque-Gothic abbey on rocky peak above Susa valley, dramatic cliff-edge structure, alpine panorama, staircase of the dead"),
    ("🇮🇹 · Puglia, Lecce barocca", "Lecce, Puglia, baroque city of ornate golden limestone facades, Piazza del Duomo, intricate carved cherubs and columns, honey-warm southern light"),
    ("🇮🇹 · Dolomiti, Cortina d'Ampezzo innevata", "Cortina d'Ampezzo, Dolomites, snow-covered luxury alpine village, Tofane and Cristallo massifs rising dramatically, powder snow, winter sun on peaks"),
    ("🇮🇹 · Campania, Caserta, Reggia e fontane", "Reggia di Caserta, Campania, vast Bourbon royal palace, kilometre-long garden axis, grand waterfall cascade, fountains with mythological statues, Versailles of Italy"),
    ("🇮🇹 · Calabria, Capo Vaticano, Costa degli Dei", "Capo Vaticano, Calabria, Costa degli Dei, turquoise sea over white pebble coves, Aeolian Islands visible on the horizon, rugged cliffs, wild coastline"),
    ("🇮🇹 · Pompei, Via dell'Abbondanza", "Via dell'Abbondanza, Pompeii, Campania, main street of ancient Roman city preserved under Vesuvius ash, stepping stones, painted shop signs, Mount Vesuvius looming above"),

    # ══ 🇵🇹 PORTOGALLO ═════════════════════════════════════
    ("🇵🇹 · Lisbona, Torre di Belém sul Tago", "Torre de Belém, Lisbon, UNESCO Manueline Gothic tower rising from Tagus river, maritime ornamentation, battlements, sunset light on honey stone"),
    ("🇵🇹 · Lisbona, Alfama e Portas do Sol", "Portas do Sol viewpoint, Alfama, Lisbon, terracotta rooftops cascading to Tagus river, blue azulejo tiles, bougainvillea, São Vicente church dome"),
    ("🇵🇹 · Lisbona, Jerónimos, archi manueline", "Jerónimos Monastery, Lisbon, Belém, UNESCO masterpiece of Manueline architecture, ornate south portal with sea motifs, vast cloister with twisted columns"),
    ("🇵🇹 · Lisbona, tram 28 e azulejos", "Tram 28, Lisbon, iconic yellow tram navigating steep narrow Alfama streets, blue azulejo tile facades on either side, typical summer morning"),
    ("🇵🇹 · Lisbona, Miradouro da Graça", "Miradouro da Graça, Lisbon, hilltop terrace at dusk, panoramic city view, Castle of São Jorge silhouette, Tagus river shimmering, warm violet sky"),
    ("🇵🇹 · Lisbona, LX Factory industriale", "LX Factory, Lisbon, repurposed 19th century industrial complex under Ponte 25 de Abril, exposed brick, street art murals, creative market weekend"),
    ("🇵🇹 · Porto, Ponte Dom Luís all'ora dorata", "Ponte Dom Luís I, Porto, double-deck iron bridge over Douro river, Vila Nova de Gaia wine cellars below, golden hour light, Ribeira district colourful facades"),
    ("🇵🇹 · Porto, Livraria Lello, scala Art Nouveau", "Livraria Lello, Porto, neo-Gothic bookshop interior, sweeping red Art Nouveau staircase, stained glass ceiling, dark wood shelves floor to ceiling, warm amber light"),
    ("🇵🇹 · Porto, Ribeira e azulejos", "Ribeira waterfront, Porto, UNESCO medieval quarter, colourful narrow facades with azulejo tiles, barcos rabelos wine boats on Douro, Cathedral hill above"),
    ("🇵🇹 · Porto, Stazione São Bento", "São Bento railway station, Porto, vast atrium covered floor to ceiling in 20,000 hand-painted blue azulejo tiles depicting Portuguese history, daily commuters below"),
    ("🇵🇹 · Sintra, Palazzo della Pena", "Palácio da Pena, Sintra, UNESCO Romantic palace on cloud-wreathed peak, eclectic towers in vivid yellow and red, Moorish battlements, forest mist"),
    ("🇵🇹 · Sintra, Quinta da Regaleira", "Quinta da Regaleira, Sintra, neo-Manueline palace, initiatic well with spiral staircase descending into earth, mystical garden, Templar symbolism, moss stones"),
    ("🇵🇹 · Sintra, Castello Moresco tra gli alberi", "Moorish Castle, Sintra, 8th century Arab fortification towers emerging from dense Atlantic forest canopy, granite walls, panoramic Serra de Sintra view"),
    ("🇵🇹 · Sintra, Monserrate, giardini romantici", "Palace of Monserrate, Sintra, neo-Gothic Moorish romantic palace, lush tropical gardens with 3,000 plant species, ornate facade with trefoil arches"),
    ("🇵🇹 · Óbidos, borgo medievale e merlate", "Óbidos, Portugal, perfectly preserved medieval walled town, whitewashed houses with yellow and blue borders, bougainvillea-draped battlements, castle"),
    ("🇵🇹 · Algarve, archi di Ponta da Piedade", "Ponta da Piedade, Lagos, Algarve, extraordinary golden limestone sea arch formations, emerald grottos, kayaks in turquoise water, vertical cliff walls"),
    ("🇵🇹 · Algarve, Praia da Marinha", "Praia da Marinha, Algarve, dramatic ochre rock formations framing secluded cove, crystal clear turquoise water, accessible via clifftop trail, no crowds"),
    ("🇵🇹 · Sagres, Fortezza atlantica", "Fortaleza de Sagres, Sagres, Algarve, promontory fortress at edge of the world, sheer Atlantic cliffs, wind-blasted, Cabo de São Vicente lighthouse visible"),
    ("🇵🇹 · Comporta, dune e oceano selvaggio", "Comporta, Alentejo coast, Portugal, wild Atlantic beach backed by rice paddies and cork oak forest, empty white sand dunes, bohemian beach village"),
    ("🇵🇹 · Tavira, ponte romano e saline", "Tavira, Eastern Algarve, Roman bridge over Gilão river, salt pans with flamingos, whitewashed Moorish town, Tavira Island barrier beach beyond"),
    ("🇵🇹 · Douro, vigneti a terrazze", "Douro Valley, Portugal, UNESCO terraced vineyards cascading to river, schist stone terraces, quintas wine estates, autumn harvest colours, river cruise boats"),
    ("🇵🇹 · Évora, cappella delle Ossa", "Chapel of Bones, Évora, Alentejo, interior walls and columns lined with 5,000 human skulls and bones, ossuary built by Franciscan monks, candlelit"),
    ("🇵🇹 · Évora, tempio romano nella piazza", "Roman Temple of Évora, Alentejo, remarkably preserved 1st century Corinthian columns, UNESCO historic centre, medieval buildings surrounding, evening light"),
    ("🇵🇹 · Tomar, Convento dei Templari", "Convento de Cristo, Tomar, Portugal, Knights Templar 12th century fortress, Manueline chapter window with marine motifs, round Templar church interior"),
    ("🇵🇹 · Viana do Castelo, Basilica di Santa Luzia", "Basilica of Santa Luzia, Viana do Castelo, Neo-Byzantine hilltop church, twin towers, panoramic Lima river estuary view, mosaic facade, northern Portugal"),
    ("🇵🇹 · Madeira, Cabo Girão, scogliera vertiginosa", "Cabo Girão, Madeira, one of Europe's highest sea cliffs at 580m, glass-floor skywalk over sheer drop to Atlantic, terraced vineyards on cliff face"),
    ("🇵🇹 · Madeira, Pico do Arieiro tra le nuvole", "Pico do Arieiro, Madeira, third highest peak at 1818m, volcanic pinnacles above cloud inversion layer, infinite sea of white clouds below, sharp ridges"),
    ("🇵🇹 · Madeira, Levada dos boschi", "Levada do Caldeirão Verde, Madeira, ancient irrigation channel trail through primeval laurisilva UNESCO forest, ferns, mossy rocks, waterfalls, cool mist"),
    ("🇵🇹 · Madeira, Funchal mercato dei fiori", "Mercado dos Lavradores, Funchal, Madeira, covered market, exotic tropical fruit and flower stalls, fishwives in traditional embroidered costume, azulejo walls"),
    ("🇵🇹 · Madeira, Ponta de São Lourenço", "Ponta de São Lourenço, Madeira, dramatic volcanic eastern peninsula, red and ochre layered cliffs, Atlantic crashing on both sides, narrow rocky ridge trail"),
    ("🇵🇹 · Azzorre, Sete Cidades, laghi gemelli", "Sete Cidades, São Miguel, Azores, twin volcanic crater lakes in blue and green, lush green caldeira walls, small village with white church, misty panorama"),
    ("🇵🇹 · Azzorre, Caldeira do Faial", "Caldeira do Faial, Azores, vast volcanic crater 2km wide and 400m deep, primeval hydrangea-lined rim path, cloud forest, volcanic silence"),
    ("🇵🇹 · Azzorre, Furnas, vapori termali", "Furnas Valley, São Miguel, Azores, steaming volcanic fumaroles and hot springs, terra nostra botanical gardens, cozido das Furnas cooked underground"),
    ("🇵🇹 · Azzorre, Flores, cascata Poço Bacalhau", "Poço do Bacalhau, Flores, Azores, dramatic 100m waterfall plunging into volcanic pool surrounded by emerald green vegetation, most beautiful in the archipelago"),
    ("🇵🇹 · Azzorre, Lagoa do Fogo in vetta", "Lagoa do Fogo, São Miguel, Azores, fire lake crater at altitude, pristine turquoise volcanic lake, white sand beach, no development, Atlantic backdrop"),
    ("🇵🇹 · Azzorre, Porto Pim, baia a mezzaluna", "Porto Pim bay, Faial, Azores, sheltered crescent bay backed by Monte da Guia volcanic headland, calm turquoise water, whale watching history, 18th century fortification"),
    ("🇵🇹 · Arrábida, caletta smeraldo", "Arrábida Natural Park, Setúbal, secluded emerald-green cove, Praia de Galapinhos, white limestone cliffs, Atlantic-Mediterranean vegetation, exceptional water clarity"),
    ("🇵🇹 · Porto, Torre dos Clérigos al tramonto", "Torre dos Clérigos, Porto, Baroque granite bell tower rising 75m above city, panoramic view over terracotta rooftops to Douro river and ocean"),
    ("🇵🇹 · Valle del Douro, nebbia mattutina", "Douro Valley dawn, Portugal, river emerging from morning fog between vine-covered schist hillsides, quinta farmhouses, perfect mirrored water reflection"),
    ("🇵🇹 · Castelo de Almourol, isola nel Tago", "Castelo de Almourol, Ribatejo, medieval Knights Templar castle on small rocky island in Tagus river, romantic isolation, tower and battlements, water surrounding"),

    # ══ 🇫🇷 FRANCIA ════════════════════════════════════════
    ("🇫🇷 · Parigi, Torre Eiffel al crepuscolo", "Eiffel Tower at dusk, Paris, France, iron lattice tower illuminated against deep blue twilight sky, Champ de Mars below, Seine river reflecting lights, city sparkle"),
    ("🇫🇷 · Parigi, Louvre, piramide di vetro", "Louvre Museum pyramid, Paris, I.M. Pei glass pyramid in Cour Napoléon, reflection in water basin, classical palace wings surrounding, winter light"),
    ("🇫🇷 · Parigi, Montmartre, Sacré-Cœur", "Sacré-Cœur Basilica, Montmartre hill, Paris, white Byzantine-Romanesque dome above city, wide steps with street artists and tourists, panoramic Paris view"),
    ("🇫🇷 · Versailles, Galleria degli Specchi", "Hall of Mirrors, Versailles, France, 357 mirrors reflecting 20,000 candles and chandeliers, gilded arched windows overlooking formal gardens, royal opulence"),
    ("🇫🇷 · Mont Saint-Michel, isola di marea", "Mont Saint-Michel, Normandy, France, medieval abbey island rising from tidal flats, causeway road, low tide sand stretching in all directions, dramatic sky"),
    ("🇫🇷 · Provenza, Gordes borgo in pietra", "Gordes, Provence, France, perched hilltop village of pale stone houses, Luberon valley panorama, lavender fields below in summer, Renaissance castle"),
    ("🇫🇷 · Provenza, lavanda in fiore", "Lavender fields of Valensole, Provence, France, endless purple rows converging to horizon, lonely stone farmhouse, golden wheat beyond, summer heat shimmer"),
    ("🇫🇷 · Costa Azzurra, Cap Ferrat", "Cap Ferrat, French Riviera, exclusive cape with Belle Époque villas hidden in pines, azure Mediterranean sea below cliffs, yacht-dotted bay, millionaire's paradise"),
    ("🇫🇷 · Alsazia, Colmar, case a graticcio", "Colmar, Alsace, France, Petite Venise canal quarter, half-timbered medieval houses in red green yellow, flower boxes at windows, canal reflection, fairy-tale atmosphere"),
    ("🇫🇷 · Parigi, Palais Royal, giardini colonnati", "Palais Royal gardens, Paris, colonnaded arcades, Buren striped columns installation in courtyard, formal French garden, hidden from boulevards, Parisian calm"),

    # ══ 🇬🇧 UK / IRLANDA ═══════════════════════════════════
    ("🇬🇧 · Londra, Tower Bridge all'alba", "Tower Bridge at dawn, London, England, Victorian Gothic drawbridge over Thames, pink and gold sky reflection, City of London skyline beyond, river mist"),
    ("🇬🇧 · Londra, Notting Hill, case colorate", "Notting Hill, London, pastel-coloured Georgian terraced houses on Portobello Road, market stalls below, antiques and flowers, quintessential English urban charm"),
    ("🇬🇧 · Londra, Big Ben e Westminster", "Houses of Parliament and Big Ben, Westminster, London, Gothic Revival architecture on Thames bank, Elizabeth Tower, reflection in river, evening light"),
    ("🇬🇧 · Scozia, Castello di Edimburgo", "Edinburgh Castle, Scotland, volcanic rock fortress dominating city skyline, medieval ramparts and crown square, city of Edinburgh spread below, dramatic clouds"),
    ("🇬🇧 · Scozia, Eilean Donan Castle", "Eilean Donan Castle, Scottish Highlands, iconic 13th century castle on small island at confluence of three lochs, stone bridge, mountain reflections, misty dawn"),
    ("🇬🇧 · Scozia, Highlands, Glen Coe", "Glen Coe, Scottish Highlands, dramatic glacier-carved valley, steep ridges of Three Sisters mountains, brooding dark clouds, purple heather, rushing stream"),
    ("🇬🇧 · Inghilterra, Stonehenge nella nebbia", "Stonehenge, Wiltshire, England, prehistoric megalith stone circle in early morning mist, Neolithic monument, Salisbury Plain, atmospheric low light, mystery"),
    ("🇬🇧 · Cotswolds, borgo in pietra dorata", "Bourton-on-the-Water, Cotswolds, England, honey-stone village, low bridges over River Windrush, weeping willows, thatched cottages, English countryside idyll"),
    ("🇮🇪 · Irlanda, Cliffs of Moher", "Cliffs of Moher, County Clare, Ireland, sheer 214m Atlantic cliffs stretching 14km along wild west coast, crashing waves below, green fields to cliff edge, seabirds"),
    ("🇮🇪 · Irlanda, Skellig Michael", "Skellig Michael, County Kerry, Ireland, UNESCO early medieval beehive monk cells on remote Atlantic rock pinnacle, 600 stone steps, puffin colony, isolation"),

    # ══ 🇩🇪 GERMANIA / AUSTRIA ═════════════════════════════
    ("🇩🇪 · Baviera, Neuschwanstein nella foresta", "Neuschwanstein Castle, Bavaria, Germany, fairy-tale 19th century royal castle perched on forested Alpine cliff, Hohenschwangau valley below, misty mountain backdrop"),
    ("🇩🇪 · Berlino, porta di Brandeburgo", "Brandenburg Gate at dusk, Berlin, Germany, neoclassical sandstone triumphal arch, Quadriga sculpture above, Pariser Platz, blue hour sky, dramatic perspective"),
    ("🇩🇪 · Rothenburg ob der Tauber", "Rothenburg ob der Tauber, Bavaria, Germany, perfectly preserved medieval walled town, half-timbered houses, Christmas market, Plönlein timber-framed corner house"),
    ("🇦🇹 · Vienna, Palazzo Schönbrunn", "Schönbrunn Palace, Vienna, Austria, UNESCO Baroque imperial residence, ochre yellow facade, formal French garden, Gloriette triumphal arch on hill above, panorama"),

    # ══ 🇪🇸 SPAGNA ═════════════════════════════════════════
    ("🇪🇸 · Alhambra, cortile moresco", "Court of the Lions, Alhambra, Granada, Andalusia, 14th century Nasrid palace, twelve marble lions fountain, intricate carved stucco, arabesque arches, water channels"),
    ("🇪🇸 · Barcellona, Sagrada Família", "Sagrada Família interior, Barcelona, Gaudí's forest of stone columns branching to stained glass canopy, morning light flooding coloured glass, transcendent architectural space"),
    ("🇪🇸 · Siviglia, Plaza de España al tramonto", "Plaza de España, Seville, Andalusia, semicircular Renaissance-Moorish palace complex, canal with gondola-style boats, ornate azulejo tile alcoves for each Spanish province"),
    ("🇪🇸 · Toledo, vista panoramica sul Tago", "Toledo, Castilla-La Mancha, Spain, UNESCO imperial city on rocky promontory above Tagus river bend, cathedral spire, mosque minaret, synagogue, three cultures panorama"),
    ("🇪🇸 · Ronda, il Ponte Nuovo sul burrone", "Ronda, Andalusia, Spain, Puente Nuevo bridge spanning 120m-deep El Tajo gorge, 18th century neoclassical arch, white village houses on cliff edge, dramatic vertigo"),

    # ══ 🌍 EST EUROPA ══════════════════════════════════════
    ("🇨🇿 · Praga, orologio astronomico", "Astronomical Clock, Prague, Czech Republic, Gothic Orloj mechanism on Old Town Hall tower, medieval zodiac dials, hourly procession of apostles, cobbled Staroměstské Square"),
    ("🇨🇿 · Praga, Ponte Carlo all'alba", "Charles Bridge at dawn, Prague, misty Vltava river, 30 Baroque saint statues on parapet, Prague Castle and Cathedral silhouette above, blue hour light"),
    ("🇭🇷 · Dubrovnik, mura sull'Adriatico", "City walls of Dubrovnik, Croatia, UNESCO medieval fortification circuit, terracotta rooftops inside, crystalline Adriatic sea below, limestone cliffs, Lokrum island"),
    ("🇵🇱 · Cracovia, Piazza del Mercato", "Main Market Square, Kraków, Poland, largest medieval square in Europe, Gothic Cloth Hall Sukiennice, St Mary's Basilica twin towers, horse-drawn carriages, evening light"),
    ("🇷🇴 · Transilvania, Castello di Bran", "Bran Castle, Transylvania, Romania, Dracula's castle on rocky cliff, 14th century fortification with towers, dense pine forest below, Carpathian mountain backdrop"),
    ("🇭🇺 · Budapest, Parlamento sul Danubio", "Hungarian Parliament Building, Budapest, reflected in Danube river, neo-Gothic spires, largest parliament in Europe, illuminated at night, Chain Bridge alongside"),

    # ══ 🇩🇪 GERMANIA / AUSTRIA ═════════════════════════════
    ("🇦🇹 · Hallstatt, specchio sul lago", "Hallstatt, Salzkammergut, Austria, UNESCO alpine village of pastel houses on narrow lakeside ledge, mirror-calm Hallstätter See reflection, salt mine above"),

    # ══ 🌍 EST EUROPA ══════════════════════════════════════
    ("🇸🇰 · Bratislava, castello sopra il Danubio", "Bratislava Castle, Slovakia, white four-towered fortress on hill above old town, Danube river below, Austria and Hungary visible beyond, inverted table silhouette"),
    ("🇸🇮 · Ljubljana, castello nella nebbia", "Ljubljana Castle on forested hill, Slovenia, medieval fortress above Baroque old town, dragon bridge below, Ljubljanica river, compact and charming capital"),
    ("🇧🇦 · Mostar, Stari Most sul Neretva", "Stari Most bridge, Mostar, Bosnia-Herzegovina, UNESCO 16th century Ottoman stone arch bridge over Neretva river, divers jumping tradition, mosque minarets, cobbled bazaar"),
    ("🇬🇷 · Grecia, Santorini Oia, caldera", "Santorini caldera, Oia, Greece, iconic white-cubic Cycladic architecture cascading down volcanic cliff, blue-domed churches, infinity pool edge, Aegean sunset panorama"),

    # ══ 🌎 AMERICA DEL NORD ════════════════════════════════
    ("🇺🇸 · New York, skyline da Central Park", "New York City skyline from Central Park, Manhattan skyscrapers above autumn tree canopy, Central Park Lake reflection, Empire State and Chrysler buildings, magic hour"),
    ("🇺🇸 · New York, Manhattan skyline notturno", "Manhattan skyline at night from Brooklyn Bridge Park, East River reflection, lights of Wall Street and One World Trade Center, suspension bridge cables in foreground"),
    ("🇺🇸 · New York, Brooklyn Bridge all'alba", "Brooklyn Bridge at sunrise, New York, stone Gothic towers and steel cables, lower Manhattan skyline golden, walking path above traffic lanes, river mist below"),
    ("🇺🇸 · Chicago, Loop Architecture", "Chicago Loop, Illinois, canyons of skyscraper architecture, Art Deco and modernist towers, Chicago River reflections, Marina City corncob towers, cloud gate surroundings"),
    ("🇺🇸 · Arizona, Antelope Canyon", "Upper Antelope Canyon, Arizona, Navajo land, slot canyon flowing sandstone walls sculpted by water, narrow light beams penetrating from above, orange and red swirling rock"),
    ("🇺🇸 · Arizona, Grand Canyon al tramonto", "Grand Canyon South Rim at sunset, Arizona, layered geological strata in crimson orange and purple, Colorado River silver thread below, mile-deep canyon, infinite scale"),
    ("🇺🇸 · Arizona, Monument Valley alba", "Monument Valley, Arizona-Utah, iconic West and East Mitten Buttes rising from desert floor at dawn, pink sky, long shadows, Navajo Nation sacred landscape"),
    ("🇺🇸 · Utah, Bryce Canyon, hoodoos", "Bryce Canyon, Utah, vast amphitheatre of orange and red hoodoo rock spires in horseshoe-shaped bowl, Navajo Loop Trail below, Ponderosa pines between formations"),
    ("🇺🇸 · California, Big Sur, Highway One", "Big Sur coastline, California, Highway 1 winding along dramatic Pacific cliff edge, Bixby Creek Bridge, turquoise sea below, rolling green hills above, fog"),
    ("🇺🇸 · Hawaii, Na Pali Coast, Kauai", "Nā Pali Coast, Kauai, Hawaii, emerald fluted sea cliffs rising 1,200m from Pacific Ocean, Kalalau Valley, tropical green ridges, isolated sea caves, boat perspective"),
    ("🇺🇸 · New Orleans, French Quarter", "French Quarter, New Orleans, Louisiana, ornate cast-iron balconies dripping Spanish moss and ferns, Bourbon Street jazz clubs, Creole architecture, humid evening light"),
    ("🇺🇸 · Miami, South Beach Art Déco", "Ocean Drive, South Beach, Miami, Florida, pastel Art Déco buildings from 1930s-40s, neon signs, palm trees, lifeguard towers, Atlantic Ocean behind, golden afternoon"),
    ("🇺🇸 · Las Vegas, Strip di notte", "Las Vegas Strip at night, Nevada, impossible concentration of illuminated casino-hotel mega-structures, Bellagio fountains, replica Eiffel Tower, neon excess, desert heat"),
    ("🇺🇸 · Yellowstone, Grand Prismatic", "Grand Prismatic Spring, Yellowstone, Wyoming, largest hot spring in USA, vivid rainbow rings of thermophilic bacteria, deep sapphire blue centre, steam rising, aerial view"),
    ("🇺🇸 · Niagara Falls, arcobaleno", "Niagara Falls, New York-Ontario border, Horseshoe Falls thundering wall of water, permanent rainbow in mist, Maid of the Mist boat below, sheer volume of water"),
    ("🇨🇦 · Banff, lago Louise turchese", "Lake Louise, Banff National Park, Alberta, Canada, glacial turquoise lake, Victoria Glacier at far end, Château Lake Louise hotel, perfect mountain reflection"),
    ("🇨🇦 · Vancouver, montagne e città", "Vancouver, British Columbia, Canada, downtown glass towers with snow-capped North Shore mountains directly behind, Stanley Park, Burrard Inlet, world's most scenic city"),
    ("🇲🇽 · Messico, Chichen Itza, El Castillo", "El Castillo pyramid, Chichen Itza, Yucatán, Mexico, UNESCO Maya pyramid, serpent shadow equinox phenomenon, jungle clearing, sacrificial cenote nearby, pre-Columbian grandeur"),
    ("🇲🇽 · Messico, Guanajuato, callejón del Beso", "Callejón del Beso, Guanajuato, Mexico, narrowest alley in colonial silver city, brightly coloured balconies nearly touching above, cobblestones, romantic legend"),
    ("🇺🇸 · San Francisco, Golden Gate nella nebbia", "Golden Gate Bridge, San Francisco, California, iconic international orange suspension bridge emerging from rolling Pacific fog bank, Marin Headlands green hills beyond"),

    # ══ 🌎 AMERICA DEL SUD ═════════════════════════════════
    ("🇵🇪 · Perù, Machu Picchu all'alba", "Machu Picchu, Peru, UNESCO Inca citadel on cloud forest mountain, terraces and temples emerging from morning mist, Huayna Picchu peak behind, Andean sacred site"),
    ("🇧🇷 · Brasile, Rio, Cristo Redentore", "Christ the Redeemer, Corcovado, Rio de Janeiro, Brazil, Art Deco statue on granite peak above city, Guanabara Bay and Sugar Loaf below, tropical atlantic forest"),
    ("🇧🇷 · Brasile, Rio, Copacabana dall'alto", "Copacabana beach, Rio de Janeiro, Brazil, iconic crescent of white sand backed by mosaic promenade and apartment blocks, Sugarloaf mountain visible, Atlantic surf"),
    ("🇦🇷 · Argentina, Cascate di Iguazú", "Iguazú Falls, Argentina-Brazil border, system of 275 waterfalls, Devil's Throat horseshoe cataract, subtropical rainforest mist, rainbow above rushing water, toucans"),
    ("🇨🇱 · Cile, Isola di Pasqua, moai", "Easter Island, Chile, Ahu Tongariki, 15 giant moai statues on coastal ahu platform, sunrise with star reflections in tidal pool, volcanic Rano Raraku crater behind"),
    ("🇧🇷 · Brasile, Baia do Sancho, Fernando de Noronha", "Baía do Sancho, Fernando de Noronha, Brazil, consistently rated world's most beautiful beach, enclosed cove with vertical green-red cliffs, electric blue water, spinner dolphins"),
    ("🇨🇴 · Colombia, Cartagena, città vecchia", "Cartagena de Indias, Colombia, UNESCO colonial walled city, bougainvillea-draped balconies in vivid colours, cobblestone streets, Caribbean heat, La Popa hill above"),
    ("🇧🇴 · Bolivia, Salar de Uyuni, cielo riflesso", "Salar de Uyuni, Bolivia, world's largest salt flat, infinite mirror of sky when flooded with thin water layer, cactus islands, perfect cloud reflections, altitude"),
    ("🇪🇨 · Ecuador, Galápagos, Pinnacle Rock", "Pinnacle Rock, Bartolomé Island, Galápagos, Ecuador, volcanic tuff tower above turquoise bay, marine iguanas, Galápagos penguins, sunrise over lava fields"),
    ("🇺🇾 · Uruguay, Colonia del Sacramento", "Colonia del Sacramento, Uruguay, UNESCO colonial Portuguese quarter, cobblestone Calle de los Suspiros, lighthouse on rocky point, Río de la Plata estuary, Buenos Aires opposite"),

    # ══ 🌍 AFRICA ══════════════════════════════════════════
    ("🇲🇦 · Marocco, Chefchaouen, medina blu", "Chefchaouen, Morocco, Rif mountains blue city, labyrinthine medina with buildings painted in a hundred shades of blue, flower pots, cat alleys, cool mountain air"),
    ("🇲🇦 · Marocco, Marrakech, Djemaa el-Fna", "Djemaa el-Fna square, Marrakech, Morocco, UNESCO living cultural space, snake charmers acrobats storytellers, orange juice stalls, spice aromas, minarets above medina"),
    ("🇪🇬 · Egitto, Piramidi di Giza al tramonto", "Great Pyramid complex, Giza, Egypt, three pyramids and Sphinx in desert, warm amber sunset light, camel silhouette foreground, Cairo haze beyond, ancient wonder"),
    ("🇪🇬 · Egitto, Abu Simbel, statue colossali", "Abu Simbel temple, Aswan, Egypt, four colossal 20m-tall seated statues of Ramesses II carved into cliff face, UNESCO rescued from Nile flooding, golden stone"),
    ("🇿🇦 · Sud Africa, Cape Town, Table Mountain", "Table Mountain, Cape Town, South Africa, flat-topped sandstone massif with tablecloth cloud waterfall, city bowl below, Twelve Apostles range, two oceans meeting"),
    ("🇳🇦 · Namibia, Sossusvlei, dune rosse", "Sossusvlei, Namib Desert, Namibia, world's highest red-orange sand dunes at 325m, Dead Vlei white salt pan with blackened camel thorn trees, sunrise rim walkers"),
    ("🇰🇪 · Kenya, Masai Mara, migrazione", "Masai Mara, Kenya, great wildebeest migration, endless savanna plain, acacia tree silhouettes, vast herds at golden hour, Mara River crossing, Africa's greatest show"),
    ("🇹🇿 · Tanzania, Kilimanjaro, cima con ghiacciai", "Mount Kilimanjaro summit zone, Tanzania, Africa's highest peak, Uhuru Peak at 5895m, receding glaciers, volcanic crater, cloud layer far below, space-like altitude"),
    ("🇸🇨 · Seychelles, Anse Source d'Argent", "Anse Source d'Argent, La Digue, Seychelles, iconic giant pink granite boulders, shallow turquoise lagoon, white sand, coconut palms, most photographed beach in world"),
    ("🇲🇿 · Mozambico, Ibo Island, fort portoghese", "Ibo Island, Quirimbas Archipelago, Mozambique, crumbling Portuguese colonial fort, coral rag stone buildings, baobab trees, dhow sailing boat in coral sea, timeless"),

    # ══ 🌏 ASIA ════════════════════════════════════════════
    ("🇯🇵 · Giappone, Kyoto, Fushimi Inari torii", "Fushimi Inari Taisha, Kyoto, Japan, thousands of vermilion torii gates winding up wooded Mount Inari, predawn visit with no crowds, fox shrine, sacred cedar forest"),
    ("🇯🇵 · Giappone, Monte Fuji con ciliegio", "Mount Fuji, Japan, perfect volcanic cone reflected in Kawaguchiko lake, Chureito Pagoda in foreground through cherry blossom cloud, quintessential Japanese composition"),
    ("🇯🇵 · Giappone, Nara, cervi e tempio", "Tōdai-ji temple and deer park, Nara, Japan, wild sika deer roaming freely among visitors, Great Buddha Hall housing largest bronze Buddha, maple autumn colours"),
    ("🇮🇳 · India, Taj Mahal all'alba", "Taj Mahal at sunrise, Agra, India, white marble mausoleum with four minarets reflected in long water channel, perfectly symmetrical Mughal garden, peachy pink sky"),
    ("🇨🇳 · Cina, Grande Muraglia, Jinshanling", "Jinshanling section, Great Wall of China, Ming dynasty stone fortification snaking over mountain ridges, watchtowers at peaks, autumn colours, Beijing region"),
    ("🇹🇭 · Thailandia, Chiang Mai, tempio Doi Suthep", "Doi Suthep temple, Chiang Mai, Thailand, 14th century golden chedi above teak forest, 300 steps with naga serpent balustrade, panoramic city view at sunset"),
    ("🇰🇭 · Cambogia, Angkor Wat all'alba", "Angkor Wat, Cambodia, 12th century Khmer temple reflected in northern reflecting pool at sunrise, lotus flowers, monks' orange robes, jungle encroaching on towers"),
    ("🇻🇳 · Vietnam, Baia di Halong", "Ha Long Bay, Vietnam, UNESCO 2000 limestone karst islands rising from emerald green sea, traditional junk boat sailing through, morning mist, fishing villages on water"),
    ("🇮🇩 · Indonesia, Bali, Terrazze di Tegalalang", "Tegalalang rice terraces, Ubud, Bali, Indonesia, UNESCO subak irrigation system, vivid green tiered paddies, coconut palms, morning light from east, Balinese offering"),
    ("🇯🇴 · Giordania, Petra, il Tesoro", "Treasury Al-Khazneh, Petra, Jordan, Nabataean rock-carved facade 40m tall emerging from rose-red sandstone canyon Siq, camel silhouette, Lawrence of Arabia atmosphere"),

    # ══ 🌏 OCEANIA ═════════════════════════════════════════
    ("🇦🇺 · Australia, Uluru al tramonto", "Uluru, Northern Territory, Australia, sacred Anangu monolith 348m high, glowing deep red-orange at sunset, spinifex grass foreground, endless flat desert, spiritual presence"),
    ("🇦🇺 · Australia, Sydney, Opera House", "Sydney Opera House, New South Wales, Australia, UNESCO white shell-sail roof structures on Bennelong Point, Harbour Bridge behind, ferry wake, morning light"),
    ("🇦🇺 · Australia, Whitsundays, Heart Reef", "Heart Reef, Whitsunday Islands, Queensland, Australia, natural coral reef in perfect heart shape seen from seaplane above, turquoise Coral Sea, Great Barrier Reef"),
    ("🇦🇺 · Australia, Great Ocean Road, Apostoli", "Twelve Apostles, Great Ocean Road, Victoria, Australia, limestone sea stacks rising from Southern Ocean surf, sandstone cliffs, helicopter perspective, sunset reds"),
    ("🇳🇿 · Nuova Zelanda, Milford Sound", "Milford Sound, Fiordland, New Zealand, Mitre Peak 1692m rising vertically from dark fjord water, waterfalls cascading down walls, cruise boat scale, rain forest mist"),
    ("🇳🇿 · Nuova Zelanda, Tongariro, crateri vulcanici", "Tongariro Alpine Crossing, New Zealand, UNESCO active volcanic landscape, Emerald Lakes with vivid turquoise acid water, Red Crater steam vents, lunar otherworldly"),
    ("🇫🇯 · Fiji, laguna di sabbia bianca", "Yasawa Islands, Fiji, remote coral-ringed island lagoon, powdery white sand, electric blue transparent water over coral, palm frond foreground, local bure hut"),
    ("🇵🇫 · Polinesia Francese, bungalow sull'acqua", "Bora Bora, French Polynesia, overwater bungalows on turquoise lagoon, Mount Otemanu volcanic peak, barrier reef, coral gardens below crystal floor, ultimate paradise"),
    ("🇼🇸 · Samoa, costa vulcanica", "Savai'i volcanic coast, Samoa, black lava fields reaching Pacific Ocean, ancient lava tubes, coconut palms, traditional fale huts, starfish beach, remote South Pacific"),

    # ══ ALTRO ═════════════════════════════════════════════

    # ══ 🚀 SPAZIO, SCI-FI & FANTASY (30) ══════════════════════════════════
    ("🌙 · Luna, allunaggio con LEM e astronauta", "Apollo lunar landing site, Moon surface, grey cratered regolith, NASA Lunar Module Eagle with gold foil legs, astronaut in white EVA suit with mirrored visor, Earth rising above lunar horizon, black star-filled space, no atmosphere, harsh directional sunlight casting sharp shadows, desolate grandeur, photorealistic NASA archive aesthetic"),
    ("🔴 · Marte, accanto al rover Perseverance", "Mars surface, Jezero Crater, rusty red iron-oxide dust plain, NASA Perseverance rover beside subject, panoramic Martian horizon, pink-ochre dusty sky, low sun angle, distant mesa formations, tyre tracks in red soil, scientific equipment visible, photorealistic NASA Mars mission aesthetic, epic isolation"),
    ("🪐 · Giove, il Monolito di 2001 Odissea nello Spazio", "2001 A Space Odyssey aesthetic, floating in Jupiter orbit, massive perfectly black rectangular Monolith hovering in space, Jupiter's swirling Great Red Spot storm below, Stanley Kubrick ultra-precise composition, blue dawn light of star alignment, Ligeti Atmosphères atmosphere, primordial cosmic awe, photorealistic hard sci-fi"),
    ("💫 · Saturno, pattinare sugli anelli", "Saturn's rings close-up perspective, subject skating on flat ice-particle ring surface, Saturn's golden banded atmosphere filling half the sky above, other ring sheets visible in layers, distant sun, deep space beyond, ring particles ranging from dust to boulders visible around, impossible dreamlike scale, photorealistic space photography aesthetic"),
    ("👽 · Pianeta alieno, con abitanti extraterrestri", "Alien planet surface, bioluminescent purple and teal vegetation, double moons in sky, crystalline rock formations, two or three friendly alien beings of original non-human design standing near subject, alien architecture in background, impossible colors, James Cameron Avatar-scale world-building, cinematic photorealistic alien landscape"),
    ("🕳️ · Astronave nel wormhole, come in Contact", "Inside spacecraft cockpit traversing wormhole, Contact film 1997 Zemeckis aesthetic, swirling iridescent tunnel of spacetime with concentric light rings stretching to infinity, stars smearing into streaks, pod chair visible, interior bathed in warm amber and cold blue light alternating, Jodie Foster wide-eyed wonder expression reference, photorealistic cinematic"),
    ("⚡ · DeLorean, ritorno al futuro", "Back to the Future DeLorean DMC-12 time machine, stainless steel gull-wing doors open, flux capacitor glowing inside, Mr. Fusion reactor on back, lightning storm at Twin Pines Mall parking lot, 88mph fire trails on asphalt, Robert Zemeckis 1985 cinematic aesthetic, neon rain, photorealistic film still"),
    ("🦇 · Batmobile, Gotham di notte", "Tim Burton Gotham City 1989 aesthetic, original Batmobile elongated jet-turbine car on rain-slicked gothic street, art deco gargoyle skyscrapers above, searchlight bat-signal in purple night sky, subject beside open cockpit, dramatic chiaroscuro street lighting, Danny Elfman atmosphere, photorealistic film noir"),
    ("🎵 · Mos Eisley Cantina, Star Wars IV", "Mos Eisley Cantina, Tatooine, Star Wars A New Hope 1977 aesthetic, dimly lit alien bar interior, Figrin D'an and the Modal Nodes playing cantina band music, diverse alien species at rounded booths, Han Solo's booth in background, warm amber practical lighting, bar stools and drinks, John Williams cantina music visual energy, photorealistic film still"),
    ("🌌 · Endor, foresta degli Ewok", "Forest moon of Endor, Star Wars Return of the Jedi, ancient redwood-scale trees, Ewok village rope bridges and wooden platforms high in canopy, Ewoks in background, dappled forest light, Imperial AT-AT walker silhouette through trees, warm golden forest light, John Williams adventure score energy, photorealistic film still"),
    ("🏜️ · Tatooine, canyon di Beggar's Canyon", "Tatooine twin sunset, Star Wars, red rock canyon walls, Lars homestead dome visible on flat desert horizon, twin suns setting in amber sky, binary sunset Luke Skywalker composition reference, desert wind dust, remote alien frontier, John Williams Force theme visual atmosphere, photorealistic film still"),
    ("🖖 · Ponte dell'Enterprise, Star Trek TOS", "USS Enterprise bridge, Star Trek Original Series 1966 aesthetic, circular command centre, Kirk's captain chair, colourful blinking control panels, Spock at science station hooded viewer, uhura communications earpiece, primary colour crew uniforms, viewscreen with stars, Alexander Courage fanfare visual energy, photorealistic 1960s TV production design"),
    ("🌀 · Pianeta Vulcano, Star Trek TOS", "Planet Vulcan surface, Star Trek Original Series aesthetic, red-orange desert landscape, twin moons, angular modernist Vulcan architecture in stone and metal, Mount Seleya in background, ceremonial grounds, logic and discipline atmosphere, ancient alien civilisation grandeur, photorealistic 1960s science fiction aesthetic updated to cinematic quality"),
    ("👾 · Città di Organa, Star Trek TOS holodeck", "Star Trek Original Series alien planet city set, primary colored geometric architecture, M-class planet with orange sky, classic series transporter beam effect, communicator prop visible, Tricorder scanning gesture, James T. Kirk swaggering diplomacy energy, bold primary color palette, photorealistic 1960s science fiction aesthetic"),
    ("⏰ · Tesseract, Interstellar", "Interstellar tesseract interior, Christopher Nolan 2014, infinite bookshelf corridor bending into five dimensions, Cooper falling through timeframes, hands reaching through shelves, gravitational anomaly sand patterns, warm dust-light filtering through dimensional cracks, Hans Zimmer pipe organ score visual energy, IMAX cinematic quality, photorealistic"),
    ("🌊 · Pianeta d'acqua, Gargantua, Interstellar", "Miller's water planet, Interstellar, Gargantua black hole looming impossibly large on horizon warping light behind it, vast shallow ocean knee-deep, enormous tidal wave wall kilometres high on horizon, wrecked Ranger spacecraft partly submerged, alien blue-white light, Hans Zimmer Cornfield Chase visual atmosphere, photorealistic IMAX cinematic"),
    ("🛸 · X-Files, campo di grano con Mulder e Scully", "X-Files aesthetic, rural Oregon cornfield at night, two FBI agents in dark suits with flashlights — male with loosened tie, female with red hair — looking up at hovering flying saucer craft with blinding white light beam, government black SUVs in background, Mark Snow paranoid score atmosphere, photorealistic 1990s TV film noir"),
    ("🌈 · Dimensione LSD onirica psichedelica", "Psychedelic surrealist dreamscape, Salvador Dali meets Yellow Submarine Beatles animation, melting clocks and impossible architecture, kaleidoscopic fractal sky in magenta violet gold, giant flowers as tall as buildings, checkered floor dissolving into clouds, M.C. Escher impossible staircases, Rick Griffin psychedelic poster palette, everything hyper-detailed and iridescent"),
    ("💍 · Contea degli Hobbit, La Shire", "The Shire, Lord of the Rings Peter Jackson trilogy aesthetic, rolling green hills of Hobbiton, round hobbit hole doors with circular windows, manicured gardens with giant vegetables, Party Tree in background, warm afternoon golden light, Bag End chimney smoke, Howard Shore pastoral score visual energy, photorealistic New Zealand landscape"),
    ("🌋 · Monte Fato, Mordor, Signore degli Anelli", "Mount Doom, Mordor, Lord of the Rings Peter Jackson, active volcanic crater edge with molten lava rivers, Barad-dûr tower with lidless Eye of Sauron in dark sky, ash falling like snow, red hellish atmosphere, extreme heat haze, Howard Shore dramatic score visual energy, photorealistic WETA Workshop cinematic quality"),
    ("🧝 · Rivendell, Ultima Casa Accogliente", "Rivendell, Lord of the Rings, elven architecture of waterfalls and elegant stone bridges, autumn forest canopy in gold and amber, Hall of Fire interior with carved pillars, Alan Lee concept art aesthetic, Howard Shore elven theme visual atmosphere, long shadows and mist over the valley, photorealistic Peter Jackson trilogy quality"),
    ("⚡ · Grande Sala di Hogwarts, Harry Potter", "Great Hall of Hogwarts, Harry Potter, enchanted ceiling showing night sky with floating candles, four house tables, owls delivering post, golden goblets and magical feast, John Williams Hedwig's Theme visual energy, stone Gothic arches, torchlight on ancient banners, photorealistic Warner Bros film aesthetic, back-to-school wonder"),
    ("🦕 · Jurassic Park, T-Rex di notte", "Jurassic Park 1993 Spielberg, Isla Nublar at night during storm, massive Tyrannosaurus Rex looming through electrified fence torn open, jeep headlights illuminating rain, John Williams score visual panic, tropical vegetation crushed by enormous feet, DANGER HIGH VOLTAGE sign fallen, photorealistic ILM visual effects aesthetic"),
    ("🕸️ · New York di Spider-Man, tetti al tramonto", "Marvel Spider-Man New York, sunset rooftop aerial view, Manhattan skyline in golden hour, web-slinging trajectory lines visible in air, water towers and fire escapes, Empire State Building in background, heroic pose on gargoyle, Danny Elfman 2002 Sam Raimi score visual energy, photorealistic cinematic Marvel"),
    ("🔨 · Asgard, il Palazzo di Odino", "Asgard, Marvel MCU, Kenneth Branagh Thor aesthetic, golden palace with rainbow Bifrost bridge stretching across space, Norse-mythology-scale architecture, cosmos and nebula sky, Mjolnir crackling with lightning, Patrick Doyle heroic fanfare visual energy, gods-eye scale grandeur, photorealistic Marvel Studios cinematic quality"),
    ("🧲 · Wakanda, trono di vibranio", "Wakanda Royal Palace, Marvel Black Panther, Ryan Coogler aesthetic, vibranium crystalline architecture with Afrofuturist design, Throne Room with carved ceremonial decor, Golden City panorama through arched window, Ludwig Göransson score visual energy, advanced technology meets ancient tradition, photorealistic Marvel Studios quality"),
    ("🌀 · Dimensione dello Specchio, Doctor Strange", "Mirror Dimension, Marvel Doctor Strange, Scott Derrickson aesthetic, New York City folding and fractalizing into impossible Escher geometry, buildings rotating and multiplying in kaleidoscopic recursion, orange golden sling ring portal sparks, Michael Giacchino score visual energy, photorealistic Marvel VFX cinematic quality"),
    ("🧊 · Palazzo di ghiaccio, Frozen", "Ice Palace, Frozen Disney, Elsa's crystalline mountain fortress, every surface of perfect blue-white transparent ice, aurora borealis sky, snowflakes frozen mid-air, grand staircase of ice leading to open balcony, Christophe Beck Let It Go visual energy, breath-visible cold air, photorealistic Disney animation aesthetic adapted to live-action"),
    ("🌺 · Pandora di notte, Avatar", "Pandora night, James Cameron Avatar, bioluminescent jungle, floating Hallelujah Mountains with waterfalls, Na'vi Tree of Souls glowing in distance, every plant emitting cyan and violet light, great leonopteryx pterodactyl silhouette in sky, James Horner score visual energy, photorealistic ILM Avatar cinematic quality"),
    ("🏰 · Hogwarts di notte, torre astronomica", "Hogwarts Astronomy Tower at night, Harry Potter, grey stone battlements under brilliant star field, telescopes set up by students in robes, owlery tower visible, forbidden forest dark mass below, Black Lake reflecting castle lights, John Williams score visual wonder, photorealistic Warner Bros film aesthetic"),

    ("🚀 · ISS, veduta dalla stazione spaziale", "International Space Station orbital photography, Earth curve visible below, random Earth region from 408km altitude — one of: Italian peninsula boot shape, Nile delta green fan, Amazon river bends, Sahara sand dunes from above, coral reef atolls, hurricane eye, Himalayan peaks above clouds, city lights grid at night — thin atmosphere blue arc, solar panel edge in frame, curvature of Earth, weightless cosmic overview perspective"),

    # ══ 👾 ALIEN — stile H.R. Giger ════════════════════════════════════════════
    ("👾 · Alien — corridoio biomeccanico della nave", "H.R. Giger biomechanical corridor, deep space derelict spacecraft interior, ribbed organic walls fused with industrial metal, bioluminescent slime trails, ovomorphs eggs in pale mist on floor, motion tracker blinking green, single emergency red light beam cutting through darkness, claustrophobic tunnel perspective, Ridley Scott Alien 1979 cinematic atmosphere, photorealistic horror science fiction"),
    ("👾 · Alien — hive chamber, uova e resina", "Xenomorph hive, Aliens 1986 James Cameron aesthetic, cavernous biomechanical chamber coated in dark organic resin secretions, hundreds of eggs in rows, faint blue-green bioluminescent glow from egg openings, cocooned forms in walls, acid burn scars on floor, atmospheric fog, hellish alien architecture, photorealistic cinematic horror"),
    ("👾 · Alien — Engineer spacecraft, sala della mappa stellare", "Prometheus 2012 Ridley Scott, Engineer derelict spacecraft interior, vast circular orrery chamber with holographic star map projecting galaxy in centre, black stone monumental architecture, murals carved in stone showing space jockey figures, green bioluminescent light, ancient alien grandeur and cosmic dread, photorealistic IMAX cinematic quality"),
    ("👾 · Alien — pianeta LV-426, tempesta di sabbia", "LV-426 exomoon surface, Alien franchise atmosphere, perpetual violent electrical storm, acidic orange-brown sky with lightning, barren volcanic rock plain, crashed spacecraft silhouette on distant horizon, abandoned colony ruins, terraformer cooling towers venting steam, no breathable atmosphere, desolate hostile alien world, photorealistic science fiction"),

    # ══ 🚀 LOST IN SPACE ═══════════════════════════════════════════════════════
    ("🚀 · Lost in Space — Jupiter 2 su pianeta alieno", "Lost in Space Netflix 2018 reboot aesthetic, Jupiter 2 spacecraft landed on alien planet surface, dramatic alien sky with unusual colored moons, crystalline rock formations, Robinson family campsite with advanced equipment, Robot B9 standing sentinel nearby, alien plant life in foreground, survival camp atmosphere, photorealistic cinematic science fiction"),
    ("🚀 · Lost in Space — foresta aliena con Robot", "Lost in Space 2018 Netflix, dense alien forest with bioluminescent blue-white tree trunks, alien fauna in shadows, Robot B9 standing tall in dramatic light, emergency flares casting orange glow, ground covered in iridescent alien moss, survival gear scattered, atmospheric fog, photorealistic cinematic science fiction"),
    ("🚀 · Lost in Space — cockpit del Jupiter 2", "Jupiter 2 spacecraft cockpit interior, Lost in Space Netflix aesthetic, curved panoramic viewport showing alien planet atmosphere below, holographic navigation displays, advanced control panels in warm amber emergency lighting, zero-gravity handholds, survival equipment secured to walls, photorealistic hard science fiction"),

    # ══ 🏝️ LOST ════════════════════════════════════════════════════════════════
    ("🏝️ · Lost — spiaggia dei sopravvissuti, relitto 815", "Lost ABC TV 2004, tropical beach crash site, Oceanic Airlines Flight 815 wreckage scattered on white sand, burning fuselage section, luggage and debris in surf, tropical jungle wall behind, golden afternoon light, distant smoke column rising, survivors in background tending fires, palm trees, desperate beauty of isolation, photorealistic cinematic TV drama"),
    ("🏝️ · Lost — la Stazione Cigno DHARMA sotterranea", "The Swan station, Lost ABC TV, underground DHARMA Initiative bunker, 1970s institutional aesthetic, harvest gold and avocado green appliances, pneumatic tube system, hieroglyph countdown timer on CRT monitor, long institutional corridor, DHARMA Initiative logos on walls, emergency lighting, mysterious computer terminal, photorealistic 1970s retrofuturist bunker"),
    ("🏝️ · Lost — giungla con la luce nera del Fumo", "Lost island jungle, ABC TV, dense tropical jungle interior, flickering black mechanical smoke entity moving between trees, bioluminescent vegetation, ancient carved stone wall with hieroglyphs, supernatural golden light through canopy, mysterious wheel buried in ground, photorealistic cinematic mystery drama"),

    # ══ 🦖 PREDATOR ════════════════════════════════════════════════════════════
    ("🦖 · Predator — giungla del Guatemala, caccia", "Predator 1987 John McTiernan, dense Central American jungle canopy, oppressive humid heat haze, thermal vision perspective overlay in oranges and reds optionally visible, camouflaged Predator shimmer partially visible in canopy, mud-covered tree trunks, guerrilla camp remnants, photorealistic action film aesthetic"),
    ("🦖 · Predator — nave madre Yautja, trofeo chamber", "Predator spacecraft interior, Yautja trophy room, biomechanical alien aesthetic with curved organic walls, skulls and spinal columns of various species mounted as trophies, plasma caster weapons on racks, glowing alien technology panels, ritual ceremonial lighting in copper and orange, alien civilisation war culture, photorealistic science fiction"),
    ("🦖 · Predator — downtown Los Angeles di notte", "Predator 2 1990, downtown Los Angeles urban warfare night scene, rain-slicked streets, neon signs reflecting in puddles, rooftop pursuit perspective, thermal overlay optionally visible, police sirens in background, 1990s urban action cinema aesthetic, photorealistic"),

    # ══ 🤖 TRANSFORMERS ════════════════════════════════════════════════════════
    ("🤖 · Transformers — Autobot City sotto attacco", "Transformers Michael Bay aesthetic, Autobot City under Decepticon assault, enormous Cybertronian robots clashing in urban environment, explosions and vehicle transforms in motion, NEST military vehicles in foreground, dawn light breaking over destruction, photorealistic ILM visual effects cinematic quality"),
    ("🤖 · Transformers — Cybertron, città di Iacon", "Planet Cybertron, Transformers, metallic alien world entirely of living metal and machinery, city of Iacon with towering geometric spires, Energon energy rivers glowing blue between buildings, massive robotic citizens moving in background, binary star system in sky, epic science fiction world-building, photorealistic"),
    ("🤖 · Transformers — bunker Sector Seven", "Sector Seven government facility, Transformers 2007, vast underground Hoover Dam bunker, giant frozen Cybertronian robot suspended in ice chamber, military personnel in hazmat suits, amber emergency lighting, classified technology racks, photorealistic US government black site aesthetic"),

    # ══ 🎬 PIXAR — soggetto reale nel mondo animato ═════════════════════════════
    ("🎬 · Pixar — soggetto in Toy Story, camera di Andy", "Live-action person inserted into Pixar Toy Story animated world, Mary Poppins genre-blend composite of real human with animated characters, subject standing in Andy's bedroom surrounded by animated Woody and Buzz Lightyear toys, Pixar Studio lighting on animated objects, cinematic colour grade unifying live-action and animation"),
    ("🎬 · Pixar — soggetto nel mondo di WALL-E", "WALL-E 2008 Pixar aesthetic, live-action person in post-apocalyptic animated Earth landscape, towers of compressed garbage cubes, WALL-E robot companion beside subject, soft warm dusty sunset light, lonely poetry of abandoned civilisation, Mary Poppins-style human-animated hybrid composite"),
    ("🎬 · Pixar — soggetto vola con la casa di Up", "Up 2009 Pixar, live-action person sitting on animated floating house lifted by thousands of colourful helium balloons, vast cloud panorama below, afternoon golden light, Carl's house wooden porch detail, Mary Poppins-style real human integrated into animated world, joyful impossible adventure"),
    ("🎬 · Pixar — soggetto a Radiator Springs, Cars", "Cars 2006 Pixar, live-action person in animated Route 66 desert town of Radiator Springs, giant talking animated cars rolling past, neon signs glowing at dusk, endless American desert highway, Mary Poppins human-cartoon hybrid world, photorealistic composite"),

    # ══ 🏰 DISNEY — soggetto reale nel mondo animato ════════════════════════════
    ("🏰 · Disney — soggetto nella Bella e la Bestia, sala da ballo", "Beauty and the Beast 1991 Disney, live-action person dancing in animated enchanted ballroom, Lumiere candlestick and Cogsworth clock animated around subject, golden candlelight, enchanted rose under glass dome visible, Alan Menken score visual romance, Mary Poppins real-human-in-cartoon-world aesthetic"),
    ("🏰 · Disney — soggetto in Fantasia, lo stregone apprendista", "Fantasia 1940 Disney, live-action person in animated Sorcerer's Apprentice sequence, magical brooms carrying water buckets in background, enchanted workshop flooding, Mickey Mouse's sorcerer hat nearby, Paul Dukas symphonic colour, Mary Poppins hybrid human-animation composite, classical animation cel aesthetic"),
    ("🏰 · Disney — soggetto ad Arendelle innevata, Frozen", "Frozen Disney animated world, live-action person in animated Arendelle village in winter, animated villagers, Elsa's ice palace on mountain above, magical snowflakes drifting, warm Norwegian architectural detail, Mary Poppins-style real human integrated into Disney animation world"),
    ("🏰 · Disney — soggetto su Pride Rock, Il Re Leone", "The Lion King 1994 Disney, live-action person standing on animated Pride Rock overlooking African savanna at sunrise, animated wildebeest herds below, Hans Zimmer Circle of Life visual grandeur, painted sky in gold orange purple, Mary Poppins human-cartoon world fusion, epic Disney composite"),
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

def _build_base_prompt(scenario):
    """Costruisce il blocco base comune a single e mosaic."""
    loc    = scenario.get('location', '')
    outfit = scenario.get('outfit', '')
    sky    = scenario.get('sky', '')
    pose   = scenario.get('pose', '')
    mood   = scenario.get('mood', '')
    style  = scenario.get('style', '')
    return (
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
    ), loc, outfit, sky, pose, mood, style


def build_flow_prompt_single(scenario):
    """Prompt per scatto singolo."""
    base, *_ = _build_base_prompt(scenario)
    shooting_block = (
        "**TASK: SINGLE EDITORIAL SHOT**\n"
        "Generate one editorial photograph of the subject in the scene below.\n"
        "Choose one strong pose, framing and expression — make it count.\n\n"
        "What MUST be present:\n"
        "- Subject identity (face, hair, beard, glasses — ZERO drift)\n"
        "- Location and background setting\n"
        "- Lighting mood and color palette\n"
        "- Outfit (same garments, same colors, same details)\n\n"
        "**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location described below MUST appear. "
        "Never replace it with a studio or neutral background.\n\n"
        "**NEGATIVE PROMPT:** studio background replacing original location, body hair, chest hair, "
        "missing glasses, missing beard, shaved face, face drift, desaturated colors, color shift.\n\n"
    )
    (_, loc, outfit, sky, pose, mood, style) = _build_base_prompt(scenario)
    return (
        f"{VALERIA_FACE}{VALERIA_BODY_STRONG}"
        f"{shooting_block}"
        f"LOCATION: {loc}\n\nOUTFIT: {outfit}\n\nLIGHTING / SKY: {sky}\n\n"
        f"POSE: {pose}\n\nMOOD / ATMOSPHERE: {mood}\n\nPHOTOGRAPHIC STYLE: {style}\n\n"
        f"TECHNICAL: 8K cinematic, 85mm lens, f/2.8, ISO 200, natural bokeh, "
        f"Subsurface Scattering, Global Illumination.\n"
        f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
        f"NEGATIVE: {VALERIA_NEGATIVE}"
    )


def build_flow_prompt_mosaic(scenario):
    """Prompt per mosaico 4 foto."""
    shooting_block = (
        "**TASK: EDITORIAL SHOOTING — 4 DISTINCT SHOTS**\n"
        "Generate exactly 4 editorial photographs of the same subject in the same scene.\n"
        "Each of the 4 shots MUST be distinctly different from the others:\n"
        "- Different pose (standing, seated, reclining, dynamic movement, etc.)\n"
        "- Different framing (full body, three-quarter, close-up bust, wide angle)\n"
        "- Different expression (confident, dreamy, fierce, playful)\n"
        "- Different angle (frontal, profile, three-quarter, back view)\n\n"
        "What MUST remain identical across all 4 shots:\n"
        "- Subject identity (face, hair, beard, glasses — ZERO drift)\n"
        "- Location and background setting\n"
        "- Lighting mood and color palette\n"
        "- Outfit (same garments, same colors, same details)\n\n"
        "**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location described below MUST appear "
        "identically in ALL 4 shots. Never replace it with a studio or neutral background.\n\n"
        "**NEGATIVE PROMPT:** duplicate poses, identical shots, studio background replacing "
        "original location, wrong setting, body hair, chest hair, missing glasses, missing beard, "
        "shaved face, face drift, desaturated colors, color shift.\n\n"
    )
    (_, loc, outfit, sky, pose, mood, style) = _build_base_prompt(scenario)
    return (
        f"{VALERIA_FACE}{VALERIA_BODY_STRONG}"
        f"{shooting_block}"
        f"LOCATION: {loc}\n\nOUTFIT: {outfit}\n\nLIGHTING / SKY: {sky}\n\n"
        f"POSE: {pose}\n\nMOOD / ATMOSPHERE: {mood}\n\nPHOTOGRAPHIC STYLE: {style}\n\n"
        f"TECHNICAL: 8K cinematic, 85mm lens, f/2.8, ISO 200, natural bokeh, "
        f"Subsurface Scattering, Global Illumination.\n"
        f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
        f"NEGATIVE: {VALERIA_NEGATIVE}"
    )


def build_flow_prompt(scenario, uid=None):
    """Compatibilità — ritorna il prompt single (usato dove serve un solo prompt)."""
    return build_flow_prompt_single(scenario)

def build_prompt(scenario, uid=None):
    return build_flow_prompt(scenario, uid=uid), "2:3", None

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
user_photo_location   = {}  # uid → location string estratta dalla foto
waiting_location_photo = {} # uid → True se in attesa foto location

# FIX 2.0.0 (bug #8): la tastiera di location/outfit mostra un pool FILTRATO
# (esclude le voci già usate in sessione), ma l'idx nel callback_data era sempre
# risolto contro il pool COMPLETO non filtrato — causava la selezione silenziosa
# di una location/outfit diversa da quella effettivamente cliccata, ogni volta
# che filtered != pool (cioè dal secondo giro in poi nella stessa sessione).
# Questo dizionario salva il pool esatto mostrato per uid+step, così la lettura
# del click usa sempre la stessa lista usata per generare la tastiera.
shown_pool = {}  # uid → {step_index: list}

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
def get_photo_choice_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📷 Sì, allego una foto", callback_data="has_photo_yes"),
        InlineKeyboardButton("🎲 No, procedi", callback_data="has_photo_no")
    )
    return markup

def get_shooting_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📷 Scatto singolo", callback_data="shooting_single"),
        InlineKeyboardButton("🗂️ Mosaico 4 foto", callback_data="shooting_mosaic")
    )
    return markup

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Automatico", callback_data="mode_auto"),
        InlineKeyboardButton("🎛️ Manuale", callback_data="mode_manual")
    )
    return markup

def _send_dual_output(cid, uid, scenario, caption_text):
    """
    Invia output in ordine:
    1. Mini prompt unico (intestazione 📷 Scatto singolo · 🗂️ Mosaico 4 foto)
    2. Caption (una sola)
    3. [Prompt Flow Scatto singolo]
    4. [Prompt Flow Mosaico] + 🎲 Nuova scena
    """
    CHUNK = 3800

    # 1. Mini prompt unico — intestazione doppia
    mini = _mini_prompt_from_scenario(scenario, "📷 <b>Scatto singolo</b> · 🗂️ <b>Mosaico 4 foto</b>")
    bot.send_message(cid, mini, parse_mode="HTML")

    # 2. Caption
    if caption_text:
        bot.send_message(cid, caption_text, parse_mode=None)

    # 3. Prompt Flow — Scatto singolo
    p_single = build_flow_prompt_single(scenario)
    chunks = [p_single[i:i+CHUNK] for i in range(0, len(p_single), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "📷 <b>Scatto singolo</b>\n" if idx == 0 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        bot.send_message(cid,
            f"{header}<code>{html.escape(chunk)}</code>",
            parse_mode="HTML")

    # 4. Prompt Flow — Mosaico 4 foto
    p_mosaic = build_flow_prompt_mosaic(scenario)
    chunks_m = [p_mosaic[i:i+CHUNK] for i in range(0, len(p_mosaic), CHUNK)]
    for idx, chunk in enumerate(chunks_m):
        header = "🗂️ <b>Mosaico 4 foto</b>\n" if idx == 0 else f"<i>({idx+1}/{len(chunks_m)})</i>\n"
        kb = get_retry_keyboard() if idx == len(chunks_m) - 1 else None
        bot.send_message(cid,
            f"{header}<code>{html.escape(chunk)}</code>",
            parse_mode="HTML", reply_markup=kb)

    # Salva prompt single per compat /conferma esistente
    last_flow_prompt[uid] = p_single


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
        shown_pool.setdefault(uid, {})[step_index] = filtered
        markup = get_pool_keyboard(filtered, 0, prefix, title, manual_state.get(uid, {}), step_index)
        if len(filtered) < len(pool):
            note = f" <i>({len(pool)-len(filtered)} già usati nascosti)</i>"
            bot.send_message(cid, f"{title}{note}", reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")
    elif step_index == 1:  # outfit
        used = used_outfits.get(uid, set())
        filtered = [o for o in pool if o[1] not in used] or pool
        shown_pool.setdefault(uid, {})[step_index] = filtered
        if len(filtered) < len(pool):
            note = f" <i>({len(pool)-len(filtered)} già usati nascosti)</i>"
            bot.send_message(cid, f"{title}{note}", reply_markup=get_pool_keyboard(filtered, 0, prefix, title, manual_state.get(uid, {}), step_index), parse_mode="HTML")
        else:
            markup = get_pool_keyboard(pool, 0, prefix, title, manual_state.get(uid, {}), step_index)
            bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")
    else:
        shown_pool.setdefault(uid, {})[step_index] = pool
        markup = get_pool_keyboard(pool, 0, prefix, title, manual_state.get(uid, {}), step_index)
        bot.send_message(cid, title, reply_markup=markup, parse_mode="HTML")

def format_scenario(s, uid=None):
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

def _mini_prompt_from_scenario(scenario, tipo):
    """
    Costruisce il mini prompt direttamente dal dict scenario — zero regex, zero API.
    tipo: stringa intestazione es. '📷 Scatto singolo' oppure '🗂️ Mosaico 4 foto'
    Valori troncati per leggibilità mobile.
    """
    import re as _re

    def _short(val, n=80):
        val = str(val).strip()
        return val[:n] + '…' if len(val) > n else val

    loc = scenario.get('location', '')
    if '{' in loc and '"subject"' in loc:
        values = _re.findall(r'"(?:subject|ground|sky|colors|lighting|depth|mood)"\s*:\s*"([^"]+)"', loc)
        loc = ", ".join(v.strip() for v in values if v.strip()) if values else loc
    loc_short = _short(loc, 200)

    return (
        f"{tipo}\n"
        f"📍 <b>Location:</b> {html.escape(loc_short)}\n"
        f"🌤 <b>Sky:</b> {html.escape(_short(scenario.get('sky', ''), 200))}\n"
        f"👗 <b>Outfit:</b> {html.escape(_short(scenario.get('outfit', ''), 200))}\n"
        f"🎨 <b>Style:</b> {html.escape(_short(scenario.get('style', ''), 200))}\n"
        f"💃 <b>Pose:</b> {html.escape(_short(scenario.get('pose', ''), 200))}\n"
        f"✨ <b>Mood:</b> {html.escape(_short(scenario.get('mood', ''), 200))}\n"
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
    shown_pool.pop(uid, None)
    last_flow_prompt.pop(uid, None)
    user_photo_location.pop(uid, None)
    waiting_location_photo.pop(uid, None)
    logger.info(f"📍 /start da {username} (id={uid})")
    bot.send_message(message.chat.id,
        f"<b>📍 SURPRISE v{VERSION}</b>\n\n"
        f"Hai una foto da usare come location di sfondo?",
        reply_markup=get_photo_choice_keyboard())

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

# --- HANDLER FOTO LOCATION ---
@bot.message_handler(content_types=['photo'])
def handle_location_photo(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        return
    if not waiting_location_photo.pop(uid, False):
        return  # foto non attesa — ignora
    cid = m.chat.id
    username = m.from_user.username or m.from_user.first_name
    try:
        file_info = bot.get_file(m.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.send_message(cid, f"❌ Errore download foto: {html.escape(str(e))}")
        return

    wait = bot.send_message(cid, "🔍 <b>Analizzo la location...</b>")

    # Prompt dedicato: estrae solo location/ambiente, non outfit
    try:
        from C_shared100 import genai_types
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        location_prompt = (
            "Describe ONLY the location, setting and environment visible in this image. "
            "Ignore completely any person, clothing, outfit or accessories. "
            "Focus on: architecture, geography, interior/exterior, surfaces, props, atmosphere, time of day, lighting mood. "
            "Return a single concise paragraph of maximum 50 words. "
            "No bullet points, no headers, no mention of any person or clothing."
        )
        from C_shared100 import GeminiClient
        location_text = gemini.generate(location_prompt, contents=[img_part])
    except Exception as e:
        location_text = None

    try: bot.delete_message(cid, wait.message_id)
    except Exception: pass

    if not location_text:
        bot.send_message(cid,
            "❌ Impossibile analizzare la foto.\n\nProcedo senza foto.",
            reply_markup=get_main_keyboard())
        return

    user_photo_location[uid] = location_text
    logger.info(f"📍 Location da foto per {username}: {location_text[:80]}")
    bot.send_message(cid,
        f"✅ <b>Location acquisita:</b>\n<i>{html.escape(location_text[:200])}</i>",
        parse_mode="HTML")
    bot.send_message(cid, "Come vuoi generare la scena?", reply_markup=get_main_keyboard())


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

    if data == "has_photo_yes":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        waiting_location_photo[uid] = True
        bot.send_message(cid, "📷 Inviami la foto — userò la location come sfondo.")
        return

    if data == "has_photo_no":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_photo_location.pop(uid, None)
        bot.send_message(cid, "Come vuoi generare la scena?", reply_markup=get_main_keyboard())
        return

    if data == "mode_auto":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        wait = bot.send_message(cid, "🎲 Generazione scena automatica...")
        def pick_auto():
            try:
                scenario = generate_scenario(uid=uid)
                try: bot.delete_message(cid, wait.message_id)
                except Exception: pass
                if not scenario:
                    bot.send_message(cid, "❌ Errore. Riprova.", reply_markup=get_main_keyboard())
                    return
                # Sostituisce location con quella dalla foto se disponibile
                photo_loc = user_photo_location.get(uid)
                if photo_loc:
                    scenario['location'] = photo_loc
                last_scenario[uid] = scenario
                used_locations.setdefault(uid, set()).add(scenario.get('location',''))
                used_outfits.setdefault(uid, set()).add(scenario.get('outfit',''))
                caption_text, _ = generate_caption_from_scenario(scenario)
                _send_dual_output(cid, uid, scenario, caption_text)
                logger.info(f"📍 AUTO {username} (id={uid}) — {scenario['location'][:60]}")
            except Exception as e:
                err_text = str(e)
                try: bot.delete_message(cid, wait.message_id)
                except Exception: pass
                if "503" in err_text or "unavailable" in err_text.lower():
                    msg = "⚠️ <b>Servizio Gemini non disponibile.</b>\nSovraccarico temporaneo — riprova tra qualche minuto."
                elif "429" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower():
                    msg = "❌ <b>Quota API esaurita.</b>\nReset alle 08:00 ora Lisbona."
                else:
                    msg = f"❌ <b>Errore generazione scenario.</b>\n<code>{html.escape(err_text[:200])}</code>"
                logger.error(f"❌ pick_auto exception: {err_text}")
                bot.send_message(cid, msg, parse_mode="HTML", reply_markup=get_main_keyboard())
        executor.submit(pick_auto)

    elif data == "mode_manual":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        photo_loc = user_photo_location.get(uid)
        if photo_loc:
            # Location dalla foto — pre-compila e salta al secondo step
            manual_state[uid] = {"location": photo_loc}
            bot.send_message(cid,
                f"📍 <b>Location:</b> <i>{html.escape(photo_loc[:200])}</i>\n"
                f"<i>(dalla foto — bloccata)</i>")
            send_manual_step(cid, uid, 1)  # salta step 0, parte dall'outfit
        else:
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
        # FIX 2.0.0 (bug #8): usa lo stesso pool filtrato già mostrato per questo
        # step, altrimenti il cambio pagina torna silenziosamente al pool completo
        # non filtrato e disallinea di nuovo idx ↔ voce selezionata.
        active_pool = shown_pool.get(uid, {}).get(step, pool)
        markup = get_pool_keyboard(active_pool, page, prefix, title, manual_state.get(uid, {}), step)
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
        # FIX 2.0.0 (bug #8): idx è relativo al pool FILTRATO mostrato nella
        # tastiera (escluse le voci già usate in sessione per location/outfit),
        # non al pool completo. Risolvo contro shown_pool — fallback sul pool
        # completo solo se per qualche motivo non è stato registrato.
        active_pool = shown_pool.get(uid, {}).get(step, pool)
        if idx >= len(active_pool):
            logger.warning(f"⚠️ idx {idx} fuori range per step {step} (uid={uid}) — tastiera obsoleta, ignoro")
            try: bot.answer_callback_query(call.id, "⚠️ Scelta non più valida, riprova.")
            except Exception: pass
            return
        chosen = active_pool[idx][1]
        label  = active_pool[idx][0]
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
            caption_text, _ = generate_caption_from_scenario(scenario)
            _send_dual_output(cid, uid, scenario, caption_text)
            logger.info(f"🎛️ MANUAL {username} (id={uid}) — {scenario['location']}")

    elif data == "tira":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        manual_state.pop(uid, None)
        last_flow_prompt.pop(uid, None)
        user_photo_location.pop(uid, None)
        waiting_location_photo.pop(uid, None)
        bot.send_message(cid,
            f"<b>📍 SURPRISE v{VERSION}</b>\n\nHai una foto da usare come location di sfondo?",
            reply_markup=get_photo_choice_keyboard())

    elif data == "no_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        last_scenario.pop(uid, None)
        last_prompt.pop(uid, None)
        manual_state.pop(uid, None)
        last_flow_prompt.pop(uid, None)
        user_photo_location.pop(uid, None)
        waiting_location_photo.pop(uid, None)
        bot.send_message(cid,
            f"<b>📍 SURPRISE v{VERSION}</b>\n\nHai una foto da usare come location di sfondo?",
            reply_markup=get_photo_choice_keyboard())

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

# --- /shared ---
@bot.message_handler(commands=['shared'])
def cmd_shared(m):
    bot.send_message(m.chat.id,
        f"📦 <b>C_shared100.py</b> v{SHARED_VERSION} — {SHARED_DATE}"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 🌈 PRIDE — Lisbona Pride 2026
# ═══════════════════════════════════════════════════════════════════════════════

WALTER_DNA = (
    "WALTER — male Italian face approximately 60 years old, silver-grey short hair "
    "(sides 1-2cm, top maximum 15cm, nape exposed), silver-grey beard 6-7cm, "
    "thin octagonal Vogue Havana dark tortoiseshell frame eyeglasses (ALWAYS present, never removed), "
    "hourglass feminine body silhouette, smooth hairless skin, soft curves. "
    "NO makeup beyond Pride styling. NO long hair. NO dark or brown hair."
)

CARLOTTA_DNA = (
    "CARLOTTA — Italian woman approximately 40 years old, long wavy voluminous auburn-red hair "
    "with golden honey highlights cascading over shoulders, warm fair skin with light freckles "
    "on cheeks and nose bridge, warm brown eyes, soft rounded feminine features, "
    "full natural pink lips, gentle direct gaze, 155cm, soft feminine hourglass figure 60kg. "
    "Preserve hair color — rich auburn-red with golden tones, never dark brown or blonde."
)

FUFOS_DNA = (
    "FUFOS — wire-haired dachshund dog, 5 years old, dark brown and black rough wiry coat, "
    "long body low to ground, characteristic sausage dog silhouette, floppy ears, "
    "alert intelligent expression."
)

FRITZ_DNA = (
    "FRITZ — terrier dog, 2 years old, sandy blonde wiry coat, compact energetic build, "
    "bright curious eyes, perky ears, lively playful expression."
)

PRIDE_LOCATION_POOL = [
    ("Praça do Marquês de Pombal, Lisbon",
     "Praça do Marquês de Pombal, Lisbon Pride parade starting point, "
     "monumental roundabout with Marquis of Pombal column statue at centre, "
     "rainbow flags lining the avenue, crowd energy, blue Lisbon sky, "
     "golden afternoon light, festive Pride atmosphere"),
    ("Avenida da Liberdade, Lisbon",
     "Avenida da Liberdade, Lisbon, wide tree-lined grand boulevard, "
     "Pride parade in full swing, rainbow banners suspended between trees, "
     "confetti in the air, music floats passing, warm June afternoon light, "
     "festive joyful crowds lining the sidewalks"),
    ("Praça dos Restauradores, Lisbon",
     "Praça dos Restauradores, Lisbon, obelisk of the Restauradores monument, "
     "Eden Teatro facade in background, Pride crowd celebrating, "
     "rainbow flags and balloons everywhere, warm golden light"),
    ("Chiado, Rua Garrett, Lisbon",
     "Chiado neighbourhood, Rua Garrett, Lisbon, elegant bohemian street with "
     "historic bookshops and cafés, cobblestone pavement, wrought iron lampposts, "
     "Pride revellers in colourful outfits, late afternoon warm light"),
    ("Miradouro de São Pedro de Alcântara, Lisbon",
     "Miradouro de São Pedro de Alcântara viewpoint, Lisbon, panoramic terrace "
     "overlooking the city rooftops and São Jorge Castle, azulejo tile wall, "
     "Pride flags visible across the cityscape, golden sunset light"),
    ("Alfama, Beco das Flores, Lisbon",
     "Alfama district, narrow cobblestone alley with colourful hanging laundry, "
     "whitewashed walls with blue azulejo tiles, terracotta rooftops, "
     "potted geraniums on windowsills, intimate festive Pride atmosphere"),
    ("LX Factory, Lisbon",
     "LX Factory creative hub, Lisbon, industrial repurposed factory complex "
     "under the 25 de Abril bridge, exposed brick arches, street art murals, "
     "Pride party atmosphere, fairy lights, creative crowd, warm evening light"),
    ("Praça do Comércio, Lisbon",
     "Praça do Comércio, Lisbon, grand neoclassical riverside square on the Tagus river, "
     "Arco da Rua Augusta triumphal arch at north end, yellow ochre arcaded buildings, "
     "Tagus river shimmering in background, Pride celebration finale, "
     "golden hour light over the water, confetti and rainbow flags filling the air"),
]

WALTER_OUTFIT_POOL = [
    "vibrant rainbow sequin blazer over fitted white crop top, high-waisted iridescent silver wide-leg trousers, platform ankle boots in metallic gold, rainbow eyeliner cat-eye, glossy red lips",
    "electric pink feather-trim mini dress, sheer rainbow tights, strappy crystal platform heels, holographic clutch, bold fuchsia lips with glitter eye shadow",
    "oversized colour-block blazer in red yellow blue green, black lycra shorts, chunky rainbow platform sneakers, iridescent nail art, subtle glitter cheekbones",
    "white mesh see-through shirt over rainbow-printed bandeau, tailored rainbow striped wide-leg trousers, patent white platform boots, dramatic winged eyeliner in blue and violet",
    "fitted rainbow gradient bodysuit, high-waisted sequin gold mini skirt, strappy gladiator heels in clear with glitter, full rainbow eye make-up with feathered lashes",
    "satin rainbow kimono robe worn open over fitted black bodysuit, thigh-high vinyl boots in red, large statement earrings, dramatic smoky rainbow eye",
    "crystal-embellished denim jacket painted with rainbow flag, matching embellished hot pants, knee-high platform boots in white, holographic face gems, bold coral lips",
    "draped one-shoulder jersey dress in gradient sunset rainbow colours, gold strappy heeled sandals, layered chunky gold chains, warm bronze glow make-up with coloured liner",
]

CARLOTTA_OUTFIT_POOL = [
    "flowing rainbow chiffon maxi dress with asymmetric hem, gold strappy platform sandals, wildflower crown headband, natural glowing make-up with pink lips",
    "vibrant tie-dye crop top in rainbow colours, high-waisted white wide-leg trousers, espadrille wedge heels in natural, delicate gold jewellery, fresh floral print scarf",
    "fitted rainbow-striped bardot top, flared high-waisted denim skirt with embroidered rainbow patch, wedge mules in tan, oversized round sunglasses, romantic loose waves",
    "colourful patchwork mini skirt in bright Pride colours, fitted white bodysuit, block-heel ankle boots in electric blue, statement earrings in multicolour acrylic",
    "rainbow sequin skirt midi length, soft white linen blouse tucked in, strappy gold flat sandals, subtle rainbow glitter at temples, relaxed natural make-up",
    "bright coral wrap dress with rainbow fringe hem, platform espadrilles in white, woven rainbow basket bag, flower earrings in multicolour",
    "printed rainbow halter top, high-waisted balloon trousers in vivid yellow, chunky flatform sandals in white, layered beaded necklaces, breezy loose hair",
    "oversized rainbow blazer as dress belted at waist, fishnet tights, ankle boots in black patent, bold make-up with coloured graphic liner, slicked-back voluminous hair",
]

DOGS_ACCESSORY_POOL = [
    ("rainbow bandana tied around neck", "rainbow floral collar with tiny rainbow charm tags"),
    ("tiny rainbow pride cape draped over back", "rainbow knitted sweater vest"),
    ("rainbow flower crown headband", "rainbow bow tie collar"),
    ("multicolour beaded collar in rainbow sequence", "rainbow polka-dot harness"),
    ("rainbow tutu skirt around waist", "rainbow striped collar with bell"),
    ("rainbow flag printed tiny cape", "rainbow friendship bracelet collar"),
]

PRIDE_STYLE_POOL = [
    "vibrant editorial photography, golden hour Lisbon light, joyful celebratory energy, high fashion meets street festival, Vogue editorial aesthetic",
    "cinematic wide-angle photography, confetti-filled air, warm festive atmosphere, luxury fashion campaign meets Pride celebration",
    "candid editorial style, dynamic movement, rainbow light flares, joyful spontaneous energy, high-resolution fashion photography",
    "bold graphic editorial, saturated colours, Pride energy at peak, fashion-forward composition, magazine cover aesthetic",
    "warm documentary editorial, authentic joyful moment, soft golden Lisbon light, intimate yet grand, fashion editorial quality",
]

PRIDE_WATERMARK = "feat. Valeria Cross & Friends 🌈"

# Stato Pride
pride_last_prompt   = {}   # uid → str
pride_last_location = {}   # uid → (name, desc)


def _build_pride_prompt(fixed_location=None):
    """Assembla un prompt Pride completo."""
    if fixed_location:
        loc_name, loc_desc = fixed_location
    else:
        loc_name, loc_desc = random.choice(PRIDE_LOCATION_POOL)

    walter_outfit   = random.choice(WALTER_OUTFIT_POOL)
    carlotta_outfit = random.choice(CARLOTTA_OUTFIT_POOL)
    fufos_acc, fritz_acc = random.choice(DOGS_ACCESSORY_POOL)
    style = random.choice(PRIDE_STYLE_POOL)

    prompt = (
        f"Generate a single high-quality fashion editorial photograph.\n\n"
        f"--- LOCATION ---\n{loc_desc}\n\n"
        f"--- SUBJECTS — 4 characters, ALL must be present in the frame ---\n\n"
        f"SUBJECT 1 — WALTER:\n{WALTER_DNA}\nOutfit: {walter_outfit}\n\n"
        f"SUBJECT 2 — CARLOTTA:\n{CARLOTTA_DNA}\nOutfit: {carlotta_outfit}\n\n"
        f"SUBJECT 3 — FUFOS (dog):\n{FUFOS_DNA}\nAccessory: {fufos_acc}\n\n"
        f"SUBJECT 4 — FRITZ (dog):\n{FRITZ_DNA}\nAccessory: {fritz_acc}\n\n"
        f"--- COMPOSITION ---\n"
        f"All four subjects together in one frame. Walter and Carlotta standing or posed naturally "
        f"together, Fufos and Fritz at their feet or being held. "
        f"Natural joyful interaction between the group. "
        f"Full body or three-quarter shot showing complete outfits.\n\n"
        f"--- STYLE ---\n{style}\n\n"
        f"--- WATERMARK ---\n"
        f"Elegant cursive watermark reading \'{PRIDE_WATERMARK}\' "
        f"very small, bottom centre, 90% opacity, champagne gold colour.\n\n"
        f"--- NEGATIVE ---\n"
        f"wrong hair colour on Carlotta, dark hair on Walter, missing glasses, "
        f"missing beard, wrong dog breed, generic crowd replacing subjects, "
        f"blurry faces, missing subjects, studio backdrop instead of location."
    )
    return prompt, loc_name, loc_desc


def _get_pride_after_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🔄 Nuovo prompt",    callback_data="pride_generate"),
        telebot.types.InlineKeyboardButton("🔁 Stessa location", callback_data="pride_samelocation"),
    )
    markup.row(
        telebot.types.InlineKeyboardButton("📝 Mini caption", callback_data="pride_minicaption"),
        telebot.types.InlineKeyboardButton("📋 Mini prompt",  callback_data="pride_miniprompt"),
    )
    return markup


def _pride_send_prompt(cid, uid, prompt, loc_name):
    pride_last_prompt[uid] = prompt
    bot.send_message(cid, f"🌈 <b>Pride Prompt — {loc_name}</b>\n\nCopia e incolla su Flow:")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=_get_pride_after_keyboard())
        else:
            bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>")
    logger.info(f"🌈 Pride prompt inviato — location: {loc_name} ({len(prompt)} chars)")


@bot.message_handler(commands=["pride"])
def cmd_pride(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /pride non autorizzato: uid={uid}")
        return
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🌈 /pride da {username} (id={uid})")
    prompt, loc_name, loc_desc = _build_pride_prompt()
    pride_last_location[uid] = (loc_name, loc_desc)
    _pride_send_prompt(m.chat.id, uid, prompt, loc_name)


@bot.callback_query_handler(func=lambda c: c.data.startswith("pride_"))
def handle_pride_callbacks(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    cid = call.message.chat.id
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    if call.data == "pride_generate":
        prompt, loc_name, loc_desc = _build_pride_prompt()
        pride_last_location[uid] = (loc_name, loc_desc)
        _pride_send_prompt(cid, uid, prompt, loc_name)

    elif call.data == "pride_samelocation":
        loc = pride_last_location.get(uid)
        prompt, loc_name, loc_desc = _build_pride_prompt(fixed_location=loc)
        if not loc:
            pride_last_location[uid] = (loc_name, loc_desc)
        _pride_send_prompt(cid, uid, prompt, loc_name)

    elif call.data == "pride_minicaption":
        prompt = pride_last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile. Usa /pride prima.")
            return
        wait = bot.send_message(cid, "📝 <b>Genero la mini caption...</b>")
        cap, err = generate_mini_caption(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, cap if cap else err or "❌ Errore.", parse_mode="HTML")

    elif call.data == "pride_miniprompt":
        prompt = pride_last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile. Usa /pride prima.")
            return
        wait = bot.send_message(cid, "📋 <b>Genero il mini prompt...</b>")
        mini, err = generate_mini_prompt(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, mini if mini else err or "❌ Errore.", parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════════
# /flag — PRIDE! MOSAIC  (zero Gemini, zero token)
# ═══════════════════════════════════════════════════════════════════════════════

_FLAG_COLORS = {
    "P": ("D90027", "FF8099",  "Red"),
    "R": ("E06600", "FFCC88",  "Orange"),
    "I": ("C8AA00", "FFF5A0",  "Yellow"),
    "D": ("006B22", "88EEA8",  "Green"),
    "E": ("003FCC", "99CCFF",  "Blue"),
    "!": ("5C0070", "DDA0FF",  "Violet"),
}

_FLAG_PANEL_ORDER = ["P", "R", "I", "D", "E", "!"]

# 5 outfit per colore — silhouette e stile volutamente molto diversi tra loro
_FLAG_OUTFITS = {
    "P": [
        "strapless scarlet red satin bubble-skirt mini dress, dramatic tiered ruffle hem, voluminous silhouette",
        "deep red asymmetric one-shoulder draped maxi gown, fabric trailing behind in wind",
        "cherry red cropped corset top + full tutu midi skirt, hard bodice vs soft skirt contrast",
        "red velvet slip dress with dramatic side slit, spaghetti straps, clingy sculptural cut",
        "scarlet red halter-neck flamenco-style dress, enormous ruffled hem cascading from hip to floor",
    ],
    "R": [
        "off-shoulder tangerine organza mini dress, full puffball skirt in lightweight silk",
        "burnt orange wrap dress, deep V-neck, long tiered ruffle skirt spinning in movement",
        "orange structured blazer-dress hybrid, oversized shoulders, asymmetric micro hem",
        "tangerine empire-waist sundress with layered flutter sleeves, light chiffon billowing",
        "copper-orange latex-look bodycon dress with dramatic thigh-high slit, sculptural neckline",
    ],
    "I": [
        "bright lemon-yellow halter sundress with full layered tulle skirt, massive volume",
        "sunshine yellow strapless gown, giant tiered ruffles from waist to hem, fabric billowing",
        "canary yellow 1950s rockabilly swing dress, nipped waist, full circle skirt with petticoat",
        "yellow sequin micro-mini dress with feathered hem, glamorous and playful",
        "pale gold asymmetric draped toga dress, one bare shoulder, fabric cascading to floor",
    ],
    "D": [
        "emerald green backless satin midi-length dress, fabric caught mid-dramatic-movement",
        "forest green deep-V wrap dress with chiffon overlay panels billowing widely outward",
        "jade green corset-boned dress with enormous princess skirt, tulle layers exploding out",
        "hunter green leather-look mini dress with peplum ruffle and dramatic opera gloves",
        "mint green sheer organza gown over strapless slip, layered translucent fabric floating",
    ],
    "E": [
        "cobalt blue one-shoulder silk charmeuse dress, cascade waterfall drape, fluid movement",
        "royal blue strapless structured bodice with enormous full skirt, fabric exploding outward",
        "sapphire blue flutter-sleeve mini dress, layered chiffon skirt catching air, mid-twirl",
        "electric blue body-con mermaid dress with dramatic ruffled fishtail train",
        "sky blue 1960s mod dress, geometric cut, A-line silhouette, bold graphic look",
    ],
    "!": [
        "deep purple organza dress, dramatically oversized balloon sleeves, full billowing skirt",
        "violet silk-satin mini with structured bustier bodice, full skirt exploding outward",
        "lavender-purple sequined jumpsuit with giant palazzo trousers, disco glam",
        "plum purple avant-garde dress with sculptural architectural ruffles, editorial high-fashion",
        "violet chiffon goddess gown, backless, deep-V, fabric floating and layered",
    ],
}

# 3 pose per pannello — diversissime tra loro per garantire variazione visiva
_FLAG_POSES = {
    "P": [
        "standing confident, one hand on hip, slight body lean forward, direct gaze to camera, chin slightly raised",
        "contrapposto stance, weight on one hip, arms crossed loosely, slight smirk, playful attitude",
        "back to camera, looking over shoulder toward lens, one hand touching hair, skirt swishing out",
    ],
    "R": [
        "caught mid-twirl, dress spinning dramatically outward, arms extended, head thrown back laughing",
        "jumping with knees bent, both feet off ground, arms punching upward, pure energy",
        "running toward camera, skirt and hair flying backward, laugh mid-stride, full movement",
    ],
    "I": [
        "both arms raised above head in full celebration, on tiptoes, wide open joyful smile",
        "cartwheel pose — one leg kicked high sideways, arms wide, skirt billowing from motion",
        "leaning dramatically backward in a theatrical dip, one leg raised, arms flung wide",
    ],
    "D": [
        "stepping dynamically forward, one leg extended in confident stride, one arm gesturing outward",
        "profile stance, one hand on wall (the giant letter), other hand on hip, powerful side pose",
        "crouching low with one knee almost to ground, skirt pooling around, then rising — dramatic",
    ],
    "E": [
        "leaning slightly back, head tilted, eyes half-closed, one hand softly touching wind-lifted hair",
        "spinning on one toe, other leg raised behind in arabesque, arms out, pure dance energy",
        "hands on knees, leaning forward conspiratorially toward camera, knowing smile, skirt swinging",
    ],
    "!": [
        "full celebratory jump, both feet off ground, arms wide open, maximum joy, dress mid-air",
        "arms thrown up in V for victory, head back in full laughter, confetti energy, triumphant",
        "blowing a kiss to camera, one wink, one hand raised with extended fingers, playful exit pose",
    ],
}

flag_last_prompt = {}   # uid → str




def _build_flag_prompt() -> str:
    """Costruisce il prompt PRIDE! mosaic — zero Gemini, outfit e pose random."""
    import random

    # Seed visivi — variano la composizione ad ogni lancio
    mood    = random.choice([
        "explosive energy and movement",
        "elegant and poised fashion editorial",
        "joyful street celebration",
        "theatrical and dramatic high-fashion",
        "playful and irreverent pop art",
    ])
    lighting = random.choice([
        "bright high-key studio lighting",
        "warm golden backlight, rim-lit edges",
        "crisp clean daylight, soft shadows",
        "dramatic side-lit editorial",
        "soft diffused fashion light, even and luminous",
    ])
    cam_dist = random.choice([
        "full body head-to-toe tight crop per panel",
        "generous full body with breathing negative space above and below",
        "dynamic crop cutting just above ankles, legs prominent",
    ])
    typo_size = random.choice([
        "letter fills 60% of panel height",
        "letter fills 65% of panel height",
        "letter oversized at 72% panel height, very dominant",
    ])

    panels_desc = ""
    for letter in _FLAG_PANEL_ORDER:
        bg, fg, color_name = _FLAG_COLORS[letter]
        outfit = random.choice(_FLAG_OUTFITS[letter])
        pose   = random.choice(_FLAG_POSES[letter])
        panels_desc += (
            f"\n**Panel {letter} — {color_name.upper()}**\n"
            f"Background: #{bg} · Letter color: #{fg} (pastel {color_name.lower()})\n"
            f"Dress: {outfit}\n"
            f"Pose: {pose}\n"
        )

    prompt = (
        "**TASK: 6-PANEL EDITORIAL MOSAIC — \"PRIDE!\" RAINBOW TYPOGRAPHY**\n\n"
        "Generate a single image: 6 vertical panels in a 3×2 grid.\n"
        "Row 1 (top): P · R · I  |  Row 2 (bottom): D · E · !\n"
        "Identical panel dimensions (1:1.4 portrait). NO borders, NO gaps — seamless tiling.\n\n"
        "---\n\n"
        "**FACE:** Use the attached reference image — ZERO identity drift across all 6 panels.\n\n"
        "**BODY — DO NOT OVERRIDE:**\n"
        "Feminine hourglass. Height 180 cm, D-cup bust, defined waist, full hips. "
        "Smooth skin — NO body hair anywhere. Long slim legs.\n\n"
        "---\n\n"
        "**PANEL TEMPLATE:**\n"
        "• Background: solid flat matte color (see per panel)\n"
        "• Letter: ultra-bold rounded sans-serif, ~65% panel height, center-right, "
        "pastel version of background, sits BEHIND subject\n"
        "• Subject: full-body, overlapping letter (subject in front), head-to-feet visible\n"
        "• Shoes: strappy heeled sandals, metallic silver or panel color\n"
        "• Expression: joyful, celebratory — unique per panel\n\n"
        "---\n\n"
        f"**PANELS:{panels_desc}"
        "---\n\n"
        "**TYPOGRAPHY:** Ultra-bold geometric rounded sans-serif (Nunito Black / Futura Heavy). "
        "Letter ~65% panel height, center-right, pastel on saturated background. "
        "No drop shadow, no outline. ! same size as letters.\n\n"
        "**CONSISTENCY:** Same face, same body, seamless tiling, bright high-key editorial lighting. "
        "Flat solid background per panel — no gradients, no texture.\n\n"
        f"**COMPOSITION SEED — changes every generation:**\n"
        f"Mood: {mood}\n"
        f"Lighting: {lighting}\n"
        f"Camera: {cam_dist}\n"
        f"Typography: {typo_size}\n\n"
        "**TECHNICAL:** Format 3:2.8 landscape. 8K sharp fashion editorial. "
        "NEGATIVE: face drift, body inconsistency, seams between panels, "
        "dark lighting, casual clothing, body hair.\n\n"
        "WATERMARK: \"Valeria Cross AI\" — champagne cursive, very small, bottom center, 90% opacity."
    )
    return prompt


def _get_flag_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("🔄 Nuovo flag", callback_data="flag_generate"),
    )
    return markup


def _flag_send_prompt(cid, uid):
    """Invia mini prompt statico + prompt Flow PRIDE! flag — zero Gemini."""
    prompt = _build_flag_prompt()
    flag_last_prompt[uid] = prompt

    # Prompt Flow completo
    bot.send_message(cid, "🏳️\u200d🌈 <b>PRIDE! Mosaic — Prompt Flow</b>\n\nCopia e incolla su Flow:",
                     parse_mode="HTML")
    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(cid,
                f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=_get_flag_keyboard())
        else:
            bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>")

    logger.info(f"🏳️‍🌈 /flag inviato uid={uid} ({len(prompt)} chars)")


@bot.message_handler(commands=["flag"])
def cmd_flag(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /flag non autorizzato: uid={uid}")
        return
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🏳️‍🌈 /flag da {username} (id={uid})")
    _flag_send_prompt(m.chat.id, uid)


@bot.callback_query_handler(func=lambda c: c.data == "flag_generate")
def handle_flag_callback(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    cid = call.message.chat.id
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass
    _flag_send_prompt(cid, uid)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import time
    logger.info(f"📍 SURPRISE v{VERSION} — avvio")
    server.start()
    if not gemini.available:
        logger.warning("⚠️ GOOGLE_API_KEY non configurata.")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            err = str(e)
            if "409" in err or "Conflict" in err:
                logger.warning("⚠️ 409 Conflict — altra istanza attiva. Attendo 15s e riprovo...")
                time.sleep(15)
            else:
                logger.error(f"❌ Polling error: {e}")
                time.sleep(5)

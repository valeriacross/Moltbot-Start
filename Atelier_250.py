import os, telebot, html, threading, io, logging, time
from PIL import Image
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed, genai_types, analyze_scene, SHARED_VERSION, SHARED_DATE
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_BODY_SAFE, VALERIA_WATERMARK
from C_shared100 import VALERIA_DNA, EDITORIAL_WRAPPER, build_valeria_identity, generate_caption, review_and_fix, body_art_clause

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
# CHANGELOG 2.0.8 (14/07/2026): fix 2.0.7 era incompleto — protetto solo
# un lato (anti-calvizie), non l'altro. Walter ha mostrato output Flow
# reali con capelli lunghi mossi oltre le spalle, in tutti e 4 gli scatti
# del mosaico: coerente, non casuale — con la calvizie bloccata dal
# negative prompt e nessuna protezione sul lato opposto, Flow è scivolato
# verso l'altro estremo. HAIR LOCK riscritto in tutte e 3 le funzioni con
# descrizione quantitativa ("short on the sides and back, nape and ears
# visible, ending well above the shoulders" invece del vago "short...
# Italian cut") + negative prompt esteso su ENTRAMBI i lati (bald/shaved
# head/buzzcut/receding hairline E long/shoulder-length/flowing/wavy long
# hair). Stesso scope di 2.0.7, solo Atelier.
# CHANGELOG 2.0.7 (13/07/2026): aggiunto "⚠️ HAIR LOCK — ABSOLUTE
# PRIORITY" + termini negative prompt (bald, shaved head, buzzcut,
# receding hairline, missing hair, hair loss) in tutte e 3 le funzioni
# di prompt-building (build_full_prompt, build_shooting_prompt single e
# mosaic) — stesso pattern già usato per BACKGROUND LOCK/OUTFIT DETAIL
# LOCK, rinforzo locale ad Atelier, non nello shared. Causa: Walter ha
# mostrato output Flow reali con testa completamente calva nonostante
# l'identità descriva "short silver-grey hair" — verificato che la
# descrizione capelli non aveva NESSUNA protezione da negative prompt in
# nessuna delle 3 funzioni (a differenza della barba, protetta sia da
# blocco MANDATORY nello shared sia da negative prompt locali qui).
# Scope volutamente limitato ad Atelier, come concordato — Vogue usa la
# stessa identity via shared ma non è stato toccato, decisione separata.
# CHANGELOG 2.0.6 (13/07/2026): ampliate le 4 liste di varietà nel ramo
# mosaic di build_shooting_prompt() (pose/framing/expression/angle, righe
# ~592-600) — da 4 opzioni ciascuna (una con "etc." vago) a 10-12 opzioni
# concrete. Causa segnalata da Walter con prompt ed esempi reali: con solo
# 4 opzioni per categoria e 4 scatti richiesti, Flow produceva spesso
# scatti quasi identici tra loro per scarsità di combinazioni disponibili.
# Nessun'altra modifica — il ramo single non ha queste liste (un solo
# scatto, non serve enumerare varietà).
# CHANGELOG 2.0.5 (13/07/2026): stringa modello in /info allineata al
# motore reale — "gemini-3-flash-preview" → "gemini-3.5-flash" (inline,
# riga cmd_info). Era rimasta disallineata dal passaggio a gemini-3.5-flash
# fatto in shared 2.3.16 (04/07). Nessun'altra modifica.
# CHANGELOG 2.0.1 (21/06/2026 → 25/06/2026):
# - Rimossi 📐 ratio e 🔢 conteggio dall'header del prompt (filtri singoli)
# - Rimossa riga FORMAT: {ratio} dal corpo del prompt in build_full_prompt()
# - Rimossi ratio e count da user_settings, firma build_full_prompt,
#   tutti i reset e dal /help — erano dead state dopo le due rimozioni sopra
# - Rimosso FACE IDENTITY LOCK duplicato hardcoded nella scene di riviera_60
#   (già coperto da build_valeria_identity() iniettato in build_full_prompt)
# CHANGELOG 2.0.4 (08/07/2026): build_full_prompt() e build_shooting_prompt()
# (entrambi i rami) ora inseriscono body_art_clause(outfit_description) dopo
# OUTFIT DETAIL LOCK — la clausola "BODY ART EXCEPTION" (shared 2.3.17,
# prima dentro build_valeria_identity()) compariva in OGNI prompt anche con
# BODY ART: None, testo condizionale inerte nel caso comune. Ora compare
# solo se analyze_scene() ha davvero trovato body art nella foto. Nessuna
# modifica al blocco identità/DNA in sé né alla logica OUTFIT DETAIL LOCK
# (2.0.3). Vedi C_shared100.py 2.3.18 e HANDOFF sezione 2decies.
# CHANGELOG 2.0.3 (07/07/2026):
# - Aggiunto blocco "⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY" in
#   build_full_prompt() e in entrambi i rami (single/mosaic) di
#   build_shooting_prompt(), subito dopo il COLOR LOCK esistente. Motivo:
#   outfit molto elaborati (filigrana, gemme, ricami densi) venivano
#   riprodotti semplificati/appiattiti — la fedeltà colore era già
#   rinforzata con priorità assoluta, quella della complessità
#   ornamentale no. Estesi anche i relativi NEGATIVE PROMPT con termini
#   che penalizzano outfit semplificati/generici. Passo 1 di 2 concordato
#   con Walter — passo 2 (tatuaggi/body paint, tocca C_shared100.py e
#   quindi tutti i bot) rimandato a dopo verifica pratica di questo primo
#   step con nuove prove sulla stessa immagine di riferimento.
# CHANGELOG 2.0.2 (25/06/2026):
# - build_shooting_prompt() (mode=single e mosaic): "Outfit" ora condizionale
#   (se OUTFIT: None, Flow non inventa vestiti dalla palette cromatica);
#   aggiunto "Props and physical interactions" nel blocco "What MUST remain
#   identical" — prop (es. ghiaccio) coerenti in tutti e 4 gli scatti;
#   aggiunto negative prompt "clothing added where none exists, garments
#   invented from color palette"
# CHANGELOG 2.0.0 (20/06/2026): fix #5 — _process() ora avvolto in try/except.
# CHANGELOG 2.5.0 (17/07/2026): cambio di motore, non un patch — versione
# alzata di conseguenza su richiesta esplicita di Walter (da 2.0.9/2.0.10
# a 2.5.0), non un incremento di patch.
# Verificato sulla documentazione ufficiale Google Cloud (prompting guide
# Nano Banana) che il modello dietro Flow NON ha un campo negativePrompt
# indipendente — architettura multimodale end-to-end, non diffusion con
# sottrazione vettoriale come Stable Diffusion/Midjourney/Imagen. La guida
# ufficiale raccomanda esplicitamente "positive framing, not negative"
# come principio di prodotto, non solo stilistico. Causa scatenante:
# Walter ha mostrato un mosaico con 2 scatti su 4 ancora calvi nonostante
# HAIR LOCK v2.0.8 (con negative prompt esteso) — la calvizie ha continuato
# a ripresentarsi perché il meccanismo "NEGATIVE PROMPT: bald, shaved
# head..." non ha mai avuto l'enforcement che il nome suggerisce su questo
# modello specifico.
# Rimossi TUTTI i blocchi "**NEGATIVE PROMPT:**"/"**⚠️ NEGATIVE PROMPT...**"
# nelle 3 funzioni (build_full_prompt, build_shooting_prompt single e
# mosaic), più due residui non legati al DNA (lens-distortion guard nel
# filtro selfie, "no fish-eye/never waxy"). Riscritti in positivo puro:
# COLOR LOCK, OUTFIT DETAIL LOCK, HAIR LOCK, BACKGROUND LOCK, la clausola
# outfit-assente. Aggiunto un nuovo blocco locale "⚠️ IDENTITY LOCK"
# (barba/occhiali/corpo, positivo) in tutte e 3 le funzioni.
# ESTESO anche allo shared (2.4.0, stessa sessione, su richiesta esplicita
# di Walter — "perché non hai toccato shared quando l'impianto del DNA è
# principalmente lì"): VALERIA_FACE e VALERIA_BODY_STRONG/SAFE riscritte in
# positivo puro, VALERIA_NEGATIVE eliminata, review_and_fix() non reinietta
# più negative prompt. Import morto di VALERIA_NEGATIVE (mai usata nel
# corpo del file) rimosso di conseguenza. Non elimina la varianza — Flow
# resta non deterministico — ma allinea l'approccio a quanto Google stessa
# dice funzionare meglio su questo modello specifico.
VERSION = "2.5.0"
TOKEN   = os.environ.get("TELEGRAM_TOKEN_CLOSET")

# GeminiClient da C_shared100 v2.2.0 — gestisce nativamente la rotation
# multi-chiave (GOOGLE_API_KEY / _2 / _3) su errore 429/quota esaurita.
gemini  = GeminiClient()
caption = CaptionGenerator(gemini)
server  = HealthServer("ATELIER", VERSION)

# Notifica cambio API key — invia messaggio all'utente attivo
_active_cid: int | None = None

def _notify_key_use(key_num: int, call_count: int):
    if _active_cid:
        try:
            bot.send_message(_active_cid, f"🔑 <b>Key {key_num}</b> · call #{call_count}", parse_mode="HTML")
        except Exception:
            pass

gemini.on_key_use(_notify_key_use)

bot      = telebot.TeleBot(TOKEN, parse_mode="HTML")
executor = ThreadPoolExecutor(max_workers=4)

logger.info(f"✦ ATELIER v{VERSION} — inizializzazione in corso...")


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
                    "**Technical:** 8K ultra-realistic, simulated 50mm focal length, natural undistorted facial proportions. "
                    "f/2.8, ISO 200, 1/160s, creamy bokeh, glossy hyper-detailed finish with realistic skin texture.\n\n"
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
                ),
            },
        ],
    },
    "spiaggia_editoriale": {
        "body_safe": True,
        "label": "🌅 Spiaggia Editoriale",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Pieno Sole",
                "scene": (
                    "**Scene:**\n"
                    "High-fashion editorial beach portrait. Exclusive luxury beach location — "
                    "pristine white sand, crystal turquoise water, clear blue sky. "
                    "The subject stands at the shoreline, waves gently lapping at their feet, "
                    "body turned three-quarters toward camera with confident editorial posture.\n\n"
                    "**Lighting:** Full midday sun, brilliant natural light, sharp shadows, warm golden tones. Light reflecting off the sea surface creating subtle shimmer on skin.\n\n"
                    "**Outfit:** High-end luxury swimwear or beach couture outfit "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Full body editorial, 85mm perspective, shallow depth of field, "
                    "ocean bokeh background. Cinematic color grade, vivid bright tones.\n\n"
                ),
            },
            {
                "name": "🌅 Tramonto",
                "scene": (
                    "**Scene:**\n"
                    "High-fashion editorial beach portrait at golden hour. Exclusive luxury beach location — "
                    "pristine white sand, crystal turquoise water, dramatic sky with warm orange and pink tones. "
                    "The subject stands at the shoreline, waves gently lapping at their feet, "
                    "body turned three-quarters toward camera with confident editorial posture.\n\n"
                    "**Lighting:** Dramatic golden hour — warm directional backlight from the setting sun creating a luminous rim around the silhouette, long soft shadows, reflected warm tones from the sea surface.\n\n"
                    "**Outfit:** High-end luxury swimwear or beach couture outfit "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Full body editorial, 85mm perspective, shallow depth of field, "
                    "ocean bokeh background. Cinematic color grade, rich warm tones.\n\n"
                ),
            },
        ],
    },
    "beach_club": {
        "label": "🍹 Beach Club",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Pieno Sole",
                "scene": (
                    "**Scene:**\n"
                    "Aperitivo moment at an exclusive Mediterranean beach club. "
                    "Elegant lounge area with designer furniture, white linen, potted olive trees, "
                    "infinity pool visible in background, sea horizon beyond. "
                    "The subject is seated or semi-reclined on a luxury sun lounger, "
                    "relaxed and confident, a cocktail glass nearby as a prop.\n\n"
                    "**Lighting:** Full midday sun, brilliant natural light, sharp shadows, warm golden tones. Light reflecting off the pool surface creating subtle shimmer.\n\n"
                    "**Outfit:** Luxury resort wear or high-end swimwear with cover-up "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Editorial fashion portrait, three-quarter body, slight low angle for elegance. "
                    "Cinematic shallow depth of field, vivid bright Mediterranean color grade.\n\n"
                ),
            },
            {
                "name": "🌅 Tramonto",
                "scene": (
                    "**Scene:**\n"
                    "Aperitivo moment at an exclusive Mediterranean beach club at golden hour. "
                    "Elegant lounge area with designer furniture, white linen, potted olive trees, "
                    "infinity pool visible in background, sea horizon glowing with sunset colors. "
                    "The subject is seated or semi-reclined on a luxury sun lounger, "
                    "relaxed and confident, a cocktail glass nearby as a prop.\n\n"
                    "**Lighting:** Dramatic golden hour — warm directional backlight from the setting sun creating a luminous rim around the silhouette, long soft shadows, reflected warm tones from the sea surface.\n\n"
                    "**Outfit:** Luxury resort wear or high-end swimwear with cover-up "
                    "faithfully extracted from the reference image provided.\n\n"
                    "**Framing:** Editorial fashion portrait, three-quarter body, slight low angle for elegance. "
                    "Cinematic shallow depth of field, warm Mediterranean golden color grade.\n\n"
                ),
            },
        ],
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
                ),
            },
        ],
    },
    "surf": {
        "body_safe": True,
        "label": "🏄 Surf",
        "is_dual": True,
        "variants": [
            {
                "name": "☀️ Pieno Sole",
                "scene": (
                    "**Scene:**\n"
                    "Dynamic action editorial on the ocean. The subject is mid-surf on a wave — "
                    "standing on a surfboard, body engaged in the ride, arms out for balance, "
                    "powerful ocean wave rising behind them. Spray and water droplets in the air. "
                    "Raw natural energy, athletic and editorial simultaneously.\n\n"
                    "**Lighting:** Full midday sun, brilliant natural ocean light, sharp shadows, sun glinting off water surface, backlit spray creating luminous halo effect, dynamic and vivid.\n\n"
                    "**Outfit:** Athletic surf-inspired swimwear or rash guard "
                    "faithfully extracted from the reference image provided, adapted for aquatic movement.\n\n"
                    "**Framing:** Dynamic low angle, wide enough to show wave and board context, "
                    "subject sharp against motion-blurred water. 85mm equivalent, cinematic.\n\n"
                ),
            },
            {
                "name": "🌅 Tramonto",
                "scene": (
                    "**Scene:**\n"
                    "Dynamic action editorial on the ocean at golden hour. The subject is mid-surf on a wave — "
                    "standing on a surfboard, body engaged in the ride, arms out for balance, "
                    "powerful ocean wave rising behind them. Spray catching the warm sunset light.\n\n"
                    "**Lighting:** Dramatic golden hour — warm directional backlight from the setting sun creating a luminous rim through the wave spray, sea surface painted in amber and rose tones.\n\n"
                    "**Outfit:** Athletic surf-inspired swimwear or rash guard "
                    "faithfully extracted from the reference image provided, adapted for aquatic movement.\n\n"
                    "**Framing:** Dynamic low angle, wide enough to show wave and board context, "
                    "subject sharp against motion-blurred water. 85mm equivalent, cinematic golden grade.\n\n"
                ),
            },
        ],
    },
    "riviera_60": {
        "label": "🎞️ Riviera '60",
        "is_dual": False,
        "scene": (
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
user_settings = defaultdict(lambda: {'mode': 'single'})
user_filter = {}       # uid → filter_key
last_prompt = {}       # uid → {'full_p': str} oppure {'is_dual': True, 'variants': [...]}
pending_caption = {}         # uid → True se in attesa foto per /caption
_caption_timers = {}         # uid → threading.Timer — scade dopo 60s

def _expire_caption(uid: int):
    """Callback del timer: rimuove il flag /caption scaduto."""
    if pending_caption.pop(uid, False):
        logger.info(f"⏱️ /caption scaduto per uid={uid}")
# --- KEYBOARDS ---
def get_filter_keyboard():
    markup = InlineKeyboardMarkup()
    keys = list(FILTERS.keys())
    # 2 per riga
    for i in range(0, len(keys), 2):
        row_keys = keys[i:i+2]
        markup.row(*[InlineKeyboardButton(FILTERS[k]["label"], callback_data=f"flt_{k}") for k in row_keys])
    return markup

def get_mode_keyboard():
    """Prima scelta: foto singola o mosaico 4."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📷 Foto singola",     callback_data="mode_single"),
        InlineKeyboardButton("🗂️ Mosaico 4 foto",   callback_data="mode_mosaic"),
    )
    return markup

def get_confirm_keyboard():
    """Keyboard post-prompt: nuova foto o home."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 Nuova foto", callback_data="cancel_gen"),
        InlineKeyboardButton("🏠 Home",       callback_data="go_home")
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
    """
    Analisi immagine centralizzata — usa analyze_scene() da C_shared100.
    Ritorna (result, err) — err contiene il testo reale dell'errore API.
    """
    try:
        logger.info(f"🔍 describe_outfit: {len(img_bytes)} bytes → analyze_scene()")
        result, err = analyze_scene(img_bytes, gemini)
        if result:
            logger.info(f"👗 Outfit descritto ({len(result)} chars)")
            return result, None
        logger.warning(f"⚠️ describe_outfit: {err}")
        return None, err
    except Exception as e:
        logger.error(f"❌ describe_outfit_from_image ECCEZIONE: {e}", exc_info=True)
        return None, f"❌ Eccezione: {e}"

# --- CAPTION --- (usa generate_caption centralizzata da C_shared100)
def generate_caption_from_image(img_bytes):
    """Caption da immagine → shared.generate_caption()."""
    return generate_caption(img_bytes, gemini)

def generate_caption_from_prompt(outfit_desc, img_bytes=None, filter_key=None, settings=None):
    """Caption: usa sempre from_image se disponibile — outfit_desc da solo è troppo povero."""
    if img_bytes:
        return generate_caption(img_bytes, gemini)
    return None, "⚠️ Caption non disponibile — nessuna immagine di riferimento."


def get_shooting_mode_keyboard():
    return get_mode_keyboard()


# --- IDENTITÀ BUILDER ---
# build_valeria_identity(), EDITORIAL_WRAPPER, generate_caption() → da C_shared100

# --- BUILD PROMPT ---
_MOSAIC_BLOCK = (
    "**TASK: 4 DISTINCT SHOTS — same scene, same outfit, different poses/framings**\n"
    "Generate exactly 4 editorial photographs of the same subject in the same scene.\n"
    "Each shot MUST differ in: pose, framing (full body / three-quarter / close-up), "
    "expression, and camera angle (frontal / profile / three-quarter / back).\n"
    "Background, lighting and outfit MUST remain identical across all 4 shots.\n\n"
)

def build_full_prompt(filter_key, outfit_description, scene_override=None, mode="single"):
    """Assembla il prompt completo: editorial wrapper + identita Valeria + scena filtro + outfit."""
    scene = scene_override if scene_override else FILTERS[filter_key]["scene"]
    safe = FILTERS[filter_key].get("body_safe", False)
    identity = build_valeria_identity(safe=safe)
    mosaic = _MOSAIC_BLOCK if mode == "mosaic" else ""
    return (
        f"{EDITORIAL_WRAPPER}\n"
        f"{identity}\n"
        f"{mosaic}"
        f"{scene}\n"
        f"**Outfit details from reference:**\n{outfit_description}\n\n"
        f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** The colors match the outfit exactly as described above, "
        f"including the precise HEX codes listed in the COLOR PALETTE section — vivid and saturated, "
        f"true to the exact hue specified (vivid cyan-turquoise stays vivid cyan-turquoise, not powder "
        f"blue or steel blue). Color fidelity is exact and non-negotiable.\n\n"
        f"**⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY:** Every embellishment, texture and construction "
        f"detail described above appears fully and precisely — filigree, embroidery, beading, gemstones, "
        f"lacing, stitching, hardware, layering, trim — in the same density and placement as described. "
        f"The outfit's full ornamental complexity is reproduced completely and precisely, with the same "
        f"richness of detail as the reference.\n\n"
        f"{body_art_clause(outfit_description)}"
        f"**⚠️ IDENTITY LOCK — ABSOLUTE PRIORITY:** The face stays mature, around 60 years old, with the "
        f"full silver-grey beard and tortoiseshell glasses always present, exactly as described above, "
        f"identical to the reference identity with zero drift. The body keeps the feminine hourglass "
        f"silhouette and full bust described above, with completely smooth, hairless skin on the torso, "
        f"arms and legs.\n\n"
        f"**⚠️ HAIR LOCK — ABSOLUTE PRIORITY:** The hairstyle is exactly: short silver-grey hair, an "
        f"Italian crop cut, short on the sides and back with the nape and ears clearly visible, slightly "
        f"voluminous only on top, ending well above the shoulders — an exact middle length, not shaved "
        f"bald and not grown long. This exact length, color and style stays fully present and unchanged.\n\n"
        f"**Technical:** 8K, cinematic, photorealistic.\n"
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
            f"- Outfit or lack thereof (if OUTFIT states None or no garments, the subject's skin stays "
            f"exactly as described, unclothed — the listed colors apply only to background, lighting and "
            f"props, as specified)\n"
            f"- Props and physical interactions exactly as described in PROPS & ACTIONS\n\n"
            f"**Reference image analysis:**\n{outfit_desc}\n\n"
            f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** The colors match exactly as described above, including "
            f"the precise HEX codes listed in the COLOR PALETTE section — vivid and saturated, true to the "
            f"exact hue specified. Color fidelity is exact and non-negotiable.\n\n"
            f"**⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY:** Every embellishment, texture and construction "
            f"detail described above appears fully and precisely — filigree, embroidery, beading, gemstones, "
            f"lacing, stitching, hardware, layering, trim — in the same density and placement as described. "
            f"The outfit's full ornamental complexity is reproduced completely and precisely, with the same "
            f"richness of detail as the reference.\n\n"
            f"{body_art_clause(outfit_desc)}"
            f"**⚠️ IDENTITY LOCK — ABSOLUTE PRIORITY:** The face stays mature, around 60 years old, with "
            f"the full silver-grey beard and tortoiseshell glasses always present, exactly as described "
            f"above, identical to the reference identity with zero drift. The body keeps the feminine "
            f"hourglass silhouette and full bust described above, with completely smooth, hairless skin "
            f"on the torso, arms and legs.\n\n"
            f"**⚠️ HAIR LOCK — ABSOLUTE PRIORITY:** The hairstyle is exactly: short silver-grey hair, an "
            f"Italian crop cut, short on the sides and back with the nape and ears clearly visible, "
            f"slightly voluminous only on top, ending well above the shoulders — an exact middle length, "
            f"not shaved bald and not grown long. This exact length, color and style stays fully present "
            f"and unchanged.\n\n"
            f"**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location and background described above appears "
            f"precisely, as the setting of the whole scene.\n\n"
            f"**Technical:** 8K, cinematic, photorealistic.\n"
        )
    else:
        prompt = (
            f"{EDITORIAL_WRAPPER}\n"
            f"{identity}\n"
            f"**TASK: EDITORIAL SHOOTING — 4 DISTINCT SHOTS**\n"
            f"Generate exactly 4 editorial photographs of the same subject in the same scene. Each of the "
            f"4 shots is a genuinely distinct combination of pose, framing, expression and angle — no two "
            f"shots repeat the same combination:\n"
            f"- Pose options: standing, seated, reclining, dynamic movement, leaning against a surface, "
            f"crouching, one knee bent, walking mid-stride, twisting torso with head turned, arms raised "
            f"overhead, hand on hip with weight shifted, kneeling\n"
            f"- Framing options: full body, three-quarter, close-up bust, wide angle, extreme close-up "
            f"on face, over-the-shoulder, low-angle full body, high-angle full body, medium shot from the "
            f"waist up, tight crop on hands and detail\n"
            f"- Expression options: confident, dreamy, fierce, playful, serene, intense stare, joyful "
            f"laugh, mysterious half-smile, contemplative, sultry gaze, surprised, determined\n"
            f"- Angle options: frontal, profile, three-quarter, back view, high angle looking down, "
            f"low angle looking up, over-the-shoulder glance back, Dutch tilt\n\n"
            f"What stays identical across all 4 shots:\n"
            f"- Subject identity (face, hair, beard, glasses — ZERO drift)\n"
            f"- Location and background setting\n"
            f"- Lighting mood and color palette\n"
            f"- Outfit or lack thereof (if OUTFIT states None or no garments, the subject's skin stays "
            f"exactly as described, unclothed, in all 4 shots — the listed colors apply only to "
            f"background, lighting and props, as specified)\n"
            f"- Props and physical interactions exactly as described in PROPS & ACTIONS — present and consistent in ALL 4 shots\n\n"
            f"**Reference image analysis:**\n{outfit_desc}\n\n"
            f"**⚠️ COLOR LOCK — ABSOLUTE PRIORITY:** The colors match exactly as described above, including "
            f"the precise HEX codes listed in the COLOR PALETTE section — vivid and saturated, true to the "
            f"exact hue specified, identically in all 4 shots. Color fidelity is exact and non-negotiable.\n\n"
            f"**⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY:** Every embellishment, texture and construction "
            f"detail described above appears fully and precisely — filigree, embroidery, beading, gemstones, "
            f"lacing, stitching, hardware, layering, trim — in the same density and placement as described, "
            f"IN ALL 4 SHOTS. The outfit's full ornamental complexity is reproduced completely and precisely "
            f"in every shot, with the same richness of detail as the reference.\n\n"
            f"{body_art_clause(outfit_desc)}"
            f"**⚠️ IDENTITY LOCK — ABSOLUTE PRIORITY:** The face stays mature, around 60 years old, with "
            f"the full silver-grey beard and tortoiseshell glasses always present, exactly as described "
            f"above, identical to the reference identity with zero drift, in EVERY shot. The body keeps "
            f"the feminine hourglass silhouette and full bust described above, with completely smooth, "
            f"hairless skin on the torso, arms and legs, identically in all 4 shots.\n\n"
            f"**⚠️ HAIR LOCK — ABSOLUTE PRIORITY:** The hairstyle is exactly: short silver-grey hair, an "
            f"Italian crop cut, short on the sides and back with the nape and ears clearly visible, "
            f"slightly voluminous only on top, ending well above the shoulders — an exact middle length, "
            f"not shaved bald and not grown long, in EVERY shot. This exact length, color and style stays "
            f"fully present and unchanged, identically across all 4 shots.\n\n"
            f"**⚠️ CRITICAL — BACKGROUND LOCK:** The exact location and background described above appears "
            f"precisely, identically in ALL 4 shots, as the setting of the whole scene.\n\n"
            f"**Technical:** 8K, cinematic, photorealistic.\n"
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
    user_settings[uid] = {'mode': 'single'}
    gemini.reset_counters()  # azzera contatori call ad ogni /start
    # NON resetta user_filter — mantiene ultimo filtro usato
    last_prompt.pop(uid, None)
    logger.info(f"▶️ /start da {username} id={uid}")
    # Se ha già un filtro → vai diretto a "invia foto"
    if user_filter.get(uid):
        flt_label = FILTERS[user_filter[uid]]["label"]
        bot.send_message(m.chat.id,
            f"<b>✦ ATELIER v{VERSION}</b>\n\n"
            f"Filtro attivo: <b>{flt_label}</b>\n\n"
            f"📸 Invia una foto, oppure premi 🏠 Home per cambiare filtro.",
            reply_markup=get_confirm_keyboard())
        return
    bot.send_message(m.chat.id,
        f"<b>✦ ATELIER v{VERSION}</b>\n\nFoto singola o mosaico di 4?",
        reply_markup=get_mode_keyboard())

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>✦ ATELIER v{VERSION} — Comandi</b>\n\n"
        f"/start · /reset — Menu principale\n"
        f"/caption — Genera caption da foto\n"
        f"/lastprompt — Mostra ultimo prompt\n"
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
        f"Modello: <code>gemini-3.5-flash</code>\n\n"
        f"<i>Output: prompt Flow-ready + caption. Nessuna generazione immagini diretta.</i>"
    )

@bot.message_handler(commands=['lastprompt'])
def cmd_lastprompt(m):
    uid = m.from_user.id
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🔍 /lastprompt da {username} (id={uid})")
    data = last_prompt.get(uid)
    if not data:
        bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile. Genera prima un prompt.")
        return
    if data.get('is_dual') and data.get('variants'):
        for v in data['variants']:
            prompt = v['full_p']
            chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
            for idx, chunk in enumerate(chunks):
                header = f"🔍 <b>{v['name']}</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
                bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")
    else:
        prompt = data.get('full_p', '')
        if not prompt:
            bot.send_message(m.chat.id, "⚠️ Nessun prompt disponibile.")
            return
        chunks = [prompt[i:i+3800] for i in range(0, len(prompt), 3800)]
        for idx, chunk in enumerate(chunks):
            header = f"🔍 <b>Ultimo prompt</b> ({idx+1}/{len(chunks)}):\n\n" if idx == 0 else f"<i>(continua {idx+1}/{len(chunks)})</i>\n\n"
            bot.send_message(m.chat.id, f"{header}<code>{html.escape(chunk)}</code>")


# --- /caption ---
@bot.message_handler(commands=['caption'])
def cmd_caption(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /caption non autorizzato: uid={uid} username={m.from_user.username}")
        return
    # Cancella eventuale timer precedente ancora attivo
    if uid in _caption_timers:
        _caption_timers[uid].cancel()
    pending_caption[uid] = True
    t = threading.Timer(60.0, _expire_caption, args=(uid,))
    t.daemon = True
    t.start()
    _caption_timers[uid] = t
    logger.info(f"📝 /caption da {m.from_user.username or m.from_user.first_name} (id={uid})")
    bot.send_message(m.chat.id, "📸 Inviami la foto per la caption. (60 secondi)")

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
        mode = user_settings[uid].get('mode', 'single')
        mode_label = "🗂️ Mosaico" if mode == "mosaic" else "📷 Singola"
        logger.info(f"🎨 {username} (id={uid}) → filtro: {label}")
        try: bot.answer_callback_query(call.id, label)
        except Exception: pass
        dual_note = " · <i>⚡ 2 varianti luce</i>" if is_dual else ""
        try:
            bot.edit_message_text(
                f"✅ {mode_label} | <b>{label}</b>{dual_note}\n\n📸 Invia la foto del costume/outfit di riferimento.",
                cid, call.message.message_id)
        except Exception: pass





    # Home
    elif data == "go_home":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_filter.pop(uid, None)
        bot.send_message(cid,
            f"<b>✦ ATELIER v{VERSION}</b>\n\nFoto singola o mosaico di 4?",
            reply_markup=get_mode_keyboard())

    # Nuova foto
    elif data == "cancel_gen":
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        bot.send_message(cid, "📸 Invia una nuova foto di riferimento.")

    # Modalità scelta (singola / mosaico) — step 1
    elif data in ("mode_single", "mode_mosaic", "shooting_mosaic", "shooting_single"):
        # Normalizza: shooting_* è alias per retrocompatibilità
        if data in ("mode_mosaic", "shooting_mosaic"):
            mode = "mosaic"
        else:
            mode = "single"
        user_settings[uid]['mode'] = mode
        user_settings[uid]['shooting_mode'] = mode   # compat shooting
        mode_label = "🗂️ Mosaico 4 foto" if mode == "mosaic" else "📷 Foto singola"
        logger.info(f"📷 {username} (id={uid}) → mode: {mode}")
        try: bot.answer_callback_query(call.id, mode_label)
        except Exception: pass
        try:
            bot.edit_message_text(
                f"✅ {mode_label}\n\n🎨 Scegli lo scenario:",
                cid, call.message.message_id,
                reply_markup=get_filter_keyboard())
        except Exception: pass

    elif data == "shooting_menu":
        # Torna al menu iniziale completo
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        user_settings[uid] = {'mode': 'single'}
        user_filter.pop(uid, None)
        last_prompt.pop(uid, None)
        logger.info(f"🏠 {username} (id={uid}) → shooting_menu (reset)")
        bot.send_message(cid,
            f"<b>✦ ATELIER v{VERSION}</b>\n\nFoto singola o mosaico di 4?",
            reply_markup=get_mode_keyboard())

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

    # --- LOOP (deprecato — flusso reale usa cancel_gen/go_home) ---
    elif data in ("loop_same", "loop_new_filter", "loop_new_photo", "loop_reset"):
        try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception: pass
        # NON resetta user_filter — mantiene ultimo filtro
        bot.send_message(cid, "📸 Invia una nuova foto.", reply_markup=None)


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
    global _active_cid
    cid = m.chat.id
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Foto non autorizzata: uid={uid} username={m.from_user.username}")
        return
    _active_cid = cid
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

    # --- flusso /caption ---
    if pending_caption.pop(uid, False):
        # Cancella il timer di scadenza — la foto è arrivata in tempo
        t = _caption_timers.pop(uid, None)
        if t:
            t.cancel()
        wait = bot.send_message(cid, "✍️ <b>Genero la caption...</b>")
        caption_text, err = generate_caption(img_data, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        if not caption_text:
            bot.send_message(cid, err or "❌ Caption fallita. Riprova.", parse_mode="HTML")
        else:
            bot.send_message(cid, caption_text)
        logger.info(f"✅ Caption generata per {username}")
        return

    # Verifica filtro selezionato
    filter_key = user_filter.get(uid)
    if not filter_key:
        # Prima volta — nessun filtro ancora scelto
        bot.send_message(cid,
            f"<b>✦ ATELIER v{VERSION}</b>\n\nFoto singola o mosaico di 4?",
            reply_markup=get_mode_keyboard())
        return

    wait_msg = bot.send_message(cid, "⧖ <b>Analisi in corso...</b>")

    def _process():
      try:
        # Analisi outfit neutra
        outfit_desc, analyze_err = describe_outfit_from_image(img_data)
        try: bot.delete_message(cid, wait_msg.message_id)
        except Exception: pass

        if not outfit_desc:
            logger.error(f"❌ Analisi outfit fallita per {username}: {analyze_err}")
            bot.send_message(cid,
                f"❌ <b>Analisi immagine fallita.</b>\n\n"
                f"{str(analyze_err)}\n\n"
                "Nessun prompt generato.",
                reply_markup=get_confirm_keyboard())
            return

        settings = user_settings[uid]
        mode = settings.get('mode', 'single')
        flt = FILTERS[filter_key]
        is_dual = flt["is_dual"]

        # --- SHOOTING EDITORIAL: genera prompt per Flow, non immagine ---
        if flt.get("shooting"):
            mode = settings.get('mode', 'mosaic')
            mode_label = "🗂️ Mosaico 4 foto" if mode == "mosaic" else "📷 Scatti separati"
            full_p = review_and_fix(build_shooting_prompt(outfit_desc, mode), gemini)
            last_prompt[uid] = {'full_p': full_p, 'outfit_desc': outfit_desc}

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

            bot.send_message(cid, "Cosa vuoi fare adesso?", reply_markup=get_confirm_keyboard())
            return

        if is_dual:
            variant_list = []
            for v in flt["variants"]:
                full_p = review_and_fix(build_full_prompt(filter_key, outfit_desc, scene_override=v["scene"], mode=mode), gemini)
                variant_list.append({'name': v["name"], 'full_p': full_p})
            last_prompt[uid] = {'is_dual': True, 'variants': variant_list, 'outfit_desc': outfit_desc}
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
            bot.send_message(cid, f"{header}Cosa vuoi fare adesso?", reply_markup=get_confirm_keyboard())
        else:
            full_p = review_and_fix(build_full_prompt(filter_key, outfit_desc, mode=mode), gemini)
            last_prompt[uid] = {'full_p': full_p, 'outfit_desc': outfit_desc}
            header = f"✅ Filtro: <b>{flt['label']}</b>\n\n"
            CHUNK = 3800
            if len(full_p) <= CHUNK:
                bot.send_message(cid, f"{header}<code>{html.escape(full_p)}</code>")
            else:
                chunks = [full_p[i:i+CHUNK] for i in range(0, len(full_p), CHUNK)]
                bot.send_message(cid, f"{header}<code>{html.escape(chunks[0])}</code>")
                for idx, chunk in enumerate(chunks[1:], 2):
                    bot.send_message(cid, f"<i>(continua {idx}/{len(chunks)})</i>\n<code>{html.escape(chunk)}</code>")
            bot.send_message(cid, "Cosa vuoi fare adesso?", reply_markup=get_confirm_keyboard())
      except Exception as e:
        # FIX 2.0.0: prima un'eccezione qui veniva inghiottita silenziosamente
        # dal ThreadPoolExecutor — l'utente restava bloccato su "Analisi in corso..."
        # senza alcun messaggio di errore e senza log.
        logger.error(f"❌ Atelier _process crash per {username}: {e}", exc_info=True)
        try: bot.delete_message(cid, wait_msg.message_id)
        except Exception: pass
        try:
            bot.send_message(cid, f"❌ <b>Errore interno durante la generazione:</b>\n<code>{html.escape(str(e))}</code>",
                reply_markup=get_confirm_keyboard())
        except Exception: pass

    executor.submit(_process)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text and m.text.startswith('/'):
        return
    uid = m.from_user.id
    bot.reply_to(m, "📸 Invia una foto del costume o outfit da replicare.\nUsa /start per scegliere il filtro.")

# --- SERVER ---

# --- /shared ---
@bot.message_handler(commands=['shared'])
def cmd_shared(m):
    bot.send_message(m.chat.id,
        f"📦 <b>C_shared100.py</b> v{SHARED_VERSION} — {SHARED_DATE}"
    )

if __name__ == "__main__":
    import time
    logger.info(f"✦ Avvio ATELIER v{VERSION}")
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

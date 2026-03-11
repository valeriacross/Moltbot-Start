import os, io, random, logging, flask, telebot, html, time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures as _cf

# --- VERSIONE ---
VERSION = "1.0.0"

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
        "art deco theatre stage", "underwater coral reef"
    ],
    "cielo": [
        "clear blue sky", "dramatic storm clouds", "golden hour sunset",
        "starry night sky", "overcast diffused light", "pink and purple dusk",
        "fog and mist", "bright midday sun", "moonlit night", "aurora borealis",
        "warm sunrise", "dark thunderstorm", "soft cloudy morning", "deep blue twilight",
        "blazing orange sunset"
    ],
    "posa": [
        "standing tall, hand on hip", "seated elegantly, legs crossed",
        "walking confidently toward camera", "three-quarter back view, glancing over shoulder",
        "leaning against a wall, arms crossed", "sitting on floor, knees up",
        "mid-stride, dynamic movement", "hands in pockets, relaxed stance",
        "arms raised, dramatic pose", "crouching low, intense gaze",
        "reclining on surface, propped on elbow", "spinning, fabric in motion",
        "profile view, chin up", "looking down, contemplative", "jumping, frozen mid-air"
    ],
    "espressione": [
        "confident smirk", "serene and calm", "intense direct gaze",
        "mysterious half-smile", "joyful laugh", "pensive and introspective",
        "fierce and bold", "soft and dreamy", "amused and playful",
        "stoic and powerful", "warm and inviting", "cold and distant",
        "surprised and wide-eyed", "sensual and knowing", "proud and regal"
    ],
    "outfit_top": [
        "structured blazer in deep burgundy", "sheer silk blouse with ruffles",
        "leather biker jacket", "elegant off-shoulder gown top", "sequined crop top",
        "oversized cashmere turtleneck", "vintage band tee knotted at waist",
        "tailored white shirt open at collar", "velvet bustier corset",
        "embroidered kimono jacket", "sportswear compression top",
        "flowing chiffon wrap top", "denim shirt rolled at sleeves",
        "sculptural architectural blazer", "backless halter neck top"
    ],
    "outfit_bottom": [
        "wide-leg palazzo trousers in ivory", "micro mini skirt in plaid",
        "floor-length bias-cut satin skirt", "high-waisted leather trousers",
        "ripped skinny jeans", "structured pencil skirt in black",
        "flowy bohemian maxi skirt", "tailored shorts in camel",
        "sequined evening trousers", "cargo pants in olive green",
        "asymmetric wrap skirt", "knit midi skirt in caramel",
        "dramatic ball gown skirt", "wide culottes in linen",
        "sheer layered tulle skirt"
    ],
    "scarpe": [
        "stiletto ankle boots in patent leather", "strappy gold heeled sandals",
        "chunky platform sneakers", "classic red-sole pumps",
        "knee-high suede boots", "embellished mule heels",
        "pointed-toe kitten heels", "metallic gladiator sandals",
        "white sneakers", "block-heel mules in nude",
        "thigh-high vinyl boots", "espadrille wedges",
        "crystal-embellished flats", "western cowboy boots",
        "transparent PVC heels"
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
        "dark gothic", "tropical resort wear",
        "Parisian chic", "Japanese avant-garde",
        "American preppy", "bohemian festival",
        "retro 1980s power dressing"
    ],
    "luce": [
        "dramatic chiaroscuro side lighting", "soft diffused natural light",
        "harsh direct sunlight with deep shadows", "warm golden hour backlight",
        "cool blue moonlight", "studio softbox portrait lighting",
        "neon sign ambient glow", "candlelight warm flicker",
        "mixed daylight and artificial", "hard rim lighting from behind",
        "flat bright fashion photography light", "moody low-key lighting",
        "dappled light through leaves", "reflected light from water",
        "overexposed bleached look"
    ],
    "punto_di_ripresa": [
        "85mm portrait, eye level", "wide angle 24mm full body",
        "high angle looking down", "low angle looking up",
        "extreme close-up on face", "from behind, three-quarter",
        "bird's eye view from above", "dutch angle tilt",
        "telephoto compressed 200mm", "fisheye distortion",
        "mid-shot waist up", "full body wide shot",
        "over-shoulder perspective", "ground level worm's eye",
        "side profile full body"
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
    "punto_di_ripresa": "📷 Inquadratura"
}

def estrai_combinazione():
    """Estrae una opzione casuale per ogni variabile."""
    return {k: random.choice(v) for k, v in VARIABILI.items()}

def build_prompt(combo):
    """Costruisce il prompt completo da una combinazione."""
    scene = (
        f"**Scene:** {combo['sfondo']}, {combo['cielo']}.\n"
        f"**Pose:** {combo['posa']}.\n"
        f"**Expression:** {combo['espressione']}.\n"
        f"**Outfit:** {combo['outfit_top']} with {combo['outfit_bottom']}, {combo['scarpe']}.\n"
        f"**Color palette:** {combo['colore']}.\n"
        f"**Accessories:** {combo['accessori']}.\n"
        f"**Style:** {combo['stile']}.\n"
        f"**Lighting:** {combo['luce']}.\n"
        f"**Shot:** {combo['punto_di_ripresa']}.\n"
    )
    return VALERIA_IDENTITY + "\n" + scene

def format_combinazione(combo):
    """Formatta la combinazione estratta per la visualizzazione."""
    lines = []
    for k, label in VARIABILI_LABELS.items():
        lines.append(f"{label}: <b>{combo[k]}</b>")
    return "\n".join(lines)

# --- GENERAZIONE ---
def execute_generation(full_prompt):
    try:
        contents = [full_prompt]
        if MASTER_PART:
            contents.append(MASTER_PART)
        else:
            logger.warning("⚠️ Generazione senza MASTER_PART.")

        def _call():
            logger.info(f"   📤 Prompt a Gemini ({len(full_prompt)} chars)")
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
    markup.add(InlineKeyboardButton("🎲 Genera sorpresa", callback_data="genera"))
    markup.add(InlineKeyboardButton("🔄 Ancora!", callback_data="genera"))
    return markup

def get_retry_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎲 Nuova sorpresa", callback_data="genera"),
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
    markup.add(InlineKeyboardButton("🎲 Genera la tua sorpresa!", callback_data="genera"))
    bot.send_message(message.chat.id,
        f"<b>🎲 SORPRESA v{VERSION}</b>\n\n"
        f"Ogni volta che premi il pulsante, il bot estrae casualmente <b>12 variabili</b> "
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
@bot.callback_query_handler(func=lambda call: call.data in ["genera", "riprova"])
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    username = call.from_user.username or call.from_user.first_name

    try: bot.answer_callback_query(call.id)
    except Exception: pass

    if call.data == "riprova":
        # Riprova ultima combinazione
        from collections import defaultdict
        saved = last_combo.get(uid)
        if not saved:
            bot.send_message(cid, "⚠️ Nessuna combinazione recente. Genera una nuova.")
            return
        combo = saved
    else:
        combo = estrai_combinazione()
        last_combo[uid] = combo

    combo_text = format_combinazione(combo)
    try:
        bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception:
        pass

    msg = bot.send_message(cid,
        f"🎲 <b>Combinazione estratta:</b>\n\n{combo_text}\n\n"
        f"⏳ Generazione in corso...")

    def run():
        t = time.time()
        full_p = build_prompt(combo)
        img, err = execute_generation(full_p)
        elapsed = round(time.time() - t, 1)

        if img:
            try:
                bot.send_document(cid, io.BytesIO(img),
                    visible_file_name="sorpresa.jpg",
                    caption=f"✅ {elapsed}s",
                    reply_markup=get_retry_keyboard())
                logger.info(f"✅ {username} (id={uid}) — sorpresa generata in {elapsed}s")
            except Exception as e:
                logger.error(f"❌ Errore invio: {e}")
                bot.send_message(cid, f"❌ Generata ma errore nell'invio.\n<code>{html.escape(str(e))}</code>")
        else:
            bot.send_message(cid, f"❌ <b>Generazione fallita</b> ({elapsed}s)\n{err}",
                reply_markup=get_retry_keyboard())
            logger.warning(f"❌ {username} (id={uid}) — fallita ({elapsed}s): {err}")

    executor.submit(run)

# --- STATO ---
last_combo = {}

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

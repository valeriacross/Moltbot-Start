import os, logging, telebot, html, time, random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from C_shared100 import GeminiClient, HealthServer, is_allowed, SHARED_VERSION, SHARED_DATE

# --- VERSIONE ---
VERSION = "1.0.0"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_PRIDE")
gemini = GeminiClient()
server = HealthServer("PRIDE", VERSION)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

logger.info(f"🌈 PRIDE v{VERSION} — inizializzazione")

# ─── DNA ──────────────────────────────────────────────────────────────────────

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

# ─── POOLS ────────────────────────────────────────────────────────────────────

LOCATION_POOL = [
    (
        "Praça do Marquês de Pombal, Lisbon",
        "Praça do Marquês de Pombal, Lisbon Pride parade starting point, "
        "monumental roundabout with Marquis of Pombal column statue at centre, "
        "rainbow flags lining the avenue, crowd energy, blue Lisbon sky, "
        "golden afternoon light, festive Pride atmosphere"
    ),
    (
        "Avenida da Liberdade, Lisbon",
        "Avenida da Liberdade, Lisbon, wide tree-lined grand boulevard, "
        "Pride parade in full swing, rainbow banners suspended between trees, "
        "confetti in the air, music floats passing, warm June afternoon light, "
        "festive joyful crowds lining the sidewalks"
    ),
    (
        "Praça dos Restauradores, Lisbon",
        "Praça dos Restauradores, Lisbon, obelisk of the Restauradores monument, "
        "Eden Teatro facade in background, Pride crowd celebrating, "
        "rainbow flags and balloons everywhere, warm golden light"
    ),
    (
        "Chiado, Rua Garrett, Lisbon",
        "Chiado neighbourhood, Rua Garrett, Lisbon, elegant bohemian street with "
        "historic bookshops and cafés, cobblestone pavement, wrought iron lampposts, "
        "Pride revellers in colourful outfits, late afternoon warm light"
    ),
    (
        "Miradouro de São Pedro de Alcântara, Lisbon",
        "Miradouro de São Pedro de Alcântara viewpoint, Lisbon, panoramic terrace "
        "overlooking the city rooftops and São Jorge Castle, azulejo tile wall, "
        "Pride flags visible across the cityscape, golden sunset light"
    ),
    (
        "Alfama, Beco das Flores, Lisbon",
        "Alfama district, narrow cobblestone alley with colourful hanging laundry, "
        "whitewashed walls with blue azulejo tiles, terracotta rooftops, "
        "potted geraniums on windowsills, intimate festive Pride atmosphere"
    ),
    (
        "LX Factory, Lisbon",
        "LX Factory creative hub, Lisbon, industrial repurposed factory complex "
        "under the 25 de Abril bridge, exposed brick arches, street art murals, "
        "Pride party atmosphere, fairy lights, creative crowd, warm evening light"
    ),
    (
        "Praça do Comércio, Lisbon",
        "Praça do Comércio, Lisbon, grand neoclassical riverside square on the Tagus river, "
        "Arco da Rua Augusta triumphal arch at north end, yellow ochre arcaded buildings, "
        "Tagus river shimmering in background, Pride celebration finale, "
        "golden hour light over the water, confetti and rainbow flags filling the air"
    ),
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

STYLE_POOL = [
    "vibrant editorial photography, golden hour Lisbon light, joyful celebratory energy, high fashion meets street festival, Vogue editorial aesthetic",
    "cinematic wide-angle photography, confetti-filled air, warm festive atmosphere, luxury fashion campaign meets Pride celebration",
    "candid editorial style, dynamic movement, rainbow light flares, joyful spontaneous energy, high-resolution fashion photography",
    "bold graphic editorial, saturated colours, Pride energy at peak, fashion-forward composition, magazine cover aesthetic",
    "warm documentary editorial, authentic joyful moment, soft golden Lisbon light, intimate yet grand, fashion editorial quality",
]

WATERMARK = "feat. Valeria Cross & Friends 🌈"

# ─── GENERAZIONE PROMPT ───────────────────────────────────────────────────────

last_prompt = {}   # uid → str

def build_pride_prompt():
    """Assembla un prompt Pride completo con selezioni casuali dalle pool."""
    location_name, location_desc = random.choice(LOCATION_POOL)
    walter_outfit  = random.choice(WALTER_OUTFIT_POOL)
    carlotta_outfit = random.choice(CARLOTTA_OUTFIT_POOL)
    fufos_acc, fritz_acc = random.choice(DOGS_ACCESSORY_POOL)
    style = random.choice(STYLE_POOL)

    prompt = (
        f"Generate a single high-quality fashion editorial photograph.\n\n"

        f"--- LOCATION ---\n"
        f"{location_desc}\n\n"

        f"--- SUBJECTS — 4 characters, ALL must be present in the frame ---\n\n"

        f"SUBJECT 1 — WALTER:\n"
        f"{WALTER_DNA}\n"
        f"Outfit: {walter_outfit}\n\n"

        f"SUBJECT 2 — CARLOTTA:\n"
        f"{CARLOTTA_DNA}\n"
        f"Outfit: {carlotta_outfit}\n\n"

        f"SUBJECT 3 — FUFOS (dog):\n"
        f"{FUFOS_DNA}\n"
        f"Accessory: {fufos_acc}\n\n"

        f"SUBJECT 4 — FRITZ (dog):\n"
        f"{FRITZ_DNA}\n"
        f"Accessory: {fritz_acc}\n\n"

        f"--- COMPOSITION ---\n"
        f"All four subjects together in one frame. Walter and Carlotta standing or posed naturally "
        f"together, Fufos and Fritz at their feet or being held. "
        f"Natural joyful interaction between the group. "
        f"Full body or three-quarter shot showing complete outfits.\n\n"

        f"--- STYLE ---\n"
        f"{style}\n\n"

        f"--- WATERMARK ---\n"
        f"Elegant cursive watermark reading '{WATERMARK}' "
        f"very small, bottom centre, 90% opacity, champagne gold colour.\n\n"

        f"--- NEGATIVE ---\n"
        f"wrong hair colour on Carlotta, dark hair on Walter, missing glasses, "
        f"missing beard, wrong dog breed, generic crowd replacing subjects, "
        f"blurry faces, missing subjects, studio backdrop instead of location."
    )
    return prompt, location_name

# ─── KEYBOARD ─────────────────────────────────────────────────────────────────

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🌈 Genera prompt", callback_data="pride_generate"),
    )
    return markup

def get_after_prompt_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔄 Nuovo prompt",    callback_data="pride_generate"),
        InlineKeyboardButton("🔁 Stessa location", callback_data="pride_samelocation"),
    )
    markup.row(
        InlineKeyboardButton("📝 Mini caption",    callback_data="pride_minicaption"),
        InlineKeyboardButton("📋 Mini prompt",     callback_data="pride_miniprompt"),
    )
    return markup

# ─── STATO ────────────────────────────────────────────────────────────────────

last_location = {}   # uid → (location_name, location_desc)

# ─── COMANDI ──────────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def cmd_start(m):
    uid = m.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 /start non autorizzato: uid={uid}")
        return
    username = m.from_user.username or m.from_user.first_name
    logger.info(f"🌈 /start da {username} (id={uid})")
    bot.send_message(m.chat.id,
        f"<b>🌈 PRIDE v{VERSION}</b>\n\n"
        f"Genera prompt Flow per il Pride di Lisbona 2026.\n"
        f"Walter, Carlotta, Fufos e Fritz — tutti e quattro insieme.\n\n"
        f"Premi il pulsante per generare!",
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(commands=['info'])
def cmd_info(m):
    bot.send_message(m.chat.id,
        f"<b>🌈 PRIDE v{VERSION}</b>\n\n"
        f"Location: {len(LOCATION_POOL)} · "
        f"Outfit Walter: {len(WALTER_OUTFIT_POOL)} · "
        f"Outfit Carlotta: {len(CARLOTTA_OUTFIT_POOL)} · "
        f"Accessori cani: {len(DOGS_ACCESSORY_POOL)}\n\n"
        f"<i>Zero chiamate Gemini — prompt generato localmente.</i>"
    )

@bot.message_handler(commands=['shared'])
def cmd_shared(m):
    bot.send_message(m.chat.id,
        f"📦 <b>C_shared100.py</b> v{SHARED_VERSION} — {SHARED_DATE}"
    )

@bot.message_handler(commands=['help'])
def cmd_help(m):
    bot.send_message(m.chat.id,
        f"<b>🌈 PRIDE v{VERSION} — Comandi</b>\n\n"
        f"/start — Menu principale\n"
        f"/info — Statistiche pool\n"
        f"/shared — Versione shared\n"
        f"/help — Questo messaggio"
    )

# ─── CALLBACKS ────────────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: c.data.startswith("pride_"))
def handle_pride_callbacks(call):
    uid = call.from_user.id
    if not is_allowed(uid):
        logger.warning(f"🚫 Callback non autorizzato: uid={uid}")
        return
    cid = call.message.chat.id
    try: bot.answer_callback_query(call.id)
    except Exception: pass
    try: bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
    except Exception: pass

    if call.data == "pride_generate":
        _generate_and_send(cid, uid)

    elif call.data == "pride_samelocation":
        loc = last_location.get(uid)
        if not loc:
            _generate_and_send(cid, uid)
            return
        _generate_and_send(cid, uid, fixed_location=loc)

    elif call.data == "pride_minicaption":
        from C_shared100 import generate_mini_caption
        prompt = last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile. Genera prima.")
            return
        wait = bot.send_message(cid, "📝 <b>Genero la mini caption...</b>")
        cap, err = generate_mini_caption(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, cap if cap else err or "❌ Errore.", parse_mode="HTML")

    elif call.data == "pride_miniprompt":
        from C_shared100 import generate_mini_prompt
        prompt = last_prompt.get(uid)
        if not prompt:
            bot.send_message(cid, "⚠️ Nessun prompt disponibile. Genera prima.")
            return
        wait = bot.send_message(cid, "📋 <b>Genero il mini prompt...</b>")
        mini, err = generate_mini_prompt(prompt, gemini)
        try: bot.delete_message(cid, wait.message_id)
        except Exception: pass
        bot.send_message(cid, mini if mini else err or "❌ Errore.", parse_mode="HTML")


def _generate_and_send(cid, uid, fixed_location=None):
    """Genera il prompt e lo invia."""
    if fixed_location:
        location_name, location_desc = fixed_location
        walter_outfit   = random.choice(WALTER_OUTFIT_POOL)
        carlotta_outfit = random.choice(CARLOTTA_OUTFIT_POOL)
        fufos_acc, fritz_acc = random.choice(DOGS_ACCESSORY_POOL)
        style = random.choice(STYLE_POOL)
        prompt = (
            f"Generate a single high-quality fashion editorial photograph.\n\n"
            f"--- LOCATION ---\n{location_desc}\n\n"
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
            f"Elegant cursive watermark reading '{WATERMARK}' "
            f"very small, bottom centre, 90% opacity, champagne gold colour.\n\n"
            f"--- NEGATIVE ---\n"
            f"wrong hair colour on Carlotta, dark hair on Walter, missing glasses, "
            f"missing beard, wrong dog breed, generic crowd replacing subjects, "
            f"blurry faces, missing subjects, studio backdrop instead of location."
        )
    else:
        prompt, location_name = build_pride_prompt()
        location_desc = next(d for n, d in LOCATION_POOL if n == location_name)
        last_location[uid] = (location_name, location_desc)

    last_prompt[uid] = prompt

    bot.send_message(cid,
        f"🌈 <b>Pride Prompt — {location_name}</b>\n\nCopia e incolla su Flow:")

    CHUNK = 3800
    chunks = [prompt[i:i+CHUNK] for i in range(0, len(prompt), CHUNK)]
    for idx, chunk in enumerate(chunks):
        header = "" if len(chunks) == 1 else f"<i>({idx+1}/{len(chunks)})</i>\n"
        if idx == len(chunks) - 1:
            bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>",
                reply_markup=get_after_prompt_keyboard())
        else:
            bot.send_message(cid, f"{header}<code>{html.escape(chunk)}</code>")

    logger.info(f"🌈 Prompt Pride generato — location: {location_name} ({len(prompt)} chars)")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"🌈 Avvio PRIDE v{VERSION}")
    server.start()
    if not gemini.available:
        logger.warning("⚠️ GOOGLE_API_KEY non configurata — mini caption/prompt disabilitati")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=25)
        except Exception as e:
            err = str(e)
            if "409" in err or "Conflict" in err:
                logger.warning("⚠️ 409 Conflict — attendo 15s...")
                time.sleep(15)
            else:
                logger.error(f"❌ Polling error: {e}")
                time.sleep(5)

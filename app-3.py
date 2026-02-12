import os, io, threading, logging, flask, telebot
from telebot import types
from google import genai
from google.genai import types as genai_types
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

MODEL_ID = "nano-banana-pro-preview"

# Preferenze utenti
user_ar = defaultdict(lambda: "16:9")    # Default Formato
user_qty = defaultdict(lambda: 1)         # Default Quantità

# Executor per il parallelismo (max 2 worker per evitare Rate Limit aggressivi)
executor = ThreadPoolExecutor(max_workers=2)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        with open("master_face.png", "rb") as f:
            return genai_types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except Exception as e:
        logger.error(f"❌ Master Face non trovata: {e}")
        return None

MASTER_PART = get_face_part()

# --- GENERAZIONE SINGOLA ---
def generate_single_task(prompt_utente, ar_scelto, img_rif_bytes=None):
    try:
        if not MASTER_PART: return None, "File master_face.png mancante."

        # Identità Valeria Cross [cite: 2026-02-08, 2025-11-21]
        system_instructions = f"""
        ROLE: Expert Vogue Photographer.
        SUBJECT: Nameless Italian transmasculine avatar named Valeria Cross.
        BODY: Soft feminine harmonious hourglass body, prosperous full breasts (Cup D), 180cm, 85kg. 
        SKIN: Completely hairless (arms, legs, chest, breasts - hair NO!).
        FACE: Male Italian face, ~60 years old. Oval-rectangular. Detailed skin. 
        BEARD: Light grey/silver, groomed, 6-7 cm. 
        GLASSES: Mandatory thin octagonal Vogue, Havana dark frame.
        HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Never touching neck/shoulders.
        TECHNICAL: Cinematic realism, 85mm, f/2.8.
        WATERMARK: Mandatory text "feat. Valeria Cross 👠" in elegant cursive champagne color at bottom center/left.
        """

        negatives = "NEGATIVE: masculine body shape, flat chest, body hair, peli, long hair, female face, 1:1 format."

        contents = [
            f"{system_instructions}\n\nSCENE: {prompt_utente}\n\nFORMAT: {ar_scelto}\n\n{negatives}",
            MASTER_PART
        ]

        if img_rif_bytes:
            contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[{"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}]
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data, None
        return None, "Generazione bloccata."
    except Exception as e:
        logger.error(f"❌ Errore Thread: {e}")
        return None, str(e)

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    markup = types.InlineKeyboardMarkup()
    
    # Riga Formati
    markup.row(types.InlineKeyboardButton("3:2 📷", callback_data="ar_3:2"),
               types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"))
    markup.row(types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
               types.InlineKeyboardButton("4:3 📰", callback_data="ar_4:3"))
    markup.row(types.InlineKeyboardButton("3:4 📱", callback_data="ar_3:4"),
               types.InlineKeyboardButton("9:16 📲", callback_data="ar_9:16"))
    
    # Riga Quantità
    markup.row(types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
               types.InlineKeyboardButton("2 Foto", callback_data="qty_2"),
               types.InlineKeyboardButton("4 Foto", callback_data="qty_4"))
               
    bot.send_message(m.chat.id, "<b>Configurazione Valeria Cross</b>\nScegli Formato e Quantità:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ar_') or call.data.startswith('qty_'))
def handle_callbacks(call):
    uid = call.from_user.id
    if call.data.startswith('ar_'):
        user_ar[uid] = call.data.replace('ar_', '')
        msg = f"✅ Formato: <b>{user_ar[uid]}</b>"
    elif call.data.startswith('qty_'):
        user_qty[uid] = int(call.data.replace('qty_', ''))
        msg = f"✅ Quantità batch: <b>{user_qty[uid]}</b>"
    
    bot.answer_callback_query(call.id, msg)
    bot.edit_message_text(f"⚙️ Impostazioni Attuali:\n📐 Formato: <b>{user_ar[uid]}</b>\n🔢 Quantità: <b>{user_qty[uid]}</b>\n\nInvia un prompt!", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['text', 'photo'])
def handle(m):
    uid = m.from_user.id
    qty = user_qty[uid]
    fmt = user_ar[uid]
    
    wait = bot.reply_to(m, f"⏳ <b>Valeria Cross</b> in posa...\nGenerazione di <b>{qty}</b> scatti ({fmt}).")
    
    prompt = m.caption if m.content_type == 'photo' else m.text
    img_data = None
    if m.content_type == 'photo':
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    # Funzione helper per inviare risultati man mano che arrivano
    def task(index):
        res, err = generate_single_task(prompt, fmt, img_data)
        if res:
            try:
                bot.send_document(m.chat.id, io.BytesIO(res), visible_file_name=f"valeria_{index+1}.jpg", caption=f"Scatto {index+1}/{qty}")
            except Exception as e:
                logger.error(f"Errore invio Telegram: {e}")
        else:
            bot.send_message(m.chat.id, f"❌ Errore scatto {index+1}: {err}")

    # Lancio parallelo dei task
    for i in range(qty):
        executor.submit(task, i)

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Valeria Bot Turbo Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling()
    

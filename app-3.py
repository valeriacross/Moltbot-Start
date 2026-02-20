import os, io, threading, logging, flask, telebot, json
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
user_ar = defaultdict(lambda: "16:9")    
user_qty = defaultdict(lambda: 1)         

# Executor (max 2 worker)
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

# --- GENERAZIONE CON DIAGNOSTICA E JSON ---
def generate_single_task(prompt_utente, ar_scelto, img_rif_bytes=None):
    # Prepariamo un dizionario che rappresenti il JSON per l'utente
    debug_payload = {
        "model": MODEL_ID,
        "config": {
            "response_modalities": ["IMAGE"],
            "aspect_ratio": ar_scelto,
            "safety_settings": "BLOCK_NONE (All Categories)"
        },
        "contents": []
    }

    try:
        if not MASTER_PART: return None, "File master_face.png mancante.", None

        system_instructions = f"""
        ROLE: Expert Vogue Photographer.
        SUBJECT: Nameless Italian transmasculine avatar named Valeria Cross.
        BODY: Soft feminine harmonious hourglass body, prosperous full breasts (Cup D), 180cm, 85kg. 
        SKIN: Completely hairless (arms, legs, chest, breasts - hair NO!).
        FACE: Male Italian face, ~60 years old. Oval-rectangular. Detailed skin. 
        BEARD: Light grey/silver, groomed, 6-7 cm. 
        GLASSES: Mandatory thin octagonal Vogue, Havana dark frame.
        HAIR: Light grey/silver. elegant Italian style, 10-15cm on top, 1-2cm on sides. Nape exposed. Never touching neck/shoulders.
        TECHNICAL: Cinematic realism, 85mm, f/2.8.
        WATERMARK: Mandatory text "feat. Valeria Cross 👠" in elegant very small scale, cursive champagne color at bottom center/left, 80% opacity.
        """
        negatives = "NEGATIVE: masculine body shape, flat chest, body hair, peli, long hair, female face, 1:1 format."
        
        full_prompt = f"{system_instructions}\n\nSCENE: {prompt_utente}\n\nFORMAT: {ar_scelto}\n\n{negatives}"
        
        # Popoliamo il debug_payload
        debug_payload["contents"].append({"text": full_prompt})
        debug_payload["contents"].append({"image": "MASTER_FACE_BYTES"})
        if img_rif_bytes:
            debug_payload["contents"].append({"image": "USER_REFERENCE_IMAGE_BYTES"})

        json_string = json.dumps(debug_payload, indent=2)

        contents = [full_prompt, MASTER_PART]
        if img_rif_bytes:
            contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))

        # Chiamata API
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
        )

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            return None, f"⛔ Prompt Illegale: {response.prompt_feedback.block_reason}", json_string

        if not response.candidates:
            return None, "❌ Errore API: Nessun candidato ritornato.", json_string

        candidate = response.candidates[0]

        if candidate.finish_reason != "STOP":
            reasons = [f"{r.category.name}: {r.probability.name}" for r in (candidate.safety_ratings or []) if r.probability not in ["NEGLIGIBLE", "LOW"]]
            reason_str = ", ".join(reasons) if reasons else "Filtro sconosciuto"
            return None, f"🛡️ Blocco Sicurezza: {candidate.finish_reason}\nDettagli: {reason_str}", json_string

        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data:
                    return part.inline_data.data, None, json_string

        return None, "Generazione fallita (No Data).", json_string

    except Exception as e:
        logger.error(f"❌ Errore Thread: {e}")
        return None, f"Crash Tecnico: {str(e)}", json.dumps(debug_payload, indent=2)

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ... (I comandi /start e handle_callbacks rimangono invariati) ...

@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("3:2 📷", callback_data="ar_3:2"),
               types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"))
    markup.row(types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
               types.InlineKeyboardButton("4:3 📰", callback_data="ar_4:3"))
    markup.row(types.InlineKeyboardButton("3:4 📱", callback_data="ar_3:4"),
               types.InlineKeyboardButton("9:16 📲", callback_data="ar_9:16"))
    markup.row(types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
               types.InlineKeyboardButton("2 Foto", callback_data="qty_2"),
               types.InlineKeyboardButton("4 Foto", callback_data="qty_4"))
    bot.send_message(m.chat.id, "<b>Configurazione Valeria Cross</b>\nScegli:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ar_') or call.data.startswith('qty_'))
def handle_callbacks(call):
    uid = call.from_user.id
    if call.data.startswith('ar_'):
        user_ar[uid] = call.data.replace('ar_', '')
        msg = f"✅ Formato: <b>{user_ar[uid]}</b>"
    elif call.data.startswith('qty_'):
        user_qty[uid] = int(call.data.replace('qty_', ''))
        msg = f"✅ Quantità: <b>{user_qty[uid]}</b>"
    bot.answer_callback_query(call.id, msg)
    bot.edit_message_text(f"⚙️ Setup:\n📐 <b>{user_ar[uid]}</b> | 🔢 <b>{user_qty[uid]}</b>", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['text', 'photo'])
def handle(m):
    uid = m.from_user.id
    qty = user_qty[uid]
    fmt = user_ar[uid]
    
    bot.reply_to(m, f"⏳ <b>Valeria Cross</b> in posa...\nGenerazione di <b>{qty}</b> scatti ({fmt}).")
    
    prompt = m.caption if m.content_type == 'photo' else m.text
    img_data = None
    if m.content_type == 'photo':
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    def task(index):
        # La funzione ora restituisce anche il json_payload
        res, err, json_payload = generate_single_task(prompt, fmt, img_data)
        
        # Invio del JSON (indipendentemente dal risultato)
        if json_payload:
            bot.send_message(m.chat.id, f"📝 <b>JSON Payload Scatto {index+1}:</b>\n<code>{json_payload}</code>", parse_mode="HTML")

        if res:
            try:
                bot.send_document(m.chat.id, io.BytesIO(res), visible_file_name=f"valeria_{index+1}.jpg", caption=f"Scatto {index+1}/{qty}")
            except Exception as e:
                logger.error(f"Errore invio: {e}")
        else:
            bot.send_message(m.chat.id, f"❌ <b>Scatto {index+1} fallito:</b>\n{err}")

    for i in range(qty):
        executor.submit(task, i)

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Valeria Debug Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling()
                             

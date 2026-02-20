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

# --- VARIABILI DI STATO ---
user_ar = defaultdict(lambda: "16:9")    
user_qty = defaultdict(lambda: 1)
pending_prompts = {}  
daily_counter = 0     

executor = ThreadPoolExecutor(max_workers=2)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                return genai_types.Part.from_bytes(data=f.read(), mime_type="image/png")
        return None
    except Exception as e:
        logger.error(f"❌ Errore master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- COSTRUZIONE PROMPT DETTAGLIATO (BLOCCHI 1-4) ---
def build_master_prompt(user_text, ar_scelto):
    # BLOCCO 1 & 2 (Identità e Soggetto)
    identity = (
        "IDENTITY: Nameless Italian transmasculine avatar named Valeria Cross. "
        "BODY: Soft feminine harmonious hourglass body, prosperous full breasts (Cup D), 180cm, 85kg. "
        "SKIN: Completely hairless (arms, legs, chest, breasts - hair NO!). "
        "FACE: Male Italian face, ~60 years old. Oval-rectangular. Ultra-detailed skin (pores, wrinkles, bags). "
        "EXPRESSION: calm, half-smile, NO teeth. EYES: dark brown/green. "
        "BEARD: light grey/silver, groomed, 6–7 cm. "
        "GLASSES: MANDATORY thin octagonal Vogue, Havana dark (NEVER removed)."
    )
    # BLOCCO 3 (Capelli e Tecnica)
    technical = (
        "HAIR: Light grey/silver, short elegant Italian style, volume. Sides 1–2 cm, nape exposed. Top <15 cm. "
        "Hair NEVER touching neck, shoulders, or clavicles. "
        "IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. "
        "CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
    )
    # BLOCCO 4 (Rendering e Watermark)
    rendering = (
        "RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. "
        "WATERMARK: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, opacity 90%)."
    )
    # NEGATIVI
    negatives = (
        "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. "
        "[Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders, buzz cut, military. "
        "[Body] body/chest/leg hair (peli NO!). masculine body shape, flat chest, 1:1 format."
    )
    
    return (
        f"--- MASTER PROMPT ACTIVE ---\n"
        f"{identity}\n\n"
        f"{technical}\n\n"
        f"SCENE: {user_text}\n"
        f"FORMAT: {ar_scelto}\n\n"
        f"{rendering}\n\n"
        f"{negatives}"
    )

# --- FUNZIONE CORE GENERAZIONE ---
def execute_generation(full_prompt, img_rif_bytes=None):
    try:
        contents = [full_prompt, MASTER_PART]
        if img_rif_bytes:
            contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in 
                                 ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH", 
                                  "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            )
        )

        if not response.candidates: return None, "❌ Errore API: No candidates."
        candidate = response.candidates[0]
        if candidate.finish_reason != "STOP":
            return None, f"🛡️ Blocco Safety: {candidate.finish_reason}"
        
        for part in candidate.content.parts:
            if part.inline_data: return part.inline_data.data, None
        return None, "Generazione fallita."
    except Exception as e:
        return None, f"Crash: {str(e)}"

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['quota'])
def check_quota(m):
    global daily_counter
    remaining = max(0, 50 - daily_counter)
    bot.reply_to(m, f"📊 <b>Monitoraggio Quota</b>\nScatti confermati: {daily_counter}\nResidui: {remaining}/50")

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_gen", "cancel_gen"])
def handle_confirmation(call):
    uid = call.from_user.id
    global daily_counter

    if call.data == "cancel_gen":
        pending_prompts.pop(uid, None)
        bot.edit_message_text("❌ <b>Annullato.</b> Quota salva.", call.message.chat.id, call.message.message_id)
        return

    data = pending_prompts.get(uid)
    if not data:
        bot.answer_callback_query(call.id, "Dati scaduti.")
        return

    daily_counter += data['qty']
    bot.edit_message_text(f"🚀 <b>Confermato.</b> Generazione di {data['qty']} scatti...", call.message.chat.id, call.message.message_id)
    
    for i in range(data['qty']):
        executor.submit(lambda idx=i: bot.send_document(call.message.chat.id, io.BytesIO(execute_generation(data['full_p'], data['img'])[0]), visible_file_name=f"valeria_{idx+1}.jpg") if execute_generation(data['full_p'], data['img'])[0] else bot.send_message(call.message.chat.id, f"❌ Fallito: {execute_generation(data['full_p'], data['img'])[1]}"))

    pending_prompts.pop(uid, None)

@bot.message_handler(content_types=['text', 'photo'])
def ask_confirmation(m):
    uid = m.from_user.id
    user_text = m.caption if m.content_type == 'photo' else m.text
    img_data = bot.download_file(bot.get_file(m.photo[-1].file_id).file_path) if m.content_type == 'photo' else None

    # COSTRUIAMO IL PROMPT COMPLETO QUI
    full_verbose_prompt = build_master_prompt(user_text, user_ar[uid])

    pending_prompts[uid] = {
        'full_p': full_verbose_prompt, 
        'qty': user_qty[uid], 
        'img': img_data
    }

    # JSON ORA CONTIENE TUTTO IL PROMPT COPIA/INCOLLA
    preview_json = {
        "status": "AWAITING_CONFIRMATION",
        "full_detailed_prompt": full_verbose_prompt,
        "metadata": {
            "model": MODEL_ID,
            "aspect_ratio": user_ar[uid],
            "samples": user_qty[uid]
        }
    }

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
    markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

    bot.reply_to(m, 
        f"📝 <b>Anteprima JSON (Copia/Incolla sotto):</b>\n<code>{json.dumps(preview_json, indent=2)}</code>\n\n"
        f"Vuoi procedere? (Consumerà {user_qty[uid]} scatti)", 
        reply_markup=markup)

# (Resto del codice Flask e Polling uguale...)
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Valeria Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling()
    

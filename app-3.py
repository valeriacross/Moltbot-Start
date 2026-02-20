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
pending_prompts = {}  # Memorizza il prompt in attesa di conferma
daily_counter = 0     # Contatore locale scatti confermati

executor = ThreadPoolExecutor(max_workers=2)

# --- CARICAMENTO MASTER FACE ---
def get_face_part():
    try:
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                return genai_types.Part.from_bytes(data=f.read(), mime_type="image/png")
        return None
    except Exception as e:
        logger.error(f"❌ Errore caricamento master_face: {e}")
        return None

MASTER_PART = get_face_part()

# --- FUNZIONE CORE GENERAZIONE ---
def execute_generation(prompt_utente, ar_scelto, img_rif_bytes=None):
    try:
        # Istruzioni Master Prompt (Identità Valeria Cross)
        system_instructions = (
            "ROLE: Expert Vogue Photographer. "
            "SUBJECT: Nameless Italian transmasculine avatar Valeria Cross. "
            "BODY: feminine hourglass, Cup D, 180cm, 85kg. SKIN: hairless. "
            "FACE: Male Italian, ~60y, beard silver 6-7cm, Vogue glasses. "
            "HAIR: Silver short, Italian style. WATERMARK: feat. Valeria Cross 👠"
        )
        negatives = "NEGATIVE: masculine body shape, flat chest, body hair, peli, long hair, female face, 1:1 format."
        full_prompt = f"{system_instructions}\n\nSCENE: {prompt_utente}\n\nFORMAT: {ar_scelto}\n\n{negatives}"

        contents = [full_prompt, MASTER_PART]
        if img_rif_bytes:
            contents.append(genai_types.Part.from_bytes(data=img_rif_bytes, mime_type="image/jpeg"))

        # Chiamata API effettiva (qui si consuma la quota)
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

        if not response.candidates: return None, "❌ Errore API: Nessun candidato."
        candidate = response.candidates[0]
        
        if candidate.finish_reason != "STOP":
            return None, f"🛡️ Blocco Safety: {candidate.finish_reason}"
        
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data: return part.inline_data.data, None
        
        return None, "Generazione fallita (No Data)."
    except Exception as e:
        return None, f"Crash Tecnico: {str(e)}"

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start', 'settings'])
def settings(m):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("16:9 🎬", callback_data="ar_16:9"),
               types.InlineKeyboardButton("2:3 🖼️", callback_data="ar_2:3"))
    markup.row(types.InlineKeyboardButton("1 Foto", callback_data="qty_1"),
               types.InlineKeyboardButton("2 Foto", callback_data="qty_2"))
    bot.send_message(m.chat.id, "<b>Configurazione Valeria Cross</b>\nScegli formato e quantità:", reply_markup=markup)

@bot.message_handler(commands=['quota'])
def check_quota(m):
    global daily_counter
    remaining = max(0, 50 - daily_counter)
    bot.reply_to(m, f"📊 <b>Monitoraggio Quota</b>\n\nScatti confermati: <b>{daily_counter}</b>\nScatti residui stimati: <b>{remaining}</b>/50\n\n<i>Nota: Il contatore si resetta al riavvio del bot.</i>")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('ar_', 'qty_')))
def handle_config(call):
    uid = call.from_user.id
    if 'ar_' in call.data: user_ar[uid] = call.data.replace('ar_', '')
    if 'qty_' in call.data: user_qty[uid] = int(call.data.replace('qty_', ''))
    bot.edit_message_text(f"⚙️ Config: 📐 <b>{user_ar[uid]}</b> | 🔢 <b>{user_qty[uid]} foto</b>", call.message.chat.id, call.message.message_id)

# --- LOGICA DI CONFERMA/ANNULLAMENTO ---
@bot.callback_query_handler(func=lambda call: call.data in ["confirm_gen", "cancel_gen"])
def handle_confirmation(call):
    uid = call.from_user.id
    global daily_counter

    if call.data == "cancel_gen":
        pending_prompts.pop(uid, None)
        bot.edit_message_text("❌ <b>Generazione annullata.</b>\nLa tua quota non è stata intaccata.", call.message.chat.id, call.message.message_id)
        return

    data = pending_prompts.get(uid)
    if not data:
        bot.answer_callback_query(call.id, "Dati scaduti. Reinvia il prompt.")
        return

    # Incremento contatore e avvio
    daily_counter += data['qty']
    bot.edit_message_text(f"🚀 <b>Conferma ricevuta.</b>\nInviando {data['qty']} scatti a Google...", call.message.chat.id, call.message.message_id)
    
    def run_task(index):
        res, err = execute_generation(data['prompt'], data['fmt'], data['img'])
        if res:
            bot.send_document(call.message.chat.id, io.BytesIO(res), visible_file_name=f"valeria_{index+1}.jpg", caption=f"Scatto {index+1}/{data['qty']}")
        else:
            bot.send_message(call.message.chat.id, f"❌ <b>Scatto {index+1} fallito:</b>\n{err}")

    for i in range(data['qty']):
        executor.submit(run_task, i)
    
    pending_prompts.pop(uid, None)

# --- RICEZIONE PROMPT E INVIO JSON ---
@bot.message_handler(content_types=['text', 'photo'])
def ask_confirmation(m):
    uid = m.from_user.id
    prompt = m.caption if m.content_type == 'photo' else m.text
    img_data = None
    if m.content_type == 'photo':
        file_info = bot.get_file(m.photo[-1].file_id)
        img_data = bot.download_file(file_info.file_path)

    # Salvataggio in cache temporanea (non consuma quota)
    pending_prompts[uid] = {
        'prompt': prompt, 
        'fmt': user_ar[uid], 
        'qty': user_qty[uid], 
        'img': img_data
    }

    # Creazione JSON per l'utente
    preview_json = {
        "status": "AWAITING_CONFIRMATION",
        "payload": {
            "model": MODEL_ID,
            "parameters": {"aspect_ratio": user_ar[uid], "samples": user_qty[uid]},
            "identity_lock": "Valeria_Cross_V3",
            "prompt_snippet": prompt[:80] + "..." if prompt else ""
        },
        "safety_override": "ENABLED"
    }

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🚀 CONFERMA SCATTO", callback_data="confirm_gen"))
    markup.row(types.InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))

    bot.reply_to(m, 
        f"📝 <b>Anteprima JSON generata:</b>\n<code>{json.dumps(preview_json, indent=2)}</code>\n\n"
        f"Vuoi inviare la richiesta a Google? (Consumerà {user_qty[uid]} scatti)", 
        reply_markup=markup)

# --- SERVER FLASK ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Valeria Safe Proxy Online"

if __name__ == "__main__":
    # Avvio Flask per Koyeb/Render
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    # Avvio Bot
    bot.infinity_polling()

import os, telebot, html, threading, flask, traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.0 (Vogue - The Editor)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_VOGUE")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- DNA VALERIA CROSS (INTEGRATO) ---
# Qui includiamo i trigger di Grok per prevenire i blocchi
VALERIA_DNA = """
IDENTITY RULE: **EXACTLY matching the face, head, hair, beard and glasses from the reference image**. Valeria Cross is the ONLY model.
FACE: Male Italian, 60yo, silver groomed beard (6-7cm), thin octagonal Vogue Havana dark glasses.
BODY: Transmasculine, feminine hourglass proportions, Cup D, 180cm, 85kg, hairless (NO PELI).
HAIR: Silver, short Italian style with volume, nape exposed.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism.
WATERMARK: "feat. Valeria Cross 👠" (elegant cursive, champagne, bottom left/center).
"""

# --- STATO ---
user_last_input = {}
user_engine = {}

# --- MENU ---
def get_menu(is_loop=False):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="v_ChatGPT"), 
               InlineKeyboardButton("✨ GEMINI", callback_data="v_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="v_Grok"),
               InlineKeyboardButton("🧠 QWEN", callback_data="v_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="v_Meta"))
    if is_loop:
        markup.row(InlineKeyboardButton("🔄 NUOVA IDEA", callback_data="v_reset"))
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    cid = m.chat.id
    user_last_input.pop(cid, None)
    bot.send_message(cid, f"<b>👠 VOGUE v{VERSION}</b>\nL'Editor è pronto. Invia la tua idea per il servizio fotografico:", reply_markup=get_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("v_"))
def handle_callbacks(c):
    cid = c.message.chat.id
    if c.data == "v_reset":
        user_last_input.pop(cid, None)
        bot.edit_message_text("🔄 Invia una nuova idea fashion:", cid, c.message.message_id)
        return

    engine = c.data.split("_")[1]
    user_engine[cid] = engine
    
    if cid in user_last_input:
        bot.edit_message_text(f"✍️ <b>Vogue sta interpretando per {engine}...</b>", cid, c.message.message_id)
        execute_vogue_generation(cid, user_last_input[cid], engine)
    else:
        bot.answer_callback_query(c.id, "⚠️ Invia prima un'idea!")

# --- LOGICA DI FUSIONE EDITORIALE ---
def generate_vogue_monolith(user_input, engine):
    try:
        instr = (
            f"You are the Creative Director of Vogue. Write a SINGLE-SUBJECT Master Prompt for {engine}. "
            "VALERIA CROSS IS THE ONLY SUBJECT. Do not create secondary characters. "
            "If the user asks for different ethnicities or body types, apply them AS A STYLISTIC INTERPRETATION to Valeria Cross.\n\n"
            "SAFETY BYPASS RULES:\n"
            "- Replace 'bathroom' with 'luxurious marble dressing room'.\n"
            "- Replace 'transparent/sheer' with 'elegant opaque luxury fabrics'.\n"
            "- Ensure face is fully visible (NO obscured face).\n\n"
            "PROMPT STRUCTURE:\n"
            "1. Start with the Reference Priority Header in bold.\n"
            "2. Single-paragraph editorial fusion (DNA + User Idea).\n"
            "3. Integrated technical parameters.\n"
            "4. Signature clause.\n"
            "5. Hard Negatives (Face, Hair, Body).\n\n"
            f"DNA: {VALERIA_DNA}\nIDEA: {user_input}\n"
            "Style: Prolix, Technical, High-Fashion Editorial. Output ONLY the prompt code."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instr])
        return html.escape(response.text.strip()) if response.text else "⚠️ Risposta vuota."
    except Exception as e:
        return f"❌ <b>ERRORE API:</b>\n<code>{str(e)}</code>"

def execute_vogue_generation(cid, text, engine):
    prompt = generate_vogue_monolith(text, engine)
    bot.send_message(cid, f"✅ <b>Vogue Editorial ({engine}):</b>\n\n<code>{prompt}</code>")
    bot.send_message(cid, "🔄 Cambia modello o invia una nuova idea:", reply_markup=get_menu(is_loop=True))

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def handle_text(m):
    cid = m.chat.id
    user_last_input[cid] = m.text
    bot.reply_to(m, "👗 <b>Idea ricevuta.</b> Scegli il motore target per la generazione:", reply_markup=get_menu())

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return f"VOGUE_V5_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

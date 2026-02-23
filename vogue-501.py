import os, telebot, html, threading, flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.0 (Closet - The Stylist)"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- DNA VALERIA CROSS ---
VALERIA_DNA = """
IDENTITY RULE: **EXACTLY matching the face, head, hair, beard and glasses from the reference image**. Valeria Cross is the ONLY model.
FACE: Male Italian, 60yo, silver groomed beard (6-7cm), thin octagonal Vogue Havana dark glasses.
BODY: Transmasculine, feminine hourglass proportions, Cup D, 180cm, 85kg, hairless (NO PELI).
HAIR: Silver, short Italian style with volume, nape exposed.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism.
WATERMARK: "feat. Valeria Cross 👠" (elegant cursive, champagne, bottom left/center).
"""

user_last_input = {}

def get_menu(is_loop=False):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="c_ChatGPT"), InlineKeyboardButton("✨ GEMINI", callback_data="c_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="c_Grok"), InlineKeyboardButton("🧠 QWEN", callback_data="c_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="c_Meta"))
    if is_loop: markup.row(InlineKeyboardButton("🔄 NUOVO OUTFIT", callback_data="c_reset"))
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_last_input.pop(m.chat.id, None)
    bot.send_message(m.chat.id, f"<b>👗 CLOSET v{VERSION}</b>\nInvia l'outfit o il tessuto che vuoi testare:", reply_markup=get_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("c_"))
def handle_callbacks(c):
    cid = c.message.chat.id
    if c.data == "c_reset":
        user_last_input.pop(cid, None)
        bot.edit_message_text("🔄 Invia una nuova idea per l'outfit:", cid, c.message.message_id)
        return
    engine = c.data.split("_")[1]
    if cid in user_last_input:
        bot.edit_message_text(f"🧵 <b>Closet sta vestendo Valeria per {engine}...</b>", cid, c.message.message_id)
        execute_closet_generation(cid, user_last_input[cid], engine)
    else: bot.answer_callback_query(c.id, "⚠️ Invia prima un'idea!")

def generate_closet_monolith(user_input, engine):
    try:
        instr = (
            f"You are the High-Fashion Stylist for Valeria Cross. Write a Master Prompt for {engine}. "
            "VALERIA CROSS IS THE ONLY SUBJECT. Do not create other people. "
            "Focus on the interaction between fabrics and her specific body (hourglass, Cup D, 180cm).\n\n"
            "SAFETY & TEXTURE RULES:\n"
            "- Replace 'bathroom' with 'luxurious marble dressing room'.\n"
            "- Replace 'transparent/sheer' with 'elegant opaque luxury fabrics'.\n"
            "- Ensure the face is always fully visible (NO obscured face).\n\n"
            "PROMPT STRUCTURE:\n"
            "1. Header: **EXACTLY matching the face, head, hair, beard and glasses from the reference image**.\n"
            "2. Verbose technical description of the outfit, textures, and how they drape on Valeria's body.\n"
            "3. Integrated technical params and signature.\n"
            "4. Hard Negatives for face, hair, and body.\n\n"
            f"DNA: {VALERIA_DNA}\nOUTFIT IDEA: {user_input}\n"
            "Style: Prolix, Technical, Stylist Journal. Output ONLY the code block."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instr])
        return html.escape(response.text.strip()) if response.text else "⚠️ Empty."
    except Exception as e: return f"❌ <b>ERRORE:</b>\n<code>{str(e)}</code>"

def execute_closet_generation(cid, text, engine):
    prompt = generate_closet_monolith(text, engine)
    bot.send_message(cid, f"✅ <b>Closet Stylist Prompt ({engine}):</b>\n\n<code>{prompt}</code>")
    bot.send_message(cid, "🔄 Cambia motore o nuovo outfit:", reply_markup=get_menu(is_loop=True))

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def handle_text(m):
    user_last_input[m.chat.id] = m.text
    bot.reply_to(m, "🧵 <b>Outfit ricevuto.</b> Scegli il motore:", reply_markup=get_menu())

app = flask.Flask(__name__)
@app.route('/')
def h(): return "CLOSET_V5_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

import os, telebot, html, threading, flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.0 (Synthetix - Monolithic Architect)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- DNA VALERIA CROSS (Istruzioni Sistemiche per l'IA) ---
# Queste non vengono più incollate, ma usate come "conoscenza base" dell'architetto.
VALERIA_DNA = """
IDENTITY: Italian transmasculine avatar (Valeria Cross).
BODY: Soft feminine proportions, hourglass, Cup D, 180cm, 85kg. Hairless (NO PELI).
FACE: Male Italian, 60yo, oval-rectangular, ultra-detailed skin (pores/wrinkles).
BEARD: Silver/grey, groomed, 6-7cm. 
GLASSES: Thin octagonal Vogue Havana dark (MANDATORY).
HAIR: Silver, short Italian style with volume, nape exposed, never touching neck/shoulders.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism, subsurface scattering.
"""

# --- STATO ---
user_engine = {}

# --- MENU MOTORI ---
def get_engine_kb():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="eng_ChatGPT"), 
               InlineKeyboardButton("✨ GEMINI", callback_data="eng_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="eng_Grok"),
               InlineKeyboardButton("🧠 QWEN", callback_data="eng_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="eng_Meta"))
    return markup

@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    cid = m.chat.id
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il target per la fusione del prompt:", reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_"))
def set_engine(c):
    cid = c.message.chat.id
    user_engine[cid] = c.data.split("_")[1]
    bot.edit_message_text(f"✅ Target: <b>{user_engine[cid]}</b>\nInvia l'idea da fondere nel Master Prompt.", cid, c.message.message_id)

# --- LOGICA DI GENERAZIONE MONOLITICA (A+B=C Integrato) ---
def generate_monolith_prompt(user_input, engine):
    """Chiede a Gemini di scrivere l'intero Master Prompt v1.1 integrando l'input."""
    try:
        system_instruction = (
            f"You are the Lead Vogue Architect. Your task is to write a MASTER PROMPT v1.1 optimized for {engine}. "
            "The output must be a single, dense, technical document. NO bullet points. NO conversational text. "
            "You must fuse the user's scene idea with the mandatory DNA of Valeria Cross. "
            "The final document must follow this structure:\n"
            "1. HEADER: MASTER PROMPT v1.1 — ZERO FACE DRIFT.\n"
            "2. IDENTITY & SUBJECT: Integrated description of the transmasculine identity and body.\n"
            "3. FACE & HAIR: Extremely detailed technical description of the 60yo male face, silver beard, and Vogue glasses.\n"
            "4. SCENE & CONCEPT: A technical, keyword-rich prose that blends the user idea with the identity. "
            "Explain how the scene materials (e.g. lemon peel, fire, water) interact with the beard and skin.\n"
            "5. TECHNICAL PARAMETERS: 85mm, f/2.8, etc.\n"
            "6. NEGATIVE PROMPTS: Dedicated sections for face, hair, and body.\n\n"
            f"VALERIA DNA: {VALERIA_DNA}\n"
            f"USER SCENE IDEA: {user_input}\n\n"
            "STYLE: Verbose, prolix, didactic, and technical. Use high-fashion editorial terminology."
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[system_instruction]
        )
        return html.escape(response.text.strip())
    except Exception as e:
        print(f"Error: {e}")
        return f"Error generating prompt. Original input: {html.escape(user_input)}"

# --- GESTORE MESSAGGI ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return

    wait = bot.send_message(cid, f"🚀 <b>Generazione Monolith per {user_engine[cid]} in corso...</b>")
    
    # Generazione integrale (non più pezzi incollati)
    final_monolith = generate_monolith_prompt(m.text, user_engine[cid])
    
    bot.delete_message(cid, wait.message_id)
    bot.reply_to(m, f"✅ <b>Master Prompt Pronto:</b>\n\n<code>{final_monolith}</code>")

@bot.message_handler(content_types=['photo', 'sticker', 'video', 'document'])
def handle_docs(m):
    bot.reply_to(m, "⚠️ Solo testo accettato per la generazione tecnica.")

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "ARCHITECT_V5_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

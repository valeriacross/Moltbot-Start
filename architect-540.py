import os, telebot, html, threading, flask, traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.4 (Synthetix - Ref-Priority & Safety)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- FIRMA MANDATORIA ---
WATERMARK_SPECS = """
Include a subtle watermark signature reading: "feat. Valeria Cross 👠"
Style: elegant handwritten cursive, champagne color, opacity 90%, bottom left/center.
"""

# --- DNA VALERIA CROSS (UPGRADED v5.4) ---
# Integriamo i nuovi trigger di sicurezza e priorità reference.
VALERIA_DNA = f"""
IDENTITY RULE: EXACTLY matching the face, head, hair, beard and glasses from the provided reference image. ZERO face drift allowed.
BODY: Soft feminine proportions, hourglass, Cup D, 180cm, 85kg. Hairless (NO PELI).
FACE: Male Italian, 60yo, oval-rectangular, ultra-detailed skin (pores/wrinkles).
BEARD: Silver/grey, groomed, 6-7cm. 
GLASSES: Thin octagonal Vogue Havana dark (MANDATORY).
HAIR: Silver, short Italian style with volume, nape exposed.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism.
WATERMARK: {WATERMARK_SPECS}
SAFETY RULES: NO transparent fabrics (use 'opaque luxury'). NO bathrooms (use 'luxurious dressing room'). NO obscured face.
"""

user_engine = {}
user_last_input = {}

# --- MENU ---
def get_engine_kb(is_loop=False):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="eng_ChatGPT"), 
               InlineKeyboardButton("✨ GEMINI", callback_data="eng_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="eng_Grok"),
               InlineKeyboardButton("🧠 QWEN", callback_data="eng_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="eng_Meta"))
    if is_loop:
        markup.row(InlineKeyboardButton("🔄 NUOVA RICHIESTA DA ZERO", callback_data="action_reset"))
    return markup

@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    cid = m.chat.id
    user_last_input.pop(cid, None)
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il modello target:", reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_") or c.data == "action_reset")
def handle_callbacks(c):
    cid = c.message.chat.id
    if c.data == "action_reset":
        user_engine.pop(cid, None); user_last_input.pop(cid, None)
        bot.edit_message_text("🔄 Reset completato. Scegli un modello:", cid, c.message.message_id, reply_markup=get_engine_kb())
        return

    engine_choice = c.data.split("_")[1]
    user_engine[cid] = engine_choice
    bot.answer_callback_query(c.id, f"Target: {engine_choice}")

    if cid in user_last_input:
        bot.edit_message_text(f"⚙️ <b>Ricalcolo Strategico per {engine_choice}...</b>", cid, c.message.message_id)
        execute_generation(cid, user_last_input[cid], engine_choice)
    else:
        bot.edit_message_text(f"✅ Target: <b>{engine_choice}</b>\nInvia l'idea da processare.", cid, c.message.message_id)

# --- LOGICA DI GENERAZIONE STRATEGICA ---
def generate_monolith_prompt(user_input, engine):
    try:
        # Istruzione di sistema potenziata con i trigger di Grok
        instr = (
            f"Write a professional MASTER PROMPT v1.1 optimized for {engine}. "
            "You must follow these STRATEGIC STEPS:\n"
            "1. START with the header: **EXACTLY matching the face, head, hair, beard and glasses from the provided reference image**.\n"
            "2. FILTER BYPASS: If the user mentions 'bathroom', use 'luxurious marble dressing room'. "
            "If the user mentions 'sheer' or 'transparent', use 'elegant opaque luxurious fabric'.\n"
            "3. NO OBSCURED FEATURES: Ensure the face is fully visible. No objects obscuring identity.\n"
            "4. INTEGRATION: Fuse the user idea with Valeria Cross DNA.\n"
            "5. NEGATIVES: Use HEAVY negatives: 'young female face, long dark hair, no beard, obscured face, low quality, 1:1 ratio'.\n"
            f"DNA: {VALERIA_DNA}\nIDEA: {user_input}\n"
            "Style: Prolix, Technical, Vogue Editorial. Output in a single monolithic code block."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instr])
        return html.escape(response.text.strip()) if response.text else "⚠️ Risposta vuota."
    except Exception as e:
        return f"❌ <b>ERRORE API:</b>\n<code>{str(e)}</code>"

def execute_generation(cid, text, engine):
    final_monolith = generate_monolith_prompt(text, engine)
    bot.send_message(cid, f"✅ <b>Master Prompt ({engine}):</b>\n\n<code>{final_monolith}</code>")
    bot.send_message(cid, f"🔄 Vuoi rigenerare per un altro modello o iniziare da zero?", reply_markup=get_engine_kb(is_loop=True))

@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return
    user_last_input[cid] = m.text
    wait = bot.send_message(cid, f"🚀 <b>Generazione Monolith v5.4 per {user_engine[cid]}...</b>")
    execute_generation(cid, m.text, user_engine[cid])
    bot.delete_message(cid, wait.message_id)

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return f"ARCHITECT_V5.4_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

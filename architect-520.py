import os, telebot, html, threading, flask, traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.2 (Synthetix - Loop Edition)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- DNA VALERIA CROSS ---
VALERIA_DNA = """
IDENTITY: Italian transmasculine avatar (Valeria Cross).
BODY: Soft feminine proportions, hourglass, Cup D, 180cm, 85kg. Hairless (NO PELI).
FACE: Male Italian, 60yo, oval-rectangular, ultra-detailed skin (pores/wrinkles).
BEARD: Silver/grey, groomed, 6-7cm. 
GLASSES: Thin octagonal Vogue Havana dark (MANDATORY).
HAIR: Silver, short Italian style with volume, nape exposed, never touching neck/shoulders.
TECHNICAL: 85mm, f/2.8, ISO 200, 1/160s. 8K, cinematic realism, subsurface scattering.
"""

# --- STATO DEL BOT ---
user_engine = {}      # Memorizza il modello target
user_last_input = {}  # Memorizza l'ultima idea (per il loop)

# --- MENU DINAMICO ---
def get_engine_kb(is_loop=False):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="eng_ChatGPT"), 
               InlineKeyboardButton("✨ GEMINI", callback_data="eng_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="eng_Grok"),
               InlineKeyboardButton("🧠 QWEN", callback_data="eng_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="eng_Meta"))
    
    if is_loop:
        # Pulsante speciale per resettare e cambiare idea
        markup.row(InlineKeyboardButton("🔄 NUOVA RICHIESTA DA ZERO", callback_data="action_reset"))
    return markup

@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    cid = m.chat.id
    user_last_input.pop(cid, None) # Pulisce l'ultima idea se presente
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il modello target:", reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_") or c.data == "action_reset")
def handle_callbacks(c):
    cid = c.message.chat.id
    
    # Caso 1: Reset Totale
    if c.data == "action_reset":
        user_engine.pop(cid, None)
        user_last_input.pop(cid, None)
        bot.edit_message_text("🔄 Stato resettato. Scegli un nuovo modello:", cid, c.message.message_id, reply_markup=get_engine_kb())
        return

    # Caso 2: Selezione Modello
    engine_choice = c.data.split("_")[1]
    user_engine[cid] = engine_choice
    bot.answer_callback_query(c.id, f"Target: {engine_choice}")

    # Se c'è già un'idea salvata, facciamo partire il loop automatico
    if cid in user_last_input:
        bot.edit_message_text(f"⚙️ <b>Ricalcolo Master Prompt per {engine_choice}...</b>", cid, c.message.message_id)
        execute_generation(cid, user_last_input[cid], engine_choice)
    else:
        # Altrimenti chiediamo l'idea per la prima volta
        bot.edit_message_text(f"✅ Target: <b>{engine_choice}</b>\nInvia la tua idea da processare.", cid, c.message.message_id)

# --- MOTORE DI GENERAZIONE ---
def generate_monolith_prompt(user_input, engine):
    try:
        instr = (
            f"Write a professional MASTER PROMPT v1.1 for {engine}. "
            "FUSE the user idea with Valeria Cross's identity. "
            "Output MUST be a single technical document. NO prose, NO chat. "
            f"DNA: {VALERIA_DNA}\nIDEA: {user_input}\n"
            "Style: Prolix, Technical, Vogue Editorial."
        )
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instr])
        return html.escape(response.text.strip()) if response.text else "⚠️ Risposta vuota dall'API."
    except Exception as e:
        return f"❌ <b>ERRORE API:</b>\n<code>{str(e)}</code>"

def execute_generation(cid, text, engine):
    """Funzione centrale per gestire la generazione e la riproposizione del menu."""
    final_monolith = generate_monolith_prompt(text, engine)
    
    # Invio del risultato
    bot.send_message(cid, f"✅ <b>Master Prompt ({engine}):</b>\n\n<code>{final_monolith}</code>")
    
    # Riproposizione del menu per il loop
    bot.send_message(
        cid, 
        f"🔄 Vuoi rigenerare la stessa idea per un altro modello o iniziare da zero?",
        reply_markup=get_engine_kb(is_loop=True)
    )

# --- GESTORE MESSAGGI TESTUALI ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return

    # Salviamo l'idea per permettere il cambio modello successivo
    user_last_input[cid] = m.text
    
    wait = bot.send_message(cid, f"🚀 <b>Generazione Monolith per {user_engine[cid]}...</b>")
    execute_generation(cid, m.text, user_engine[cid])
    bot.delete_message(cid, wait.message_id)

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return f"ARCHITECT_V5.2_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

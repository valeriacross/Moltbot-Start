import os, telebot, html, threading, flask, traceback
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "5.1 (Synthetix - Debug Mode)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Inizializzazione client
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

user_engine = {}

# --- MENU ---
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
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION}</b>\nScegli il target:", reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_"))
def set_engine(c):
    cid = c.message.chat.id
    user_engine[cid] = c.data.split("_")[1]
    bot.answer_callback_query(c.id, f"Target: {user_engine[cid]}")
    bot.edit_message_text(f"✅ Target impostato: <b>{user_engine[cid]}</b>\nInvia l'idea della scena.", cid, c.message.message_id)

# --- LOGICA DI GENERAZIONE ---
def generate_monolith_prompt(user_input, engine):
    try:
        # Prompt di sistema ultra-dettagliato
        instr = (
            f"Write a professional MASTER PROMPT v1.1 for {engine}. "
            "FUSE the user idea with Valeria Cross's identity. "
            "Output MUST be a single technical document. NO prose, NO chat. "
            f"DNA: {VALERIA_DNA}\nIDEA: {user_input}\n"
            "Style: Prolix, Technical, Vogue Editorial."
        )
        
        # Chiamata API
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[instr]
        )
        
        # Gestione sicura della risposta
        if response and response.text:
            return html.escape(response.text.strip())
        else:
            return "⚠️ L'API ha restituito una risposta vuota. Possibile blocco di sicurezza."
            
    except Exception as e:
        # Questo cattura l'errore e lo trasforma in testo per il bot
        error_msg = f"❌ <b>ERRORE API:</b>\n<code>{str(e)}</code>"
        return error_msg

# --- GESTORE MESSAGGI ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    
    # 1. Verifica se il motore esiste
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Seleziona prima un target con /motore")
        return

    # 2. Feedback immediato (se non vedi questo, il bot non riceve il messaggio)
    wait = bot.send_message(cid, f"⚙️ <b>Elaborazione Monolith ({user_engine[cid]})...</b>")
    
    try:
        # 3. Generazione
        final_monolith = generate_monolith_prompt(m.text, user_engine[cid])
        
        # 4. Invio risultato
        bot.delete_message(cid, wait.message_id)
        bot.reply_to(m, f"✅ <b>Master Prompt Pronto:</b>\n\n<code>{final_monolith}</code>")
        
    except Exception as e:
        # 5. Report di crash strutturale
        full_error = traceback.format_exc()
        bot.send_message(cid, f"🆘 <b>CRASH INTERNO:</b>\n<code>{full_error}</code>")

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "ARCHITECT_V5.1_ONLINE"

if __name__ == "__main__":
    print("Bot in partenza...")
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

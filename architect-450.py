import os, telebot, html, threading, flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
# Versione 4.50: Implementazione sanificazione HTML, gestione errori API e nuovi motori.
VERSION = "4.50 (Architect - Resilient Edition)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BLOCCHI VALERIA CROSS (MANDATORI) ---
# Questi blocchi sono costanti e vengono iniettati in ogni prompt finale.
B1 = "BLOCK 1: Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject): Italian transmasculine Valeria Cross. Body: feminine, Cup D, 180cm, 85kg. Face: Male, 60yo, Beard: silver. Glasses: thin octagonal Vogue Havana dark."
B3 = "BLOCK 3 (Technique): 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Shallow depth of field, natural bokeh. Hair: Silver, short Italian style, volume."
B4 = "BLOCK 4 (Output): Watermark: 'feat. Valeria Cross 👠' (bottom center/left, opacity 90%). RENDERING: Subsurface Scattering, Global Illumination, Fresnel."
NEG = "NEGATIVE PROMPTS: female face, smooth skin, distortion, long hair, body hair, flat chest, 1:1 format."

# --- STATO ---
user_engine = {} # Salva il tool scelto (ChatGPT, Gemini, ecc.)

# --- MENU MOTORI (Aggiornato v4.50) ---
def get_engine_kb():
    markup = InlineKeyboardMarkup()
    # Suddivisione in righe per una migliore leggibilità su mobile
    markup.row(InlineKeyboardButton("🤖 CHATGPT", callback_data="eng_ChatGPT"), 
               InlineKeyboardButton("✨ GEMINI", callback_data="eng_Gemini"))
    markup.row(InlineKeyboardButton("🦁 GROK", callback_data="eng_Grok"),
               InlineKeyboardButton("🧠 QWEN", callback_data="eng_Qwen"))
    markup.row(InlineKeyboardButton("♾️ META", callback_data="eng_Meta"))
    return markup

@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    cid = m.chat.id
    text = (f"<b>📂 ARCHITECT v{VERSION}</b>\n"
            f"Configurazione attuale: <b>{user_engine.get(cid, 'Nessuna')}</b>\n\n"
            "Per quale modello dobbiamo costruire il prompt tecnico?")
    bot.send_message(cid, text, reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_"))
def set_engine(c):
    cid = c.message.chat.id
    user_engine[cid] = c.data.split("_")[1]
    bot.edit_message_text(
        f"✅ Target impostato su: <b>{user_engine[cid]}</b>\nOra invia l'idea della scena.",
        cid, c.message.message_id
    )

# --- MOTORE TECNICO (Logica A+B=C) ---
def get_technical_prompt(user_input, engine):
    """Converte l'input in prompt tecnico puro tramite Gemini 2.0 Flash."""
    try:
        # Prompt di sistema per forzare l'output tecnico
        prompt_istruzione = (
            f"Role: Expert Image Prompt Architect for {engine}. "
            "Task: Convert the user idea into technical descriptors. "
            "Constraints: NO prose, NO full sentences, ONLY keywords about materials, lighting, "
            "textures, and camera angles. Focus on hyper-realism. "
            f"User input: {user_input}"
        )
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt_istruzione]
        )
        
        # Sanificazione HTML per evitare che simboli come < o > rompano il bot
        return html.escape(response.text.strip())
    except Exception as e:
        print(f"ERRORE API GEMINI: {e}")
        # In caso di errore, restituiamo l'input originale pulito per non bloccare il bot
        return html.escape(user_input)

# --- GESTORE MESSAGGI (Resiliente) ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'), content_types=['text'])
def build_prompt(m):
    cid = m.chat.id
    
    # Controllo se l'utente ha scelto un motore
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Per favore, seleziona prima un modello con /motore")
        return

    # Feedback visivo di lavorazione
    wait = bot.send_message(cid, f"⚙️ <b>Architect sta elaborando per {user_engine[cid]}...</b>")
    
    # Generazione della parte variabile (C)
    scene_technical = get_technical_prompt(m.text, user_engine[cid])
    
    # Assemblaggio finale con tag <code> per il copia-incolla rapido
    # NOTA: Usiamo html.escape anche sugli altri blocchi per sicurezza assoluta
    final_output = (
        f"<code>{html.escape(B1)}\n\n"
        f"{html.escape(B2)}\n\n"
        f"{html.escape(B3)}\n\n"
        f"SCENE ({user_engine[cid]}): {scene_technical}\n\n"
        f"{html.escape(B4)}\n\n"
        f"{html.escape(NEG)}</code>"
    )
    
    bot.delete_message(cid, wait.message_id)
    bot.reply_to(m, f"✅ <b>Prompt Tecnico Pronto:</b>\n\n{final_output}")

# --- PROTEZIONE CONTRO INPUT NON TESTUALI ---
@bot.message_handler(content_types=['photo', 'sticker', 'video', 'document'])
def handle_docs(m):
    bot.reply_to(m, "⚠️ <b>Architect v4.50</b> accetta solo descrizioni testuali. Le immagini non sono supportate.")

# --- SERVER FLASK (Keep-alive) ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "ARCHITECT_V4.50_ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    # Avvio server in thread separato
    threading.Thread(target=run_flask, daemon=True).start()
    # Avvio Polling infinito
    bot.infinity_polling()

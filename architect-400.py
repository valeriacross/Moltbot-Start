import os, telebot, html, threading, flask, json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai

# --- CONFIGURAZIONE ---
VERSION = "4.0 (Architect - Pure Technical)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BLOCCHI VALERIA CROSS (MANDATORI) ---
B1 = "BLOCK 1: Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject): Italian transmasculine Valeria Cross. Body: feminine, Cup D, 180cm, 85kg. Face: Male, 60yo, Beard: silver. Glasses: thin octagonal Vogue Havana dark."
B3 = "BLOCK 3 (Technique): 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Shallow depth of field, natural bokeh. Hair: Silver, short Italian style, volume."
B4 = "BLOCK 4 (Output): Watermark: 'feat. Valeria Cross 👠' (bottom center/left, opacity 90%). RENDERING: Subsurface Scattering, Global Illumination, Fresnel."
NEG = "NEGATIVE PROMPTS: female face, smooth skin, distortion, long hair, body hair, flat chest, 1:1 format."

# --- STATO ---
user_engine = {} # Salva il motore scelto (Vogue, Closet, Midjourney, ecc.)

# --- MENU MOTORI ---
def get_engine_kb():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("👠 VOGUE", callback_data="eng_Vogue"), 
               InlineKeyboardButton("👗 CLOSET", callback_data="eng_Closet"))
    markup.row(InlineKeyboardButton("🌌 MIDJOURNEY", callback_data="eng_Midjourney"),
               InlineKeyboardButton("🤖 GEMINI", callback_data="eng_Gemini"))
    return markup

@bot.message_handler(commands=['start', 'reset', 'motore'])
def start(m):
    cid = m.chat.id
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION}</b>\nPer quale motore dobbiamo costruire il prompt?", reply_markup=get_engine_kb())

@bot.callback_query_handler(func=lambda c: c.data.startswith("eng_"))
def set_engine(c):
    cid = c.message.chat.id
    user_engine[cid] = c.data.split("_")[1]
    bot.edit_message_text(f"✅ Motore impostato su: <b>{user_engine[cid]}</b>\nOra invia la tua idea (A+B=C).", cid, c.message.message_id)

# --- MOTORE TECNICO (A+B=C) ---
def get_technical_prompt(user_input, engine):
    """Converte l'input in prompt tecnico puro senza testi narrativi."""
    try:
        prompt_istruzione = (
            f"Convert this idea into a technical, keyword-rich scene description for {engine}. "
            "NO STORYTELLING. NO PROSE. NO 'Once upon a time'. "
            "ONLY MATERIALS, LIGHTING, AND COMPOSITION. "
            f"User input: {user_input}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt_istruzione]
        )
        return response.text.strip()
    except:
        return user_input

@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def build_prompt(m):
    cid = m.chat.id
    if cid not in user_engine:
        bot.reply_to(m, "⚠️ Scegli prima il motore con /motore")
        return

    wait = bot.send_message(cid, f"⚙️ <b>Architect sta lavorando per {user_engine[cid]}...</b>")
    
    # TRADUZIONE PURA A+B=C
    scene_technical = get_technical_prompt(m.text, user_engine[cid])
    
    # Costruzione finale pulita
    final_prompt = (
        f"<code>{B1}\n\n{B2}\n\n{B3}\n\n"
        f"SCENE ({user_engine[cid]}): {scene_technical}\n\n"
        f"{B4}\n\n{NEG}</code>"
    )
    
    bot.delete_message(cid, wait.message_id)
    bot.reply_to(m, f"✅ <b>Prompt Tecnico Pronto:</b>\n\n{final_prompt}")

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "ARCHITECT_V4_PURE_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()
    

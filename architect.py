import os, telebot, html, json, threading, flask
from telebot import types
from google import genai
from datetime import datetime
import pytz

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash" 

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- CLOSET VERSIONING LOG ---
VERSION = "2.8"
LAST_UPDATE = "2026-02-20"

# --- BLOCCHI RIGIDI (DNA VALERIA CROSS) ---
B1 = "BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body completely hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark."
B3 = "BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
B4 = "BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, opacity 90%)."
NEG = "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders. [Body] body/chest/leg hair (peli NO!)."

user_session = {} 

def get_engine_keyboard(show_fine=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    if show_fine: markup.row("🏁 FINE / NUOVA IDEA")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_session[m.chat.id] = {'engine': None, 'last_idea': None}
    bot.send_message(m.chat.id, f"<b>🏛️ Architect v{VERSION}</b>\nScegli il motore target:", reply_markup=get_engine_keyboard())

@bot.message_handler(func=lambda m: m.text == "🏁 FINE / NUOVA IDEA")
def reset_session(m):
    user_session[m.chat.id] = {'engine': None, 'last_idea': None}
    bot.send_message(m.chat.id, "✅ Inserisci una nuova idea:", reply_markup=get_engine_keyboard())

@bot.message_handler(func=lambda m: m.text in ["Gemini 🍌", "Grok 𝕏", "ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮"])
def handle_engine(m):
    engine_clean = m.text.split()[0]
    cid = m.chat.id
    if cid not in user_session: user_session[cid] = {'engine': None, 'last_idea': None}
    user_session[cid]['engine'] = engine_clean
    if user_session[cid]['last_idea']: generate_prompt(m, cid)
    else: bot.send_message(cid, f"🎯 Target: <b>{engine_clean}</b>\nInviami l'idea:")

@bot.message_handler(func=lambda m: True)
def process_text(m):
    cid = m.chat.id
    if cid not in user_session or user_session[cid]['engine'] is None:
        bot.send_message(cid, "⚠️ Scegli un motore:", reply_markup=get_engine_keyboard())
        return
    user_session[cid]['last_idea'] = m.text
    generate_prompt(m, cid)

def generate_prompt(m, cid):
    engine = user_session[cid]['engine']
    idea = user_session[cid]['last_idea']
    wait = bot.send_message(cid, f"🏗️ <b>Generazione per {engine}...</b>")
    
    tz = pytz.timezone('Europe/Lisbon')
    now = datetime.now(tz).strftime("%H:%M:%S")

    # Istruzione: Espandi SOLO la scena. Ignora identità.
    instructions = (
        f"Expand the following idea into a detailed, cinematic scene description in English. "
        f"Focus only on lighting, environment, and clothes. Do not describe the person's face. "
        f"Target Engine: {engine}.\n\nIdea: {idea}"
    )

    try:
        response = client.models.generate_content(model=MODEL_ID, contents=[instructions])
        scene = response.text.strip()
        
        # Assemblaggio (Scene-First per motori tecnici)
        if engine in ["Grok", "Qwen"]:
            final_prompt = f"SCENE: {scene}\n\n{B1}\n\n{B2}\n\n{B3}\n\n{B4}\n\n{NEG}"
        else:
            final_prompt = f"{B1}\n\n{B2}\n\n{B3}\n\nSCENE: {scene}\n\n{B4}\n\n{NEG}"
        
        header = f"📂 <b>CLOSET LOG</b>\nv: <code>{VERSION}</code> | e: <code>{engine}</code> | t: <code>{now}</code>\n--------------------------"
        bot.delete_message(cid, wait.message_id)
        bot.send_message(cid, f"{header}\n\n<code>{html.escape(final_prompt)}</code>", reply_markup=get_engine_keyboard(show_fine=True))
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

# Server per Koyeb
app = flask.Flask(__name__)
@app.route('/')
def h(): return "OK"
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling()
    

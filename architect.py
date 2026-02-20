import os, telebot, html, json, threading, flask
from telebot import types
from google import genai

# --- CONFIG ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash" 

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- MASTER PROMPT (I 4 BLOCCHI RIGIDI) ---
MASTER_DIRECTIVES = """
BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity.
BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body completely hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark.
BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh.
BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: "feat. Valeria Cross 👠" (elegant cursive, champagne, bottom center/left, opacity 90%). 
NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders. [Body] body/chest/leg hair (peli NO!).
"""

user_state = {} 

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_state[m.chat.id] = None
    bot.send_message(m.chat.id, 
        "<b>🏛️ Moltbot Architect v1.2</b>\nScegli il motore di destinazione:", 
        reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text in ["Gemini 🍌", "Grok 𝕏", "ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮"])
def set_engine(m):
    engine_clean = m.text.split()[0]
    user_state[m.chat.id] = engine_clean
    bot.send_message(m.chat.id, f"🎯 Target: <b>{engine_clean}</b>\nInviami l'idea per lo scatto.")

@bot.message_handler(func=lambda m: True)
def process_optimization(m):
    if m.chat.id not in user_state or user_state[m.chat.id] is None:
        bot.send_message(m.chat.id, "⚠️ Scegli un motore:", reply_markup=get_main_keyboard())
        return

    engine = user_state[m.chat.id]
    wait = bot.reply_to(m, f"🏗️ <b>Architetto al lavoro per {engine}...</b>")

    prompt_logic = (
        f"Professional Prompt Engineer. Expand user idea into a detailed image prompt in English. "
        f"STRICTLY include: {MASTER_DIRECTIVES}. "
        f"ADAPT FOR {engine}: "
        f"- Gemini: Artistic/editorial style. "
        f"- Grok: Raw realism and high contrast. "
        f"Output ONLY the optimized prompt text."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[f"{prompt_logic}\n\nUSER INPUT: {m.text}"]
        )
        final_msg = f"✨ <b>Prompt per {engine}</b>\n\n<code>{html.escape(response.text)}</code>"
        bot.delete_message(m.chat.id, wait.message_id)
        bot.send_message(m.chat.id, final_msg)
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Errore: {str(e)}")

# --- SERVER FLASK PER KOYEB (IL FIX) ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Architect Online"

if __name__ == "__main__":
    # Avvia Flask in un thread separato
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    # Avvia il bot
    bot.infinity_polling()
    

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

# Memoria della sessione: {chat_id: {'engine': str, 'last_idea': str}}
user_session = {} 

def get_engine_keyboard(show_fine=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    if show_fine:
        markup.row("🏁 FINE / NUOVA IDEA")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_session[m.chat.id] = {'engine': None, 'last_idea': None}
    bot.send_message(m.chat.id, 
        "<b>🏛️ Moltbot Architect v2.0</b>\n"
        "Configurato per ottimizzazione multi-motore.\n\n"
        "<b>Scegli il motore di partenza:</b>", 
        reply_markup=get_engine_keyboard())

@bot.message_handler(func=lambda m: m.text == "🏁 FINE / NUOVA IDEA")
def reset_session(m):
    user_session[m.chat.id] = {'engine': None, 'last_idea': None}
    bot.send_message(m.chat.id, "✅ Sessione chiusa. Scegli un motore per una nuova idea:", 
                     reply_markup=get_engine_keyboard())

@bot.message_handler(func=lambda m: m.text in ["Gemini 🍌", "Grok 𝕏", "ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮"])
def handle_engine_selection(m):
    engine_clean = m.text.split()[0]
    cid = m.chat.id
    
    # Se non c'è una sessione, creala
    if cid not in user_session:
        user_session[cid] = {'engine': None, 'last_idea': None}
    
    user_session[cid]['engine'] = engine_clean
    
    # Se abbiamo già un'idea in memoria, generiamo subito per il nuovo motore
    if user_session[cid]['last_idea']:
        generate_optimized_prompt(m, cid)
    else:
        bot.send_message(cid, f"🎯 Target: <b>{engine_clean}</b>\nScrivi la tua idea per lo scatto:")

@bot.message_handler(func=lambda m: True)
def process_text_input(m):
    cid = m.chat.id
    
    # Verifica che sia stato scelto un motore
    if cid not in user_session or user_session[cid]['engine'] is None:
        bot.send_message(cid, "⚠️ Scegli prima un motore:", reply_markup=get_engine_keyboard())
        return

    # Salva l'idea in memoria per poterla riutilizzare con altri motori
    user_session[cid]['last_idea'] = m.text
    generate_optimized_prompt(m, cid)

def generate_optimized_prompt(m, cid):
    engine = user_session[cid]['engine']
    idea = user_session[cid]['last_idea']
    
    wait = bot.send_message(cid, f"🏗️ <b>Generazione per {engine}...</b>")

    instructions = (
        f"You are a professional Prompt Engineer. Expand this idea into a verbose, detailed, "
        f"and didactic image prompt in English. Strictly include: {MASTER_DIRECTIVES}. "
        f"Specific tuning for {engine}: "
        f"- Gemini: Use artistic/editorial safe language. "
        f"- Grok: Use raw realism and extreme technical detail. "
        f"- ChatGPT/MetaAI/Qwen: Focus on technical weights and lighting tags. "
        f"Output ONLY the final optimized text."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[f"{instructions}\n\nUSER IDEA: {idea}"]
        )
        
        final_msg = (
            f"✨ <b>Prompt Ottimizzato per {engine}</b>\n\n"
            f"<code>{html.escape(response.text)}</code>\n\n"
            f"🔄 <b>Vuoi lo stesso prompt per un altro motore?</b>\n"
            f"Seleziona un tasto o premi Fine per cambiare idea."
        )
        
        bot.delete_message(cid, wait.message_id)
        bot.send_message(cid, final_msg, reply_markup=get_engine_keyboard(show_fine=True))
        
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

# --- SERVER FLASK PER KOYEB ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Architect Online"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    bot.infinity_polling()
    

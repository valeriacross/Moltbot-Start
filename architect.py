import os, telebot, html, json, threading, flask
from telebot import types
from google import genai

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash" # Modello di punta per velocità e intelligenza

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- MASTER PROMPT (I 4 BLOCCHI ORIGINALI) ---
# Questi dati sono il DNA di Valeria Cross e vengono iniettati come vincoli assoluti.
MASTER_DIRECTIVES = """
BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity.
BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body completely hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark.
BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh.
BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: "feat. Valeria Cross 👠" (elegant cursive, champagne, bottom center/left, opacity 90%). 
NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders. [Body] body/chest/leg hair (peli NO!).
"""

# Memoria della sessione utente
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
        "<b>🏛️ Moltbot Architect v2.1</b>\n"
        "Configurato per ottimizzazione narrativa multi-motore.\n\n"
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
    
    if cid not in user_session:
        user_session[cid] = {'engine': None, 'last_idea': None}
    
    user_session[cid]['engine'] = engine_clean
    
    if user_session[cid]['last_idea']:
        generate_optimized_prompt(m, cid)
    else:
        bot.send_message(cid, f"🎯 Target: <b>{engine_clean}</b>\nScrivi la tua idea per lo scatto:")

@bot.message_handler(func=lambda m: True)
def process_text_input(m):
    cid = m.chat.id
    if cid not in user_session or user_session[cid]['engine'] is None:
        bot.send_message(cid, "⚠️ Scegli prima un motore:", reply_markup=get_engine_keyboard())
        return
    
    user_session[cid]['last_idea'] = m.text
    generate_optimized_prompt(m, cid)

def generate_optimized_prompt(m, cid):
    engine = user_session[cid]['engine']
    idea = user_session[cid]['last_idea']
    
    wait = bot.send_message(cid, f"🏗️ <b>Generazione per {engine}...</b>")

    # ISTRUZIONI DI SISTEMA (Il Prompt del Prompt)
    instructions = (
        f"You are the world's leading Prompt Engineer for Vogue photography. "
        f"Your task is to take a simple 'USER IDEA' and expand it into a massive, multi-paragraph, "
        f"professional image prompt in English for the avatar 'Valeria Cross'.\n\n"
        f"CRITICAL RULES:\n"
        f"1. NARRATIVE INTEGRATION: Do NOT list the blocks. Weave the USER IDEA into a sophisticated scene. "
        f"Describe the clothing (elegant, form-fitting to show hourglass shape), the lighting, and the mood.\n"
        f"2. SUBJECT (VALERIA CROSS): You MUST integrate these exact details naturally: "
        f"60yo Italian male face, silver 6cm beard, Havana octagonal Vogue glasses. "
        f"Body: feminine hourglass, Cup D breasts, 180cm, 85kg, hairless.\n"
        f"3. TECHNICALS: Include 85mm lens, f/2.8, ISO 200, SSS rendering, and the champagne cursive watermark.\n"
        f"4. CLEANLINESS: Never write 'BLOCK 1', 'BLOCK 2', etc. No headers. No intro/outro text.\n"
        f"5. ENGINE STYLE ({engine}):\n"
        f"   - If Grok: Use raw, visceral, hyper-realistic, and gritty language. Focus on skin pores and fabric micro-details.\n"
        f"   - If Gemini: Use poetic, sophisticated, and high-fashion artistic language.\n\n"
        f"USER IDEA TO EXPAND: {idea}"
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[instructions]
        )
        
        # Pulizia automatica di eventuali intestazioni residue
        text = response.text
        for i in range(1, 5):
            text = text.replace(f"BLOCK {i}:", "").replace(f"BLOCK {i}", "").replace(f"Block {i}:", "")
        
        final_msg = (
            f"✨ <b>Prompt Ottimizzato per {engine}</b>\n\n"
            f"<code>{html.escape(text.strip())}</code>\n\n"
            f"🔄 <b>Vuoi lo stesso prompt per un altro motore?</b>\n"
            f"Seleziona un tasto o premi Fine per cambiare idea."
        )
        
        bot.delete_message(cid, wait.message_id)
        bot.send_message(cid, final_msg, reply_markup=get_engine_keyboard(show_fine=True))
        
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

# --- SERVER FLASK PER KOYEB HEALTH CHECK ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "Architect Online"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    bot.infinity_polling()
    

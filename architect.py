import os, telebot, html, json, threading, flask
from telebot import types
from google import genai

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.0-flash" 

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Dati di base di Valeria (non più chiamati 'BLOCKS' per non confondere l'AI)
VALERIA_DNA = """
SUBJECT: Valeria Cross, Italian transmasculine avatar. 
APPEARANCE: 60yo male face, ultra-detailed skin (pores, wrinkles), light grey/silver 6cm groomed beard, thin octagonal Vogue Havana dark glasses.
BODY: Soft feminine hourglass, prosperous Cup D breasts, 180cm, 85kg, hairless skin.
HAIR: Short silver elegant Italian style, volume, nape exposed.
TECHNICAL: 85mm lens, f/2.8, ISO 200, 1/160s, shallow depth of field, 8K resolution, SSS rendering.
WATERMARK: 'feat. Valeria Cross 👠' cursive champagne bottom center/left.
"""

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
    bot.send_message(m.chat.id, "<b>🏛️ Moltbot Architect v2.2</b>\nScegli il motore:", reply_markup=get_engine_keyboard())

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
    if user_session[cid]['last_idea']: generate_optimized_prompt(m, cid)
    else: bot.send_message(cid, f"🎯 Target: <b>{engine_clean}</b>\nScrivi la tua idea:")

@bot.message_handler(func=lambda m: True)
def process_text(m):
    cid = m.chat.id
    if cid not in user_session or user_session[cid]['engine'] is None:
        bot.send_message(cid, "⚠️ Scegli un motore:", reply_markup=get_engine_keyboard())
        return
    user_session[cid]['last_idea'] = m.text
    generate_optimized_prompt(m, cid)

def generate_optimized_prompt(m, cid):
    engine = user_session[cid]['engine']
    idea = user_session[cid]['last_idea']
    wait = bot.send_message(cid, f"🏗️ <b>Architetto al lavoro per {engine}...</b>")

    # ESEMPIO DI COSA VOGLIAMO (Few-Shot)
    example = (
        "EXAMPLE OF OUTPUT:\n"
        "Idea: 'Valeria in a cafe'\n"
        "Output: 'A cinematic high-fashion Vogue cover shot of Valeria Cross sitting at a marble cafe table in Lisbon. "
        "The soft morning light hits her 60-year-old Italian male face, highlighting the deep textures of her silver 6cm beard "
        "and her octagonal Havana Vogue glasses. She wears a form-fitting black silk blouse that accentuates her feminine "
        "hourglass figure and prominent Cup D breasts. 85mm lens, f/2.8, shallow bokeh, SSS rendering, 8K. "
        "Watermark: feat. Valeria Cross 👠 bottom left.'\n\n"
    )

    instructions = (
        f"You are a professional Prompt Engineer. Task: Expand the 'USER IDEA' into a long, detailed, narrative prompt in English.\n"
        f"MANDATORY SUBJECT DETAILS: {VALERIA_DNA}\n"
        f"{example}"
        f"RULES:\n"
        f"1. Never mention 'BLOCK' or 'DNA'.\n"
        f"2. Integrate the idea into a rich scene with lighting and clothes.\n"
        f"3. Engine Style ({engine}): Grok=Raw/Gritty, Gemini=Elegant/Artistic.\n"
        f"4. Be very prolix and descriptive.\n\n"
        f"USER IDEA: {idea}"
    )

    try:
        response = client.models.generate_content(model=MODEL_ID, contents=[instructions])
        # Rimuove eventuali scorie di testo
        text = response.text.replace("Output:", "").replace("Prompt:", "").strip()
        
        final_msg = (
            f"✨ <b>Prompt Ottimizzato per {engine}</b>\n\n"
            f"<code>{html.escape(text)}</code>\n\n"
            f"🔄 <b>Vuoi lo stesso per un altro motore?</b>"
        )
        bot.delete_message(cid, wait.message_id)
        bot.send_message(cid, final_msg, reply_markup=get_engine_keyboard(show_fine=True))
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

app = flask.Flask(__name__)
@app.route('/')
def h(): return "Architect Online"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    bot.infinity_polling()
    

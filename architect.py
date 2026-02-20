import os, telebot, html, threading, flask
from telebot import types
from google import genai
from datetime import datetime
import pytz

# --- CONFIG ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- I 4 BLOCCHI (TESTO FISSO, L'AI NON LI VEDE MAI) ---
B1 = "BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark."
B3 = "BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
B4 = "BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, opacity 90%)."
NEG = "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid. [Body] body/chest/leg hair (peli NO!)."

user_session = {}

def get_kb(show_fine=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏", "Qwen 🏮")
    if show_fine: markup.row("🏁 NUOVA IDEA")
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    user_session[m.chat.id] = {'e': None, 'i': None}
    bot.send_message(m.chat.id, "<b>🏛️ Architect v3.0</b>\nScegli il motore:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: m.text == "🏁 NUOVA IDEA")
def reset(m):
    user_session[m.chat.id] = {'e': None, 'i': None}
    bot.send_message(m.chat.id, "✅ Inserisci una nuova idea:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: m.text in ["Gemini 🍌", "Grok 𝕏", "Qwen 🏮"])
def set_e(m):
    user_session[m.chat.id]['e'] = m.text.split()[0]
    if user_session[m.chat.id]['i']: generate(m)
    else: bot.send_message(m.chat.id, f"🎯 Target: {m.text}\nScrivi l'idea:")

@bot.message_handler(func=lambda m: True)
def handle_msg(m):
    cid = m.chat.id
    if cid not in user_session or not user_session[cid]['e']:
        bot.send_message(cid, "⚠️ Scegli un motore:", reply_markup=get_kb())
        return
    user_session[cid]['i'] = m.text
    generate(m)

def generate(m):
    cid = m.chat.id
    engine = user_session[cid]['e']
    idea = user_session[cid]['i']
    wait = bot.send_message(cid, "🏗️ <b>Espansione scena in corso...</b>")
    
    # L'AI riceve SOLO l'idea. Non sa nulla di blocchi o Valeria.
    prompt_ai = (
        f"Act as a fashion copywriter. Describe this scene in English for a photo shoot: '{idea}'. "
        f"Focus on environment, luxury details, and clothing. Be extremely descriptive and poetic. "
        f"Output ONLY the description. No intro, no names."
    )

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt_ai])
        scena_espansa = response.text.strip()
        
        # Assemblaggio meccanico finale
        final = f"{B1}\n\n{B2}\n\n{B3}\n\nSCENE: {scena_espansa}\n\n{B4}\n\n{NEG}"
        
        now = datetime.now(pytz.timezone('Europe/Lisbon')).strftime("%H:%M")
        header = f"📂 <b>CLOSET v3.0</b> | {engine} | {now}\n--------------------------"
        
        bot.delete_message(cid, wait.message_id)
        bot.send_message(cid, f"{header}\n\n<code>{html.escape(final)}</code>", reply_markup=get_kb(True))
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

app = flask.Flask(__name__)
@app.route('/')
def h(): return "OK"
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling()
    

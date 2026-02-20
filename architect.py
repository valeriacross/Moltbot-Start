import os, telebot, html, threading, flask
from telebot import types
from google import genai
from datetime import datetime
import pytz

# --- CONFIG ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- I 4 BLOCCHI FISSI (DNA VALERIA CROSS) ---
B1 = "BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark."
B3 = "BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
B4 = "BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, opacity 90%)."
NEG = "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid. [Body] body/chest/leg hair (peli NO!)."

user_session = {} 

def get_kb(show_fine=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    if show_fine: markup.row("🏁 NUOVA IDEA")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_session[m.chat.id] = {'e': None, 'i': None}
    bot.send_message(m.chat.id, "<b>🏛️ Architect v3.2 + Ping</b>\nScegli il motore:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: m.text == "🏁 NUOVA IDEA")
def reset_idea(m):
    if m.chat.id in user_session: user_session[m.chat.id]['i'] = None
    bot.send_message(m.chat.id, "✅ Inserisci una nuova idea:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: any(x in m.text for x in ["Gemini", "Grok", "ChatGPT", "MetaAI", "Qwen"]))
def set_engine(m):
    cid = m.chat.id
    if cid not in user_session: user_session[cid] = {'e': None, 'i': None}
    user_session[cid]['e'] = m.text.split()[0]
    if user_session[cid]['i']: generate_final_prompt(m)
    else: bot.send_message(cid, f"🎯 Target: <b>{user_session[cid]['e']}</b>\nScrivi la tua idea:")

@bot.message_handler(func=lambda m: True)
def collect_idea(m):
    cid = m.chat.id
    if cid not in user_session or not user_session[cid]['e']:
        user_session[cid] = {'e': None, 'i': None}
        bot.send_message(cid, "⚠️ Scegli prima un motore:", reply_markup=get_kb())
        return
    user_session[cid]['i'] = m.text
    generate_final_prompt(m)

def generate_final_prompt(m):
    cid = m.chat.id
    engine = user_session[cid]['e']
    idea = user_session[cid]['i']
    wait = bot.send_message(cid, f"🏗️ <b>Espansione scena ({engine})...</b>")
    
    instruction = (
        f"You are a professional Vogue copywriter. Expand this idea into a detailed SCENE: '{idea}'. "
        f"Focus only on setting, lighting, and clothes. Do not describe the person's face. English only."
    )

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[instruction])
        scena = response.text.strip()
        final = f"{B1}\n\n{B2}\n\n{B3}\n\nSCENE: {scena}\n\n{B4}\n\n{NEG}"
        
        now = datetime.now(pytz.timezone('Europe/Lisbon')).strftime("%H:%M")
        header = f"📂 <b>CLOSET v3.2</b> | {engine} | {now}\n--------------------------\n\n"
        full_msg = header + final
        
        bot.delete_message(cid, wait.message_id)

        if len(full_msg) > 4090:
            for x in range(0, len(full_msg), 4090):
                bot.send_message(cid, f"<code>{html.escape(full_msg[x:x+4090])}</code>")
        else:
            bot.send_message(cid, f"<code>{html.escape(full_msg)}</code>", reply_markup=get_kb(True))
            
    except Exception as e:
        bot.send_message(cid, f"❌ Errore: {str(e)}")

# --- FLASK PING PER KOYEB ---
app = flask.Flask(__name__)
@app.route('/')
def health(): return "OK"

if __name__ == "__main__":
    # Avvio Flask su porta 10000
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()
    

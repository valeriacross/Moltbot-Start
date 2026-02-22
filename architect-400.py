import os, telebot, html, threading, flask, json, io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google import genai
from google.genai import types as genai_types
from io import BytesIO
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURAZIONE ---
VERSION = "4.0 (Architect - No Novels)"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
executor = ThreadPoolExecutor(max_workers=2)

# --- BLOCCHI VALERIA CROSS (MANDATORI) ---
B1 = "BLOCK 1: Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject): Italian transmasculine Valeria Cross. Body: feminine, Cup D, 180cm, 85kg. Face: Male, 60yo, Beard: silver. Glasses: thin octagonal Vogue Havana dark."
B3 = "BLOCK 3 (Technique): 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Shallow depth of field, natural bokeh. Hair: Silver, short Italian style, volume."
B4 = "BLOCK 4 (Output): Watermark: 'feat. Valeria Cross 👠' (bottom center/left, opacity 90%). RENDERING: Subsurface Scattering, Global Illumination, Fresnel."
NEG = "NEGATIVE PROMPTS: female face, smooth skin, distortion, long hair, body hair, flat chest, 1:1 format."

# --- LOGICA A+B=C (IL TRADUTTORE) ---
def get_architect_scene(user_input):
    """Converte l'input in un prompt tecnico puro senza testi narrativi."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"Convert this idea into a technical, keyword-rich scene description for high-end AI image generation. NO STORYTELLING. NO PROSE. NO ADJECTIVES LIKE 'BEAUTIFUL' OR 'STARK'. ONLY MATERIALS, LIGHTING, AND COMPOSITION. User input: {user_input}"]
        )
        return response.text.strip()
    except:
        return user_input # Fallback se Gemini fallisce

# --- STATO UTENTE ---
user_settings = defaultdict(lambda: {'ratio': '2:3', 'count': 1})
pending_prompts = {}

# --- COMANDI ---
@bot.message_handler(commands=['start', 'reset'])
def start(m):
    cid = m.chat.id
    user_settings[cid] = {'ratio': '2:3', 'count': 1}
    bot.send_message(cid, f"<b>📂 ARCHITECT v{VERSION} Online</b>\nInvia la tua idea. Genererò solo il prompt tecnico (A+B=C).")

@bot.message_handler(commands=['formato'])
def menu_ar(m):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("2:3", callback_data="ar_2:3"), InlineKeyboardButton("16:9", callback_data="ar_16:9"))
    bot.send_message(m.chat.id, "📐 Scegli Formato:", reply_markup=markup)

# --- HANDLER INPUT ---
@bot.message_handler(func=lambda m: not m.text.startswith('/'))
def handle_architect(m):
    cid, uid = m.chat.id, m.from_user.id
    wait = bot.send_message(cid, "⚙️ <b>Compressione tecnica in corso...</b>")
    
    # TRADUZIONE PURA A+B=C
    scene_technical = get_architect_scene(m.text)
    settings = user_settings[cid]
    
    final_p = f"{B1}\n\n{B2}\n\n{B3}\n\nSCENE: {scene_technical}\nFORMAT: {settings['ratio']}\n\n{B4}\n\n{NEG}"
    pending_prompts[uid] = {'full_p': final_p, 'count': settings['count']}
    
    bot.delete_message(cid, wait.message_id)
    
    # JSON PERSISTENTE COME RICHIESTO
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🚀 GENERA", callback_data="confirm_gen"), InlineKeyboardButton("❌ ANNULLA", callback_data="cancel_gen"))
    bot.reply_to(m, f"📝 <b>Prompt Tecnico:</b>\n<code>{html.escape(json.dumps({'SCENE': scene_technical}, indent=2))}</code>", reply_markup=markup)

# --- CALLBACK GENERAZIONE ---
@bot.callback_query_handler(func=lambda c: True)
def handle_query(c):
    cid, uid = c.message.chat.id, c.from_user.id
    if c.data.startswith("ar_"):
        user_settings[cid]['ratio'] = c.data.split("_")[1]
        bot.answer_callback_query(c.id, f"Formato impostato: {user_settings[cid]['ratio']}")
    elif c.data == "confirm_gen":
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=None)
        p = pending_prompts.get(uid)
        if not p: return
        bot.send_message(cid, "📸 <b>Rendering in corso...</b>")
        def run_task():
            res, err = execute_gen(p['full_p'])
            if res: bot.send_document(cid, io.BytesIO(res), visible_file_name="architect_scatto.jpg")
            else: bot.send_message(cid, f"❌ Errore: {err}")
        executor.submit(run_task)
    elif c.data == "cancel_gen":
        bot.edit_message_reply_markup(cid, c.message.message_id, reply_markup=None)
        bot.send_message(cid, "❌ Annullato.")

def execute_gen(prompt):
    try:
        # Carica master_face se esiste
        contents = [prompt]
        if os.path.exists("master_face.png"):
            with open("master_face.png", "rb") as f:
                contents.append(genai_types.Part.from_bytes(data=f.read(), mime_type="image/png"))
        
        response = client.models.generate_content(
            model="nano-banana-pro-preview",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            )
        )
        return response.candidates[0].content.parts[0].inline_data.data, None
    except Exception as e: return None, str(e)

# --- SERVER ---
app = flask.Flask(__name__)
@app.route('/')
def h(): return "ARCHITECT_V4_ONLINE"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

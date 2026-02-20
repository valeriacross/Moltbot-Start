import os, telebot, html, json
from telebot import types
from google import genai

# --- CONFIG ---
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Gemini 2.0 Flash risolve l'errore 404 riscontrato nei log
MODEL_ID = "gemini-2.0-flash" 

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- I 4 BLOCCHI ORIGINALI (IL MASTER PROMPT) ---
MASTER_DIRECTIVES = """
BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity.
BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body completely hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark.
BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: High-fashion Vogue cover, 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh.
BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: "feat. Valeria Cross 👠" (elegant cursive, champagne, bottom center/left, opacity 90%). 
NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid, touching neck/shoulders. [Body] body/chest/leg hair (peli NO!).
"""

# Dizionario per gestire lo stato dell'utente
user_state = {} 

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    user_state[m.chat.id] = None # Reset stato
    bot.send_message(m.chat.id, 
        "<b>🏛️ Moltbot Architect v1.2</b>\n"
        "Benvenuto nel centro di comando creativo di Valeria Cross.\n\n"
        "<b>Per favore, scegli il motore di generazione:</b>", 
        reply_markup=get_main_keyboard())

# Gestione della selezione del motore
@bot.message_handler(func=lambda m: m.text in ["Gemini 🍌", "Grok 𝕏", "ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮"])
def set_engine(m):
    engine_clean = m.text.split()[0] # Toglie l'emoji
    user_state[m.chat.id] = engine_clean
    bot.send_message(m.chat.id, 
        f"🎯 Motore impostato su: <b>{engine_clean}</b>\n\n"
        "Ora inviami la tua idea per lo scatto. Può essere una descrizione in italiano, "
        "una lista di parole o delle emoji. Io penserò a tutto il resto.")

@bot.message_handler(func=lambda m: True)
def process_optimization(m):
    # Se l'utente non ha scelto un motore, lo obblighiamo a farlo
    if m.chat.id not in user_state or user_state[m.chat.id] is None:
        bot.send_message(m.chat.id, "⚠️ <b>Attenzione!</b>\nDevi prima scegliere un motore usando i pulsanti qui sotto.", 
                         reply_markup=get_main_keyboard())
        return

    engine = user_state[m.chat.id]
    wait = bot.reply_to(m, f"🏗️ <b>Architetto al lavoro per {engine}...</b>")

    # Istruzioni di sistema specifiche per l'ottimizzazione
    prompt_logic = (
        f"You are a professional Prompt Engineer for high-end fashion photography. "
        f"Task: Expand the user's idea into a prolix, detailed, and didactic image prompt in English. "
        f"You MUST strictly include all 4 MASTER BLOCKS: {MASTER_DIRECTIVES}. "
        f"ADAPTATION FOR {engine}: "
        f"- Gemini: Use sophisticated artistic/editorial language to ensure safety compliance. "
        f"- Grok: Use raw, hyper-realistic, and high-contrast technical terms. "
        f"- Others: Use a balanced mix of technical tags and descriptive prose. "
        f"The output must contain ONLY the final optimized prompt text."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[f"{prompt_logic}\n\nUSER INPUT: {m.text}"]
        )
        
        optimized_text = response.text
        
        final_msg = (
            f"✨ <b>Prompt Ottimizzato per {engine}</b>\n\n"
            f"<code>{html.escape(optimized_text)}</code>\n\n"
            f"📸 <i>Copia il testo e incollalo nel bot Vogue allegando la Master Face.</i>"
        )
        bot.delete_message(m.chat.id, wait.message_id)
        bot.send_message(m.chat.id, final_msg)
        
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ <b>Errore Tecnico:</b>\n<code>{str(e)}</code>")

if __name__ == "__main__":
    bot.infinity_polling()
    

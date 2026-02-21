import os, telebot, html, threading, flask
from telebot import types
from google import genai
from datetime import datetime
import pytz

# --- CONFIGURAZIONE E VERSIONAMENTO ---
# La v3.5 introduce il Reset Totale della sessione per evitare loop di generazione
VERSION = "3.5"
TOKEN = os.environ.get("TELEGRAM_TOKEN_ARCHITECT")
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- I 4 BLOCCHI MANDATORI (DNA VALERIA CROSS) ---
# Nota: Il Blocco 3 è stato depurato dai riferimenti a "Vogue" come richiesto.
B1 = "BLOCK 1 (Activation & Priority): Reference image has ABSOLUTE PRIORITY. ZERO face drift allowed. Male Italian face identity."
B2 = "BLOCK 2 (Subject & Face): Nameless Italian transmasculine avatar (Valeria Cross). Body: soft feminine, harmonious hourglass, prosperous full breasts (cup D), 180cm, 85kg. Body hairless. FACE: Male Italian face, ~60 years old, ultra-detailed skin (pores, wrinkles, bags). Expression: calm, half-smile, NO teeth. Beard: light grey/silver, groomed, 6–7 cm. Glasses MANDATORY: thin octagonal Vogue, Havana dark."
B3 = "BLOCK 3 (Hair & Technique): HAIR: Light grey/silver. Short elegant Italian style, volume. Nape exposed. Top <15 cm. IMAGE CONCEPT: 8K, cinematic realism. CAMERA: 85mm, f/2.8, ISO 200, 1/160s. Focus on face/torso. Shallow depth of field, natural bokeh."
B4 = "BLOCK 4 (Rendering & Output): RENDERING: Subsurface Scattering, Global Illumination, Fresnel, Frequency separation on skin. Watermark: 'feat. Valeria Cross 👠' (elegant cursive, champagne, bottom center/left, opacity 90%)."
NEG = "NEGATIVE PROMPTS: [Face] female/young face, smooth skin, distortion. [Hair] long/medium hair, ponytail, bun, braid. [Body] body/chest/leg hair (peli NO!)."

# Dizionario per gestire lo stato dell'utente (Motore, Idea, Post-Prod)
user_session = {} 

def get_kb(show_reset=False):
    """Genera la tastiera dinamica. Mostra 'NUOVA IDEA' solo se c'è un'operazione in corso."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Gemini 🍌", "Grok 𝕏")
    markup.row("ChatGPT 🤖", "MetaAI 🌀", "Qwen 🏮")
    if show_reset: markup.row("🏁 NUOVA IDEA")
    return markup

@bot.message_handler(commands=['start', 'reset'])
def start(m):
    """Inizializzazione pulita della sessione."""
    user_session[m.chat.id] = {'e': None, 'i': None, 'post_prod': None}
    bot.send_message(m.chat.id, f"<b>🏛️ Architect v{VERSION} Online</b>\nScegli un motore per iniziare:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: m.text == "🏁 NUOVA IDEA")
def reset_logic(m):
    """
    LOGICA DI RESET (CORRETTA): 
    Invece di pulire solo l'idea, azzera completamente la sessione.
    Questo impedisce al bot di riutilizzare il vecchio motore o la vecchia idea.
    """
    user_session[m.chat.id] = {'e': None, 'i': None, 'post_prod': None}
    bot.send_message(m.chat.id, "✅ Sessione azzerata. Seleziona un motore o invia un nuovo input:", reply_markup=get_kb())

@bot.message_handler(func=lambda m: any(x in m.text for x in ["Gemini", "Grok", "ChatGPT", "MetaAI", "Qwen"]))
def set_engine(m):
    """Imposta il motore di destinazione e verifica se c'è un'idea pendente."""
    cid = m.chat.id
    engine_name = m.text.split()[0]
    
    if cid not in user_session:
        user_session[cid] = {'e': engine_name, 'i': None, 'post_prod': None}
    else:
        user_session[cid]['e'] = engine_name
        
    # Se NON c'è un'idea salvata, il bot si ferma e chiede l'input.
    if not user_session[cid]['i']:
        bot.send_message(cid, f"🎯 Motore impostato: <b>{engine_name}</b>\nOra invia la tua idea o rispondi a un messaggio per la post-produzione.")
    else:
        # Se l'utente cambia motore avendo già un'idea, rigenera per il nuovo target.
        generate_final_prompt(m)

@bot.message_handler(func=lambda m: True)
def collect_input(m):
    """Riceve l'idea o rileva se si tratta di una risposta (Post-Produzione)."""
    cid = m.chat.id
    
    # Protezione: Se l'utente non ha scelto un motore, blocca l'esecuzione.
    if cid not in user_session or not user_session[cid]['e']:
        bot.send_message(cid, "⚠️ Per favore, seleziona prima un motore di destinazione:", reply_markup=get_kb())
        return

    # Gestione della Post-Produzione tramite Reply
    if m.reply_to_message:
        orig_text = m.reply_to_message.caption if m.reply_to_message.caption else m.reply_to_message.text
        user_session[cid]['post_prod'] = orig_text
    else:
        user_session[cid]['post_prod'] = None

    user_session[cid]['i'] = m.text
    generate_final_prompt(m)

def generate_final_prompt(m):
    """Innesca la generazione del prompt tramite Gemini 2.0 Flash."""
    cid = m.chat.id
    engine = user_session[cid]['e']
    idea = user_session[cid]['i']
    context = user_session[cid].get('post_prod')
    
    wait = bot.send_message(cid, f"🏗️ <b>Elaborazione {engine}...</b>")
    
    # Istruzioni differenziate tra Nuova Scena e Post-Produzione
    if context:
        prompt_instruction = (
            f"Context: '{context}'. Action: Apply these changes: '{idea}'. "
            f"Rewrite the SCENE description in English. Focus on visual details. No face/identity talk."
        )
    else:
        prompt_instruction = (
            f"Expand this idea into a high-fashion cinematic SCENE: '{idea}'. "
            f"Describe environment, clothing, and lighting. Do not describe the face. English only."
        )

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt_instruction])
        scena_espansa = response.text.strip()
        
        # Assemblaggio finale con i 4 Blocchi (B3 è senza Vogue)
        final_output = f"{B1}\n\n{B2}\n\n{B3}\n\nSCENE: {scena_espansa}\n\n{B4}\n\n{NEG}"
        
        now = datetime.now(pytz.timezone('Europe/Lisbon')).strftime("%H:%M")
        header = f"📂 <b>ARCHITECT v{VERSION}</b> | {engine} | {now}\n--------------------------\n\n"
        full_message = header + final_output
        
        bot.delete_message(cid, wait.message_id)
        
        # Split del messaggio se supera il limite di Telegram (4096 caratteri)
        if len(full_message) > 4090:
            for x in range(0, len(full_message), 4090):
                bot.send_message(cid, f"<code>{html.escape(full_message[x:x+4090])}</code>")
        else:
            bot.send_message(cid, f"<code>{html.escape(full_message)}</code>", reply_markup=get_kb(True))
            
    except Exception as e:
        bot.send_message(cid, f"❌ Errore critico: {str(e)}")

# --- SERVER FLASK PER MONITORAGGIO (PORTA 10000) ---
app = flask.Flask(__name__)
@app.route('/')
def health_check(): return "ARCHITECT_READY"

if __name__ == "__main__":
    # Avvio del thread per il ping di Flask per evitare lo stato 'Sleeping' su Koyeb
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()
    bot.infinity_polling()

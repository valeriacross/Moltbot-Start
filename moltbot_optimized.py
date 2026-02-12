import os
import io
import threading
import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import flask
import telebot
from telebot import types
from PIL import Image
from google import genai

# --- CONFIGURAZIONE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TOKEN or not API_KEY:
    logger.critical("❌ TOKEN o API_KEY mancanti nelle variabili d'ambiente!")
    raise ValueError("Configurazione incompleta")

client = genai.Client(api_key=API_KEY)
MODEL_ID = "imagen-4.0-ultra-generate-001"

# --- CONFIGURAZIONE RATE LIMITING ---
MAX_REQUESTS_PER_HOUR = 10
MAX_REQUESTS_PER_DAY = 50

# Dizionari per tracciare richieste per utente
user_requests_hourly = defaultdict(lambda: deque(maxlen=MAX_REQUESTS_PER_HOUR))
user_requests_daily = defaultdict(lambda: deque(maxlen=MAX_REQUESTS_PER_DAY))

# --- GESTIONE FACCIA MANDATORIA ---
def get_master_face_bytes():
    """Carica l'immagine di riferimento del volto"""
    try:
        with open("master_face.png", "rb") as f:
            face_bytes = f.read()
            logger.info("✅ master_face.png caricato correttamente")
            return face_bytes
    except FileNotFoundError:
        logger.warning("⚠️ master_face.png non trovato - funzionalità face reference disabilitata")
        return None
    except Exception as e:
        logger.error(f"❌ Errore nel caricamento master_face.png: {e}")
        return None

MASTER_FACE_BYTES = get_master_face_bytes()

# --- RATE LIMITING ---
def check_rate_limit(user_id):
    """
    Verifica se l'utente ha superato i limiti di richieste.
    Ritorna (può_procedere, messaggio_errore)
    """
    now = datetime.now()
    
    # Pulisci richieste vecchie (oltre 1 ora)
    hour_ago = now - timedelta(hours=1)
    user_requests_hourly[user_id] = deque(
        [req_time for req_time in user_requests_hourly[user_id] if req_time > hour_ago],
        maxlen=MAX_REQUESTS_PER_HOUR
    )
    
    # Pulisci richieste vecchie (oltre 24 ore)
    day_ago = now - timedelta(days=1)
    user_requests_daily[user_id] = deque(
        [req_time for req_time in user_requests_daily[user_id] if req_time > day_ago],
        maxlen=MAX_REQUESTS_PER_DAY
    )
    
    # Controlla limiti
    hourly_count = len(user_requests_hourly[user_id])
    daily_count = len(user_requests_daily[user_id])
    
    if hourly_count >= MAX_REQUESTS_PER_HOUR:
        return False, f"⏱️ Limite orario raggiunto ({MAX_REQUESTS_PER_HOUR}/h). Riprova tra un'ora."
    
    if daily_count >= MAX_REQUESTS_PER_DAY:
        return False, f"📅 Limite giornaliero raggiunto ({MAX_REQUESTS_PER_DAY}/giorno). Riprova domani."
    
    # Aggiungi timestamp della richiesta corrente
    user_requests_hourly[user_id].append(now)
    user_requests_daily[user_id].append(now)
    
    return True, None

# --- FUNZIONE DI UPSCALING 4K INTELLIGENTE ---
def upscale_to_4k(image_bytes, target_size=3840):
    """
    Upscala l'immagine a 4K preservando l'aspect ratio.
    Se l'immagine è già >= 4K, la restituisce così com'è.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        original_width, original_height = img.size
        
        logger.info(f"📐 Dimensioni originali: {original_width}x{original_height}")
        
        # Se già in 4K o superiore, non modificare
        if original_width >= target_size and original_height >= target_size:
            logger.info("✅ Immagine già in 4K o superiore")
            return image_bytes
        
        # Calcola nuovo aspect ratio preservando proporzioni
        aspect_ratio = original_width / original_height
        
        if aspect_ratio >= 1:  # Landscape o quadrata
            new_width = target_size
            new_height = int(target_size / aspect_ratio)
        else:  # Portrait
            new_height = target_size
            new_width = int(target_size * aspect_ratio)
        
        logger.info(f"🔄 Upscaling a: {new_width}x{new_height}")
        
        # Upscale con algoritmo di alta qualità
        upscaled = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Salva in PNG con massima qualità
        output = io.BytesIO()
        upscaled.save(output, format="PNG", optimize=True, compress_level=1)
        
        logger.info("✅ Upscaling completato")
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"❌ Errore durante upscaling: {e}")
        # In caso di errore, restituisci l'immagine originale
        return image_bytes

# --- GENERAZIONE IMMAGINE + UPSCALE ---
def generate_image(prompt_utente, immagine_riferimento=None, aspect_ratio="1:1", num_images=1):
    """
    Genera immagini con Imagen 4 Ultra, utilizzando face reference se disponibile.
    
    Args:
        prompt_utente: Descrizione della scena
        immagine_riferimento: Bytes di un'immagine di riferimento aggiuntiva (opzionale)
        aspect_ratio: Rapporto aspetto ("1:1", "16:9", "9:16", "4:3", "3:4")
        num_images: Numero di immagini da generare (1-4)
    
    Returns:
        (lista_immagini_bytes, errore)
    """
    try:
        BODY_MANDATE = """
CRITICAL MANDATE: The final image MUST depict a strictly FEMININE BODY shape, completely HAIRLESS,
curvaceous hourglass figure, full D-cup breasts, soft contours, narrow waist, wide hips.
"""

        NEGATIVE_PROMPTS = """
NEGATIVE PROMPT - BODY: masculine body shape, broad male shoulders, flat chest, muscular frame, body hair
NEGATIVE PROMPT - FACE: young female face, blurry face, face drift, distorted face
"""

        full_prompt = f"""
{BODY_MANDATE}

SCENE DETAILS: {prompt_utente}

AVOID STRICTLY: {NEGATIVE_PROMPTS}
"""

        logger.info(f"🎨 Generazione immagine - Prompt: {prompt_utente[:100]}...")
        logger.info(f"📏 Aspect ratio: {aspect_ratio}, Numero immagini: {num_images}")
        
        # Prepara parametri per l'API
        generation_config = {
            "number_of_images": min(num_images, 4),  # Max 4 immagini
            "aspect_ratio": aspect_ratio,
        }
        
        # Prepara le immagini di riferimento
        reference_images = []
        
        # Aggiungi master_face se disponibile
        if MASTER_FACE_BYTES:
            reference_images.append({
                "image": {
                    "image_bytes": MASTER_FACE_BYTES
                },
                "reference_type": "FACE"
            })
            logger.info("👤 Face reference aggiunta")
        
        # Aggiungi immagine di riferimento utente se fornita
        if immagine_riferimento:
            reference_images.append({
                "image": {
                    "image_bytes": immagine_riferimento
                },
                "reference_type": "STYLE"  # Usa come riferimento di stile
            })
            logger.info("🖼️ Immagine riferimento utente aggiunta")
        
        # Chiamata API
        if reference_images:
            response = client.models.generate_images(
                model=MODEL_ID,
                prompt=full_prompt,
                config=generation_config,
                reference_images=reference_images
            )
        else:
            response = client.models.generate_images(
                model=MODEL_ID,
                prompt=full_prompt,
                config=generation_config
            )

        if response.generated_images:
            logger.info(f"✅ Generati {len(response.generated_images)} immagini")
            
            # Upscala tutte le immagini generate
            upscaled_images = []
            for idx, img in enumerate(response.generated_images):
                logger.info(f"🔄 Upscaling immagine {idx + 1}/{len(response.generated_images)}")
                image_4k = upscale_to_4k(img.image.image_bytes)
                upscaled_images.append(image_4k)
            
            return upscaled_images, None
        
        logger.warning("⚠️ Nessuna immagine generata dalla API")
        return None, "Nessuna immagine generata."

    except Exception as e:
        logger.error(f"❌ Errore durante generazione: {e}", exc_info=True)
        return None, f"Errore: {str(e)}"

# --- BOT TELEGRAM ---
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Messaggio di benvenuto"""
    welcome_text = """
👋 <b>Benvenuto in MoltBot 4K!</b>

Questo bot genera immagini in <b>qualità 4K</b> utilizzando Google Imagen 4 Ultra.

<b>📝 Come usare:</b>
• Invia un testo descrittivo per generare un'immagine
• Invia una foto con didascalia per usarla come riferimento di stile
• Usa /settings per configurare aspect ratio e numero immagini

<b>🎯 Comandi disponibili:</b>
/start - Messaggio di benvenuto
/help - Guida completa
/settings - Configura generazione
/stats - Statistiche utilizzo
/cancel - Annulla operazione

<b>⚡ Limiti:</b>
• {}/ora
• {}/giorno

Inizia inviando una descrizione!
""".format(MAX_REQUESTS_PER_HOUR, MAX_REQUESTS_PER_DAY)
    
    bot.send_message(message.chat.id, welcome_text)
    logger.info(f"👤 Nuovo utente: {message.from_user.id} - {message.from_user.username}")

@bot.message_handler(commands=['help'])
def send_help(message):
    """Guida dettagliata"""
    help_text = """
<b>📖 GUIDA COMPLETA</b>

<b>🎨 Generazione Base:</b>
Invia semplicemente un testo descrittivo:
<i>"Una ragazza su una spiaggia al tramonto"</i>

<b>🖼️ Con Riferimento Stile:</b>
Invia una foto con didascalia descrittiva per usare l'immagine come riferimento di stile.

<b>⚙️ Impostazioni Avanzate:</b>
Usa /settings per configurare:
• Aspect Ratio (1:1, 16:9, 9:16, 4:3, 3:4)
• Numero immagini (1-4)

<b>📊 Statistiche:</b>
Usa /stats per vedere il tuo utilizzo

<b>🔧 Tecnologia:</b>
• Modello: Google Imagen 4 Ultra
• Risoluzione: 4K (upscaling intelligente)
• Face Reference: Attiva{}

<b>💡 Suggerimenti:</b>
• Sii specifico nelle descrizioni
• Include dettagli su illuminazione, stile, atmosfera
• Sperimenta con diversi aspect ratio
""".format(" ✅" if MASTER_FACE_BYTES else " ❌")
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['settings'])
def send_settings(message):
    """Menu impostazioni interattivo"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Pulsanti aspect ratio
    markup.add(
        types.InlineKeyboardButton("1:1 (Quadrato)", callback_data="ar_1:1"),
        types.InlineKeyboardButton("16:9 (Landscape)", callback_data="ar_16:9")
    )
    markup.add(
        types.InlineKeyboardButton("9:16 (Portrait)", callback_data="ar_9:16"),
        types.InlineKeyboardButton("4:3", callback_data="ar_4:3")
    )
    markup.add(
        types.InlineKeyboardButton("3:4", callback_data="ar_3:4")
    )
    
    # Pulsanti numero immagini
    markup.add(
        types.InlineKeyboardButton("1 immagine", callback_data="num_1"),
        types.InlineKeyboardButton("2 immagini", callback_data="num_2")
    )
    markup.add(
        types.InlineKeyboardButton("3 immagini", callback_data="num_3"),
        types.InlineKeyboardButton("4 immagini", callback_data="num_4")
    )
    
    bot.send_message(
        message.chat.id,
        "<b>⚙️ IMPOSTAZIONI</b>\n\nSeleziona aspect ratio e numero di immagini:",
        reply_markup=markup
    )

# Dizionari per memorizzare preferenze utente
user_aspect_ratio = defaultdict(lambda: "1:1")
user_num_images = defaultdict(lambda: 1)

@bot.callback_query_handler(func=lambda call: call.data.startswith('ar_') or call.data.startswith('num_'))
def handle_settings_callback(call):
    """Gestisce le scelte nelle impostazioni"""
    user_id = call.from_user.id
    
    if call.data.startswith('ar_'):
        aspect_ratio = call.data.replace('ar_', '')
        user_aspect_ratio[user_id] = aspect_ratio
        bot.answer_callback_query(call.id, f"✅ Aspect ratio: {aspect_ratio}")
        logger.info(f"User {user_id} - Aspect ratio: {aspect_ratio}")
    
    elif call.data.startswith('num_'):
        num = int(call.data.replace('num_', ''))
        user_num_images[user_id] = num
        bot.answer_callback_query(call.id, f"✅ Numero immagini: {num}")
        logger.info(f"User {user_id} - Num images: {num}")
    
    # Aggiorna il messaggio con le impostazioni correnti
    current_settings = f"""
<b>⚙️ IMPOSTAZIONI ATTUALI</b>

📏 Aspect Ratio: <b>{user_aspect_ratio[user_id]}</b>
🖼️ Numero Immagini: <b>{user_num_images[user_id]}</b>

Invia ora il tuo prompt per generare!
"""
    bot.edit_message_text(
        current_settings,
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Mostra statistiche utilizzo utente"""
    user_id = message.from_user.id
    
    # Calcola richieste rimanenti
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    
    hourly_used = len([t for t in user_requests_hourly[user_id] if t > hour_ago])
    daily_used = len([t for t in user_requests_daily[user_id] if t > day_ago])
    
    hourly_remaining = MAX_REQUESTS_PER_HOUR - hourly_used
    daily_remaining = MAX_REQUESTS_PER_DAY - daily_used
    
    stats_text = f"""
<b>📊 STATISTICHE UTILIZZO</b>

<b>⏱️ Ultima ora:</b>
• Utilizzate: {hourly_used}/{MAX_REQUESTS_PER_HOUR}
• Rimanenti: {hourly_remaining}

<b>📅 Ultime 24 ore:</b>
• Utilizzate: {daily_used}/{MAX_REQUESTS_PER_DAY}
• Rimanenti: {daily_remaining}

<b>⚙️ Impostazioni correnti:</b>
• Aspect Ratio: {user_aspect_ratio[user_id]}
• Numero Immagini: {user_num_images[user_id]}
"""
    
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    """Annulla operazione in corso"""
    bot.send_message(message.chat.id, "❌ Operazione annullata.")

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    """Gestisce richieste di generazione immagini"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Controlla rate limiting
    can_proceed, error_msg = check_rate_limit(user_id)
    if not can_proceed:
        bot.reply_to(message, error_msg)
        logger.warning(f"⛔ Rate limit per user {user_id} - {username}")
        return
    
    # Invia messaggio di attesa
    wait_msg = bot.reply_to(message, "⏳ Generazione 4K in corso...\n\n<i>Questo può richiedere 30-60 secondi</i>")
    
    try:
        # Estrai prompt e immagine
        prompt = message.caption if message.content_type == 'photo' else message.text
        img_data = None
        
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)
            logger.info(f"📸 Immagine riferimento ricevuta da user {user_id}")
        
        # Ottieni impostazioni utente
        aspect_ratio = user_aspect_ratio[user_id]
        num_images = user_num_images[user_id]
        
        logger.info(f"🎯 Richiesta da {username} (ID: {user_id})")
        logger.info(f"📝 Prompt: {prompt[:100]}...")
        
        # Genera immagini
        start_time = time.time()
        risultati, errore = generate_image(
            prompt,
            immagine_riferimento=img_data,
            aspect_ratio=aspect_ratio,
            num_images=num_images
        )
        elapsed_time = time.time() - start_time
        
        if risultati:
            logger.info(f"✅ Generazione completata in {elapsed_time:.2f}s")
            
            # Aggiorna messaggio di attesa
            bot.edit_message_text(
                f"✅ Generazione completata in {elapsed_time:.1f}s!\n\n📤 Invio immagini...",
                message.chat.id,
                wait_msg.message_id
            )
            
            # Invia tutte le immagini generate
            for idx, img_bytes in enumerate(risultati):
                file_name = f"moltbot_4k_{idx+1}.png"
                bot.send_document(
                    message.chat.id,
                    io.BytesIO(img_bytes),
                    visible_file_name=file_name,
                    caption=f"🎨 Immagine {idx+1}/{len(risultati)}\n📏 {aspect_ratio}" if len(risultati) > 1 else f"🎨 Immagine 4K\n📏 {aspect_ratio}"
                )
                logger.info(f"📤 Immagine {idx+1} inviata a user {user_id}")
            
            # Elimina messaggio di attesa
            bot.delete_message(message.chat.id, wait_msg.message_id)
            
        else:
            logger.error(f"❌ Errore generazione per user {user_id}: {errore}")
            bot.edit_message_text(
                f"❌ <b>ERRORE</b>\n\n{errore}\n\n💡 Prova a riformulare il prompt o riprova più tardi.",
                message.chat.id,
                wait_msg.message_id
            )
    
    except Exception as e:
        logger.error(f"❌ Errore critico per user {user_id}: {e}", exc_info=True)
        try:
            bot.edit_message_text(
                f"❌ <b>ERRORE IMPREVISTO</b>\n\n{str(e)}\n\n🔧 L'errore è stato registrato.",
                message.chat.id,
                wait_msg.message_id
            )
        except:
            pass

# --- WEB SERVER PER RENDER ---
server = flask.Flask(__name__)

@server.route('/')
def health():
    """Health check endpoint"""
    return flask.jsonify({
        "status": "online",
        "bot": "MoltBot 4K",
        "model": MODEL_ID,
        "face_reference": MASTER_FACE_BYTES is not None,
        "timestamp": datetime.now().isoformat()
    })

@server.route('/stats')
def stats():
    """Endpoint statistiche globali"""
    total_users = len(user_requests_daily)
    total_requests_today = sum(len(reqs) for reqs in user_requests_daily.values())
    
    return flask.jsonify({
        "total_users": total_users,
        "total_requests_today": total_requests_today,
        "max_requests_per_hour": MAX_REQUESTS_PER_HOUR,
        "max_requests_per_day": MAX_REQUESTS_PER_DAY
    })

# --- AVVIO BOT ---
if __name__ == "__main__":
    logger.info("🚀 Avvio MoltBot 4K...")
    logger.info(f"📱 Model: {MODEL_ID}")
    logger.info(f"👤 Face Reference: {'Attiva ✅' if MASTER_FACE_BYTES else 'Disattivata ❌'}")
    logger.info(f"⏱️ Rate Limit: {MAX_REQUESTS_PER_HOUR}/h, {MAX_REQUESTS_PER_DAY}/giorno")
    
    # Avvia web server in thread separato
    threading.Thread(
        target=lambda: server.run(
            host='0.0.0.0',
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()
    
    logger.info("🌐 Web server avviato")
    logger.info("🤖 Bot in polling...")
    
    # Avvia bot con gestione errori
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Errore polling: {e}", exc_info=True)
            logger.info("🔄 Riavvio polling in 5 secondi...")
            time.sleep(5)

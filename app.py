import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE CORE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Modello Pro identificato dalla tua lista
MODEL_ID = "nano-banana-pro-preview" 

# --- CARICAMENTO IDENTITÀ MASTER ---
def get_master_face():
    """Carica l'immagine master per garantire la coerenza del volto."""
    try:
        # Il file deve essere caricato su GitHub con questo nome esatto
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except Exception as e:
        print(f"⚠️ Nota: master_face.png non trovato. Procedo solo con testo. Errore: {e}", flush=True)
        return None

MASTER_FACE = get_master_face()

# Master Prompt derivato dal tuo JSON e dalle regole di identità
MASTER_PROMPT = """VALERIA CROSS MASTER IDENTITY:
- REFERENCE: Use the facial features from the attached master_face.png.
- FACE: 60yo Italian male, silver-white wavy hair, receding hairline, full trimmed white beard. 
- DETAILS: Dark brown eyes, crow's feet, nasolabial folds, visible skin pores.
- ACCESSORIES: Hexagonal-rounded dark brown tortoiseshell glasses.
- BODY: 180cm, 85kg, hourglass feminine figure, full D-cup bust, completely hairless [cite: 2026-02-08].
- STYLE: High-end Vogue photography, 8K, cinematic fashion lighting.
- SAFETY: SynthID verifiable face. Maintain masculine facial features on the feminine body."""

# --- LOGICA DI GENERAZIONE ---
def generate_valeria(prompt_utente, immagine_utente=None):
    """Funzione universale per generare Valeria (usata da Telegram e Gradio)."""
    try:
        # Prepariamo i contenuti: Prompt + Faccia Master + (eventuale) Foto Utente + Messaggio
        contents = [MASTER_PROMPT]
        if MASTER_FACE: 
            contents.append(MASTER_FACE)
        if immagine_utente: 
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))
        
        contents.append(f"SCENE DESCRIPTION: {prompt_utente}")

        # Configurazione senza aspect_ratio per evitare errori di validazione
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH")
            ]
        )

        response = client.models.generate_content(model=MODEL_ID, contents=contents, config=config)
        
        if response and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        return None
    except Exception as e:
        print(f"❌ Errore Generazione: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Telegram Online: @{bot.get_me().username}", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "💎 Elaborazione Valeria Cross (Nanobanana Pro)...")
                
                img_data = None
                if m.content_type == 'photo':
                    f_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(f_info.file_path)
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                risultato = generate_valeria(prompt, img_data)
                
                if risultato:
                    bot.send_photo(m.chat.id, io.BytesIO(risultato), caption="💎 Valeria Cross | Master Identity")
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Immagine filtrata o errore tecnico.", m.chat.id, wait.message_id)
            except Exception as e:
                print(f"❌ Errore Bot: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- GRADIO WEB UI (Emergency Access) ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_valeria(prompt)
        if img_bytes:
            return io.BytesIO(img_bytes).read()
        return None

    ui = gr.Interface(
        fn=web_interface,
        inputs=gr.Textbox(label="Prompt per Valeria"),
        outputs=gr.Image(label="Risultato Pro"),
        title="Valeria Cross Web-UI",
        description="Backup per generare quando Telegram non risponde."
    )
    ui.launch(server_name="0.0.0.0", server_port=10000)

# --- AVVIO SISTEMA ---
if __name__ == "__main__":
    # Heartbeat per Render
    def heartbeat():
        while True:
            print("💓 Heartbeat: Sistema Attivo", flush=True)
            time.sleep(30)
    
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
              

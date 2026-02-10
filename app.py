import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# ID MODELLO ULTRA (Alta Risoluzione)
MODEL_ID = "imagen-4.0-ultra-generate-001" 

def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            # Per Imagen usiamo i raw bytes o un oggetto Part generico
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except:
        return None

MASTER_FACE = get_master_face()

# MASTER PROMPT: Ottimizzato per Imagen Ultra
MASTER_PROMPT = """ generate a photorealistic image of VALERIA CROSS.
SUBJECT: 60yo Italian male face (silver hair, white beard, glasses) on a voluptuous female hourglass body (D-cup).
DETAILS: 8K resolution, skin pores visible, cinematic lighting, Vogue Italia style.
IMPORTANT: The face MUST match the reference provided but adapt expression and lighting to the scene."""

def generate_valeria(prompt_utente, immagine_utente=None):
    try:
        # Costruiamo il prompt combinato
        full_prompt = f"{MASTER_PROMPT}. SCENE: {prompt_utente}"
        
        # ELENCO CONTENUTI (Prompt + Faccia)
        contents = [full_prompt]
        if MASTER_FACE:
            contents.append(MASTER_FACE)
        if immagine_utente:
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))

        # --- FIX CRITICO: CONFIGURAZIONE COME DIZIONARIO ---
        # Rimuoviamo 'types.GenerateImageConfig' che causava l'errore.
        # Passiamo un dizionario semplice.
        config_dict = {
            "aspect_ratio": "2:3",
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
            ]
        }

        # Chiamata generica che supporta Imagen tramite 'generate_content' o 'generate_images'
        # Usiamo generate_content perché gestisce meglio i mix testo/immagini nell'SDK attuale
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config_dict
        )
        
        # Estrazione immagine dalla risposta
        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
                
        # Fallback per endpoint specifici immagine (se il primo metodo non restituisce dati)
        if hasattr(response, 'generated_images'):
             return response.generated_images[0].image_bytes

        return None

    except Exception as e:
        print(f"❌ Errore Imagen Ultra: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Motore Imagen Ultra Online", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "📸 Sviluppo Pellicola Ultra-HD...")
                img_data = None
                if m.content_type == 'photo':
                    f_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(f_info.file_path)
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                risultato = generate_valeria(prompt, img_data)
                
                if risultato:
                    # Inviamo come DOCUMENTO per evitare la compressione di Telegram
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="valeria_vogue_ultra.jpg", 
                        caption="💎 Valeria Cross | 4.2MPx Raw Output"
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore API o Filtro Google.", m.chat.id, wait.message_id)
            except Exception as e:
                print(f"❌ Errore Bot: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash: {e}", flush=True)

# --- GRADIO WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_valeria(prompt)
        return io.BytesIO(img_bytes).read() if img_bytes else None

    ui = gr.Interface(fn=web_interface, inputs=gr.Textbox(label="Prompt"), outputs=gr.Image())
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

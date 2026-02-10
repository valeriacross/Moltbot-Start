import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# USIAMO IL MOTORE SPECIALIZZATO PER ALTA RISOLUZIONE
MODEL_ID = "imagen-4.0-ultra-generate-001" 

def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except:
        return None

MASTER_FACE = get_master_face()

# Master Prompt ottimizzato per il realismo fotografico estremo
MASTER_PROMPT = """VALERIA CROSS MASTER IDENTITY:
- SUBJECT: 60yo Italian male, silver wavy hair, groomed white beard, octagonal Havana glasses.
- BODY: Female hourglass figure, D-cup bust, 180cm, 85kg, hairless skin.
- REFERENCE: Use facial features from the attached image.
- QUALITY: Extreme 4.2MPx resolution, ultra-detailed skin pores, cinematic Vogue lighting.
- STYLE: Professional high-fashion photography, 85mm lens, f/2.8."""

def generate_valeria(prompt_utente, immagine_utente=None):
    try:
        # Per Imagen 4.0 Ultra usiamo il metodo 'generate_image' (specializzato)
        # invece di 'generate_content' (generico)
        
        testo_finale = f"{MASTER_PROMPT}. SCENE: {prompt_utente}"
        
        # Configurazione specifica per Imagen (High Res + Aspect Ratio)
        config_imagen = types.GenerateImageConfig(
            number_of_images=1,
            aspect_ratio="2:3",
            add_watermark=False,
            output_mime_type="image/jpeg",
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE")
            ]
        )

        # Chiamata al motore Ultra
        response = client.models.generate_image(
            model=MODEL_ID,
            prompt=testo_finale,
            config=config_imagen
        )
        
        if response and response.generated_images:
            return response.generated_images[0].image_bytes
        return None
    except Exception as e:
        print(f"❌ Errore Ultra Engine: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Motore Imagen 4.0 Ultra Online", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "📸 Generazione Ultra-HD (4.2MPx) in corso...")
                img_data = None
                if m.content_type == 'photo':
                    f_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(f_info.file_path)
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                risultato = generate_valeria(prompt, img_data)
                
                if risultato:
                    bot.send_document(m.chat.id, io.BytesIO(risultato), visible_file_name="Valeria_Cross_UltraHD.jpg", caption="💎 Qualità Ultra 4.2MPx")
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Il motore Ultra ha filtrato la richiesta.", m.chat.id, wait.message_id)
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

    ui = gr.Interface(fn=web_interface, inputs=gr.Textbox(label="Prompt High-Res"), outputs=gr.Image())
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

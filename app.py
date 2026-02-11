import os, telebot, io, threading, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# MOTORE AD ALTA RISOLUZIONE (IMAGEN 4.0 ULTRA)
MODEL_ID = "imagen-4.0-ultra-generate-001" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, image_bytes=None):
    try:
        if not prompt_utente and not image_bytes: return None

        contents = []
        
        # Se viene fornita un'immagine, la inseriamo come riferimento
        if image_bytes:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )
        
        # Inserimento del prompt testuale
        if prompt_utente:
            contents.append(prompt_utente)

        # Configurazione ottimizzata per la massima fedeltà
        config_raw = {
            "response_modalities": ["IMAGE"],
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        # Generazione tramite Imagen 4.0 Ultra
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config_raw
        )
        
        if response and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        return None
    except Exception as e:
        print(f"❌ Errore Generazione ({MODEL_ID}): {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Online - Motore: {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                prompt = ""
                img_data = None
                
                wait = bot.reply_to(m, "💎 Generazione in Alta Risoluzione (Ultra)...")

                if m.content_type == 'photo':
                    file_id = m.photo[-1].file_id
                    file_info = bot.get_file(file_id)
                    img_data = bot.download_file(file_info.file_path)
                    prompt = m.caption if m.caption else ""
                else:
                    prompt = m.text
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    # Inviamo come documento per preservare la qualità originale (senza compressione Telegram)
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="ultra_quality_render.jpg", 
                        caption="✨ Immagine generata con Imagen 4.0 Ultra."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore: Il modello Ultra non ha prodotto risultati.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- WEB UI ---
def avvia_web():
    def web_interface(prompt, image):
        img_bytes = None
        if image:
            import PIL.Image
            buf = io.BytesIO()
            image.save(buf, format='JPEG')
            img_bytes = buf.getvalue()
            
        gen_bytes = generate_image(prompt, img_bytes)
        return io.BytesIO(gen_bytes).read() if gen_bytes else None

    ui = gr.Interface(
        fn=web_interface, 
        inputs=[
            gr.Textbox(label="Prompt"), 
            gr.Image(type="pil", label="Immagine di riferimento (Opzionale)")
        ], 
        outputs=gr.Image(label="Risultato Ultra")
    )
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

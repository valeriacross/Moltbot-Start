import os, telebot, io, threading, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# IL MOTORE HIGH-RES COMPATIBILE CON GENERATE_CONTENT
MODEL_ID = "gemini-2.0-flash-exp-image-generation" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, image_bytes=None):
    try:
        if not prompt_utente and not image_bytes: return None

        contents = []
        
        # Se c'è un'immagine di riferimento, la aggiungiamo come "Part"
        if image_bytes:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )
        
        # Aggiungiamo il prompt testuale
        # Nota: Più dettagliato è il prompt, migliore sarà la risoluzione percepita
        if prompt_utente:
            contents.append(prompt_utente)

        config_raw = {
            "response_modalities": ["IMAGE"],
            "safety_settings": [
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config_raw
        )
        
        # Estrazione dell'immagine generata
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
        print(f"✅ Bot Online - Motore High-Res: {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                prompt = ""
                img_data = None
                
                wait = bot.reply_to(m, "✨ Generazione High-Res in corso...")

                if m.content_type == 'photo':
                    # Scarichiamo l'immagine originale inviata dall'utente
                    file_id = m.photo[-1].file_id
                    file_info = bot.get_file(file_id)
                    img_data = bot.download_file(file_info.file_path)
                    # Usiamo la didascalia come prompt, o un testo di default se vuota
                    prompt = m.caption if m.caption else "generazione basata su questa immagine"
                else:
                    prompt = m.text
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    # Invio come documento per evitare la compressione di Telegram
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="gemini_2_highres.jpg", 
                        caption="✅ Immagine generata con Gemini 2.0 Flash."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Non è stato possibile generare l'immagine. Riprova con un prompt diverso.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- WEB UI (GRADIO) ---
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
            gr.Image(type="pil", label="Immagine sorgente (Opzionale)")
        ], 
        outputs=gr.Image(label="Risultato Gemini 2.0"),
        title="Gemini 2.0 High-Res Generator"
    )
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

import os, telebot, io, threading, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# USIAMO IL MODELLO 2.0 FLASH: Stabile, veloce e alta qualità
MODEL_ID = "gemini-2.0-flash" 

# --- GENERAZIONE ---
def generate_image(prompt_utente, image_bytes=None):
    try:
        if not prompt_utente and not image_bytes: return None

        contents = []
        if image_bytes:
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        
        # Rendiamo il prompt più "forte" per forzare la generazione
        full_prompt = f"{prompt_utente}. Generate a high-resolution, detailed image based on this."
        contents.append(full_prompt)

        # Configurazione specifica per l'output immagine
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF")
            ]
        )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=config
        )
        
        # DEBUG: Stampa la risposta nel terminale per capire se ci sono blocchi safety
        # print(f"DEBUG Response: {response}")

        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        
        print("⚠️ Il modello non ha restituito dati immagine (possibile blocco Safety).")
        return None

    except Exception as e:
        print(f"❌ Errore Tecnico: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Online - Motore: {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "✍️ Elaborazione in corso...")
                
                img_data = None
                prompt = m.text
                
                if m.content_type == 'photo':
                    file_id = m.photo[-1].file_id
                    file_info = bot.get_file(file_id)
                    img_data = bot.download_file(file_info.file_path)
                    prompt = m.caption if m.caption else "Upscale and enhance this image"
                
                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="high_res_result.jpg", 
                        caption="✨ Generazione completata con successo."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("❌ Errore: Generazione bloccata o non riuscita. Prova un prompt più descrittivo.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}")

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}")

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

    ui = gr.Interface(fn=web_interface, inputs=["text", "image"], outputs="image")
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
    

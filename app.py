import os, telebot, io, threading, time, sys
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# MODELLO DALLA TUA LISTA: Imagen 4.0 Fast
MODEL_ID = "imagen-4.0-fast-generate-001" 

def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        # Se l'utente manda una foto, la carichiamo come riferimento
        img_input = None
        if immagine_riferimento:
            img_input = types.Image(data=immagine_riferimento, mime_type="image/jpeg")

        # Usiamo il metodo dedicato alle immagini
        response = client.models.generate_image(
            model=MODEL_ID,
            prompt=prompt_utente if prompt_utente else "High quality photography",
            config=types.GenerateImageConfig(
                number_of_images=1,
                # Se c'è un'immagine, la usiamo come guida
                image=img_input if img_input else None,
                # Risoluzione automatica (non 1:1)
                safety_settings=[
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
                ]
            )
        )
        
        if response and response.generated_images:
            return response.generated_images[0].image_bytes
            
        return None

    except Exception as e:
        print(f"❌ Errore Imagen 4.0: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Online con {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Generazione in corso...")
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                img_data = None
                
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)

                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="generazione.jpg", 
                        caption="✅ Ecco l'immagine."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Il server ha bloccato il prompt o c'è un errore.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash: {e}", flush=True)

if __name__ == "__main__":
    avvia_bot()
    

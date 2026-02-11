import os, telebot, io, threading, time, sys
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Modello Nanobanana Pro (L'unico stabile per questo scopo)
MODEL_ID = "nano-banana-pro-preview" 

def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        contents = []
        
        # Gestione Immagine Allegata (per volti o scenari)
        if immagine_riferimento:
            contents.append(types.Part.from_bytes(data=immagine_riferimento, mime_type="image/jpeg"))
        
        # Prompt pulito: forziamo il formato NO 1:1 e la qualità 2K
        istruzioni_formato = "High quality, 2K detail, cinematic, rectangular aspect ratio (3:4 or 16:9), NO SQUARE 1:1."
        testo_finale = f"{prompt_utente}. {istruzioni_formato}" if prompt_utente else istruzioni_formato
        contents.append(testo_finale)

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
        
        # Estrazione della prima immagine valida
        if response and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        return None
    except Exception as e:
        print(f"❌ Errore Nanobanana: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Online con {MODEL_ID}", flush=True)

        @bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "🎨 Elaborazione (Nanobanana)...")
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                img_data = None
                
                if m.content_type == 'photo':
                    file_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(file_info.file_path)

                risultato = generate_image(prompt, img_data)
                
                if risultato:
                    # Documento con estensione .jpg per visibilità immediata
                    bot.send_document(
                        m.chat.id, 
                        io.BytesIO(risultato), 
                        visible_file_name="generazione.jpg", 
                        caption="✅ Completato."
                    )
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Errore o Filtro Google.", m.chat.id, wait.message_id)
            
            except Exception as e:
                print(f"❌ Errore Handler: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash: {e}", flush=True)

if __name__ == "__main__":
    avvia_bot()

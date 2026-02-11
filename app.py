import os, telebot, io, threading, sys
from google import genai
from google.genai import types

# --- CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# Modello dalla tua lista (Stessa famiglia di Nanobanana)
MODEL_ID = "gemini-3-pro-image-preview" 

def generate_image(prompt_utente, immagine_riferimento=None):
    try:
        contents = []
        if immagine_riferimento:
            contents.append(types.Part.from_bytes(data=immagine_riferimento, mime_type="image/jpeg"))
        
        # Prompt pulito
        contents.append(f"{prompt_utente}. Cinematic, high resolution, 16:9.")

        # Configurazione snella per evitare errori di validazione
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF")
                ]
            )
        )
        
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data, None
        
        return None, "Il modello non ha restituito immagini (possibile blocco filtri)."

    except Exception as e:
        # Restituiamo l'errore tecnico esatto
        return None, str(e)

# --- TELEGRAM BOT ---
def avvia_bot():
    bot = telebot.TeleBot(TOKEN)
    print(f"✅ Bot Online su {MODEL_ID}")

    @bot.message_handler(content_types=['text', 'photo'])
    def handle(m):
        wait = bot.reply_to(m, "⏳ Elaborazione...")
        
        prompt = m.caption if m.content_type == 'photo' else m.text
        img_data = None
        if m.content_type == 'photo':
            file_info = bot.get_file(m.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)

        risultato, errore = generate_image(prompt, img_data)
        
        if risultato:
            bot.send_document(m.chat.id, io.BytesIO(risultato), visible_file_name="output.jpg")
            bot.delete_message(m.chat.id, wait.message_id)
        else:
            # Ti scrive l'errore tecnico reale
            bot.edit_message_text(f"❌ ERRORE TECNICO:\n{errore}", m.chat.id, wait.message_id)

    bot.infinity_polling()

if __name__ == "__main__":
    avvia_bot()
    

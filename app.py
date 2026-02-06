import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr

# Setup
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Identità Valeria
SYSTEM_PROMPT = """
Soggetto: Valeria Cross, 60 anni, transmaschile, 180cm, 85kg, coppa D. 
Look: Capelli grigio platino, occhiali da vista Vogue Havana.
Stile: Vogue Editoriale, 85mm, f/2.8, 8K, watermark 'feat. Valeria Cross 👠'.
"""

def avvia_bot():
    # Modello di testo
    text_model = genai.GenerativeModel('gemini-flash-latest')
    
    # Modello Immagini: si usa ImageGenerationModel per Imagen 3
    imagen = genai.ImageGenerationModel("imagen-3.0-generate-001")
    
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(func=lambda m: True)
    def gestisci(m):
        wait_msg = bot.reply_to(m, "📸 Moltbot in azione...")
        try:
            # 1. Gemini crea il prompt
            p_res = text_model.generate_content(f"{SYSTEM_PROMPT}. Crea un prompt per: {m.text}")
            
            # 2. Imagen genera la foto (Metodo corretto: generate_images)
            response = imagen.generate_images(
                prompt=p_res.text,
                number_of_images=1,
                aspect_ratio="3:4"
            )
            
            # 3. Invio
            for img in response.images:
                img_io = io.BytesIO()
                img._pil_image.save(img_io, format='PNG')
                img_io.seek(0)
                bot.send_photo(m.chat.id, img_io, caption="Ecco lo scatto. ✨")
            
            bot.delete_message(m.chat.id, wait_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait_msg.message_id)

    bot.infinity_polling(skip_pending=True)

def web_service():
    gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
            prompt_finito = p_res.text
            
            # B. Imagen genera la foto
            # IMPORTANTE: Usiamo generate_content ma con il modello Imagen 3 configurato
            img_res = imagen.generate_content(prompt_finito)
            
            # C. Invio a Telegram
            if img_res.candidates:
                for candidate in img_res.candidates:
                    # Estrazione dell'immagine dai dati del candidato
                    for part in candidate.content.parts:
                        if part.inline_data:
                            img_data = part.inline_data.data
                            bot.send_photo(m.chat.id, img_data, caption="Ecco Valeria. ✨")
            
            bot.delete_message(m.chat.id, wait_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait_msg.message_id)

    # Avvio pulito senza code pendenti
    bot.infinity_polling(skip_pending=True)

# Interfaccia minima per Render
def web_service():
    gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

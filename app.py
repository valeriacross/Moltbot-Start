import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr
from PIL import Image

# Setup Chiavi
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Configurazione
genai.configure(api_key=API_KEY)

# Identità Valeria
SYSTEM_PROMPT = """Soggetto: Valeria Cross, 60 anni, transmaschile, 180cm, 85kg, coppa D. 
Look: Capelli grigio platino, occhiali Vogue Havana. Stile: Vogue Editoriale, 85mm, f/2.8."""

def avvia_bot():
    try:
        # Modelli
        text_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        # Usiamo il metodo corretto per Imagen 3
        imagen = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Scatto in corso...")
            try:
                # 1. Prompt
                p_res = text_model.generate_content(f"{SYSTEM_PROMPT}. Crea prompt per: {m.text}")
                
                # 2. Immagine
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
                    bot.send_photo(m.chat.id, img_io, caption="Valeria Cross ✨")
                
                bot.delete_message(m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait.message_id)

        bot.infinity_polling(skip_pending=True)
    except Exception as startup_error:
        print(f"CRASH ALL'AVVIO: {startup_error}")

def web_service():
    gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()
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
                    bot.send_photo(m.chat.id, img_io, caption="Valeria Cross ✨")
                
                bot.delete_message(m.chat.id, wait.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Errore: {e}", m.chat.id, wait.message_id)

        bot.infinity_polling(skip_pending=True)
    except Exception as startup_error:
        print(f"CRASH ALL'AVVIO: {startup_error}")

def web_service():
    gr.Interface(fn=lambda x:x, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    threading.Thread(target=avvia_bot, daemon=True).start()
    web_service()

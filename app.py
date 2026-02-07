import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr
from PIL import Image

# --- SETUP CHIAVI E CONFIGURAZIONE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Inizializzazione Google AI
genai.configure(api_key=API_KEY)

# Identità Valeria Cross
SYSTEM_PROMPT = """Soggetto: Valeria Cross, 60 anni, uomo italiano transmaschile. 
Look: Capelli grigio platino (15cm, lati corti), barba grigia corta e curata, occhiali da vista Vogue Havana scuri (forma ottagonale).
Fisico: 180cm, 85kg, seno coppa D, forme morbide.
Stile fotografico: Vogue Editoriale, 85mm, f/2.8, 8K, illuminazione da studio professionale. 
Rendering: Global Illumination, Ambient Occlusion, Subsurface scattering.
Watermark: 'feat. Valeria Cross 👠'."""

def avvia_bot():
    try:
        # Modelli aggiornati
        text_model = genai.GenerativeModel('gemini-1.5-flash')
        # Utilizziamo il modello Imagen 3
        imagen = genai.GenerativeModel('imagen-3.0-generate-001')
        
        bot = telebot.TeleBot(TOKEN)

        @bot.message_handler(commands=['start'])
        def send_welcome(m):
            bot.reply_to(m, "Ciao! Sono Moltbot. Mandami un'idea e genererò un'immagine di Valeria Cross per te. 📸")

        @bot.message_handler(func=lambda m: True)
        def gestisci(m):
            wait = bot.reply_to(m, "📸 Moltbot in azione... Sto creando Valeria per te.")
            try:
                # 1. Crea il prompt tecnico usando Gemini
                prompt_input = f"{SYSTEM_PROMPT}\n\nCrea un prompt tecnico dettagliato in inglese per generare questa scena: {m.text}"
                p_res = text_model.generate_content(prompt_input)
                prompt_finale = p_res.text

                # 2. Genera l'immagine con Imagen 3
                response = imagen.generate_content(prompt_finale)
                
                # 3. Estrai l'immagine dalla risposta
                image_found = False
                if response.candidates:
                    for candidate in response.candidates:
                        for part in candidate.content.parts:
                            if part.inline_data:
                                # Conversione dati binari per Telegram
                                photo_stream = io.BytesIO(part.inline_data.data)
                                photo_stream.name = 'valeria_cross.png'
                                bot.send_photo(m.chat.id, photo_stream, caption="Valeria Cross ✨")
                                image_found = True
                                break
                
                if not image_found:
                    bot.edit_message_text("❌ Google non ha restituito immagini. Potrebbe esserci un filtro di sicurezza o il modello non è ancora attivo.", m.chat.id, wait.message_id)
                else:
                    bot.delete_message(m.chat.id, wait.message_id)

            except Exception as e:
                errore_str = str(e)
                if "404" in errore_str:
                    msg = "❌ Errore 404: Il modello Imagen 3 non è ancora abilitato sulla tua API Key in questa regione."
                else:
                    msg = f"❌ Errore tecnico: {errore_str}"
                bot.edit_message_text(msg, m.chat.id, wait.message_id)

        print("Moltbot sta partendo...")
        bot.infinity_polling(skip_pending=True)
    except Exception as startup_error:
        print(f"CRASH: {startup_error}")

# Web Service per tenere in vita il bot su Render (Piano Free)
def web_service():
    # Creiamo un'interfaccia minima che risponde sulla porta 10000
    demo = gr.Interface(fn=lambda x: "Moltbot è attivo!", inputs="text", outputs="text")
    demo.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    # Avvia il bot in un thread separato
    threading.Thread(target=avvia_bot, daemon=True).start()
    # Avvia il web service Gradio (blocca il main thread)
    web_service()

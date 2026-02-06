import os
import telebot
import google.generativeai as genai
import io
import threading
import gradio as gr

# 1. RECUPERO CHIAVI
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# 2. CONFIGURAZIONE GOOGLE
genai.configure(api_key=API_KEY)

# MASTER PROMPT (Identità Valeria Cross)
SYSTEM_PROMPT = """
Sei Moltbot, fotografo di alta moda per Valeria Cross.
CARATTERISTICHE SOGGETTO: Valeria Cross, 60 anni, transmaschile, 180cm, 85kg, coppa D. 
LOOK: Capelli grigio platino, occhiali da vista Vogue Havana.
STILE: Vogue Editoriale, 85mm, f/2.8, 8K, watermark 'feat. Valeria Cross 👠' in basso a sinistra.
"""

def avvia_bot():
    # Modelli corretti dal tuo AI Studio
    text_model = genai.GenerativeModel('gemini-flash-latest', system_instruction=SYSTEM_PROMPT)
    # Per le immagini usiamo la classe specifica Imagen
    imagen = genai.GenerativeModel('imagen-3.0-generate-001')
    
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(func=lambda m: True)
    def gestisci_messaggio(m):
        wait_msg = bot.reply_to(m, "📸 Preparo lo scatto... (Imagen 3)")
        try:
            # A. Gemini crea il prompt tecnico
            p_res = text_model.generate_content(f"Crea il prompt perfetto per un'immagine di: {m.text}")
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

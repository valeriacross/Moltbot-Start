import os
import telebot
import google.generativeai as genai
import threading
import time
import gradio as gr

# Recupero le chiavi da Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")

# --- IL CERVELLO DEL FOTOGRAFO (MASTER PROMPT) ---
# Qui ci sono tutte le regole: volto, fisico, stile Vogue e Watermark.
ISTRUZIONI_SISTEMA = """
Sei un assistente per la fotografia di moda. Il tuo compito è generare prompt dettagliati per Imagen 3 rispettando RIGOROSAMENTE queste specifiche:

1. REFERENCE: Se l'utente allega una foto, usala come riferimento assoluto per il volto.
2. SOGGETTO: Valeria Cross. 
   - Volto: 60 anni, italiano, espressione saggia, occhiali ottagonali Vogue Havana, capelli grigio platino mossi (15cm sopra, corti ai lati).
   - Fisico: Transmaschile, 180cm, 85kg, Coppa D, pelle liscia e depilata.
3. STILE FOTOGRAFICO: 
   - Obiettivo 85mm, Apertura f/2.8, ISO 200.
   - Illuminazione: Global Illumination, luce morbida da studio.
   - Dettagli: Pori visibili, texture 8K, Frequency Separation.
4. WATERMARK OBBLIGATORIO: 
   - Ogni immagine deve avere la firma 'feat. Valeria Cross 👠' in basso a sinistra.
   - Stile: Corsivo elegante color champagne, opacità 90%.
5. NEGATIVE PROMPT: No occhiali da sole, no barba lunga, no capelli neri, no distorsioni, no look cartone animato.

Rispondi all'utente confermando la generazione con tono professionale.
"""

def avvia_bot():
    # Configurazione Google (Modello Flash: Veloce, Gratuito e Stabile)
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=ISTRUZIONI_SISTEMA)

    bot = telebot.TeleBot(TOKEN)

    # Pulizia delle vecchie connessioni per evitare errori
    try:
        bot.remove_webhook()
        time.sleep(1)
    except:
        pass

    @bot.message_handler(func=lambda m: True)
    def rispondi(m):
        try:
            # Il bot legge il messaggio dell'utente e risponde usando le istruzioni Vogue
            risposta = model.generate_content(m.text)
            bot.reply_to(m, risposta.text)
        except Exception as e:
            bot.reply_to(m, f"⚠️ Errore: {e}")

    print("--- MOLTBOT È ONLINE ---")
    bot.infinity_polling(skip_pending=True)

# Questo serve solo a tenere sveglio il server su Render
def interfaccia_web(x): return "Il bot è attivo."
threading.Thread(target=avvia_bot, daemon=True).start()
gr.Interface(fn=interfaccia_web, inputs="text", outputs="text").launch(server_name="0.0.0.0", server_port=10000)

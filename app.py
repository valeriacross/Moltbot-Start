import os, telebot, io, threading, time, sys, gradio as gr
from google import genai
from google.genai import types

# --- CONFIGURAZIONE CORE ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL_ID = "nano-banana-pro-preview" 

# --- CARICAMENTO IDENTITÀ MASTER ---
def get_master_face():
    try:
        with open("master_face.png", "rb") as f:
            return types.Part.from_bytes(data=f.read(), mime_type="image/png")
    except Exception as e:
        print(f"⚠️ Nota: master_face.png non trovato. Errore: {e}", flush=True)
        return None

MASTER_FACE = get_master_face()

# MASTER PROMPT: Riscritto per priorità assoluta sull'identità
MASTER_PROMPT = """MANDATORY IDENTITY RULE: 
You are generating VALERIA CROSS, a transmasculine icon. 
IDENTITY: Male Italian face on a female body. THIS CONTRAST IS MANDATORY.

FACE (MANDATORY): 60yo Italian man, silver 15cm hair, white groomed 6cm beard, thin octagonal Havana eyeglasses. 
Deep brown eyes, visible skin pores, and natural aging wrinkles.

BODY (MANDATORY): Female hourglass figure, full breasts (D-cup), 180cm, 85kg. 
The body must be COMPLETELY HAIRLESS (NO chest hair, NO leg hair).

STYLE: High-fashion Vogue Italia editorial. Cinematic warm lighting. 
8K resolution, f/2.8 shallow depth of field.

NEGATIVE (DO NOT GENERATE): Generic male suits, male-coded chests, youthful faces, low quality."""

# --- LOGICA DI GENERAZIONE ---
def generate_valeria(prompt_utente, immagine_utente=None):
    try:
        # Protezione per prompt brevi: se l'utente scrive poco, forziamo il contesto Vogue
        testo_finale = prompt_utente
        if len(prompt_utente) < 10:
            testo_finale = f"{prompt_utente}, posing for a luxury Vogue fashion editorial, high-end couture outfit."

        contents = [MASTER_PROMPT]
        if MASTER_FACE: 
            contents.append(MASTER_FACE)
        if immagine_utente: 
            contents.append(types.Part.from_bytes(data=immagine_utente, mime_type="image/jpeg"))
        
        contents.append(f"SCENE TO RENDER: {testo_finale}")

        # Configurazione con filtri disattivati per permettere l'anatomia di Valeria [cite: 2026-02-08]
        safety = [
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE")
        ]

        response = client.models.generate_content(
            model=MODEL_ID, 
            contents=contents, 
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=safety
            )
        )
        
        if response and response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
        return None
    except Exception as e:
        print(f"❌ Errore Generazione: {e}", flush=True)
        return None

# --- TELEGRAM BOT ---
def avvia_bot():
    try:
        bot = telebot.TeleBot(TOKEN)
        print(f"✅ Bot Valeria Cross Online", flush=True)

        @bot.message_handler(content_types=['photo', 'text'])
        def handle(m):
            try:
                wait = bot.reply_to(m, "💎 Generazione Valeria Cross (Pro Engine)...")
                img_data = None
                if m.content_type == 'photo':
                    f_info = bot.get_file(m.photo[-1].file_id)
                    img_data = bot.download_file(f_info.file_path)
                
                prompt = m.caption if m.content_type == 'photo' else m.text
                risultato = generate_valeria(prompt, img_data)
                
                if risultato:
                    bot.send_photo(m.chat.id, io.BytesIO(risultato), caption="Valeria Cross | Vogue Edition")
                    bot.delete_message(m.chat.id, wait.message_id)
                else:
                    bot.edit_message_text("⚠️ Filtro o errore tecnico. Prova a cambiare prompt.", m.chat.id, wait.message_id)
            except Exception as e:
                print(f"❌ Errore Bot: {e}", flush=True)

        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"💥 Crash Bot: {e}", flush=True)

# --- GRADIO WEB UI ---
def avvia_web():
    def web_interface(prompt):
        img_bytes = generate_valeria(prompt)
        if img_bytes: return io.BytesIO(img_bytes).read()
        return None

    ui = gr.Interface(
        fn=web_interface,
        inputs=gr.Textbox(label="Prompt"),
        outputs=gr.Image(label="Risultato Pro"),
        title="Valeria Cross Web-UI"
    )
    ui.launch(server_name="0.0.0.0", server_port=10000)

if __name__ == "__main__":
    def heartbeat():
        while True:
            print("💓 Heartbeat: Alive", flush=True)
            time.sleep(30)
    
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=avvia_bot, daemon=True).start()
    avvia_web()
        

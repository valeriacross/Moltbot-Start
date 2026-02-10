import os
from google import genai

# Carica la tua chiave
API_KEY = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

def verifica_motori():
    print("--- 🔍 VERIFICA MODELLI DISPONIBILI ---")
    try:
        # Recupera la lista completa dei modelli
        for model in client.models.list():
            # Filtriamo solo quelli che possono generare immagini
            if 'generate_content' in model.supported_generation_methods:
                print(f"Modello ID: {model.name}")
                print(f"Capacità: {model.supported_generation_methods}")
                print(f"Descrizione: {model.description}")
                print("-" * 30)
    except Exception as e:
        print(f"❌ Errore durante il recupero: {e}")

if __name__ == "__main__":
    verifica_motori()

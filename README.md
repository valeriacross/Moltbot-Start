# 🤖 MoltBot 4K - Bot Telegram per Generazione Immagini

Bot Telegram avanzato per la generazione di immagini in qualità 4K utilizzando Google Imagen 4 Ultra con face reference e upscaling intelligente.

## ✨ Nuove Funzionalità

### 🎯 Migliorie Implementate

1. **✅ Face Reference Attiva**
   - Il file `master_face.png` viene ora utilizzato effettivamente nella generazione
   - Supporto per face reference mandatoria su tutte le immagini

2. **🖼️ Immagine di Riferimento Funzionante**
   - Le foto inviate dagli utenti vengono usate come riferimento di stile
   - Supporto simultaneo per face reference + style reference

3. **📏 Upscaling Intelligente**
   - Preserva l'aspect ratio originale
   - Non distorce più le immagini
   - Skip automatico se già in 4K
   - Algoritmo LANCZOS per massima qualità

4. **⚙️ Configurazioni Avanzate**
   - Aspect ratio configurabile: 1:1, 16:9, 9:16, 4:3, 3:4
   - Generazione multipla: 1-4 immagini contemporaneamente
   - Preferenze salvate per utente

5. **🛡️ Rate Limiting**
   - Limite orario: 10 richieste/ora
   - Limite giornaliero: 50 richieste/giorno
   - Protezione automatica anti-spam

6. **📊 Logging Completo**
   - File di log dettagliato (`bot.log`)
   - Tracciamento errori con stack trace
   - Metriche di performance

7. **🎮 Comandi Interattivi**
   - `/start` - Benvenuto
   - `/help` - Guida completa
   - `/settings` - Menu impostazioni con bottoni
   - `/stats` - Statistiche utilizzo
   - `/cancel` - Annulla operazione

8. **🔄 Auto-Recovery**
   - Riavvio automatico in caso di errori
   - Gestione robusta delle eccezioni
   - Resilienza ai crash

9. **🌐 Web Server Migliorato**
   - Endpoint `/` con health check
   - Endpoint `/stats` con statistiche globali
   - JSON response strutturate

10. **💬 Interfaccia Utente Migliorata**
    - Messaggi formattati in HTML
    - Progressi in tempo reale
    - Feedback dettagliato sugli errori

## 🚀 Installazione

### 1. Clona o scarica il codice

```bash
git clone <repository-url>
cd moltbot
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura le variabili d'ambiente

Crea un file `.env` nella root del progetto:

```env
TELEGRAM_TOKEN=il_tuo_token_telegram
GOOGLE_API_KEY=la_tua_api_key_google
PORT=10000
```

**Come ottenere i token:**

- **TELEGRAM_TOKEN**: 
  1. Apri Telegram e cerca `@BotFather`
  2. Invia `/newbot` e segui le istruzioni
  3. Copia il token fornito

- **GOOGLE_API_KEY**:
  1. Vai su [Google AI Studio](https://aistudio.google.com/app/apikey)
  2. Crea un nuovo progetto
  3. Genera una API key

### 4. Aggiungi il file master_face.png

Posiziona il tuo file `master_face.png` nella stessa directory del bot.

**Requisiti:**
- Formato: PNG
- Contenuto: Foto chiara del volto di riferimento
- Qualità: Alta risoluzione consigliata

### 5. Avvia il bot

```bash
python moltbot_optimized.py
```

## 📖 Guida all'Uso

### Comandi Base

| Comando | Descrizione |
|---------|-------------|
| `/start` | Messaggio di benvenuto e introduzione |
| `/help` | Guida dettagliata all'utilizzo |
| `/settings` | Configura aspect ratio e numero immagini |
| `/stats` | Visualizza statistiche personali di utilizzo |
| `/cancel` | Annulla l'operazione corrente |

### Generazione Immagini

**Metodo 1: Solo Testo**
```
Invia semplicemente una descrizione:
"Una ragazza su una spiaggia al tramonto, stile fotografico"
```

**Metodo 2: Con Riferimento Stile**
```
1. Invia una foto
2. Aggiungi una didascalia con la descrizione
```

### Impostazioni

Usa `/settings` per aprire il menu interattivo:

**Aspect Ratio:**
- 1:1 - Quadrato (Instagram)
- 16:9 - Landscape (Desktop)
- 9:16 - Portrait (Stories)
- 4:3 - Classico
- 3:4 - Portrait classico

**Numero Immagini:**
- 1-4 immagini per richiesta

## 🔧 Configurazione Avanzata

### Rate Limiting

Modifica i limiti nel file `moltbot_optimized.py`:

```python
MAX_REQUESTS_PER_HOUR = 10  # Richieste per ora
MAX_REQUESTS_PER_DAY = 50   # Richieste per giorno
```

### Upscaling

Modifica la dimensione target 4K:

```python
def upscale_to_4k(image_bytes, target_size=3840):
    # target_size: larghezza/altezza target in pixel
```

### Prompt Template

Personalizza i prompt mandatori in `generate_image()`:

```python
BODY_MANDATE = """
Modifica qui le tue richieste mandatorie...
"""

NEGATIVE_PROMPTS = """
Aggiungi qui cosa evitare...
"""
```

## 📊 Monitoring

### Log File

Il bot genera un file `bot.log` con tutti gli eventi:

```bash
tail -f bot.log  # Monitora in tempo reale
```

### Endpoint Web

**Health Check:**
```bash
curl http://localhost:10000/
```

**Statistiche Globali:**
```bash
curl http://localhost:10000/stats
```

## 🐛 Troubleshooting

### Problema: "master_face.png non trovato"

**Soluzione:**
- Verifica che il file esista nella stessa directory del bot
- Controlla i permessi di lettura del file

### Problema: "Rate limit raggiunto"

**Soluzione:**
- Attendi il reset del periodo (1 ora o 24 ore)
- Oppure aumenta i limiti nel codice

### Problema: Bot non risponde

**Soluzione:**
1. Verifica che il bot sia in esecuzione
2. Controlla i log: `tail bot.log`
3. Verifica connessione internet
4. Controlla validità del TELEGRAM_TOKEN

### Problema: Errori API Google

**Soluzione:**
1. Verifica validità GOOGLE_API_KEY
2. Controlla quota API su Google Cloud Console
3. Verifica billing attivo su Google Cloud

### Problema: Immagini di bassa qualità

**Soluzione:**
- Sii più specifico nel prompt
- Aggiungi dettagli su stile, illuminazione, atmosfera
- Usa riferimenti di stile quando possibile

## 🔒 Sicurezza

- Le API key sono caricate da variabili d'ambiente (mai hardcoded)
- Rate limiting previene abusi
- Logging per audit trail
- Gestione sicura dei file temporanei

## 📈 Performance

- **Generazione**: ~30-60 secondi per immagine
- **Upscaling**: ~2-5 secondi per immagine
- **Memoria**: ~500MB RAM in idle
- **Banda**: ~10-20MB per immagine 4K

## 🛠️ Deploy su Render

### 1. Crea file `render.yaml`

```yaml
services:
  - type: web
    name: moltbot-4k
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python moltbot_optimized.py
    envVars:
      - key: TELEGRAM_TOKEN
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
      - key: PORT
        value: 10000
```

### 2. Deploy

1. Crea account su [Render](https://render.com)
2. Collega repository GitHub
3. Crea nuovo Web Service
4. Configura variabili d'ambiente
5. Deploy!

## 📝 Changelog

### v2.0.0 (Versione Ottimizzata)

- ✅ Face reference ora funzionante
- ✅ Style reference da immagini utente
- ✅ Upscaling intelligente con preservazione aspect ratio
- ✅ Rate limiting per utente
- ✅ Sistema di logging completo
- ✅ Comandi interattivi (/start, /help, /settings, /stats)
- ✅ Configurazione aspect ratio
- ✅ Generazione multipla (1-4 immagini)
- ✅ Auto-recovery da errori
- ✅ Web server con endpoint stats
- ✅ UI migliorata con HTML formatting
- ✅ Gestione errori robusta

### v1.0.0 (Versione Originale)

- Generazione base con Imagen 4 Ultra
- Upscaling a 3840x3840 (rigido)
- Comando singolo

## 🤝 Contributi

Contributi benvenuti! Per modifiche importanti:

1. Fai fork del repository
2. Crea un branch (`git checkout -b feature/nuova-funzione`)
3. Commit (`git commit -am 'Aggiunge nuova funzione'`)
4. Push (`git push origin feature/nuova-funzione`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è fornito "as-is" senza garanzie.

## 🆘 Supporto

Per problemi o domande:
- Controlla la sezione Troubleshooting
- Consulta i log (`bot.log`)
- Apri una issue su GitHub

## ⚠️ Note Importanti

- **Costi API**: Google Imagen 4 ha costi associati, verifica i prezzi
- **Quota Limits**: Controlla limiti giornalieri su Google Cloud
- **Content Policy**: Rispetta le policy di Google AI e Telegram
- **Privacy**: Non salvare immagini degli utenti senza consenso

## 🎯 Roadmap

- [ ] Database per persistenza preferenze
- [ ] Modalità batch per generazioni multiple
- [ ] Preview a bassa risoluzione prima di 4K
- [ ] Supporto video generation
- [ ] WebUI admin panel
- [ ] Analytics avanzate
- [ ] A/B testing prompts
- [ ] Cache intelligente

---

**Versione:** 2.0.0 Ottimizzata  
**Ultimo aggiornamento:** Febbraio 2026  
**Autore:** MoltBot Team

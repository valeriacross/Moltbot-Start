# 👠 Valeria Cross — Bot Suite

Repository contenente i bot Telegram per la generazione di immagini AI di **Valeria Cross**.

---

## Indice

- [VogueBot](#-voguebot)
- [ArchitectBot](#-architectbot)
- [Infrastruttura comune](#infrastruttura-comune)

---

# 👠 VogueBot

Bot Telegram per la generazione di immagini editoriali fashion di Valeria Cross, a partire da una descrizione testuale o da una foto di riferimento.

## Versione attuale
`5.0.2`

---

## Cosa fa

Riceve una scena descritta in testo (o una foto con didascalia), ottimizza il prompt tramite Gemini Flash (modello testo), e genera un'immagine editoriale 2K di Valeria Cross nella scena richiesta.

---

## Stack tecnico

| Componente | Dettaglio |
|---|---|
| Linguaggio | Python 3.x |
| Framework bot | pyTelegramBotAPI (`telebot`) |
| AI generazione immagini | Google Gemini API (`gemini-3-pro-image-preview`) |
| AI ottimizzazione prompt | Google Gemini API (`gemini-3-flash-preview`) |
| Web server | Flask (per health check su Koyeb) |
| Deployment | Koyeb |
| Threading | `ThreadPoolExecutor` (max 4 worker) |

---

## Variabili d'ambiente richieste

```
TELEGRAM_TOKEN      — Token del bot Telegram
GOOGLE_API_KEY      — Chiave API Google Gemini
PORT                — Porta Flask (default: 10000)
```

---

## File richiesti nella root del progetto

```
master_face.png   — Immagine di riferimento del volto di Valeria Cross.
                    Passata all'API ad ogni generazione come riferimento identità.
                    Se non trovata, il bot funziona senza riferimento volto.
```

---

## Comandi disponibili

| Comando | Funzione |
|---|---|
| `/start` o `/settings` | Pannello formato e quantità foto |
| `/help` | Guida rapida |
| `/info` | Versione, modello, ora server, stato master face |
| `/prompt` | Mostra il Master Identity completo |
| `/lastprompt` | Mostra l'ultimo prompt inviato all'API (debug) |

---

## Formati disponibili

`16:9` `2:3`

Default: `2:3`

Quantità: `1` o `2` foto per generazione.

---

## Come si usa

1. Invia una **descrizione testuale** della scena desiderata, oppure una **foto** con didascalia opzionale come riferimento visivo
2. Il bot ottimizza il prompt tramite `gemini-3-flash-preview` (fase di ~5s)
3. Mostra il **prompt ottimizzato completo** con i pulsanti CONFERMA / ANNULLA
4. Alla conferma, genera le foto in **risoluzione 2K** e le invia come documenti `.jpg`

---

## Struttura del prompt

Il prompt finale è costruito in due fasi:

### Fase 1 — Ottimizzazione testuale
Il testo utente viene passato a `gemini-3-flash-preview` in modalità testo con un system prompt che:
- Estrae solo gli elementi visivi (scena, ambiente, luce, posa, outfit, mood)
- Integra **integralmente** il Master Identity di Valeria Cross in forma narrativa fluida
- **Traduce sempre in inglese** (regola 9 del system prompt)
- Produce un prompt **completo e autosufficiente** — utilizzabile su qualsiasi motore esterno senza modifiche
- Riscrive tutto in linguaggio editoriale fashion neutro (niente termini anatomici espliciti)
- Forza il formato (AR) richiesto
- Vieta frasi tipo "FILTER BYPASS" o "SAFETY OVERRIDE"
- `max_output_tokens`: 2500

### Fase 2 — Generazione immagine
Il prompt ottimizzato viene passato a `gemini-3-pro-image-preview` in modalità `IMAGE` con:
- `master_face.png` come riferimento identità
- Foto allegata dall'utente come riferimento visivo (se presente)
- Risoluzione: `image_size="2K"`
- Safety settings: `BLOCK_NONE` su tutte le categorie
- `response_modalities: ["IMAGE"]`

### Fallback
Se l'ottimizzazione fallisce (timeout 30s o errore API), il bot usa direttamente `MASTER_IDENTITY + testo utente` come prompt grezzo e avvisa l'utente con "⚠️ Ottimizzazione non disponibile".

---

## Master Identity

Il blocco identità fisso di Valeria Cross integrato in ogni prompt:

```
IDENTITY: Nameless Italian transmasculine editorial figure.
BODY: Sculptural hourglass silhouette, generous haute couture décolleté, 180cm.
      Flawlessly smooth porcelain skin, impeccable editorial finish.
FACE: Strong Italian male face, ~60yo. Ultra-detailed skin texture.
EXPRESSION: calm, half-smile, NO teeth. EYES: dark brown/green.
BEARD: light grey/silver, groomed, 6–7cm.
GLASSES: MANDATORY thin octagonal Vogue frames, Havana dark tortoiseshell.
HAIR: Light grey/silver, short Italian cut, voluminous. Nape exposed.
RENDERING: 85mm, f/2.8, ISO 200, 1/160s. SSS, GI, Fresnel. Natural bokeh.
WATERMARK: 'feat. Valeria Cross 👠' (champagne, bottom center/left, small).
NEGATIVE: female/young face, long hair, ponytail, hair touching neck/shoulders.
```

---

## Sanitizzazione prompt

Prima della generazione, il prompt viene sanitizzato:
- Rimozione righe contenenti: `FILTER BYPASS`, `BYPASS ACTIVATED`, `NO OBSCURED FEATURES`, `SAFETY OVERRIDE`, `IGNORE SAFETY`, `DISABLE FILTER`
- Sostituzione di `{` `}` `[` `]` con parentesi tonde

---

## Funzionalità chiave

### Ottimizzazione prompt in thread
L'ottimizzazione gira in un thread separato con timeout di 30 secondi — il bot rimane reattivo.

### Due modelli separati
`gemini-3-flash-preview` per ottimizzazione testo (veloce, economico), `gemini-3-pro-image-preview` per generazione immagini. Il modello immagini non viene mai usato per testo.

### /lastprompt
Salva l'ultimo prompt inviato all'API per ogni utente. Utile per debug in caso di blocchi (`IMAGE_OTHER`, `IMAGE_SAFETY`, ecc.).

### Logging
```
🟢  Avvio bot
📋  /settings
✏️  Input utente
✅  Prompt ottimizzato (con chars)
🚀  Generazione avviata
🎨  Singolo scatto in corso
✅  Scatto inviato (con tempo)
❌  Errori
⚠️  Warning
```

---

## Note operative

- **Una sola istanza attiva** — due istanze causano errore 409. In caso di redeploy, attendere che la vecchia istanza sia terminata.
- Il bot usa `uid` (user ID) per lo stato per-utente.
- Blocchi comuni: `IMAGE_OTHER` (falso positivo del modello, cambiare immagine), `IMAGE_SAFETY` (combinazione scena/outfit giudicata borderline, riprovare o modificare la scena).
- Generazione tipica: 20–35s per immagine a 2K.

---

## Cronologia versioni

| Versione | Novità |
|---|---|
| 4.0.1 | Base funzionante, error handling iniziale |
| 4.1–4.2 | Fix IMAGE_SAFETY, fix MALFORMED_FUNCTION_CALL |
| 4.3.0 | Smart Prompt: ottimizzazione testuale prima della generazione |
| 4.4.x | Selettore modello multi-engine (poi rimosso) |
| 4.5.0 | Codice ripulito, aggiunto /lastprompt |
| 5.0.0 | Migrazione a `gemini-3-pro-image-preview`, risoluzione 2K |
| 5.0.1 | Modello ottimizzazione separato (`gemini-3-flash-preview`), regola traduzione in inglese (regola 8) |
| 5.0.2 | System prompt ottimizzazione riscritto: prompt completo e autosufficiente, NON abbreviare MASTER IDENTITY, `max_output_tokens` → 2500 |

---
---

# 🏛️ ArchitectBot

Bot Telegram per la generazione di **Master Prompt** ottimizzati per diversi motori AI di generazione immagini, a partire da testo o da una foto di riferimento.

## Versione attuale
`7.0.0`

---

## Cosa fa

Riceve un testo descrittivo o una foto, e genera un Master Prompt professionale ottimizzato per il motore AI scelto (ChatGPT, Gemini, Grok, Qwen, Meta). Il prompt integra il DNA di Valeria Cross espanso inline (mai il nome "Valeria Cross" nell'output) e viene adattato al livello di restrizioni del motore target.

Il prompt generato è **esportabile** — può essere copiato e usato direttamente su qualsiasi piattaforma di generazione immagini.

---

## Stack tecnico

| Componente | Dettaglio |
|---|---|
| Linguaggio | Python 3.x |
| Framework bot | pyTelegramBotAPI (`telebot`) |
| AI generativa | Google Gemini API (`gemini-3-flash-preview`) |
| Web server | Flask (per health check su Koyeb) |
| Deployment | Koyeb |
| Threading | `ThreadPoolExecutor` (max 4 worker) |

---

## Variabili d'ambiente richieste

```
TELEGRAM_TOKEN_ARCHITECT    — Token del bot Telegram
GOOGLE_API_KEY              — Chiave API Google Gemini
```

---

## Comandi disponibili

| Comando | Funzione |
|---|---|
| `/start` o `/reset` o `/motore` | Seleziona il motore target e azzera lo stato |
| `/help` | Guida rapida |
| `/info` | Versione, motore attuale |

---

## Motori disponibili

| Label | Motore | Profilo restrizioni |
|---|---|---|
| 🤖 ChatGPT | OpenAI | Molto restrittivo — linguaggio editoriale puro |
| ✨ Gemini | Google | Medio — artistico/fotografico |
| 🦁 Grok | xAI | Permissivo — linguaggio diretto |
| 🧠 Qwen | Alibaba | Restrittivo — neutro culturale |
| ♾️ Meta | Meta AI | Medio — editoriale cinematografico |

---

## Come si usa

### Da testo
1. `/motore` → scegli il motore target
2. Invia la descrizione della scena
3. Il bot genera e invia il Master Prompt ottimizzato
4. Puoi riadattarlo per un altro motore senza reinserire la scena

### Da immagine (Vision mode)
1. `/motore` → scegli il motore target
2. Invia una **foto** con didascalia opzionale
3. Gemini analizza la scena (ambiente, luce, posa, outfit, mood) e genera il Master Prompt sostituendo il soggetto con il DNA di Valeria Cross

---

## Struttura del prompt generato

Ogni Master Prompt contiene:

```
1. Apertura fissa:
   "EXACTLY matching the face, head, hair, beard and glasses
    from the provided reference image."

2. Integrazione scena utente + DNA Valeria Cross espanso inline
   (MAI scrivere "Valeria Cross" o "DNA of Valeria Cross" nell'output)

3. Auto-review: secondo passaggio API che corregge contraddizioni
   (hair bleed, negative conflicts, ecc.)

4. Negative prompts:
   "young female face, long dark hair, no beard,
    obscured face, low quality, 1:1 ratio"
```

---

## Adattamento per motore (ENGINE_PROFILES)

Dopo la generazione, il testo viene post-processato con:

### Sostituzioni (case-insensitive regex)
Termini anatomici o espliciti vengono sostituiti con equivalenti editoriali in base al profilo del motore. Esempio per ChatGPT:
```
"breasts"  →  "editorial décolleté"
"Cup D"    →  "generous haute couture silhouette"
"hairless" →  "flawlessly smooth porcelain skin"
"naked"    →  "nude-effect editorial bodysuit"
```

### Rimozione righe vietate
Righe contenenti termini nella lista `forbidden` del motore vengono rimosse completamente.

---

## Pulizia output

La funzione `clean_output()` rimuove le frasi introduttive tipiche di Gemini:
`"Ok, here is"`, `"Here's"`, `"Sure"`, `"Certainly"`, `"Below is"`, ecc.
Il prompt inizia direttamente con il contenuto utile.

---

## Riadattamento motore

Dopo ogni generazione, il bot offre i pulsanti per riadattare lo stesso prompt per un altro motore — senza reinserire la scena. Il bot salva l'ultimo input (testo o immagine) per ogni utente.

---

## Logging

```
🟢  Avvio bot
🔄  /start e reset
⚙️  Selezione motore
✏️  Input testo
🖼️  Foto ricevuta
🚀  execute_generation chiamata
📤  Chiamata API in corso
✅  Risposta ricevuta (con chars)
✅  Prompt generato e adattato
❌  Errori API o generazione
```

---

## Note operative

- **Una sola istanza attiva** — due istanze causano errore 409.
- Il bot usa `uid` per lo stato per-utente.
- Le generazioni girano in thread separati — il polling non si blocca mai.
- Il modello usato è `gemini-3-flash-preview` (testo), mai il modello immagini.

---

## Cronologia versioni

| Versione | Novità |
|---|---|
| 5.4 | Base funzionante, generazione prompt testo |
| 5.5 | Fix bug uid/cid, fix html.escape |
| 6.0 | ENGINE_PROFILES: adattamento per motore |
| 6.1 | Vision mode: generazione prompt da immagine |
| 6.20 | Fix critico: execute_generation in ThreadPoolExecutor |
| 6.21 | Fix execute_generation orfana, logging dettagliato |
| 7.0.0 | Migrazione a `gemini-3-flash-preview`, DNA expansion inline, auto-review secondo passaggio |

---
---

## Infrastruttura comune

### Deployment — Koyeb
Tutti i bot girano su Koyeb come servizi separati. Ogni bot espone un endpoint Flask su `/` che risponde con la stringa versione — usato da Koyeb come health check.

### Errore 409 — Conflict
Se appare `Error code: 409: Conflict: terminated by other getUpdates request`, significa che ci sono due istanze dello stesso bot in polling simultaneo. Soluzione: verificare su Koyeb che sia attiva una sola istanza per bot. In alternativa, forzare la pulizia del webhook:
```
https://api.telegram.org/botTOKEN/deleteWebhook?drop_pending_updates=true
```

### Model ID corretti (aggiornati febbraio 2026)

| Uso | Model ID |
|---|---|
| Generazione immagini (alta qualità) | `gemini-3-pro-image-preview` |
| Generazione immagini (veloce) | `gemini-2.5-flash-image` |
| Testo avanzato | `gemini-3-pro-preview` |
| Testo veloce / ottimizzazione | `gemini-3-flash-preview` |

### Risoluzione immagini
Parametro supportato: `image_config=genai_types.ImageConfig(image_size="2K")`
Valori: `"1K"` (default), `"2K"`, `"4K"`. La K maiuscola è obbligatoria.
VogueBot, ClosetBot e ValeriaFX usano tutti `"2K"`.

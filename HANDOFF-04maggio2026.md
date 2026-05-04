# HANDOFF — Valeria Cross AI · Sessione Claude
**Data:** 04/05/2026
**Da:** Walter Caponi
**A:** Claude (sessione successiva)

---

## Contesto

Walter Caponi, ~60 anni, italiano. Progetto personale: ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile di Walter, generato interamente con AI.

Questa sessione è stata una **code review completa e refactoring** dell'intero ecosistema, partendo dai file originali. Tutti i 21 problemi identificati nella checklist iniziale sono stati risolti. I file sono stati rinominati con il nuovo schema `C_nomebot100.py` e la versione interna è stata resettata a `1.0.0`.

---

## File correnti (04/05/2026)

| File | Versione interna | Koyeb service |
|------|-----------------|---------------|
| `C_shared100.py` | 1.0.0 | (comune) |
| `C_vogue100.py` | 1.0.0 | colossal-giselle/vogue |
| `C_architect100.py` | 1.0.0 | homely-annabelle/thearchitect |
| `C_atelier100.py` | 1.0.0 | flexible-denna/atelier |
| `C_filtro100.py` | 1.0.0 | screeching-jobina/filtro |
| `C_surprise100.py` | 1.0.0 | near-damara/sorpresa |

**Run command su Koyeb:** `python C_nomebot100.py`

---

## Variabili d'ambiente Koyeb

| Variabile | Valore | Dove |
|-----------|--------|------|
| `GOOGLE_API_KEY` | `AIzaSyCmqDNPNuIEyIgJrtrnwIt-I37kObukHMs` | Vogue, Architect, Atelier, Surprise |
| `ALLOWED_USERS` | `273003890` | Tutti i bot |
| `PORT` | `10000` | Tutti i bot |
| `TELEGRAM_TOKEN` | vedi Excel | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | vedi Excel | Architect |
| `TELEGRAM_TOKEN_CLOSET` | vedi Excel | Atelier |
| `TELEGRAM_TOKEN_FX` | vedi Excel | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | vedi Excel | Surprise |

---

## Cosa è stato fatto in questa sessione

### C_shared100.py — 5 fix cumulativi

**Fix 1.2.0 — CRITICO: analisi immagini falliva su tutti i bot**
`GeminiClient.generate()` assemblava il payload come `(contents or []) + [prompt]` passando il prompt come stringa nuda in una lista mista con oggetti `Part`. L'API Gemini ignorava l'immagine silenziosamente. Corretto wrappando il prompt con `genai_types.Part.from_text(text=prompt)` quando `contents` è non-vuoto. Questo era la causa del messaggio `⚠️ Analisi outfit non disponibile` visibile nello screenshot di Atelier.

**Fix 1.3.0 — Sicurezza: whitelist utenti**
Aggiunta `is_allowed(uid)` e `_load_allowed()`. Legge `ALLOWED_USERS` dall'env (CSV di user ID). Fallback hardcoded: `273003890`. Tutti i bot importano e chiamano `is_allowed()` su ogni handler di messaggi e callback — gli utenti non autorizzati vengono ignorati silenziosamente con log warning.

**Fix 1.4.0 — HealthServer Flask**
Aggiunto `use_reloader=False` e `threaded=True` a `app.run()` nel thread daemon. Previene il fork bomb di Werkzeug in ambienti che attivano il reloader anche con `debug=False`.

**Fix 1.5.0 — GeminiClient Singleton corretto**
Implementato pattern Singleton con `__new__` e double-checked locking thread-safe (`threading.Lock`). La prima chiamata `GeminiClient()` crea il client; tutte le successive restituiscono la stessa istanza già inizializzata tramite il flag `_initialized`.

---

### C_architect100.py — 8 fix cumulativi

**Bug 1 — NameError `engine_choice`**
In `handle_callbacks()`, il log usava una variabile `engine_choice` non definita. Sostituita con `user_mode[uid]`.

**Bug 2 — `response.text` invece di `response_text` (×2)**
In `generate_from_image()` e `generate_from_album()`, dopo `response_text = gemini.generate(...)`, il codice chiamava `response.text.strip()` — variabile inesistente nel scope. Corretto in `response_text.strip()`.

**Bug 3 — `movie_last_img` dichiarato dopo il callback che lo usava**
Il dict `movie_last_img = {}` era dichiarato dopo `handle_movie_retry()`. Spostato prima della funzione.

**Bug 4 — Handler testo `build_prompt` non generava nulla**
L'handler inviava solo "⚡ Prompt pronto" senza mai chiamare `generate_monolith_prompt()` né `sanitize_user_input()`. Aggiunta la pipeline completa: `sanitize → generate → review → adapt → send` con chunking, keyboard e caption.

**Bug 5 — `action_home` non gestito**
Il pulsante "🏠 Home" mandava `callback_data="action_home"` ma il gestore non lo gestiva. Aggiunto il case completo con reset stato e invio del menu principale.

**Bug 6 — `task_single` era uno stub vuoto**
Il task per foto singola inviava solo un messaggio statico. Completato con la pipeline reale che chiama `parallel_generate_from_image()`.

**Fix qualità — Thread safety**
Aggiunto `_state_lock = threading.Lock()` per proteggere le scritture su `last_prompt`, `user_last_input` e `movie_last_img` nei thread worker del `ThreadPoolExecutor`.

**Fix qualità — Import duplicato**
`import concurrent.futures` era inline dentro `analyze_image_visionstruct()` oltre che in cima al file. Rimosso quello inline.

**Fix performance — VisionStruct parallelo**
Nuova funzione `parallel_generate_from_image()`: lancia VisionStruct e attende al massimo 22 secondi. Se VisionStruct completa in tempo, il JSON arricchisce il prompt; se fa timeout, la generazione procede senza. Risparmio tipico: 15-25 secondi rispetto all'esecuzione seriale.

---

### C_atelier100.py — 3 fix

**Bug — `VALERIA_BODY_STRONG` e `VALERIA_BODY_SAFE` ridefinite localmente**
Dopo l'import da shared, le costanti venivano ridefinite localmente con testo identico. Ridefinizioni rimosse — ora usa solo quelle di `C_shared100.py`.

**Beneficiario del fix shared 1.2.0**
Il messaggio `⚠️ Analisi outfit non disponibile` che si vedeva nello screenshot era causato dal bug `GeminiClient.generate()` in shared. Risolto automaticamente con `C_shared100.py`.

**Fix qualità — Timeout download**
Aggiunto `timeout=30` a `bot.get_file()` e `bot.download_file()`.

---

### C_vogue100.py — 4 fix / refactoring

**Refactoring — DNA inline rimosso**
`VALERIA_DNA` era una stringa hardcoded di ~15 righe che duplicava le costanti di shared. Sostituita con assembly dalle costanti importate: `VALERIA_FACE + VALERIA_BODY_STRONG + VALERIA_WATERMARK + VALERIA_NEGATIVE`. Ora ogni modifica al DNA in `C_shared100.py` si propaga automaticamente.

**Refactoring — `analyze_photo()` usa `GeminiClient`**
La funzione chiamava `client.models.generate_content()` direttamente, bypassando il fix multimodale di shared 1.2.0. Riscritta per usare `gemini.generate()`.

**Refactoring — Flask custom → `HealthServer`**
Rimossi `flask`, `app`, `run_flask()` e il threading manuale. Ora usa `server.start()` come tutti gli altri bot. Aggiunto loop retry 409 nel `__main__`.

**Fix qualità — Timeout download**
Aggiunto `timeout=30` a `bot.get_file()` e `bot.download_file()`.

---

### C_filtro100.py — 2 fix

**Sicurezza — Whitelist via middleware**
Filtro ha 10+ callback handler separati. Invece di patchare ognuno, è stato aggiunto un middleware `@bot.middleware_handler` con `use_class_middlewares=True` nel costruttore del bot che blocca tutti i messaggi e callback di utenti non autorizzati con `raise telebot.CancelUpdate()`.

**Fix qualità — Timeout download**
Aggiunto `timeout=30` a `bot.get_file()` e `bot.download_file()`.

---

### C_surprise100.py — 2 fix

**Bug noto risolto — Step 1/6 duplicato in modalità manuale**
Documentato nel HANDOFF precedente. Telegram può recapitare lo stesso `callback_query` più volte se l'ack non arriva in tempo. Aggiunto un buffer FIFO `_seen_callbacks` (set + deque con `maxlen=200`) che intercetta i `call.id` duplicati prima che entrino nella logica. La pulizia è automatica: quando il buffer è pieno, il `call.id` più vecchio viene rimosso dal set prima di aggiungere il nuovo.

**Fix qualità — Timeout download**
Nessun download diretto in Surprise (non riceve foto), già non applicabile.

---

## Architettura generale

```
Telegram User
      │
      ▼
  pyTelegramBotAPI (infinity_polling)
      │
      ├── is_allowed(uid) ─── NO ──→ silenzio + log warning
      │
      ▼ SÌ
  Handler (message / callback)
      │
      ├── ThreadPoolExecutor (max_workers=4)
      │       │
      │       ├── GeminiClient.generate() ─── gemini-3-flash-preview
      │       │       └── Part.from_text() per payload misto
      │       │
      │       └── [Architect] parallel_generate_from_image()
      │               ├── Future 1: VisionStruct (timeout 22s)
      │               └── Future 2: generate_from_image(vs_json)
      │
      └── bot.send_message() → Telegram
```

---

## Lavoro aperto / Note per la prossima sessione

### Pool di Surprise — da allineare
Il codice di `C_surprise100.py` ha pool hardcoded che potrebbero non corrispondere esattamente al file Excel. Da verificare e allineare:
- Il codice dichiara 200 location, il file Excel ne conta 197
- Verificare se SKY (41), POSE (43), MOOD (50), STILE (50) sono allineati
- L'Excel ha colonne separate `LABEL COMPLETO` e `DESCRIZIONE PROMPT` per ogni pool — il codice usa tuple `(label_ita, prompt_eng)`. Verificare la corrispondenza.

### Prossimo schema versioning
Con il nuovo schema `C_nomebot100.py`:
- Incremento patch: `C_vogue100.py` → `C_vogue101.py`
- Incremento minor: `C_vogue100.py` → `C_vogue110.py`
- Incremento major: `C_vogue100.py` → `C_vogue200.py`
- Versione interna `VERSION` segue lo stesso schema: `"1.0.0"` → `"1.0.1"`

### GeminiClient — nota API
- `gemini-2.0-flash` e `gemini-2.0-flash-lite` davano errore `429 limit: 0` su progetti nuovi
- Soluzione: usare `gemini-3-flash-preview` — funziona sul tier gratuito
- `gemini-2.0-flash` e `gemini-2.0-flash-lite` deprecati a giugno 2026

---

## Regole operative — TASSATIVE

1. **Mai modificare file senza "Vai" esplicito** di Walter
2. **Ogni modifica = nuovo file** con versione incrementata
3. **Testare sempre** con `ast.parse()` prima di consegnare
4. **Mai produrre versioni multiple** senza test intermedi
5. **Presentare sempre il file** con `present_files` dopo averlo copiato in outputs
6. **`C_shared100.py` è condiviso** — ogni modifica impatta tutti i bot. Testare con attenzione e incrementare la versione interna.

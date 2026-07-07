# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 07/07/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb | Chiavi |
|-----|------|---------|-------|--------|
| VogueBot | `Vogue_200.py` | 2.0.0 | colossal-giselle/vogue | 2 |
| ArchitectBot | `Architect_202.py` | 2.0.2 | homely-annabelle/thearchitect | 1 |
| AtelierBot | `Atelier_203.py` | 2.0.3 | flexible-denna/atelier | 5 |
| FiltroBot | `Filtro_200.py` | 2.0.0 | screeching-jobina/filtro | 1 |
| SurpriseBot | `Surprise_200.py` | 2.0.0 | surprise1/sorpresa | 1 |

**Shared:** `C_shared100.py` v2.3.17 · **10 API key totali**

---

## Struttura file

```
C_shared100.py       # Libreria condivisa
Vogue_200.py         # Analisi foto/testo → prompt Flow
Architect_202.py     # Prompt testo/foto → editoriale · /generico (prompt neutro)
Atelier_203.py       # Outfit analysis → prompt con filtri (filtro persistente)
Filtro_200.py        # 7 categorie + LEGO + Mosaic + Scarabocchio
Surprise_200.py      # Location + outfit random + /pride + /flag
requirements.txt
README.md
```

---

## Call Gemini per bot

| Bot | Call/foto | Caption | Extra |
|-----|-----------|---------|-------|
| Atelier | 2 | `/caption` on-demand | — |
| Vogue | 2 | `/caption` on-demand | — |
| Architect | 1-2 | nessuna | `/generico` (1 call) |
| Filtro | 1 | `/caption` on-demand | — |
| Surprise | 1 | nessuna | — |

---

## Contatori chiave

Ogni bot con `on_key_use` mostra `🔑 Key N · call #N` ad ogni chiamata Gemini — contatore PER CHIAVE, non globale. Si azzera:
- Automaticamente ogni giorno alle **08:00 ora di Lisbona** (07:00 UTC)
- Su `/start` (Atelier, Vogue)
- Al riavvio del servizio Koyeb

---

## Dipendenze

```
pyTelegramBotAPI==4.34.0
flask==3.1.3
Pillow>=12.2.0
google-genai>=2.6.0
openpyxl>=3.1.5
```

---

## Variabili d'ambiente (Koyeb)

| Variabile | Descrizione |
|-----------|-------------|
| `TELEGRAM_TOKEN` | VogueBot |
| `TELEGRAM_TOKEN_ARCHITECT` | ArchitectBot |
| `TELEGRAM_TOKEN_CLOSET` | AtelierBot |
| `TELEGRAM_TOKEN_FX` | FiltroBot |
| `TELEGRAM_TOKEN_SORPRESA` | SurpriseBot |
| `GOOGLE_API_KEY` (+_2, +_3, +_4) | Chiavi Gemini — quantità varia per bot |
| `ALLOWED_USERS` | `273003890` |
| `PORT` | `10000` |

---

## Fix robustezza (20/06/2026 → 07/07/2026)

Audit completo il 20/06, fix puntuali il 25/06 e 27/06. Modifiche principali: reset giornaliero contatori reso resiliente (shared 2.3.12), `analyze_scene()` ora cattura prop interattivi con campo dedicato `PROPS & ACTIONS` (shared 2.3.13), 5ª chiave API aggiunta per Atelier (shared 2.3.14), rimozione ratio/count e miglioramento fedeltà scena in Atelier (202). Su Architect, fix `/generico` in due passaggi: la versione 201 (25/06) era preventiva ma non centrata sulla causa reale; la 202 (27/06) ha individuato e corretto la causa effettiva — `task_generico` allegava bottoni post-prompt fuori contesto tramite `send_prompt()`. Il 01/07: pulizia documentale — requirements (README/xlsx/requirements.txt) riallineati, commento obsoleto corretto in shared (2.3.15). Il 04/07: modello Gemini aggiornato da `gemini-3-flash-preview` a `gemini-3.5-flash` (shared 2.3.16) per risolvere 503 diffusi legati ai limiti del livello preview; corrette 3 assegnazioni chiave errate su Koyeb (Atelier/Surprise/Filtro condividevano/scambiavano chiavi per errore, ora ciascuno ha la propria su progetto Google Cloud distinto). Il 07/07, in due step concordati con Walter dopo test su Atelier con foto a body art elaborato: **step 1** — Atelier (203), blocco "OUTFIT DETAIL LOCK" per contrastare la semplificazione di outfit elaborati, verificato con esito positivo su prova pratica; **step 2** — shared (2.3.17), nuovo campo `BODY ART` in `_ANALYZE_PROMPT` e clausola condizionale "BODY ART EXCEPTION" in `VALERIA_BODY_STRONG`/`SAFE` che permette a tatuaggi/body paint descritti di sostituire la pelle liscia di default solo sulle zone indicate — tocca tutti e 5 i bot. Dettagli in `HANDOFF-MASTER`, sezioni 2bis, 2ter, 2quater, 2quinquies, 2sexies e 2septies.

**TODO aperto:** il contatore `🔑 Key N · call #N` mostrato dai bot è in realtà globale (somma di tutte le chiavi), non per-chiave come il nome suggerisce — bug noto in `C_shared100.py`, lasciato volutamente intatto finora su scelta esplicita di Walter. Da correggere in una prossima sessione.

**TODO aperto (04/07):** le stringhe `/info` dei 5 bot mostrano ancora `gemini-3-flash-preview` (Vogue `MODEL_TEXT`, Filtro `MODEL_TEXT_ID`, testo inline in Architect/Atelier/Surprise) nonostante il motore reale sia passato a `gemini-3.5-flash` in shared 2.3.16 — sono costanti locali ai singoli bot, non lette da `C_shared100.py`. Da allineare al prossimo giro di modifiche sui bot, insieme all'incremento di versione file per ciascuno.

**TODO aperto (07/07):** shared 2.3.17 (campo BODY ART + eccezione pelle) non ancora verificato con una prova pratica — Walter deve testarlo su Atelier con la stessa foto di riferimento (tatuaggi/body paint) usata per validare lo step 1, prima di considerarlo definitivo.

## Nota tecnica importante

`review_and_fix()` in C_shared ha un prompt di sistema interno che **forza** il DNA Valeria Cross (viso, corpo, watermark). Non usarla per task che richiedono di rimuovere o alterare quel DNA — usare `gemini.generate()` direttamente con un prompt dedicato (vedi `/generico` in Architect come esempio).

---

## Comandi per bot

### VogueBot
`/start` · `/info` · `/shared` · `/dna` · `/caption`

### ArchitectBot
`/start` · `/help` · `/info` · `/lastprompt` · `/generico` · `/shared`

### AtelierBot
`/start` · `/help` · `/info` · `/lastprompt` · `/caption` · `/shared`

### FiltroBot
`/start` · `/filtro` · `/help` · `/info` · `/lastprompt` · `/caption` · `/mosaic` · `/done` · `/shared`

### SurpriseBot
`/start` · `/flag` · `/pride` · `/help` · `/info` · `/shared` · `/lastprompt`

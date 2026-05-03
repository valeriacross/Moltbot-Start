# HANDOFF — Valeria Cross AI · Ecosistema Bot Telegram
**Data:** 03/05/2026
**A:** Claude (sessione successiva)
**Da:** Walter Caponi

---

## Contesto

Walter Caponi, ~60 anni, italiano. Progetto personale: ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile di Walter, generato interamente con AI.

---

## Identità Valeria Cross

- **Chi è:** Walter Caponi, 60 anni, italiano
- **Occhiali:** Vogue Havana ottagonali — SEMPRE presenti
- **Barba:** argento, 6-7 cm
- **Corpo:** femminile, 180 cm, 85 kg, D-cup, hourglass, pelle liscia
- **Watermark:** `feat. Valeria Cross 👠` — corsivo, champagne, bottom center

---

## Versioni correnti (03/05/2026)

| Bot | Versione | File | Koyeb |
|-----|----------|------|-------|
| VogueBot | **7.1.3** | `vogue-713.py` | colossal-giselle/vogue |
| ArchitectBot | **9.0.0** | `architect-900.py` | homely-annabelle/thearchitect |
| ATELIER | **4.0.1** | `atelier-401.py` | flexible-denna/cabina |
| Filtro | **6.0.0** | `filtro-600.py` | screeching-jobina/valeriafx |
| SURPRISE | **5.0.7** | `surprise-507.py` | near-damara/sorpresa |
| ~~SorpresaBot~~ | **DISMESSA** | — | — |

---

## Infrastruttura

- **Deploy:** Koyeb — Flask health check porta **10000**
- **Generazione immagini:** Flow (Google Labs) + NanoBanana 2 — **nessun bot genera immagini**
- **Modello AI:** `gemini-3-flash-preview` (Vogue + Atelier + Surprise) — tier gratuito Google AI Studio
- **GOOGLE_API_KEY:** presente su Vogue, Atelier e Surprise — **NON su Filtro**
- **Repository GitHub:** github.com/valeriacross/Moltbot-Start (deploy Koyeb)

---

## Regole operative — TASSATIVE

1. **Mai modificare file senza "Vai" esplicito** di Walter
2. **Ogni modifica = nuovo file** con versione incrementata (es. `vogue-713.py` → `vogue-714.py`)
3. **Testare sempre prima di consegnare** — usare test con mock
4. **Mai produrre versioni multiple** senza test intermedi
5. **Presentare sempre il file** con `present_files` dopo averlo copiato in `/mnt/user-data/outputs/`

---

## Dettaglio bot

### VogueBot 7.1.3
- Analizza foto o testo → genera prompt Flow-ready con DNA Valeria
- Modello: `gemini-3-flash-preview`
- Keyboard post-prompt: **📸 Nuova foto** · **🔁 Riusa prompt** · **🏠 Home**
- Formato AR rimosso — scelta fatta direttamente su Flow
- Token env: `TELEGRAM_TOKEN`

### ArchitectBot 9.0.0
- Genera prompt per Flow/ChatGPT/Grok/Qwen/Meta
- Google AI solo per analisi testo/foto — nessuna generazione immagini
- Token env: `TELEGRAM_TOKEN_ARCHITECT` (verificare)

### ATELIER 4.0.1
- Genera prompt editoriali da foto outfit di riferimento
- Modello: `gemini-3-flash-preview`
- Fix 4.0.1: aggiunti `from google import genai`, `from google.genai import types as genai_types`, `API_KEY`, `client` — mancavano per errore
- Token env: `TELEGRAM_TOKEN_CLOSET`

### Filtro 6.0.0
- Applica filtri stilistici a foto, include `/mosaic` (2-9 foto)
- Nessuna Google API

### SURPRISE 5.0.7
- Genera scenari editoriali random da pool fissi
- Modello: `gemini-3-flash-preview` (caption via Gemini — come Atelier)
- Pool: 200 location (🇮🇹→🇵🇹→EU→Mondo) · 100 outfit · 50 stili · 50 pose · 50 sky · 50 mood
- Location pool: label in **italiano**, prompt per Flow in **inglese**
- Flusso: Auto o Manuale → scena → caption Gemini → **📋 Prompt Flow** + **🏠 Home** → prompt → **🎲 Nuova scena**
- 5.0.3: keyboard semplificata, "Annulla" → "🏠 Home", rimosso handler ridondante
- 5.0.7: caption generata da Gemini, aggiunti `google-genai`, `client`, `API_KEY`
- **BUG APERTO:** passo 1/6 duplicato in modalità manuale — retry Telegram non risolto. Non toccare senza test mock funzionante.
- Token env: `TELEGRAM_TOKEN_SORPRESA`

---

## Lavoro sessione 03/05/2026

- **Atelier 4.0.1:** fix `client is not defined` — aggiunti import Google genai mancanti
- **Vogue 7.1.1 → 7.1.2 → 7.1.3:** cambio modello (flash → flash-lite → gemini-3-flash-preview), rimosso AR, aggiunta keyboard post-prompt
- **Surprise 5.0.3 → 5.0.7:** keyboard semplificata, caption locale poi migrata a Gemini, aggiunti google-genai/client/API_KEY
- **XLSX:** aggiornato a `Telegram_Bot_updated-5.xlsx`
- **Repository GitHub:** valeriacross/Moltbot-Start aggiornato con tutte le versioni finali
- **Memorie Claude:** aggiornate (6 voci)

---

## Note Google API

- La chiave `AIzaSy...kHMs` è la **Default Gemini API Key** del progetto `gen-lang-client-0992880992` creato il 03/05/2026 su AI Studio — tier gratuito
- `gemini-2.0-flash` e `gemini-2.0-flash-lite` davano `429 limit: 0` — anomalia quota progetto nuovo
- Soluzione: usare `gemini-3-flash-preview` come Atelier — funziona
- `gemini-2.0-flash` e `gemini-2.0-flash-lite` deprecati a giugno 2026

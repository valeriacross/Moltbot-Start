# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 27/06/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb | Chiavi |
|-----|------|---------|-------|--------|
| VogueBot | `Vogue_200.py` | 2.0.0 | colossal-giselle/vogue | 2 |
| ArchitectBot | `Architect_202.py` | 2.0.2 | homely-annabelle/thearchitect | 1 |
| AtelierBot | `Atelier_202.py` | 2.0.2 | flexible-denna/atelier | 5 |
| FiltroBot | `Filtro_200.py` | 2.0.0 | screeching-jobina/filtro | 1 |
| SurpriseBot | `Surprise_200.py` | 2.0.0 | surprise1/sorpresa | 1 |

**Shared:** `C_shared100.py` v2.3.14 · **10 API key totali**

---

## Struttura file

```
C_shared100.py       # Libreria condivisa
Vogue_200.py         # Analisi foto/testo → prompt Flow
Architect_202.py     # Prompt testo/foto → editoriale · /generico (prompt neutro)
Atelier_202.py       # Outfit analysis → prompt con filtri (filtro persistente)
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
pyTelegramBotAPI==4.31.0
flask==3.0.0
Pillow>=10.0.0
google-genai>=1.66.0
pilmoji>=2.0.4
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

## Fix robustezza (20/06/2026 → 27/06/2026)

Audit completo il 20/06, fix puntuali il 25/06 e 27/06. Modifiche principali: reset giornaliero contatori reso resiliente (shared 2.3.12), `analyze_scene()` ora cattura prop interattivi con campo dedicato `PROPS & ACTIONS` (shared 2.3.13), 5ª chiave API aggiunta per Atelier (shared 2.3.14), rimozione ratio/count e miglioramento fedeltà scena in Atelier (202). Su Architect, fix `/generico` in due passaggi: la versione 201 (25/06) era preventiva ma non centrata sulla causa reale; la 202 (27/06) ha individuato e corretto la causa effettiva — `task_generico` allegava bottoni post-prompt fuori contesto tramite `send_prompt()`. Dettagli in `HANDOFF-MASTER`, sezioni 2bis e 2ter.

**TODO aperto:** il contatore `🔑 Key N · call #N` mostrato dai bot è in realtà globale (somma di tutte le chiavi), non per-chiave come il nome suggerisce — bug noto in `C_shared100.py`, da correggere nella prossima sessione.

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

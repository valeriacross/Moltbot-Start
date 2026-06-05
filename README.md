# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 05/06/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb |
|-----|------|---------|-------|
| VogueBot | `Vogue_102.py` | 1.0.2 | colossal-giselle/vogue |
| ArchitectBot | `Architect_101.py` | 1.0.1 | homely-annabelle/thearchitect |
| AtelierBot | `Atelier_104.py` | 1.0.4 | flexible-denna/atelier |
| FiltroBot | `Filtro_104.py` | 1.0.4 | screeching-jobina/filtro |
| SurpriseBot | `Surprise_124.py` | 1.2.4 | surprise1/sorpresa |

**Shared:** `C_shared100.py` v2.3.2 — comune a tutti i bot

---

## Struttura file

```
C_shared100.py      # Libreria condivisa — GeminiClient, prompt, utils
Vogue_102.py        # VogueBot — analisi foto → prompt Flow
Architect_101.py    # ArchitectBot — prompt testo/foto → editoriale
Atelier_104.py      # AtelierBot — outfit analysis → prompt con filtri
Filtro_104.py       # FiltroBot — 7 categorie filtro + LEGO + Mosaic
Surprise_124.py     # SurpriseBot — location + outfit random + /pride + /flag
requirements.txt    # Dipendenze pip
README.md           # Questo file
```

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
| `TELEGRAM_TOKEN_SORPRESA` | SurpriseBot / Pride / Flag |
| `GOOGLE_API_KEY` | Chiave Gemini principale (tutti i bot) |
| `GOOGLE_API_KEY_2` | Chiave Gemini secondaria (Vogue, Atelier) |
| `GOOGLE_API_KEY_3` | Chiave Gemini terziaria (Vogue, Atelier) |
| `ALLOWED_USERS` | `273003890` |
| `PORT` | `10000` |

---

## GeminiClient

- Max 3 chiavi per bot (`GOOGLE_API_KEY`, `_2`, `_3`)
- Rotation round-robin ad ogni chiamata
- Callback `on_key_rotation` per notifica utente
- Safety block: messaggio chiaro all'utente

---

## Comandi per bot

### VogueBot
`/start` · `/info` · `/shared` · `/dna` · `/caption`

### ArchitectBot
`/start` · `/help` · `/info` · `/lastprompt` · `/shared`

### AtelierBot
`/start` · `/help` · `/info` · `/lastprompt` · `/caption` · `/shared`

### FiltroBot
`/start` · `/filtro` · `/help` · `/info` · `/lastprompt` · `/caption` · `/mosaic` · `/done` · `/shared`

### SurpriseBot
`/start` · `/flag` · `/pride` · `/help` · `/info` · `/shared` · `/lastprompt`

---

## Repository

`valeriacross/Moltbot-Start` — Frankfurt

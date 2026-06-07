# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 07/06/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb |
|-----|------|---------|-------|
| VogueBot | `Vogue_104.py` | 1.0.4 | colossal-giselle/vogue |
| ArchitectBot | `Architect_103.py` | 1.0.3 | homely-annabelle/thearchitect |
| AtelierBot | `Atelier_108.py` | 1.0.8 | flexible-denna/atelier |
| FiltroBot | `Filtro_107.py` | 1.0.7 | screeching-jobina/filtro |
| SurpriseBot | `Surprise_124.py` | 1.2.4 | surprise1/sorpresa |

**Shared:** `C_shared100.py` v2.3.5 — comune a tutti i bot

---

## Struttura file

```
C_shared100.py       # Libreria condivisa — GeminiClient, CaptionGenerator, prompt, utils
Vogue_104.py         # VogueBot — analisi foto/testo → prompt Flow
Architect_103.py     # ArchitectBot — prompt testo/foto → editoriale
Atelier_108.py       # AtelierBot — outfit analysis → prompt con filtri
Filtro_107.py        # FiltroBot — 7 categorie filtro + LEGO + Mosaic + Scarabocchio
Surprise_124.py      # SurpriseBot — location + outfit random + /pride + /flag
requirements.txt     # Dipendenze pip
README.md            # Questo file
```

---

## Strategia call Gemini

| Bot | Call/operazione | Caption |
|-----|----------------|---------|
| Atelier | 2 (analyze + review) | locale — zero call |
| Vogue | 2 (analyze + review) | locale — zero call |
| Architect | 1-2 | locale — zero call |
| Filtro | 1 (analyze) | locale — zero call |
| Surprise | 1 (review) | locale — zero call |

`/caption` on-demand = 1 call Gemini (qualità superiore).

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
| `GOOGLE_API_KEY` | Chiave Gemini principale |
| `GOOGLE_API_KEY_2` | Chiave Gemini secondaria |
| `GOOGLE_API_KEY_3` | Chiave Gemini terziaria |
| `ALLOWED_USERS` | `273003890` |
| `PORT` | `10000` |

---

## GeminiClient v2.3.5

- Rotation round-robin ad ogni chiamata
- Retry su tutti gli errori transitori (429, 503, timeout, connection)
- `CaptionGenerator.local()` — caption zero call per tutti i bot
- `/caption` on-demand via `from_image()` — 1 call Gemini

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

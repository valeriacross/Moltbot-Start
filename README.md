# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 08/06/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb | Chiavi |
|-----|------|---------|-------|--------|
| VogueBot | `Vogue_106.py` | 1.0.6 | colossal-giselle/vogue | 3 |
| ArchitectBot | `Architect_104.py` | 1.0.4 | homely-annabelle/thearchitect | 2 |
| AtelierBot | `Atelier_111.py` | 1.1.1 | flexible-denna/atelier | 3 |
| FiltroBot | `Filtro_108.py` | 1.0.8 | screeching-jobina/filtro | 1 |
| SurpriseBot | `Surprise_124.py` | 1.2.4 | surprise1/sorpresa | 1 |

**Shared:** `C_shared100.py` v2.3.7 · **10 API key totali**

---

## Struttura file

```
C_shared100.py       # Libreria condivisa
Vogue_106.py         # Analisi foto/testo → prompt Flow
Architect_104.py     # Prompt testo/foto → editoriale
Atelier_111.py       # Outfit analysis → prompt con filtri (filtro persistente)
Filtro_108.py        # 7 categorie + LEGO + Mosaic + Scarabocchio
Surprise_124.py      # Location + outfit random + /pride + /flag
requirements.txt
README.md
```

---

## Call Gemini per bot

| Bot | Call/foto | Caption |
|-----|-----------|---------|
| Atelier | 2 | `/caption` on-demand |
| Vogue | 2 | `/caption` on-demand |
| Architect | 1-2 | nessuna |
| Filtro | 1 | `/caption` on-demand |
| Surprise | 1 | nessuna |

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

## Comandi

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

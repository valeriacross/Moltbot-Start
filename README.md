# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 1.3.0 | (comune a tutti) | — |
| `C_vogue121.py` | 1.2.1 | colossal-giselle/vogue | `python C_vogue121.py` |
| `C_architect132.py` | 1.3.2 | homely-annabelle/thearchitect | `python C_architect132.py` |
| `C_atelier124.py` | 1.2.4 | flexible-denna/atelier | `python C_atelier124.py` |
| `C_filtro215.py` | 2.1.5 | screeching-jobina/filtro | `python C_filtro215.py` |
| `C_nosurprise106.py` | 1.0.6 | near-damara/sorpresa | `python C_nosurprise106.py` |

---

## Architettura

Tutti i bot importano da `C_shared100.py` che centralizza:

- `GeminiClient` — Singleton Gemini API con BLOCK_NONE. Rilancia eccezioni con `finish_reason` reale.
- `HealthServer` — Flask health check su porta 10000 (necessario per Koyeb)
- `is_allowed()` — whitelist utenti via env `ALLOWED_USERS`
- `detect_mime_type()` — rileva JPEG/PNG/WebP dai magic bytes
- `analyze_scene()` — singolo tentativo, classifica errori: quota / safety / timeout / generico
- `generate_caption()` — 5 emoji + 5/10 parole EN; `extract_caption()` filtra ragionamento Gemini
- `CaptionGenerator` — caption da scenario/filtro (Nosurprise, Filtro)
- `VALERIA_DNA`, `EDITORIAL_WRAPPER`, `build_valeria_identity()` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — verificabili via `/shared`

### Regole architetturali

- **Tutti i bot generano SOLO prompt testuali per Flow** — eccetto filtri LEGO che elaborano localmente con PIL.
- **Flow usa le proprie immagini di riferimento. `masterface.png` rimossa.**
- I filtri di Filtro si applicano al soggetto — NON iniettano DNA Valeria.

---

## Comandi comuni

| Comando | Funzione |
|---------|---------|
| `/start` | Avvia il bot |
| `/help` | Lista comandi |
| `/info` | Versione bot e stato API |
| `/shared` | Versione e data di C_shared100.py |

---

## Filtro v2.1.5 — 7 categorie

**Stilistici** · **Fantasy & Art** · **Scenografici** · **Collage** · **Mosaic** · **🎨 Stile Artistico** · **✨ Altri**

### 🎨 Stile Artistico (menu 2 livelli — 20 artisti)
Leonardo · Raffaello · Michelangelo · Caravaggio · Renoir · Van Gogh · Matisse · Chagall · Klimt · Mirò · Mondrian · Picasso · Magritte · Dalì · De Chirico · Banksy · Lichtenstein · Mucha · Hopper · Basquiat

### 🌟 Y2K Pop Collage
Pool 20 pose, 5 casuali ad ogni generazione.

### 🧱 LEGO Mosaic (Altri)
- Griglia A3: 52×37 studs, stud 40px con 3D sottile
- Palette LEGO ufficiale 50 colori
- Post-generazione: **lista mattoncini Excel** con colori, tipi, codici BrickLink, link cliccabili

### 🌌 LEGO Galaxy (Altri)
- Stessa griglia A3
- Bokeh automatico (radiale/verticale) rilevato dall'analisi dell'immagine
- Tre elementi visivi: round piatti (sfondo), stud standard (soggetto), stud tall (zone omogenee)
- Lista mattoncini Excel con 3 tipi distinti: Plate Round 1×1 · Plate 1×1 · Brick Round 1×1

> ⚠️ I filtri LEGO non consumano quota Gemini — elaborazione locale con PIL.
> Post-prompt Filtro: reminder per caricare l'immagine di riferimento su Flow.

---

## Nosurprise v1.0.6

LOCATION_POOL: 254 location (inclusi Alien, Lost, Lost in Space, Predator, Transformers, Pixar, Disney).

---

## Dipendenze (requirements.txt)

```
pyTelegramBotAPI==4.31.0
flask==3.1.3
Pillow>=12.2.0
google-genai>=2.6.0
openpyxl>=3.1.0
```

---

## Variabili d'ambiente Koyeb

| Variabile | Dove |
|-----------|------|
| `GOOGLE_API_KEY` | Ogni bot — chiave separata (5 progetti) |
| `ALLOWED_USERS` | `273003890` — tutti |
| `PORT` | `10000` — tutti |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Nosurprise |

---

## Quota Gemini

- `gemini-3-flash-preview` — 20 req/giorno per chiave, reset 08:00 Lisbona
- 5 chiavi = 100 req/giorno totali · Filtri LEGO: zero quota

---

## File nel repo

```
C_shared100.py · C_vogue121.py · C_architect132.py
C_atelier124.py · C_filtro215.py · C_nosurprise106.py
requirements.txt · README.md
```

### Da eliminare (obsoleti)
```
architect-902.py · filtro-602.py · shared.py · surprise-508.py · vogue-713.py
```

---

## Aggiornare C_shared100.py

1. Aggiornare `SHARED_VERSION`, `SHARED_DATE` e docstring changelog
2. Push su GitHub · 3. Koyeb redeploy di **tutti** i bot

## Update — procedura completa

1. HANDOFF · 2. README.md · 3. VERSIONI_BOT Excel

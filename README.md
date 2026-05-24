# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 1.5.0 | (comune a tutti) | — |
| `C_vogue123.py` | 1.2.3 | colossal-giselle/vogue | `python C_vogue123.py` |
| `C_architect134.py` | 1.3.4 | homely-annabelle/thearchitect | `python C_architect134.py` |
| `C_atelier127.py` | 1.2.7 | flexible-denna/atelier | `python C_atelier127.py` |
| `C_filtro215.py` | 2.1.5 | screeching-jobina/filtro | `python C_filtro215.py` |
| `C_nosurprise106.py` | 1.0.6 | near-damara/sorpresa | `python C_nosurprise106.py` |

---

## Architettura

Tutti i bot importano da `C_shared100.py` v1.5.0:

- `GeminiClient` — Singleton, BLOCK_NONE, rilancia eccezioni con finish_reason reale
- `HealthServer` — Flask porta 10000 (necessario per Koyeb)
- `analyze_scene()` — singolo tentativo, classifica errori
- `generate_caption()` — caption da immagine, 5 emoji + frase
- `generate_mini_caption(text)` — caption da testo prompt, 5 emoji + frase, no gender
- `generate_mini_prompt(text)` — mini prompt strutturato formato Nosurprise
- `CaptionGenerator` — Nosurprise, Filtro
- `VALERIA_DNA`, `EDITORIAL_WRAPPER` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — via `/shared`

### Regole architetturali

- **Tutti i bot generano SOLO prompt testuali per Flow** — eccetto filtri LEGO (PIL locale).
- **Flow usa le proprie immagini. masterface.png rimossa.**
- I filtri di Filtro NON iniettano DNA Valeria.

---

## Comandi comuni

`/start` · `/help` · `/info` · `/shared`

---

## Pulsanti post-prompt (Vogue, Architect, Atelier)

Dopo ogni prompt generato:
```
📸 Nuova foto    🏠 Home / ✏️ Nuovo testo
📝 Mini caption  📋 Mini prompt
```

**Mini caption** — 5 emoji + frase breve no-gender dall'essenza visiva del prompt.
**Mini prompt** — formato strutturato Nosurprise:
`📍 Location · 🌤 Sky · 👗 Outfit · 🎨 Style · 💃 Pose · ✨ Mood · 🏛 Body`

---

## Filtro v2.1.5 — 7 categorie

**Stilistici** · **Fantasy & Art** · **Scenografici** · **Collage** · **Mosaic** · **🎨 Stile Artistico** · **✨ Altri**

**Stile Artistico:** 20 artisti in 5 categorie (menu 2 livelli)

**Y2K Pop Collage:** pool 20 pose, 5 casuali per generazione

**🧱 LEGO Mosaic (Altri):** griglia A3 (52×37 studs), Plate 1×1, lista Excel BrickLink

**🌌 LEGO Galaxy (Altri):** stessa griglia, bokeh automatico, 3 tipi elemento, lista Excel

> Post-prompt Filtro: reminder per caricare immagine di riferimento su Flow.

---

## Nosurprise v1.0.6

254 location — inclusi Alien, Lost, Lost in Space, Predator, Transformers, Pixar, Disney.

---

## Dipendenze

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
| `GOOGLE_API_KEY` | Ogni bot — chiave separata |
| `ALLOWED_USERS` | `273003890` — tutti |
| `PORT` | `10000` — tutti |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Nosurprise |

---

## Quota Gemini

20 req/giorno per chiave · reset 08:00 Lisbona · 5 chiavi = 100 req/giorno
Filtri LEGO: zero quota · Mini caption/prompt: 1 req ciascuno

---

## File nel repo

```
C_shared100.py · C_vogue123.py · C_architect134.py
C_atelier127.py · C_filtro215.py · C_nosurprise106.py
requirements.txt · README.md
```

### Obsoleti da eliminare
```
architect-902.py · filtro-602.py · shared.py · surprise-508.py · vogue-713.py
```

---

## Aggiornare shared

1. SHARED_VERSION + SHARED_DATE + docstring changelog
2. Push GitHub · 3. Redeploy **tutti** i bot su Koyeb

## Update completo

HANDOFF · README · VERSIONI_BOT Excel

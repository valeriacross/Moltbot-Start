# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI**.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 2.1.0 | (comune a tutti) | — |
| `Vogue_100.py` | 1.0.0 | colossal-giselle/vogue | `python Vogue_100.py` |
| `Architect_100.py` | 1.0.0 | homely-annabelle/thearchitect | `python Architect_100.py` |
| `Atelier_100.py` | 1.0.0 | flexible-denna/atelier | `python Atelier_100.py` |
| `Filtro_100.py` | 1.0.0 | screeching-jobina/filtro | `python Filtro_100.py` |
| `Surprise_100.py` | 1.0.0 | near-damara/sorpresa | `python Surprise_100.py` |

> **Nota:** `C_shared100.py` mantiene il nome originale — tutti i bot lo importano come `C_shared100`.
> Aggiornare il Run command su Koyeb coi nuovi nomi file.

---

## Shared v2.1.0

GeminiClient multi-chiave (max 3, rotation su 429) · review_and_fix · sanitize_user_input · generate_mini_caption · generate_mini_prompt (parser locale) · analyze_scene · generate_caption · CaptionGenerator · detect_mime_type · VALERIA_DNA / EDITORIAL_WRAPPER / build_valeria_identity

---

## Pipeline per bot

**Atelier** — `analyze_scene → review_and_fix → prompt → caption automatica` · 60 gen/giorno con 3 chiavi · pulsanti 📸 Nuova foto / 🏠 Home

**Vogue / Architect** — prompt → caption · Mini caption + Mini prompt (parser locale, zero Gemini)

**Surprise** — pool locale · `/pride` integrato (Walter, Carlotta, Fufos, Fritz) · pick_auto protetto su 503

**Filtro** — 7 categorie · 20 artisti · Y2K Pop Collage · LEGO Mosaic/Galaxy con lista Excel BrickLink

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
| `GOOGLE_API_KEY` (+_2, +_3) | ogni bot — chiavi separate |
| `ALLOWED_USERS` | `273003890` |
| `PORT` | `10000` |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Surprise + Pride |

---

## Quota Gemini

20 req/giorno per chiave · reset 08:00 Lisbona · con 3 chiavi = 60/giorno per bot
LEGO e Pride: zero quota

---

## File nel repo

```
C_shared100.py · Vogue_100.py · Architect_100.py
Atelier_100.py · Filtro_100.py · Surprise_100.py
requirements.txt · README.md
```

## Update completo

HANDOFF · README · VERSIONI_BOT Excel

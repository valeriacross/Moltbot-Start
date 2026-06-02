# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI**.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 2.3.1 | (comune a tutti) | — |
| `Vogue_101.py` | 1.0.1 | colossal-giselle/vogue | `python Vogue_101.py` |
| `Architect_100.py` | 1.0.0 | homely-annabelle/thearchitect | `python Architect_100.py` |
| `Atelier_102.py` | 1.0.2 | flexible-denna/atelier | `python Atelier_102.py` |
| `Filtro_100.py` | 1.0.0 | screeching-jobina/filtro | `python Filtro_100.py` |
| `Surprise_124.py` | 1.2.4 | surprise1/sorpresa | `python Surprise_124.py` |

> `C_shared100.py` mantiene il nome originale — tutti i bot lo importano come `C_shared100`.

---

## Shared v2.3.1

GeminiClient multi-chiave (max 3, rotation loop su 429, on_key_rotation callback) · review_and_fix (max_tokens=8192) · sanitize_user_input · generate_mini_caption · generate_mini_prompt (parser locale) · analyze_scene · generate_caption · CaptionGenerator · detect_mime_type · VALERIA_DNA / EDITORIAL_WRAPPER / build_valeria_identity

**Safety block:** messaggio utente chiaro quando Gemini blocca un'immagine per contenuto sensibile.

---

## Pipeline per bot

**Atelier** — `analyze_scene → review_and_fix → prompt → caption automatica` · 60 gen/giorno con 3 chiavi · pulsanti 📸 Nuova foto / 🏠 Home

**Vogue** — foto/testo → review → prompt → caption · Mini caption + Mini prompt · on_key_rotation notifica

**Architect** — prompt testo o foto → review → caption

**Surprise** — pool locale · output duplice (single + mosaic) · `/pride` (Walter/Carlotta/Fufos/Fritz, 8 location Lisbona) · `/flag` (PRIDE! mosaic 3×2, zero token, 11M+ combinazioni)

**Filtro** — 7 categorie · LEGO Mosaic/Galaxy con lista Excel BrickLink

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
| `TELEGRAM_TOKEN_SORPRESA` | Surprise + Pride + Flag |

---

## Quota Gemini

20 req/giorno per chiave · reset 08:00 Lisbona · con 3 chiavi = 60/giorno per bot
LEGO, Pride e Flag: zero quota

---

## File nel repo

```
C_shared100.py · Vogue_101.py · Architect_100.py
Atelier_102.py · Filtro_100.py · Surprise_124.py
requirements.txt · README.md
```

## Update completo

HANDOFF · README · VERSIONI_BOT Excel

# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 1.7.0 | (comune a tutti) | — |
| `C_vogue125.py` | 1.2.5 | colossal-giselle/vogue | `python C_vogue125.py` |
| `C_architect136.py` | 1.3.6 | homely-annabelle/thearchitect | `python C_architect136.py` |
| `C_atelier128.py` | 1.2.8 | flexible-denna/atelier | `python C_atelier128.py` |
| `C_filtro215.py` | 2.1.5 | screeching-jobina/filtro | `python C_filtro215.py` |
| `C_nosurprise107.py` | 1.0.7 | near-damara/sorpresa | `python C_nosurprise107.py` |

---

## Architettura

Tutti i bot importano da `C_shared100.py` v1.7.0:

- `GeminiClient` — Singleton, BLOCK_NONE, rilancia eccezioni con finish_reason reale
- `HealthServer` — Flask porta 10000
- `analyze_scene()` — singolo tentativo, classifica errori
- `review_and_fix(prompt, client)` — corregge contraddizioni DNA (capelli, occhiali, body hair, watermark)
- `sanitize_user_input(text, client)` — rimuove elementi incompatibili dal testo utente
- `generate_caption()` — caption da immagine
- `generate_mini_caption(text)` — caption da testo, no gender
- `generate_mini_prompt(text)` — formato strutturato Nosurprise
- `CaptionGenerator` — Nosurprise, Filtro
- `VALERIA_DNA`, `EDITORIAL_WRAPPER`, `build_valeria_identity()` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — via `/shared`

### Pipeline prompt unificata (Vogue, Architect, Atelier)

```
Input → [sanitize] → build_prompt → review_and_fix → send → caption
```

---

## Comandi comuni

`/start` · `/help` · `/info` · `/shared`

---

## Pulsanti post-prompt (Vogue, Architect, Atelier)

```
📸 Nuova foto    🏠 Home / ✏️ Nuovo testo
📝 Mini caption  📋 Mini prompt
```

---

## Bot per bot

### 👠 Vogue — foto + testo → prompt Flow
Sanitize testo · build_prompt · review_and_fix · caption automatica

### 📐 Architect — foto + testo → Master Prompt
Sanitize · generate_monolith/from_image · review_and_fix · caption foto

### ✦ Atelier — foto → prompt shooting
analyze_scene · build_full/shooting_prompt · review_and_fix · caption

### 🎨 Filtro v2.1.5 — 7 categorie, 30+ filtri
Stile Artistico: 20 artisti · Y2K Pop Collage · LEGO Mosaic · LEGO Galaxy + lista Excel BrickLink

### 📍 Nosurprise v1.0.7
`/start` → prompt da pool · `/pride` → Pride Lisbona 2026 (Walter + Carlotta + Fufos + Fritz)

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
| `TELEGRAM_TOKEN_SORPRESA` | Nosurprise + Pride |

---

## Quota Gemini

20 req/giorno · reset 08:00 Lisbona · 5 chiavi = 100/giorno
LEGO e Pride: zero quota · review_and_fix, sanitize, mini caption/prompt: 1 req ciascuno

---

## File nel repo

```
C_shared100.py · C_vogue125.py · C_architect136.py
C_atelier128.py · C_filtro215.py · C_nosurprise107.py
requirements.txt · README.md
```

### Obsoleti da eliminare
```
architect-902.py · filtro-602.py · shared.py · surprise-508.py · vogue-713.py
```

---

## Aggiornare shared

1. VERSION + SHARED_VERSION + SHARED_DATE + docstring changelog
2. Push GitHub · 3. Redeploy **tutti** i bot

## Update completo

HANDOFF · README · VERSIONI_BOT Excel

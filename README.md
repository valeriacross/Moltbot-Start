# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI**.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 2.0.5 | (comune a tutti) | — |
| `C_vogue125.py` | 1.2.5 | colossal-giselle/vogue | `python C_vogue125.py` |
| `C_architect137.py` | 1.3.7 | homely-annabelle/thearchitect | `python C_architect137.py` |
| `C_atelier135.py` | 1.3.5 | flexible-denna/atelier | `python C_atelier135.py` |
| `C_filtro216.py` | 2.1.6 | screeching-jobina/filtro | `python C_filtro216.py` |
| `C_nosurprise109.py` | 1.0.9 | near-damara/sorpresa | `python C_nosurprise109.py` |

---

## Shared v2.0.5

`review_and_fix` · `sanitize_user_input` · `generate_mini_caption` · `generate_mini_prompt` (parser locale) · `GeminiClient` multi-chiave (max 3, rotation su 429)

---

## Pipeline per bot

**Atelier** — `analyze_scene → review_and_fix → prompt → caption automatica` · 2 token/gen · 60 gen/giorno con 3 chiavi

**Vogue / Architect** — prompt → caption → mini caption · mini prompt (parser locale, zero Gemini)

**Nosurprise** — pool locale · `/pride` integrato · pick_auto protetto da try/except su 503

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

## File nel repo

```
C_shared100.py · C_vogue125.py · C_architect137.py
C_atelier135.py · C_filtro216.py · C_nosurprise109.py
requirements.txt · README.md
```

## Update completo

HANDOFF · README · VERSIONI_BOT Excel

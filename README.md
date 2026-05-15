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
| `C_filtro204.py` | 2.0.4 | screeching-jobina/filtro | `python C_filtro204.py` |
| `C_nosurprise105.py` | 1.0.5 | near-damara/sorpresa | `python C_nosurprise105.py` |

---

## Architettura

Tutti i bot importano da `C_shared100.py` che centralizza:

- `GeminiClient` — Singleton Gemini API con BLOCK_NONE. Rilancia eccezioni con `finish_reason` reale.
- `HealthServer` — Flask health check su porta 10000 (necessario per Koyeb)
- `is_allowed()` — whitelist utenti via env `ALLOWED_USERS`
- `detect_mime_type()` — rileva JPEG/PNG/WebP dai magic bytes
- `analyze_scene()` — singolo tentativo, classifica errori: quota / safety / timeout / generico
- `generate_caption()` — 5 emoji + 5/10 parole EN
- `CaptionGenerator` — caption da scenario/filtro; `extract_caption()` filtra ragionamento interno Gemini
- `VALERIA_DNA`, `EDITORIAL_WRAPPER`, `build_valeria_identity()` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — verificabili via `/shared`

### Regole architetturali

- **Tutti i bot generano SOLO prompt testuali per Flow. Nessun bot genera immagini.**
- **Flow usa le proprie immagini di riferimento. `masterface.png` rimossa.**
- L'outfit viene estratto tramite `analyze_scene()` e inserito nel prompt come testo.
- I filtri di Filtro si applicano al soggetto dell'immagine — NON iniettano DNA Valeria.

---

## Comandi comuni a tutti i bot

| Comando | Funzione |
|---------|---------|
| `/start` | Avvia il bot |
| `/help` | Lista comandi |
| `/info` | Versione bot e stato API |
| `/shared` | Versione e data di C_shared100.py |

---

## Comandi per bot

### 👠 Vogue
`[foto]` → analizza → prompt + DNA Valeria → caption. `/caption` per caption manuale. `[testo]` → prompt diretto.
Pulsanti: 📸 Nuova foto | 🏠 Home

### 📐 Architect
`/start` → Testo | Foto. Pipeline: sanitize → generate → review_and_fix → send → caption.
Intestazione prompt: `EDITORIAL_WRAPPER`. NEGATIVE PROMPT: 3 blocchi (Face, Hair, Body).
Pulsanti: 📸 Nuova foto | ✏️ Nuovo testo (non sovrascrivono il prompt).

### ✦ Atelier
`[foto]` → analisi outfit → prompt shooting → caption. `/caption` per caption manuale.

### 🎨 Filtro — 7 categorie, 30+ filtri
Stilistici · Fantasy & Art · Scenografici · Collage · Mosaic · **🎨 Stile Artistico** · Altri

**Stile Artistico:** menu a 2 livelli — 5 categorie → 20 artisti (Leonardo, Raffaello, Michelangelo, Caravaggio, Renoir, Van Gogh, Matisse, Chagall, Klimt, Mirò, Mondrian, Picasso, Magritte, Dalì, De Chirico, Banksy, Lichtenstein, Mucha, Hopper, Basquiat)

**Y2K Pop Collage:** pool 20 pose, 5 casuali ad ogni generazione.

Post-prompt: reminder per caricare immagine di riferimento su Flow.

### 📍 Nosurprise
`/start` → foto opzionale come location → formato → Auto/Manuale → prompt → caption.

---

## Variabili d'ambiente Koyeb

| Variabile | Dove |
|-----------|------|
| `GOOGLE_API_KEY` | Ogni bot — chiave separata (5 progetti Google Cloud) |
| `ALLOWED_USERS` | `273003890` — tutti |
| `PORT` | `10000` — tutti |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Nosurprise |

> ⚠️ **Non scrivere mai chiavi API nel repo.**

---

## Quota Gemini

- `gemini-3-flash-preview` — free tier, 20 req/giorno per chiave, reset 08:00 Lisbona
- 5 chiavi = 100 req/giorno totali
- `analyze_scene()` usa singolo tentativo

---

## Infrastruttura

- **Deploy:** Koyeb — un servizio per bot
- **Health check:** Flask porta 10000 — necessario per Koyeb
- **409 Conflict:** Koyeb → Deployments → stoppare vecchi

---

## Aggiornare C_shared100.py

1. Aggiornare `SHARED_VERSION`, `SHARED_DATE` e docstring changelog
2. Push su GitHub
3. Koyeb redeploy di **tutti** i bot

## Update — procedura completa

1. HANDOFF · 2. README.md · 3. VERSIONI_BOT Excel

---

## File nel repo

```
C_shared100.py
C_vogue121.py
C_architect132.py
C_atelier124.py
C_filtro204.py
C_nosurprise105.py
requirements.txt
README.md
```

### Da eliminare (obsoleti)
```
architect-902.py · filtro-602.py · shared.py · surprise-508.py · vogue-713.py
```

---

## Convenzione versioni

- `C_shared100.py` — nome fisso, versione interna scala
- Altri bot — nome file = versione: `C_architect132.py` = v1.3.2
- Ogni modifica → versione incrementata → nuovo file
- **Mai due file con lo stesso numero**

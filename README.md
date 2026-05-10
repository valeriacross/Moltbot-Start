# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 1.1.0 | (comune a tutti) | — |
| `C_vogue120.py` | 1.2.0 | colossal-giselle/vogue | `python C_vogue120.py` |
| `C_architect121.py` | 1.2.1 | homely-annabelle/thearchitect | `python C_architect121.py` |
| `C_atelier121.py` | 1.2.1 | flexible-denna/atelier | `python C_atelier121.py` |
| `C_filtro127.py` | 1.2.7 | screeching-jobina/filtro | `python C_filtro127.py` |
| `C_surprise112.py` | 1.1.2 | near-damara/sorpresa | `python C_surprise112.py` |
| `C_nosurprise105.py` | 1.0.5 | (deploy separato) | `python C_nosurprise105.py` |

---

## Architettura

Tutti i bot importano da `C_shared100.py` che centralizza:

- `GeminiClient` — Singleton Gemini API con BLOCK_NONE su tutti i safety settings
- `HealthServer` — Flask health check su porta 10000
- `is_allowed()` — whitelist utenti via env `ALLOWED_USERS`
- `detect_mime_type()` — rileva JPEG/PNG/WebP dai magic bytes (usata ovunque)
- `analyze_scene()` — singolo tentativo, prompt neutro, restituisce errore reale API
- `generate_caption()` — 5 emoji + 5/10 parole EN
- `CaptionGenerator` — caption da scenario/filtro (Surprise, Nosurprise, Filtro)
- `VALERIA_DNA`, `EDITORIAL_WRAPPER`, `build_valeria_identity()` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — versione shared verificabile via `/shared`

### Regole architetturali

- **Tutti i bot generano SOLO prompt testuali per Flow. Nessun bot genera immagini direttamente.**
- **Flow usa SOLO `masterface.png` come riferimento. Le immagini inviate ai bot NON vengono mai allegate a Flow.**
- L'outfit viene estratto tramite `analyze_scene()` e inserito nel prompt come testo.

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
| Comando | Funzione |
|---------|---------|
| `/dna` | Mostra DNA Valeria Cross |
| `/caption` | Genera caption social da foto |
| `[foto]` | Analizza scena → prompt Flow-ready → caption automatica |
| `[testo]` | Genera prompt da descrizione testuale |

### 📐 Architect
| Comando | Funzione |
|---------|---------|
| `/reset` | Resetta sessione |
| `/lastprompt` | Reinvia ultimo prompt |
| `[foto]` | Genera Master Prompt certificato → caption automatica |
| `[testo]` | Genera prompt da descrizione |

### ✦ Atelier
| Comando | Funzione |
|---------|---------|
| `/reset` | Resetta sessione |
| `/caption` | Genera caption da foto |
| `[foto]` | Analisi outfit → prompt shooting → caption automatica |

### 🎨 Filtro
| Comando | Funzione |
|---------|---------|
| `/reset` | Resetta sessione |
| `/filtro` `/filter` | Selezione filtro artistico |
| `/lastprompt` | Reinvia ultimo prompt |
| `/caption` | Genera caption da foto |
| `[foto]` | Analizza soggetto → applica filtro → prompt Flow-ready → caption automatica |

### 🎲 Surprise
| Comando | Funzione |
|---------|---------|
| `/start` | Avvia: formato → auto/manuale → prompt → caption |

### 📍 Nosurprise
Come Surprise ma con foto opzionale come location. La foto viene analizzata e la location estratta sostituisce quella dalla pool. In manuale il primo step (location) viene saltato.

---

## Variabili d'ambiente Koyeb

| Variabile | Dove |
|-----------|------|
| `GOOGLE_API_KEY` | Ogni bot ha la sua chiave separata (5 progetti Google Cloud) |
| `ALLOWED_USERS` | `273003890` — tutti i bot |
| `PORT` | `10000` — tutti i bot |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Surprise / Nosurprise |

> ⚠️ **Non scrivere mai chiavi API in file di testo nel repo.**

---

## Quota Gemini

- Modello: `gemini-3-flash-preview` (free tier)
- 20 richieste/giorno per chiave — reset alle 08:00 ora Lisbona
- 5 chiavi separate = **100 richieste/giorno totali**
- `analyze_scene()` usa un singolo tentativo — nessuno spreco di quota su fallimento

---

## Infrastruttura

- **Deploy:** Koyeb (un servizio per bot)
- **Health check:** Flask su porta 10000
- **Polling:** `infinity_polling` con gestione 409 Conflict (`sleep(15)`) e altri errori (`sleep(5)`)

> ⚠️ **409 Conflict:** su Koyeb → servizio → Deployments → stoppare tutti i deployment vecchi, lasciare solo l'ultimo.

---

## Aggiornare C_shared100.py

Ogni modifica a shared richiede:
1. Aggiornare `SHARED_VERSION` e `SHARED_DATE` nel file
2. Push su GitHub
3. Koyeb redeploy di **tutti** i bot

---

## File nel repo

### Attivi
```
C_shared100.py
C_vogue120.py
C_architect121.py
C_atelier121.py
C_filtro127.py
C_surprise112.py
C_nosurprise105.py
masterface.png
requirements.txt
README.md
```

### Da eliminare (obsoleti)
```
architect-902.py
filtro-602.py
shared.py
surprise-508.py
vogue-713.py
```

---

## Convenzione versioni

- `C_shared100.py` — nome fisso, versione interna scala (1.0.0 → 1.1.0 → ...)
- Tutti gli altri bot — nome file rispecchia la versione: `C_vogue120.py` = v1.2.0
- Ogni modifica incrementa versione e nome file
- **Mai due file con lo stesso numero di versione**

---

## masterface.png

Usata da `C_atelier121.py` e `C_filtro127.py`. Non usata da Vogue, Architect, Surprise, Nosurprise.

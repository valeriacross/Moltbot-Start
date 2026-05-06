# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| Bot | File | Versione | Koyeb service | Run command |
|-----|------|---------|---------------|-------------|
| 👠 Vogue | `C_vogue110.py` | 1.1.0 | colossal-giselle/vogue | `python C_vogue110.py` |
| 📐 Architect | `C_architect110.py` | 1.1.0 | homely-annabelle/thearchitect | `python C_architect110.py` |
| ✦ Atelier | `C_atelier110.py` | 1.1.0 | flexible-denna/atelier | `python C_atelier110.py` |
| 🎨 Filtro | `C_filtro110.py` | 1.1.0 | screeching-jobina/filtro | `python C_filtro110.py` |
| 🎲 Surprise | `C_surprise110.py` | 1.1.0 | near-damara/sorpresa | `python C_surprise110.py` |
| 📦 Shared | `C_shared100.py` | 1.0.0 | (comune a tutti) | — |

---

## Architettura

Tutti i bot importano da `C_shared100.py` che espone:

- `GeminiClient` — wrapper Singleton su Google Gemini API
- `CaptionGenerator` — caption da scenario (usata da Surprise)
- `HealthServer` — Flask health check su porta 10000 (Koyeb)
- `is_allowed()` — whitelist utenti via env `ALLOWED_USERS`
- `analyze_scene()` — analisi immagine centralizzata (Vogue, Architect, Atelier)
- `generate_caption()` — caption social da immagine (Vogue, Architect, Atelier, Filtro)
- `VALERIA_DNA` — identità completa assemblatada FACE + BODY + WATERMARK + NEGATIVE
- `EDITORIAL_WRAPPER` — testo di apertura prompt editoriale
- `build_valeria_identity(safe=False)` — assembla identità con body strong o safe

---

## Comandi per bot

### 👠 Vogue
| Comando | Funzione |
|---------|---------|
| `/start` | Avvia il bot |
| `/info` | Versione e stato API |
| `/dna` | Mostra DNA Valeria Cross |
| `/caption` | Genera caption social da foto (5 emoji + 5/10 parole EN) |
| `[foto]` | Analizza la scena e genera prompt Flow-ready |
| `[testo]` | Genera prompt Flow-ready da descrizione testuale |

### 📐 Architect
| Comando | Funzione |
|---------|---------|
| `/start` `/reset` | Avvia / resetta |
| `/help` | Lista comandi |
| `/info` | Versione e stato API |
| `/lastprompt` | Reinvia l'ultimo prompt generato |
| `/stop` | Ferma sessione corrente |
| `/movie` | Modalità album multi-foto |
| `[foto]` | Genera Master Prompt certificato |
| `[testo]` | Genera prompt da descrizione |

### ✦ Atelier
| Comando | Funzione |
|---------|---------|
| `/start` `/reset` | Avvia / resetta |
| `/help` | Lista comandi |
| `/info` | Versione e stato API |
| `[foto]` | Analizza outfit e genera prompt shooting (mosaico 4 foto o scatti separati) |

### 🎨 Filtro
| Comando | Funzione |
|---------|---------|
| `/start` `/reset` | Avvia / resetta |
| `/filtro` `/filter` | Selezione filtro artistico |
| `/help` | Lista comandi |
| `/info` | Versione e stato API |
| `/lastprompt` | Reinvia l'ultimo prompt |
| `/caption` | Genera caption da foto |
| `/mosaic` | Modalità mosaico |
| `/done` | Conferma selezione |
| `[foto]` | Applica filtro e genera prompt Flow-ready |

### 🎲 Surprise
| Comando | Funzione |
|---------|---------|
| `/start` | Avvia e sceglie formato (singolo / mosaico) |
| `/help` | Lista comandi |
| `/info` | Versione e stato API |
| `/lastprompt` | Reinvia l'ultimo scenario generato |
| `[bottoni]` | Flusso guidato: formato → auto/manuale → prompt |

---

## Variabili d'ambiente Koyeb

| Variabile | Dove |
|-----------|------|
| `GOOGLE_API_KEY` | Ogni bot ha la sua chiave separata |
| `ALLOWED_USERS` | `273003890` — tutti i bot |
| `PORT` | `10000` — tutti i bot |
| `TELEGRAM_TOKEN` | Vogue |
| `TELEGRAM_TOKEN_ARCHITECT` | Architect |
| `TELEGRAM_TOKEN_CLOSET` | Atelier |
| `TELEGRAM_TOKEN_FX` | Filtro |
| `TELEGRAM_TOKEN_SORPRESA` | Surprise |

> ⚠️ **Non scrivere mai chiavi API in file di testo nel repo.**

---

## Quota Gemini

- Modello: `gemini-3-flash-preview` (free tier)
- 20 richieste/giorno per chiave — reset alle 08:00 ora Lisbona
- 5 chiavi separate = **100 richieste/giorno totali**

---

## Infrastruttura

- **Deploy:** Koyeb (un servizio per bot)
- **Health check:** Flask su porta 10000 — endpoint `/` e `/health`
- **Polling:** `infinity_polling` con gestione automatica errore 409 Conflict

> ⚠️ **409 Conflict:** se un bot non riceve comandi, verificare su Koyeb che ci sia un solo deployment attivo per quel servizio. Stoppare tutti i deployment vecchi e lasciare solo l'ultimo.

---

## File nel repo

### Attivi
```
C_shared100.py
C_vogue110.py
C_architect110.py
C_atelier110.py
C_filtro110.py
C_surprise110.py
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

- `C_shared100.py` — nome fisso, versione interna scala (1.0.0, 1.0.1, ...)
- Tutti gli altri bot — nome file rispecchia la versione: `C_vogue110.py` = v1.1.0
- Ogni modifica incrementa la versione: 1.1.0 → 1.1.1 → 1.1.2 → 1.2.0 ...
- **Mai due file con lo stesso numero di versione**

---

## masterface.png

Usata da:
- `C_atelier110.py` ✅
- `C_filtro110.py` ✅

Non usata da Vogue, Architect, Surprise.

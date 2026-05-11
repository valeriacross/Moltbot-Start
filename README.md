# Valeria Cross AI — Moltbot

Ecosistema di bot Telegram per il personaggio **Valeria Cross AI** — alter ego femminile generato interamente con AI.

---

## Bot attivi

| File | Versione | Koyeb service | Run command |
|------|---------|---------------|-------------|
| `C_shared100.py` | 1.2.0 | (comune a tutti) | — |
| `C_vogue121.py` | 1.2.1 | colossal-giselle/vogue | `python C_vogue121.py` |
| `C_architect130.py` | 1.3.0 | homely-annabelle/thearchitect | `python C_architect130.py` |
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
- `CaptionGenerator` — caption da scenario/filtro (Nosurprise, Filtro)
- `VALERIA_DNA`, `EDITORIAL_WRAPPER`, `build_valeria_identity()` — identità Valeria
- `SHARED_VERSION`, `SHARED_DATE` — verificabili via `/shared`

### Regole architetturali

- **Tutti i bot generano SOLO prompt testuali per Flow. Nessun bot genera immagini.**
- **Flow usa le proprie immagini di riferimento. `masterface.png` rimossa dal repo e dal codice.**
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
| Comando | Funzione |
|---------|---------|
| `/dna` | Mostra DNA Valeria Cross |
| `/caption` | Genera caption social da foto |
| `[foto]` | Analizza scena → prompt Flow-ready → caption automatica |
| `[testo]` | Genera prompt da descrizione testuale |

Pulsanti post-prompt: 📸 Nuova foto | 🏠 Home

### 📐 Architect
| Comando | Funzione |
|---------|---------|
| `/reset` | Resetta sessione |
| `/lastprompt` | Reinvia ultimo prompt |
| `[Testo]` | sanitize → generate → review → send |
| `[Foto]` | analyze + generate → review → send → caption |

Pulsanti post-prompt: 📸 Nuova foto | ✏️ Nuovo testo

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
| `[foto]` | Analizza → applica filtro → prompt → reminder → caption |

**Filtri disponibili — 7 categorie:**

*Stilistici:* Cinematic High-Angle, Dramatic Low-Angle, Glossy Opal, Iridescent, Galaxy Couture, Arabesque, Dissolvence, Ghost Temporal, Long Exposure

*Fantasy & Art:* Stained Glass, Underwater Gold, 3D Synthetic, Graffiti Artist, Cloud Sculpture, LEGO

*Scenografici:* Giantess NYC, Action Figure, Art Doll Exhibition, Toy Store Window, Selfie Stick POV

*Collage:* New Pose, Triple Set, Pastel Clones, Collage 2×2, Photobooth 4×4, Full Body 3×3, 🌟 Y2K Pop Collage (pool 20 pose random)

*Mosaic:* Pet Mosaic 4×4, Mirror Selfie, Triptych GHI

*🎨 Stile Artistico (menu a 2 livelli — 20 artisti):*
- Rinascimento & Classici: Leonardo, Raffaello, Michelangelo, Caravaggio
- Impressionismo & Post: Renoir, Van Gogh, Matisse, Chagall
- Modernismo & Astratto: Klimt, Mirò, Mondrian, Picasso
- Surrealismo: Magritte, Dalì, De Chirico
- Contemporaneo & Pop: Banksy, Lichtenstein, Mucha, Hopper, Basquiat

*Altri:* (vari)

> ⚠️ Dopo ogni prompt Filtro: reminder per caricare l'immagine di riferimento su Flow.

### 📍 Nosurprise
`/start` → "Hai una foto?" Sì/No → formato → Auto/Manuale → prompt → caption

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
| `TELEGRAM_TOKEN_SORPRESA` | Nosurprise |

> ⚠️ **Non scrivere mai chiavi API in file di testo nel repo.**

---

## Quota Gemini

- Modello: `gemini-3-flash-preview` (free tier)
- 20 richieste/giorno per chiave — reset alle 08:00 ora Lisbona
- 5 chiavi separate = **100 richieste/giorno totali**
- `analyze_scene()` usa singolo tentativo — nessuno spreco su fallimento

---

## Infrastruttura

- **Deploy:** Koyeb (un servizio per bot)
- **Health check:** Flask su porta 10000 — necessario per Koyeb
- **Polling:** `infinity_polling` con gestione 409 Conflict (`sleep(15)`) e altri errori (`sleep(5)`)

> ⚠️ **409 Conflict:** Koyeb → servizio → Deployments → stoppare deployment vecchi.

---

## Aggiornare C_shared100.py

1. Aggiornare `SHARED_VERSION` e `SHARED_DATE` nel file
2. Push su GitHub
3. Koyeb redeploy di **tutti** i bot

## Procedura update completa

Ad ogni sessione di modifiche aggiornare:
1. HANDOFF
2. README.md
3. VERSIONI_BOT Excel (CODICE + VERS. CODICE manualmente)

---

## File nel repo

```
C_shared100.py
C_vogue121.py
C_architect130.py
C_atelier124.py
C_filtro204.py
C_nosurprise105.py
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

- `C_shared100.py` — nome fisso, versione interna scala
- Tutti gli altri bot — nome file rispecchia la versione: `C_filtro204.py` = v2.0.4
- Ogni modifica incrementa versione e nome file
- **Mai due file con lo stesso numero di versione**

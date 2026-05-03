# README — Valeria Cross AI · Ecosistema Bot Telegram
**Aggiornato:** 03/05/2026

---

## Versioni attive

| Bot | Versione | File | Deploy |
|-----|----------|------|--------|
| VogueBot | **7.1.3** | `vogue-713.py` | colossal-giselle/vogue |
| ArchitectBot | **9.0.0** | `architect-900.py` | homely-annabelle/thearchitect |
| ATELIER | **4.0.1** | `atelier-401.py` | flexible-denna/cabina |
| Filtro | **6.0.0** | `filtro-600.py` | screeching-jobina/valeriafx |
| SURPRISE | **5.0.7** | `surprise-507.py` | near-damara/sorpresa |
| ~~SorpresaBot~~ | DISMESSA | — | — |

> **Nota:** Nessun bot genera immagini direttamente. Tutti producono prompt da copiare su Flow (Google Labs).

---

## VogueBot 7.1.3
Analizza foto o testo e genera prompt Flow-ready con DNA Valeria Cross.

**Modello:** `gemini-3-flash-preview` (Google AI Studio, tier gratuito)
**Comandi:** `/start` · `/info` · `/dna`
**Flusso:** foto o testo → analisi Gemini → prompt Flow-ready → keyboard (Nuova foto · Riusa prompt · Home)
**Note:** Formato AR rimosso — la scelta viene fatta direttamente su Flow.

---

## ArchitectBot 9.0.0
Genera prompt ottimizzati per Flow/ChatGPT/Grok/Qwen/Meta. Analisi foto con Google AI (solo testo).

**Modello:** `gemini-3-flash-preview` (solo analisi testo/foto — nessuna generazione immagini)

---

## ATELIER 4.0.1
Genera prompt editoriali da foto outfit di riferimento.

**Modello:** `gemini-3-flash-preview`
**Filtri:** Canvas Swimsuit · Selfie Spiaggia · Letto · Spiaggia Editoriale · Beach Club · Yacht · Surf · Riviera '60 · Pool Party · Underwater · Shooting Editorial
**Comandi:** `/start` · `/mosaic` · `/done` · `/formato` · `/settings` · `/info` · `/lastprompt`
**Fix 4.0.1:** Aggiunti import mancanti `google-genai`, `client`, `API_KEY` (erano stati rimossi per errore).

---

## Filtro 6.0.0
Applica filtri stilistici a foto. Include `/mosaic` (2-9 foto).

---

## SURPRISE 5.0.7
Genera scenari editoriali random con pool fissi.

**Modello:** `gemini-3-flash-preview` (caption via Gemini)
**Pool:** 200 location (🇮🇹 IT → 🇵🇹 PT → EU → Mondo, con bandiere) · 100 outfit · 50 stili · 50 pose · 50 sky · 50 mood
**Flusso:** scelta modalità (Auto/Manuale) → scena → caption Gemini → keyboard (📋 Prompt Flow · 🏠 Home) → prompt → keyboard (🎲 Nuova scena)
**5.0.3:** Keyboard semplificata. "Annulla" → "🏠 Home". Rimosso handler ridondante.
**5.0.4–5.0.6:** Versioning incrementale, caption locale migliorata.
**5.0.7:** Caption generata da Gemini (come Atelier). Aggiunti `google-genai`, `client`, `API_KEY`.

---

## Infrastruttura
- **Deploy:** Koyeb · Flask health check porta 10000
- **Generazione immagini:** Flow (Google Labs) + NanoBanana 2
- **Modello AI:** `gemini-3-flash-preview` su Vogue, Atelier e Surprise
- **masterface.png:** SEMPRE primo elemento in contents Gemini (dove applicabile)
- **Repository GitHub:** github.com/valeriacross/Moltbot-Start (deploy Koyeb)

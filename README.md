# README — Valeria Cross AI · Ecosistema Bot Telegram
**Aggiornato:** 12/04/2026

---

## Versioni attive

| Bot | Versione | File | Deploy |
|-----|----------|------|--------|
| ATELIER (ex Cabina) | **3.0.1** | `atelier-301.py` | flexible-denna/cabina |
| SURPRISE | **1.5.6** | `surprise-156.py` | near-damara/sorpresa |
| Filtro | **4.8.5** | `filtro-485.py` | screeching-jobina/valeriafx |
| VogueBot | **6.7.1** | `vogue-671.py` | colossal-giselle/vogue |
| ArchitectBot | **8.2.2** | `architect-822.py` | homely-annabelle/thearchitect |
| ~~SorpresaBot~~ | ~~2.4.0~~ | ~~sorpresa-240.py~~ | ⏸️ sospesa |

---

## ATELIER 3.0.1 (ex CabinaBot)
Genera immagini editoriali da foto outfit di riferimento.

**Filtri disponibili:**
- 🎨 Canvas Swimsuit
- 🤳 Selfie Spiaggia (☀️ / 🌅)
- 🛌 Letto (☀️ / 🌙)
- 🌅 Spiaggia Editoriale
- 🍹 Beach Club
- ⛵ Yacht (☀️ / 🌅)
- 🏄 Surf
- 🎞️ Riviera '60
- 🌊 Pool Party
- 🤿 Underwater
- 🎬 Shooting Editorial (Mosaico 4 foto / Scatti separati)
- ⚡ Generazione rapida

**Comandi:**
- `/start` — menu filtri
- `/mosaic` — collage da 2 a 9 foto (layout automatico, timer 5 min)
- `/done` — forza assemblaggio mosaic
- `/formato` — cambia aspect ratio
- `/settings` — numero foto
- `/info` — stato bot
- `/lastprompt` — ultimo prompt API

---

## SURPRISE 1.5.6
Genera scenari editoriali completamente random.

**Flusso:**
1. `/start` → flag artista (🎨 Con stile artistico / 📷 Solo fotografico)
2. 🎲 Surprise me! → scena estratta
3. Caption generata dallo scenario
4. Vuoi generare? ✅ Sì / 🏠 No
5. Immagine

**Pool:** 65 location · 36 outfit · 20 stili fotografici · 5 artisti + None

---

## VogueBot 6.7.1
Genera da prompt testuale o foto. Modalità: testo libero, faceswap, batch.

## ArchitectBot 8.2.2
Genera prompt ottimizzati per Flow/ChatGPT/Grok/Qwen/Meta. Non usa masterface.

## Filtro 4.8.5
Applica filtri stilistici a foto. Include `/mosaic` (2-9 foto).

---

## Infrastruttura
- **Deploy:** Koyeb · Flask health check porta 10000
- **Modello immagini:** gemini-3-pro-image-preview
- **Modello testo:** gemini-3-flash-preview
- **Quota:** 50 immagini/giorno (piano gratuito)
- **masterface.png:** SEMPRE primo elemento in contents Gemini
- **Repository:** github.com/valeriacross/Moltbot-Start · github.com/valeriacross/il-mio-moltbot

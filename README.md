# README — Valeria Cross AI · Ecosistema Bot Telegram
**Aggiornato:** 20/04/2026

---

## Versioni attive

| Bot | Versione | File | Deploy |
|-----|----------|------|--------|
| ATELIER | **3.4.2** | `atelier-342.py` | flexible-denna/cabina |
| SURPRISE | **2.0.1** | `surprise-201.py` | near-damara/sorpresa |
| Filtro | **5.0.1** | `filtro-501.py` | screeching-jobina/filtro |
| VogueBot | **6.7.1** | `vogue-671.py` | colossal-giselle/vogue |
| ArchitectBot | **8.2.2** | `architect-822.py` | homely-annabelle/thearchitect |
| ~~SorpresaBot~~ | ~~2.4.0~~ | ~~sorpresa-240.py~~ | ⏸️ sospesa |

---

## ATELIER 3.4.2
Genera immagini editoriali da foto outfit di riferimento.

**Filtri disponibili:**
- 🎨 Canvas Swimsuit
- 🤳 Selfie Spiaggia (☀️ / 🌅)
- 🛏️ Letto (☀️ / 🌙)
- 🌅 Spiaggia Editoriale
- 🍹 Beach Club
- ⛵ Yacht (☀️ / 🌅)
- 🏄 Surf
- 🎞️ Riviera '60
- 🌊 Pool Party
- 🤿 Underwater
- 🎬 Shooting Editorial (Mosaico 4 foto / Scatti separati)

**Comandi:**
- `/start` — menu filtri
- `/formato` — cambia aspect ratio
- `/settings` — numero foto
- `/info` — stato bot
- `/lastprompt` — ultimo prompt API

**Novità v3.4.x:**
- Caption generata per tutti i filtri (da outfit_desc, non dal prompt — niente riferimenti alla persona)
- COLOR LOCK con HEX codes in tutti i prompt
- Shooting Editorial salta la scelta formato
- Annulla → loop keyboard invece di fermarsi
- describe_outfit_from_image: OUTFIT+ACCESSORIES prima, HEX per ogni colore, 3000 token

---

## SURPRISE 2.0.1
Genera scenari editoriali completamente random.

**Pool fissi:**
- 84 location (Europa, Italia, Portogallo, Americhe, Asia, Africa, Oceania, Luxury venues)
- 64 outfit con calzature coerenti
- 20 fotografi/stili
- 30 pose fisiche
- 30 sky/lighting
- 30 mood

**Logica coerenza:** Gemini riceve la location estratta e sceglie sky/pose/mood coerenti con essa.

**Flusso:**
1. `/start` → 🎲 Surprise me!
2. Scena estratta dai pool + Gemini per coerenza
3. Caption + Conferma
4. Immagine finale

---

## Filtro 5.0.1
Applica filtri stilistici, scenografici e collage a foto.

**Stilistici:**
- 💧 Dissolvence
- 👻 Ghost Temporal
- 📸 Long Exposure ← nuovo

**Include `/mosaic`** da 2 a 9 foto con layout automatico.

---

## VogueBot 6.7.1
Genera da prompt testuale o foto. Modalità: testo libero, faceswap, batch.

## ArchitectBot 8.2.2
Genera prompt ottimizzati per Flow/ChatGPT/Grok/Qwen/Meta. Non usa masterface.

---

## Infrastruttura
- **Deploy:** Koyeb · Flask health check porta 10000
- **Modello immagini:** `gemini-3-pro-image-preview`
- **Modello testo:** `gemini-3-flash-preview`
- **Quota:** 50 immagini/giorno (piano gratuito)
- **masterface.png:** sempre primo elemento in `contents` Gemini
- **Repository:** `github.com/valeriacross/Moltbot-Start` · `github.com/valeriacross/il-mio-moltbot`

---

## Workflow UPDATE
Quando viene scritto **UPDATE**, bisogna produrre:
- handoff completo aggiornato;
- `README.md` aggiornato;
- `Telegram_Bot_updated.xlsx` aggiornato;
- output finale pronto da salvare su Drive.

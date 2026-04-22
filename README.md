# README — Valeria Cross AI · Ecosistema Bot Telegram
**Aggiornato:** 21/04/2026

---

## Versioni attive

| Bot | Versione | File | Deploy |
|-----|----------|------|--------|
| ATELIER | **3.4.2** | `atelier-342.py` | flexible-denna/cabina |
| **SURPRISE** | **3.0.0** | `surprise-300.py` | near-damara/sorpresa |
| Filtro | **5.0.1** | `filtro-501.py` | screeching-jobina/filtro |
| VogueBot | **6.7.1** | `vogue-671.py` | colossal-giselle/vogue |
| ArchitectBot | **8.2.2** | `architect-822.py` | homely-annabelle/thearchitect |
| ~~SorpresaBot~~ | ~~2.4.0~~ | ~~sorpresa-240.py~~ | ⏸️ sospesa |

---

## SURPRISE 3.0.0
Genera scenari editoriali — automatici o manuali.

**Modalità Automatica:** location dal pool, Gemini sceglie sky/pose/mood coerenti, caption automatica.

**Modalità Manuale:** 6 menu paginati (8 voci/pagina, ◀️ ▶️) — Location → Outfit → Sky → Pose → Mood → Stile. Zero filtro coerenza, libertà totale.

**Pool:** 100 location (30 IT · 20 PT · 10 spiagge specifiche · 50 siti storici iconici) · 50 outfit con colori e calzature · 20 stili · 30 pose · 30 sky · 30 mood

---

## ATELIER 3.4.2
Genera immagini editoriali da foto outfit di riferimento.

**Filtri:** Canvas Swimsuit · Selfie Spiaggia (2v) · Letto (2v) · Spiaggia Editoriale · Beach Club · Yacht (2v) · Surf · Riviera '60 · Pool Party · Underwater · Shooting Editorial

**Novità 3.4.x:** Caption da outfit_desc (no riferimenti alla persona) · COLOR LOCK con HEX · Annulla → loop keyboard · Shooting Editorial salta formato

---

## Filtro 5.0.1
Stilistici: 💧 Dissolvence · 👻 Ghost Temporal · 📸 Long Exposure · + scenografici e collage · `/mosaic` 2-9 foto

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
- **masterface.png:** sempre primo elemento in `contents` Gemini
- **Repository:** `github.com/valeriacross/Moltbot-Start` · `github.com/valeriacross/il-mio-moltbot`

---

## Workflow UPDATE
Quando viene scritto **UPDATE**: handoff + README + XLSX aggiornati, pronti da salvare.

# README — Ecosistema Bot Valeria Cross
**Aggiornato:** 31 Marzo 2026

---

## ECOSISTEMA BOT

```
ARCHITECT (A) = 🖼️/T → Prompt ottimizzato (T2T)
VOGUE (B)     = T/Prompt + A → {Immagine} (T2I) + Batch + /caption
FILTRO (D)    = {Immagine} + Filtro → {Immagine filtrata} (I2I)
CABINA (C)    = 🖼️ costume → {Valeria in costume}
SURPRISE (F)  = 🎲 Gemini sceglie tutto → {Immagine} (T2I libero)
~~SORPRESA~~  = ⏸️ sospesa
```

---

## VERSIONI CORRENTI

| Bot | Versione | File | Stato |
|-----|----------|------|-------|
| SURPRISE | 1.4.1 | `surprise-141.py` | ✅ |
| CabinaBot | 2.3.1 | `cabina-231.py` | ✅ |
| Filtro | 4.8.0 | `filtro-480.py` | ✅ |
| VogueBot | 6.6.3 | `vogue-663.py` | ✅ |
| ArchitectBot | 8.2.1 | `architect-821.py` | ✅ |
| ~~SorpresaBot~~ | 2.4.0 | `sorpresa-240.py` | ⏸️ sospesa |

**Token env:**
- `TELEGRAM_TOKEN` — Vogue
- `TELEGRAM_TOKEN_ARCHITECT` — Architect
- `TELEGRAM_TOKEN_SORPRESA` — Sorpresa + Surprise
- `TELEGRAM_TOKEN_CLOSET` — Cabina
- `TELEGRAM_TOKEN_FX` — Filtro

---

## CAPTION — STATO ATTUALE

| Bot | Caption |
|-----|---------|
| Sorpresa | ⏸️ Sospesa con bot |
| Cabina | ❌ Rimossa — da ricreare |
| Filtro | ❌ Rimossa — da ricreare |
| Vogue | ✅ /caption + pulsante + auto post-gen |
| Architect | ✅ Funziona |
| SURPRISE | ❌ Rimossa — da ricreare |

---

## IDENTITÀ VALERIA CROSS
- 60 anni, uomo italiano (Walter Caponi), viso ovale-rettangolare
- Occhiali Vogue Havana tartaruga scura ottagonali (SEMPRE, mai toccati)
- Barba argento 6-7cm, capelli corti argento
- Corpo femminile: 180cm, 85kg, seno D-cup, hourglass, pelle liscia
- Watermark: `feat. Valeria Cross 👠` — corsivo champagne, bottom center
- Tutti i bot usano `masterface.png` · Architect non usa master face
- Genera con Flow (Google Labs) + NanoBanana 2

---

## REGOLE OPERATIVE
- Ogni modifica = bump versione; file precedente resta vivo
- NON applicare modifiche senza ok di Walter ("Vai" = ok)
- Nomenclatura: Major=`X00`, Minor=`X10`, Patch=`X01`
- Filtro: `filtro-XYZ.py`

---

## VOGUE BOT v6.6.3
**Flow:** foto → Faceswap / Batch → prompt → generazione + caption

**Caption:** `/caption` chiede sempre foto · pulsante `📝 Solo Caption` · auto post-gen
**Comandi:** `/lastprompt` `/caption` `/help` `/info` `/settings`

---

## FILTRO v4.8.0
**Flow:** foto → categoria → filtro → conferma (con prompt) → immagine

**Categorie:** Stilistici · Fantasy & Art · Scenografici · Collage · Altri

**Nuovo:** `🎨 Stile Artistico` in Fantasy — estrae casualmente Magritte/Dalì/De Chirico/Mondrian/Banksy

**Comandi:** `/start` `/reset` `/filtro` `/help` `/info` `/lastprompt` `/mosaic`

---

## CABINA BOT v2.3.1
**Flow:** foto outfit → analisi → prompt → conferma → generazione
**Comandi:** `/start` `/reset` `/formato` `/settings` `/info` `/help` `/lastprompt`

---

## ARCHITECT BOT v8.2.1
**Flow:** testo/immagini → motore → ottimizzazione → caption → prompt
**Motori:** Gemini · Grok · Qwen · ChatGPT · Meta
**Comandi:** `/start` `/reset` `/motore` `/movie` `/stop` `/lastprompt` `/help` `/info`

---

## SURPRISE v1.4.1
**Flow:** "Surprise me!" → scenario Gemini → conferma → generazione

**Assi:** location · cielo · outfit VS/alta moda · stile fotografo · posa · mood
**Nuovo asse:** stile artistico casuale — Magritte, Dalì, De Chirico, Mondrian, Banksy (o nessuno)

**Comandi:** `/start` `/info` `/lastprompt`

---

## NOTE TECNICHE
- **Gemini 2.0 Flash:** shutdown 1 giugno 2026 — tutti i bot già su 3.x ✅
- **Caption Vogue:** usa img_data originale, non il prompt ottimizzato
- **MODEL_TEXT_ID (Flash):** non consuma quota immagini (50/giorno)
- **pending_artistic_style:** preserva lo stile tra _send_confirmation e _run_generation

---

## TODO APERTI
| Bot | Issue | Priorità |
|-----|-------|----------|
| Cabina, Filtro, SURPRISE | Caption da ricreare | 🔴 Alta |
| SURPRISE | D-cup non sempre visibile | 🟡 Media |

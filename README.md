# README — Ecosistema Bot Valeria Cross
**Aggiornato:** 4 Aprile 2026

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
| SURPRISE | 1.4.4 | `surprise-144.py` | ✅ |
| CabinaBot | 2.3.3 | `cabina-233.py` | ✅ |
| Filtro | 4.8.1 | `filtro-481.py` | ✅ |
| VogueBot | 6.7.1 | `vogue-671.py` | ✅ |
| ArchitectBot | 8.2.2 | `architect-822.py` | ✅ |
| ~~SorpresaBot~~ | 2.4.0 | `sorpresa-240.py` | ⏸️ sospesa |

**Token env:**
- `TELEGRAM_TOKEN` — Vogue
- `TELEGRAM_TOKEN_ARCHITECT` — Architect
- `TELEGRAM_TOKEN_SORPRESA` — Sorpresa + Surprise
- `TELEGRAM_TOKEN_CLOSET` — Cabina
- `TELEGRAM_TOKEN_FX` — Filtro

---

## COMPORTAMENTO /start (tutti i bot)
Reset completo: cancella tutti i dizionari di stato + timer attivi. Mostra `✅ Reset completo.` + menu principale.

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
- UPDATE = HANDOFF + README + XLSX + memorie + tabella versioni

---

## VOGUE BOT v6.7.1
**Flusso faceswap:** Flash descrive → prompt + masterface → genera da zero (NO img originale)
**Caption:** `/caption` chiede sempre foto · `📝 Solo Caption` · auto post-gen
**Comandi:** `/start` `/lastprompt` `/caption` `/help` `/info` `/settings`

---

## FILTRO v4.8.1
**Categorie:** Stilistici · Fantasy & Art · Scenografici · Collage · Altri
**Stile Artistico:** Magritte/Dalì/De Chirico/Mondrian/Banksy casuale in Fantasy
**Comandi:** `/start` `/reset` `/filtro` `/help` `/info` `/lastprompt` `/mosaic`

---

## CABINA BOT v2.3.3
**Flow:** foto outfit → analisi → prompt (con preview dual) → conferma → generazione
**Fix:** v_text NameError · execute_generation ritorna sempre tupla
**Comandi:** `/start` `/reset` `/formato` `/settings` `/info` `/help` `/lastprompt`

---

## ARCHITECT BOT v8.2.2
**Flow:** testo/immagini → motore → ottimizzazione → caption → prompt
**Motori:** Gemini · Grok · Qwen · ChatGPT · Meta
**Comandi:** `/start` `/reset` `/motore` `/movie` `/stop` `/lastprompt` `/help` `/info`

---

## SURPRISE v1.4.4
**Assi:** location (categorie iconiche) · cielo · outfit · stile fotografo · posa · mood · stile artistico
**Temperature:** 1.2 · Location da 4 categorie esplicite · sfondo_ok con luoghi reali
**Comandi:** `/start` `/info` `/lastprompt`

---

## NOTE TECNICHE
- **execute_generation:** sempre `return None, str(e)` nel except — mai None implicito
- **Faceswap Vogue:** `img: None` — `caption_img` separato per caption
- **Gemini 2.0 Flash:** shutdown 1 giugno 2026 — tutti i bot già su 3.x ✅
- **MODEL_TEXT_ID (Flash):** non consuma quota immagini

---

## TODO APERTI
| Bot | Issue | Priorità |
|-----|-------|----------|
| Cabina, Filtro, SURPRISE | Caption da ricreare | 🔴 Alta |
| SURPRISE | D-cup non sempre visibile | 🟡 Media |

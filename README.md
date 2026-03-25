# README — Ecosistema Bot Valeria Cross
**Aggiornato:** 25 Marzo 2026

---

## ECOSISTEMA BOT

```
ARCHITECT (A) = 🖼️/T → Prompt ottimizzato (T2T)
VOGUE (B)     = T/Prompt + A → {Immagine generata} (T2I)
FILTRO (D)    = {Immagine generata} + Filtro → {Immagine filtrata} (I2I)
CABINA (C)    = 🖼️ costume + Filtro → {Valeria in costume} (pipeline neutra)
SORPRESA (E)  = 🎲 Random 14 variabili → {Immagine generata} (T2I)
SURPRISE (F)  = 🎲 Gemini sceglie tutto → {Immagine generata} (T2I, completamente libero)
```

---

## VERSIONI CORRENTI

| Bot | Versione | File | Stato |
|-----|----------|------|-------|
| SorpresaBot | 2.1.0 | `sorpresa-210.py` | ✅ deployato |
| CabinaBot | 2.2.0 | `cabina-220.py` | ✅ pronto, verificato |
| Filtro | 4.5.2 | `filtro-452.py` | ✅ pronto |
| VogueBot | 6.2.0 | `vogue-620.py` | ✅ pronto |
| ArchitectBot | 8.1.1 | `architect-811.py` | ✅ pronto |
| SURPRISE | 1.1.2 | `surprise-112.py` | 🧪 in test |

> **Deployati su Koyeb:** Architect 8.0.1 · Vogue 6.0.0 · Sorpresa 2.1.0

**Token env:**
- `TELEGRAM_TOKEN` — Vogue
- `TELEGRAM_TOKEN_ARCHITECT` — Architect
- `TELEGRAM_TOKEN_SORPRESA` — Sorpresa **e** Surprise (stesso token, deploy separato)
- `TELEGRAM_TOKEN_CLOSET` — Cabina
- `TELEGRAM_TOKEN_FX` — Filtro

**Deploy:** tutti su Koyeb — Flask health check obbligatorio su porta 10000

---

## HASHTAG FISSI (tutti i bot)

`#genderfluid #selfexpression #bodypositivity`

---

## IDENTITÀ VALERIA CROSS

- 60 anni, uomo italiano (Walter Caponi), viso ovale-rettangolare
- Occhiali Vogue Havana tartaruga scura ottagonali (SEMPRE presenti, mai toccati con le mani)
- Barba argento 6-7cm, capelli corti argento
- Corpo femminile: 180cm, 85kg, seno D-cup, hourglass
- Pelle liscia (zero peli su tutto il corpo)
- Watermark: `feat. Valeria Cross 👠` — corsivo champagne, piccolo, bottom center
- Tutti i bot usano `masterface.png` (non `master_face.png`)
- Architect non usa master face (genera solo prompt testuali)
- Genera con Flow (Google Labs) + NanoBanana 2
- Crossdresser dal 2009, drag queen fino al 2019

---

## REGOLE OPERATIVE

- Ogni modifica = bump versione; file precedente resta vivo (non sovrascrivere)
- NON applicare modifiche senza esplicito ok di Walter ("Vai" = ok)
- File di lavoro: `/home/claude/` — Output finali: `/mnt/user-data/outputs/`
- Quota Gemini: 50 immagini/giorno (piano gratuito)
- Versione nel filename E versione dentro il file devono essere aggiornate insieme
- 409 Conflict = due istanze in parallelo → restart manuale sul deploy nuovo
- Excel e README: consegnare solo su richiesta esplicita
- HANDOFF: inviare su richiesta o a fine sessione
- Nomenclatura: Major=`X00`, Minor=`X10`, Patch=`X01`
- **Filtro** si chiama `filtro-XYZ.py` (non più `valeriafx-XYZ.py`) dalla versione 4.5.1

---

## SORPRESA BOT v2.1.0

**Flow:** estrazione casuale (11 assi filtrati) → generazione → caption Threads + hashtag

**Variabili:** 14 assi randomizzati inclusi 5 stili artistici (Magritte, Dalì, De Chirico, Mondrian, Banksy) con overrides asse 11

**Note:** filtri FX rimossi dalla variabile random in v2.1.0

**Comandi:** `/start` `/reset` `/lastprompt`

---

## VOGUE BOT v6.2.0

**Flow:** testo/prompt → ottimizzazione → generazione → immagine + caption + hashtag

**Modifiche v6.2.0:**
- Fix `run_refine`: `MASTER_IDENTITY` aggiunto al refine_prompt
- try/except globale in `run_refine` — errori nel thread producono messaggio visibile
- `/lastprompt` disponibile anche dopo modifica fallita

**Comandi:** `/lastprompt` `/help` `/info` `/settings`

---

## FILTRO v4.5.2 (ex ValeriaFX)

**Flow:** foto → scelta categoria → scelta filtro → conferma → immagine filtrata

**Categorie:**
- `stylistic` — Baroque, Arabesque, Crystal, Dissolve, Ghost Temporal...
- `fantasy` — Stained Glass, Underwater, 3D Synthetic, Graffiti, Cloud, **LEGO**, Giantess...
- `collage` — New Pose, Triptych, collage multi-frame
- `altri` — 3D Stereo, Mirror Outfits, Pet Mosaic

**Filtri notevoli:**
- **`arabesque`** *(stylistic)* — massimalismo barocco, palette crimson/oro/cobalto, trasforma tutto tranne viso
- **`lego`** *(fantasy)* — soggetto costruito in mattoncini LEGO con brick explosion cinematografico

**Modifiche v4.5.x:**
- v4.5.0: filtro `🧱 LEGO` aggiunto
- v4.5.1: pulsanti loop dopo `/mosaic`; rinominato da ValeriaFX a Filtro
- v4.5.2: caption generata anche quando bloccata da IMAGE_SAFETY

**Comandi:** `/start` `/reset` `/filtro` `/help` `/info` `/lastprompt` `/mosaic` `/done`

---

## CABINA BOT v2.2.0

**Flow:** foto outfit → analisi → generazione → immagine + caption + hashtag

**Modalità:** Standard · Dual (due varianti con preview prompt)

**Note tecniche:**
- `VALERIA_FACE` testuale come fallback masterface
- `last_prompt` salvato prima della conferma
- `loop_same` preserva `outfit_desc` — **bug "Outfit non trovato" risolto**

**Comandi:** `/start` `/reset` `/formato` `/settings` `/info` `/help` `/lastprompt`

---

## ARCHITECT BOT v8.1.1

**Flow:** testo/immagine → scelta motore → ottimizzazione → output

**Motori:** Gemini · Grok · Qwen · ChatGPT · Meta (Gemini + Grok in prima riga)

**Funzionalità:**
- `/movie` — collage 3×3 cinematografico, 8 registi random
- Anti-mani-occhiali: doppio blocco DNA+STEPS + `review_and_fix`
- `/lastprompt` — salva prompt singolo e album

**Comandi:** `/start` `/reset` `/motore` `/movie` `/lastprompt` `/help` `/info`

---

## SURPRISE v1.1.2 (NUOVO)

**Flow:** "Surprise me!" → Gemini genera scenario JSON → conferma → generazione

**Scenario (temperature 1.8, tutto scelto da Gemini):**
- 📍 Location iconica mondiale
- 🌤 Cielo/atmosfera
- 👗 Outfit alta moda o Victoria's Secret
- 🎨 Stile pittore o fotografo
- 💃 Posa realistica
- ✨ Mood

**Formato:** 2:3 o 16:9 random. Token stesso di SORPRESA, deploy separato.

**Comandi:** `/start` `/info` `/lastprompt`

---

## TODO APERTI

| Bot | Issue | Priorità |
|-----|-------|----------|
| SURPRISE | Integrazione volto da migliorare | 🟡 Media |
| SURPRISE | Caption a volte generica | 🟡 Media |

---

## LEZIONI APPRESE

- **Hashtag fissi:** seconda riga dopo caption
- **Cabina senza face:** `VALERIA_FACE` testuale necessario come fallback
- **Chunking:** prompt superano 4096 chars — chunks da 3800
- **Glasses pose:** doppio blocco DNA+STEPS più efficace
- **loop_same Cabina:** non preservava `outfit_desc`
- **IMAGE_SAFETY Gemini:** non deterministico
- **Artefatti condivisi:** cancellare un artefatto condiviso può eliminare l'intera chat
- **File artefatti:** sopravvivono alla cancellazione — primo punto di recupero
- **run_refine Vogue:** closure in thread — sempre wrappare in try/except
- **SURPRISE two-step:** pipeline T2I + faceswap peggiora l'integrazione — single-step superiore
- **SURPRISE JSON:** max_output_tokens=2500 necessario
- **Gemini contents:** masterface PRIMA del prompt testuale

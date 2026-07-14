# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 14/07/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb | Chiavi |
|-----|------|---------|-------|--------|
| VogueBot | `Vogue_202.py` | 2.0.2 | colossal-giselle/vogue | 2 |
| ArchitectBot | `Architect_302.py` | 3.0.2 | homely-annabelle/thearchitect | 1 |
| AtelierBot | `Atelier_208.py` | 2.0.8 | flexible-denna/atelier | 5 |
| FiltroBot | `Filtro_201.py` | 2.0.1 | screeching-jobina/filtro | 1 |
| SurpriseBot | `Surprise_202.py` | 2.0.2 | surprise1/sorpresa | 1 |

**Shared:** `C_shared100.py` v2.3.18 · **10 API key totali**

---

## Struttura file

```
C_shared100.py       # Libreria condivisa
Vogue_202.py         # Analisi foto/testo → prompt Flow
Architect_302.py     # Prompt testuale completo di un'immagine — nessun DNA Valeria
Atelier_208.py       # Outfit analysis → prompt con filtri (filtro persistente)
Filtro_201.py        # 7 categorie + LEGO + Mosaic + Scarabocchio
Surprise_202.py      # Location + outfit random + /pride + /flag
requirements.txt
README.md
```

---

## Call Gemini per bot

| Bot | Call/foto | Caption | Extra |
|-----|-----------|---------|-------|
| Atelier | 2 | `/caption` on-demand | — |
| Vogue | 2 | `/caption` on-demand | — |
| Architect | 1 | nessuna | prompt testuale completo, nessun DNA |
| Filtro | 1 | `/caption` on-demand | — |
| Surprise | 1 | nessuna | — |

---

## Contatori chiave

Ogni bot con `on_key_use` mostra `🔑 Key N · call #N` ad ogni chiamata Gemini. Nota: `call #N` è un contatore GLOBALE (somma di tutte le chiavi), non per-chiave nonostante l'etichetta — comportamento confermato e voluto da Walter il 14/07/2026, non più considerato un bug. Si azzera:
- Automaticamente ogni giorno alle **08:00 ora di Lisbona** (07:00 UTC)
- Su `/start` (Atelier, Vogue)
- Al riavvio del servizio Koyeb

---

## Dipendenze

```
pyTelegramBotAPI==4.34.0
flask==3.1.3
Pillow>=12.3.0
google-genai>=2.11.0
openpyxl>=3.1.5
```

---

## Variabili d'ambiente (Koyeb)

| Variabile | Descrizione |
|-----------|-------------|
| `TELEGRAM_TOKEN` | VogueBot |
| `TELEGRAM_TOKEN_ARCHITECT` | ArchitectBot |
| `TELEGRAM_TOKEN_CLOSET` | AtelierBot |
| `TELEGRAM_TOKEN_FX` | FiltroBot |
| `TELEGRAM_TOKEN_SORPRESA` | SurpriseBot |
| `GOOGLE_API_KEY` (+_2, +_3, +_4) | Chiavi Gemini — quantità varia per bot |
| `ALLOWED_USERS` | `273003890` |
| `PORT` | `10000` |

---

## Fix robustezza (20/06/2026 → 14/07/2026)

**Chiusura sessione 14/07** — Walter ha testato in produzione e confermato funzionanti: Architect (testo in chat), allineamento `/info` sui 4 bot, ampliamento pool mosaico Atelier, HAIR LOCK v2.0.8, clausola BODY ART Vogue/Atelier, analisi location Surprise, bump `requirements.txt`. Decisioni: contatore `🔑 Key N` resta globale non per-chiave (preferenza esplicita, non più considerato bug); le 5 location con IP Disney nel pool restano invariate (rischio accettato). Corrette anche le 2 celle contaminate nell'Excel (presunta 3ª chiave Vogue/2ª chiave Architect → erano davvero la 4ª/5ª chiave di Atelier, ora nella posizione corretta). Trovato per caso durante quest'ultimo fix e non ancora chiuso: la chiave Google di Surprise e quella di Filtro nell'Excel risultano identiche — da verificare se è un refuso o una condivisione reale su Koyeb; e la cella REQUIREMENTS del foglio BOT riporta ancora le versioni pre-bump di Pillow/google-genai. Dettagli in HANDOFF, sezione 12, punti 22-23.

Il 14/07, ancora sullo stesso punto: il fix del 13/07 (v2.0.7) era incompleto — proteggeva solo un lato (anti-calvizie), non l'altro. Walter ha mostrato output Flow reali (mosaico 4 scatti) con capelli lunghi mossi oltre le spalle, in tutti e 4 gli scatti — coerente, non casuale: con la calvizie bloccata dal negative prompt e nessuna protezione sul lato opposto, Flow è scivolato verso l'altro estremo. HAIR LOCK riscritto in tutte e 3 le funzioni con descrizione quantitativa della lunghezza ("short on the sides and back, nape and ears visible, ending well above the shoulders") + negative prompt esteso su entrambi i lati (bald/shaved/buzzcut/receding hairline E long/shoulder-length/flowing/wavy) (Atelier 207→208). Stesso scope della sessione precedente, solo Atelier.

Sempre il 13/07, terzo giro sullo stesso bot in giornata: Walter ha mostrato output Flow reali (mosaico 4 scatti) con testa completamente calva, nonostante l'identità descriva "short silver-grey hair". Causa verificata nel codice: la descrizione capelli non aveva alcuna protezione da negative prompt in nessuna delle 3 funzioni che costruiscono i prompt di Atelier — a differenza della barba, protetta sia da un blocco MANDATORY nello shared sia da negative prompt locali. Aggiunto "⚠️ HAIR LOCK — ABSOLUTE PRIORITY" + termini negative (bald, shaved head, buzzcut, receding hairline, missing hair, hair loss) in tutte e 3 le funzioni (Atelier 206→207). Scope limitato ad Atelier per scelta esplicita — Vogue usa la stessa identity via shared ma non è stato toccato.

Sempre il 13/07, dopo il giro precedente: Walter ha segnalato — con prompt ed esempi di output Flow alla mano — che il mosaico di 4 scatti di Atelier produceva spesso pose/inquadrature quasi identiche tra loro. Causa reale: le 4 liste di varietà nel ramo mosaic di `build_shooting_prompt()` (pose/framing/expression/angle) avevano solo 4 opzioni ciascuna, una delle quali vaga ("etc."). Ampliate a 10-12 opzioni concrete per categoria (Atelier 205→206). Nessuna modifica al ramo single (un solo scatto, non serve enumerare varietà) né al numero di scatti richiesti (resta fisso a 4 lato prompt — quanti Flow ne restituisca davvero è fuori dal controllo del bot).

Il 13/07: allineamento stringhe `/info` al motore reale `gemini-3.5-flash` — Vogue (201→202), Atelier (204→205), Surprise (201→202). Filtro (200→201) non aveva la stringa da correggere (verificato via grep: `MODEL_ID`/`MODEL_TEXT_ID` erano dead code, mai mostrate all'utente), rimosse come pulizia. Colto in Surprise un conteggio errato adiacente ("200 location" contro le 254 reali di `LOCATION_POOL`) — corretto con `len()` invece di un numero fisso, per evitare che torni a disallinearsi in futuro. Nella stessa giornata, foglio `LOCATION` di `VERSIONI_BOT.xlsx` riscritto da zero con le 254 voci reali estratte via AST da `LOCATION_POOL` (era fermo a 230 righe, disallineato dal codice) — vedi nota su 5 voci con riferimenti a IP Disney trovate nel pool, sezione dedicata in HANDOFF.

Audit completo il 20/06, fix puntuali il 25/06 e 27/06. Modifiche principali: reset giornaliero contatori reso resiliente (shared 2.3.12), `analyze_scene()` ora cattura prop interattivi con campo dedicato `PROPS & ACTIONS` (shared 2.3.13), 5ª chiave API aggiunta per Atelier (shared 2.3.14), rimozione ratio/count e miglioramento fedeltà scena in Atelier (202). Il 01/07: pulizia documentale — requirements (README/xlsx/requirements.txt) riallineati, commento obsoleto corretto in shared (2.3.15). Il 04/07: modello Gemini aggiornato da `gemini-3-flash-preview` a `gemini-3.5-flash` (shared 2.3.16) per risolvere 503 diffusi legati ai limiti del livello preview; corrette 3 assegnazioni chiave errate su Koyeb (Atelier/Surprise/Filtro condividevano/scambiavano chiavi per errore, ora ciascuno ha la propria su progetto Google Cloud distinto). Il 07/07, in due step concordati con Walter dopo test su Atelier con foto a body art elaborato: **step 1** — Atelier (203), blocco "OUTFIT DETAIL LOCK" per contrastare la semplificazione di outfit elaborati, verificato con esito positivo; **step 2** — shared (2.3.17), nuovo campo `BODY ART` in `_ANALYZE_PROMPT` e clausola condizionale "BODY ART EXCEPTION" in `VALERIA_BODY_STRONG`/`SAFE`, **verificato con esito positivo da Walter** (tatuaggi riprodotti fedelmente, zero drift identità). Il secondo 08/07: risolto il testo morto della clausola "BODY ART EXCEPTION" — analisi bot-per-bot ha rivelato che solo Vogue e Atelier hanno un campo BODY ART reale da controllare (Filtro non usa mai il DNA Valeria nei suoi prompt, Surprise non analizza mai foto). Rimossa da `VALERIA_BODY_STRONG`/`SAFE` (shared 2.3.18), isolata in `BODY_ART_EXCEPTION_TEXT` + nuova funzione `body_art_clause()` che la include solo se la scena ha body art reale — applicata a Vogue (201) e Atelier (204). Il 12/07: controllo versioni `requirements.txt` contro PyPI — Pillow e google-genai aggiornati (12.2.0→12.3.0 patch di sicurezza CVE-2026-4775; 2.6.0→2.11.0 dopo verifica del changelog ufficiale, zero breaking change nel range per l'uso che ne fanno questi bot); Architect passato da JSON (3.0.0) a prompt testuale (3.0.1, su richiesta di Walter — il JSON era "ingestibile e non pubblicabile") a testo diretto in chat invece di file scaricabile (3.0.2, coerente con gli altri 4 bot); Surprise (201) — analisi location da foto era limitata a 50 parole, riscritta con lo stesso livello di dettaglio e la stessa struttura a sezioni di Architect (BACKGROUND/LIGHTING/CAMERA/MOOD, senza SUBJECT/OUTFIT dato che qui serve solo la location), messaggio di conferma non più troncato a 200 caratteri, mime_type corretto da hardcoded a rilevato automaticamente.

**Architect — riscrittura completa il 10/07/2026 (v2.0.6 → v3.0.0), poi due correzioni il 12/07/2026 (v3.0.0 → v3.0.1 → v3.0.2).** Cinque tentativi di fix su `/generico` (201→206, dal 25/06 al 10/07 — vedi storico precedente di questa sezione, ora superato) non hanno mai risolto il problema alla radice, perché la causa era strutturale: Architect faceva analisi e scrittura in un'unica chiamata Gemini, senza mai produrre un testo intermedio ispezionabile — lo stesso motivo per cui non poteva nemmeno avere la clausola BODY ART condizionale (vedi sopra). Su richiesta esplicita di Walter, `/generico` e tutta la modalità Testo/Foto sono stati **rimossi interamente**. Nuovo scopo del bot: riceve una foto, restituisce l'analisi completa e fedele della scena — soggetto reale incluso (viso, corpo, capelli, espressione, così come appaiono, nessuna sostituzione), outfit, accessori, body art, sfondo, luce, palette colori — **senza alcun DNA Valeria Cross**. Se il soggetto della foto è Valeria, la descrizione includerà barba/occhiali/corpo di Valeria perché è quello visibile, non perché forzato. La prima versione (3.0.0) consegnava un file `.json` strutturato — Walter l'ha segnalato come "ingestibile" e "non pubblicabile": un JSON va riformattato a mano prima di poterlo usare come prompt. Corretto in 3.0.1: sezioni etichettate in chiaro (SUBJECT/OUTFIT/ACCESSORIES/BODY ART/PROPS & ACTIONS/BACKGROUND/LIGHTING/CAMERA/COLOR PALETTE/MOOD), ancora come file `.txt`. Corretto ulteriormente in 3.0.2, sempre il 12/07: dato che il testo è sufficientemente breve, consegnato ora come testo diretto in chat invece di file, coerente con Vogue/Atelier/Filtro/Surprise. Stesso servizio Koyeb e stesso token Telegram, contenuto internamente ripensato. Comando: `/lastprompt` → `/lastjson` (3.0.0) → di nuovo `/lastprompt` (3.0.1, invariato in 3.0.2). Dettagli completi in `HANDOFF-MASTER`, sezioni 2duodecies, 2terdecies e 2quaterdecies.

Dettagli storici in `HANDOFF-MASTER`, sezioni 2bis, 2ter, 2quater, 2quinquies, 2sexies, 2septies, 2octies, 2novies, 2decies, 2undecies e 2duodecies.

**TODO aperto:** il contatore `🔑 Key N · call #N` mostrato dai bot è in realtà globale (somma di tutte le chiavi), non per-chiave come il nome suggerisce — bug noto in `C_shared100.py`, lasciato volutamente intatto finora su scelta esplicita di Walter. Da correggere in una prossima sessione.

**Risolto il 13/07:** le stringhe `/info` di Vogue (`MODEL_TEXT`), Atelier e Surprise (inline) mostravano ancora `gemini-3-flash-preview` — allineate a `gemini-3.5-flash` (motore reale, shared 2.3.16). **Filtro non aveva bisogno del fix**: verificato via grep che `MODEL_ID`/`MODEL_TEXT_ID` non erano mai referenziate fuori dalla propria dichiarazione — `/info` di Filtro non mostra alcuna stringa modello. Le due costanti morte sono state rimosse (Filtro 2.0.0 → 2.0.1). Colto anche un bug adiacente in Surprise: `/info` dichiarava "200 location" mentre `LOCATION_POOL` ne contiene realmente 254 — corretto usando `len(LOCATION_POOL)` invece di un numero scritto a mano, per non disallinearsi più in futuro se il pool cambia. Vogue → 2.0.2, Atelier → 2.0.5, Surprise → 2.0.2.

**TODO aperto (08/07):** fix Vogue (201) e Atelier (204) per la clausola BODY ART condizionale non ancora testati in produzione — Walter deve verificare con foto con/senza tatuaggi prima di considerarli definitivi.

**TODO aperto (12/07):** `Architect_302.py` (prompt testuale in chat, senza più file) non ancora testato in produzione — Walter deve verificare su Koyeb che il testo arrivi correttamente in chat (chunk multipli se >3800 caratteri) e sia effettivamente pubblicabile/usabile come prompt. Da testare anche con una foto di Valeria, per confermare che la descrizione del soggetto reale includa correttamente barba/occhiali/corpo senza alcun intervento di DNA.

**TODO aperto (12/07):** analisi location dettagliata (BACKGROUND/LIGHTING/CAMERA/MOOD, ex 50 parole), ora in `Surprise_202.py`, non ancora testata in produzione — Walter deve verificare su Koyeb che sia effettivamente più utile della versione breve precedente, e che il messaggio di conferma (senza troncamento) si comporti bene in chat.

## Nota tecnica importante

`review_and_fix()` in C_shared ha un prompt di sistema interno che **forza** il DNA Valeria Cross (viso, corpo, watermark). Non usarla per task che richiedono di rimuovere o alterare quel DNA — usare `gemini.generate()` direttamente con un prompt dedicato, senza chiamare `review_and_fix()`. (Fino al 10/07 l'esempio di riferimento era `/generico` in Architect — rimosso in quella data, vedi sezione dedicata in HANDOFF; Architect ora non usa più `review_and_fix()` né alcun DNA.)

---

## Comandi per bot

### VogueBot
`/start` · `/info` · `/shared` · `/dna` · `/caption`

### ArchitectBot
`/start` · `/help` · `/info` · `/lastprompt` · `/shared`

### AtelierBot
`/start` · `/help` · `/info` · `/lastprompt` · `/caption` · `/shared`

### FiltroBot
`/start` · `/filtro` · `/help` · `/info` · `/lastprompt` · `/caption` · `/mosaic` · `/done` · `/shared`

### SurpriseBot
`/start` · `/flag` · `/pride` · `/help` · `/info` · `/shared` · `/lastprompt`

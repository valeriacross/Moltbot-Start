# Valeria Cross AI — Moltbot

**Ultimo aggiornamento:** 11/07/2026

Sistema multi-bot Telegram per la generazione di prompt Flow con il DNA di Valeria Cross.

---

## Bot attivi

| Bot | File | Versione | Koyeb | Chiavi |
|-----|------|---------|-------|--------|
| VogueBot | `Vogue_201.py` | 2.0.1 | colossal-giselle/vogue | 2 |
| ArchitectBot | `Architect_301.py` | 3.0.1 | homely-annabelle/thearchitect | 1 |
| AtelierBot | `Atelier_204.py` | 2.0.4 | flexible-denna/atelier | 5 |
| FiltroBot | `Filtro_200.py` | 2.0.0 | screeching-jobina/filtro | 1 |
| SurpriseBot | `Surprise_200.py` | 2.0.0 | surprise1/sorpresa | 1 |

**Shared:** `C_shared100.py` v2.3.18 · **10 API key totali**

---

## Struttura file

```
C_shared100.py       # Libreria condivisa
Vogue_201.py         # Analisi foto/testo → prompt Flow
Architect_301.py     # Prompt testuale completo di un'immagine — nessun DNA Valeria
Atelier_204.py       # Outfit analysis → prompt con filtri (filtro persistente)
Filtro_200.py        # 7 categorie + LEGO + Mosaic + Scarabocchio
Surprise_200.py      # Location + outfit random + /pride + /flag
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

Ogni bot con `on_key_use` mostra `🔑 Key N · call #N` ad ogni chiamata Gemini — contatore PER CHIAVE, non globale. Si azzera:
- Automaticamente ogni giorno alle **08:00 ora di Lisbona** (07:00 UTC)
- Su `/start` (Atelier, Vogue)
- Al riavvio del servizio Koyeb

---

## Dipendenze

```
pyTelegramBotAPI==4.34.0
flask==3.1.3
Pillow>=12.2.0
google-genai>=2.6.0
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

## Fix robustezza (20/06/2026 → 10/07/2026)

Audit completo il 20/06, fix puntuali il 25/06 e 27/06. Modifiche principali: reset giornaliero contatori reso resiliente (shared 2.3.12), `analyze_scene()` ora cattura prop interattivi con campo dedicato `PROPS & ACTIONS` (shared 2.3.13), 5ª chiave API aggiunta per Atelier (shared 2.3.14), rimozione ratio/count e miglioramento fedeltà scena in Atelier (202). Il 01/07: pulizia documentale — requirements (README/xlsx/requirements.txt) riallineati, commento obsoleto corretto in shared (2.3.15). Il 04/07: modello Gemini aggiornato da `gemini-3-flash-preview` a `gemini-3.5-flash` (shared 2.3.16) per risolvere 503 diffusi legati ai limiti del livello preview; corrette 3 assegnazioni chiave errate su Koyeb (Atelier/Surprise/Filtro condividevano/scambiavano chiavi per errore, ora ciascuno ha la propria su progetto Google Cloud distinto). Il 07/07, in due step concordati con Walter dopo test su Atelier con foto a body art elaborato: **step 1** — Atelier (203), blocco "OUTFIT DETAIL LOCK" per contrastare la semplificazione di outfit elaborati, verificato con esito positivo; **step 2** — shared (2.3.17), nuovo campo `BODY ART` in `_ANALYZE_PROMPT` e clausola condizionale "BODY ART EXCEPTION" in `VALERIA_BODY_STRONG`/`SAFE`, **verificato con esito positivo da Walter** (tatuaggi riprodotti fedelmente, zero drift identità). Il secondo 08/07: risolto il testo morto della clausola "BODY ART EXCEPTION" — analisi bot-per-bot ha rivelato che solo Vogue e Atelier hanno un campo BODY ART reale da controllare (Filtro non usa mai il DNA Valeria nei suoi prompt, Surprise non analizza mai foto). Rimossa da `VALERIA_BODY_STRONG`/`SAFE` (shared 2.3.18), isolata in `BODY_ART_EXCEPTION_TEXT` + nuova funzione `body_art_clause()` che la include solo se la scena ha body art reale — applicata a Vogue (201) e Atelier (204).

**Architect — riscrittura completa il 10/07/2026 (v2.0.6 → v3.0.0), formato corretto l'11/07/2026 (v3.0.0 → v3.0.1).** Cinque tentativi di fix su `/generico` (201→206, dal 25/06 al 10/07 — vedi storico precedente di questa sezione, ora superato) non hanno mai risolto il problema alla radice, perché la causa era strutturale: Architect faceva analisi e scrittura in un'unica chiamata Gemini, senza mai produrre un testo intermedio ispezionabile — lo stesso motivo per cui non poteva nemmeno avere la clausola BODY ART condizionale (vedi sopra). Su richiesta esplicita di Walter, `/generico` e tutta la modalità Testo/Foto sono stati **rimossi interamente**. Nuovo scopo del bot: riceve una foto, restituisce un file con l'analisi completa e fedele della scena — soggetto reale incluso (viso, corpo, capelli, espressione, così come appaiono, nessuna sostituzione), outfit, accessori, body art, sfondo, luce, palette colori — **senza alcun DNA Valeria Cross**. Se il soggetto della foto è Valeria, la descrizione includerà barba/occhiali/corpo di Valeria perché è quello visibile, non perché forzato. La prima versione (3.0.0) consegnava un file `.json` strutturato — Walter l'ha segnalato come "ingestibile" e "non pubblicabile": un JSON va riformattato a mano prima di poterlo usare come prompt. Corretto in 3.0.1: output ora un file `.txt` con sezioni etichettate in chiaro (SUBJECT/OUTFIT/ACCESSORIES/BODY ART/PROPS & ACTIONS/BACKGROUND/LIGHTING/CAMERA/COLOR PALETTE/MOOD), pronto da copiare e pubblicare senza passaggi intermedi. Stesso servizio Koyeb e stesso token Telegram, contenuto internamente ripensato. Comando rinominato due volte: `/lastprompt` → `/lastjson` (3.0.0) → di nuovo `/lastprompt` (3.0.1, coerente con gli altri bot). Dettagli completi in `HANDOFF-MASTER`, sezioni 2duodecies e 2terdecies.

Dettagli storici in `HANDOFF-MASTER`, sezioni 2bis, 2ter, 2quater, 2quinquies, 2sexies, 2septies, 2octies, 2novies, 2decies, 2undecies e 2duodecies.

**TODO aperto:** il contatore `🔑 Key N · call #N` mostrato dai bot è in realtà globale (somma di tutte le chiavi), non per-chiave come il nome suggerisce — bug noto in `C_shared100.py`, lasciato volutamente intatto finora su scelta esplicita di Walter. Da correggere in una prossima sessione.

**TODO aperto (04/07), ridotto il 10/07:** le stringhe `/info` di Vogue (`MODEL_TEXT`), Filtro (`MODEL_TEXT_ID`), Atelier e Surprise (testo inline) mostrano ancora `gemini-3-flash-preview` nonostante il motore reale sia passato a `gemini-3.5-flash` in shared 2.3.16 — sono costanti locali ai singoli bot, non lette da `C_shared100.py`. Architect è **già corretto** dal 10/07 (riscritto da zero con `/info` aggiornato). Restano da allineare Vogue, Filtro, Atelier, Surprise al prossimo giro di modifiche, insieme all'incremento di versione file per ciascuno.

**TODO aperto (08/07):** fix Vogue (201) e Atelier (204) per la clausola BODY ART condizionale non ancora testati in produzione — Walter deve verificare con foto con/senza tatuaggi prima di considerarli definitivi.

**TODO aperto (11/07):** `Architect_301.py` (formato prompt testuale, ex JSON) non ancora testato in produzione — Walter deve verificare su Koyeb che l'output `.txt` sia effettivamente pubblicabile/usabile come prompt end-to-end (foto → file `.txt` ricevuto in chat → incollabile in Flow). Da testare anche con una foto di Valeria, per confermare che la descrizione del soggetto reale includa correttamente barba/occhiali/corpo senza alcun intervento di DNA.

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

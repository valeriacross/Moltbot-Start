# HANDOFF MASTER — Valeria Cross AI · Moltbot
**Generato:** 12/07/2026, fine sessione (aggiornato da versione 10/07)
**Da:** Walter Caponi
**Per:** prossima sessione Claude

---

## 0. RACCOMANDAZIONE MODELLO

**Usa Sonnet 4.6, modalità ALTA, con ragionamento ATTIVO.**

Motivo: il lavoro richiede precisione su stack trace, AST verification, retry logic, gestione versioni rigorosa. Haiku rischia di reintrodurre bug di indentazione/logica come quelli già visti. "Massima" è overkill per task ripetitivi nella struttura. Ragionamento attivo è specialmente importante per qualsiasi modifica a `C_shared100.py`, il file più fragile e più centrale del progetto.

**Nota sessione 01/07/2026 → 04/07/2026:** entrambe le sessioni sono state svolte su Claude Sonnet 5 (non più disponibile la 4.6 indicata sopra come raccomandazione storica). Il principio resta valido — ragionamento attivo, niente Haiku su modifiche a `C_shared100.py` — va solo riletto sostituendo "Sonnet 4.6" con il modello disponibile più capace al momento.

---

## 1. CHI SONO E COSA FACCIO

Walter Caponi, sviluppatore solo, basato a Lisbona. Progetto: "Valeria Cross AI" — ecosistema di 5 bot Telegram che generano prompt per Flow (Google) per editoriali di alta moda con un personaggio fisso (Valeria Cross). Deploy su Koyeb via push GitHub. Claude è l'unico partner di sviluppo.

**Stile di lavoro richiesto (PERMANENTE — salvato in memoria Claude):**
- Advisor diretto, non assistente compiacente
- Mai iniziare una risposta con accordo/conferma — prima frase deve sfidare un'assunzione, segnalare un gap, o porre una domanda critica
- Indicare confidenza (certo/probabile/ipotesi) quando rilevante
- Vietate frasi: "ottima domanda", "hai perfettamente ragione", "assolutamente", "decisamente"
- In disaccordo: spiegare motivo, proporre alternativa, indicare rischio — poi discutere insieme, non insistere ciecamente
- Risposta scomoda/diretta PRIMA, senza preamboli
- Non cedere un punto senza nuove informazioni concrete

**Regole operative TASSATIVE:**
1. MAI modificare o creare file senza "Vai" esplicito di Walter
2. `C_shared100.py` sempre in-place — mai rinominare
3. Tutti gli altri bot → nomi incrementali — **MAI riusare un nome file già deployato su Koyeb**, anche per errore
4. Testare SEMPRE con `ast.parse()` + verifica integrità decorator (`@bot.message_handler`, `@bot.callback_query_handler`) prima di consegnare
5. Presentare sempre con `present_files`
6. Mai scrivere chiavi API nei file
7. Fare TUTTE le domande necessarie prima di procedere — attendere sempre "Vai" esplicito, anche se sembra ovvio cosa fare
8. Ad ogni update richiesto: HANDOFF + README + VERSIONI_BOT Excel, tutti e tre insieme
9. Modifiche a shared: aggiornare VERSION, SHARED_VERSION, SHARED_DATE, docstring iniziale con "Versione: X.X.X"
10. **`review_and_fix()` in C_shared FORZA il DNA Valeria nel suo prompt di sistema interno — non è bypassabile passando istruzioni diverse.** Per qualsiasi task che richiede rimuovere/alterare quel DNA, usare `gemini.generate()` direttamente con un prompt di sistema dedicato (vedi esempio `/generico` in Architect)
11. **Prima di ogni bump di versione, verificare con `grep "^VERSION"` la versione REALE nel file su cui si sta lavorando** — non fidarsi della cronologia HANDOFF, perché può essere disallineata dal file effettivamente caricato dall'utente

---

## 2. STATO FILE ATTUALE (12/07/2026)

| File | Versione | Koyeb service | Run command | Chiavi API |
|------|---------|---------------|--------------|-----------|
| `C_shared100.py` | **2.3.18** | (comune a tutti) | — | — |
| `Vogue_201.py` | **2.0.1** | colossal-giselle/vogue | `python Vogue_201.py` | 2 |
| `Architect_302.py` | **3.0.2** | homely-annabelle/thearchitect | `python Architect_302.py` | 1 |
| `Atelier_204.py` | **2.0.4** | flexible-denna/atelier | `python Atelier_204.py` | 5 |
| `Filtro_200.py` | **2.0.0** | screeching-jobina/filtro | `python Filtro_200.py` | 1 |
| `Surprise_201.py` | **2.0.1** | surprise1/sorpresa | `python Surprise_201.py` | 1 |

**Totale chiavi API: 10** (Atelier 5 + Vogue 2 + Architect 1 + Filtro 1 + Surprise 1) — tutte e 10 confermate su progetti Google Cloud distinti il 04/07 (vedi sezione 2quinquies). Prima di quella verifica, Filtro e Surprise condividevano la stessa chiave fisica per un errore di assegnazione: risolto.

Repository: `valeriacross/Moltbot-Start` — region Frankfurt.

**Nota versioning (corretta il 10/07):** il numero nel nome file **corrisponde sempre esattamente** alla VERSION interna, senza punti (es. `2.0.4` → `Atelier_204.py`, `3.0.2` → `Architect_302.py`) — non è un contatore progressivo indipendente. Su un salto di versione non incrementale (es. `2.0.6` → `3.0.0`), il nome file deve riflettere il nuovo numero di versione per intero, non "il prossimo della sequenza". Vedi sezione 2duodecies per il dettaglio dell'errore fatto e corretto in questa data.

**Nota chiavi (25/06):** una chiave spostata da Architect (2→1) ad Atelier (4→5). `C_shared100.py` ora legge fino a `GOOGLE_API_KEY_5`.

---

## 2quindecies. SESSIONE 12/07/2026 (continua) — SURPRISE 2.0.1, ANALISI LOCATION DETTAGLIATA

Walter ha segnalato che l'analisi location da foto di Surprise (`handle_location_photo`) genera un testo "estremamente breve e non dettagliato" — mostrando come esempio una descrizione da 200 caratteri, e chiedendo che il livello di analisi sia uguale a quello di Architect.

**Causa trovata:** `location_prompt` chiedeva esplicitamente *"Return a single concise paragraph of maximum 50 words"* — non era un problema del messaggio di conferma, era la generazione stessa a essere volutamente corta. In più, il messaggio di conferma troncava comunque a 200 caratteri (`location_text[:200]`) qualunque cosa venisse generata — un secondo taglio sopra il primo.

**Modifiche applicate: `Surprise_200.py` → `Surprise_201.py`.**
1. `location_prompt` riscritto con la stessa struttura a sezioni di `ANALYSIS_PROMPT` in Architect — `BACKGROUND:`, `LIGHTING:`, `CAMERA:`, `MOOD:` — ma **senza** `SUBJECT:`/`OUTFIT:`/`ACCESSORIES:`/`BODY ART:`, esclusi di proposito: questa funzione serve solo a catturare la location, l'outfit lo genera Surprise stesso in modo casuale altrove nel bot, non ha senso descriverlo qui. Tolto il limite di 50 parole.
2. `max_tokens` aumentato da default (3000) a 2048 esplicito — in realtà il default era già sufficiente, ma esplicitato per chiarezza dato l'output più lungo atteso.
3. Messaggio di conferma: non più troncato a 200 caratteri — ora mostra il testo intero, a pezzi da 3800 caratteri se necessario (stesso pattern di Vogue/Architect).
4. **Colto anche un bug adiacente non segnalato da Walter:** `mime_type` era hardcoded a `"image/jpeg"` invece di rilevato con `detect_mime_type()` — corretto, ora supporta correttamente anche PNG/WebP come gli altri bot. Segnalato esplicitamente nel changelog come fix aggiuntivo, non richiesto ma a rischio minimo e coerente con lo standard degli altri bot.

`ast.parse()` superato. Diff verificato riga per riga contro l'originale — solo il blocco `handle_location_photo` toccato (prompt, mime detection, messaggio di conferma), nessun'altra parte di Surprise modificata (scenario random, `/pride`, `/flag` invariati).

**Non ancora testato in produzione.** Da verificare su Koyeb: (a) upload di una foto location → le 4 sezioni arrivano complete e dettagliate in chat, non più il paragrafo generico di prima; (b) il testo completo (non più troncato) si comporta bene con chat lunghe, chunking se necessario; (c) foto in formato PNG/WebP (non solo JPEG) → confermare che il fix mime_type funzioni.

---

## 2quaterdecies. SESSIONE 12/07/2026 (continua) — REQUIREMENTS.TXT E ARCHITECT 3.0.2

Due task distinti nella stessa sessione, dopo la conferma di Architect 3.0.1.

**1. Controllo `requirements.txt` contro PyPI, pacchetto per pacchetto.** Risultato:

| Pacchetto | Nel file | Ultima su PyPI | Esito |
|---|---|---|---|
| `pyTelegramBotAPI` | `==4.34.0` | 4.34.0 (3 giu 2026) | già aggiornato |
| `flask` | `==3.1.3` | 3.1.3 (19 feb 2026) | già aggiornato |
| `Pillow` | `>=12.2.0` | 12.3.0 (1 lug 2026) | **aggiornato** — patch di sicurezza CVE-2026-4775 (libtiff) |
| `google-genai` | `>=2.6.0` | 2.11.0 (9 lug 2026) | **aggiornato** — dopo verifica changelog |
| `openpyxl` | `>=3.1.5` | 3.1.5 | già aggiornato |

Per `google-genai`, il salto di 5 versioni minori ha richiesto una verifica dedicata: changelog ufficiale (`github.com/googleapis/python-genai/blob/main/CHANGELOG.md`) controllato riga per riga da 2.6.0 a 2.10.0 (2.11.0 non ancora comparso nel changelog al momento del controllo). Zero breaking change nel range — solo aggiunte (nuovi campi/tool, supporto `gemini-3.5-flash` che già usiamo) e fix su funzionalità che questi bot non toccano (Live API, Interactions API, Computer Use, generazione video). Unica nota rilevante, in 2.9.0: *"l'implementazione delle Interactions è stata completamente sostituita, la superficie pubblica dell'API resta invariata"* — refactor interno, non visibile per chi chiama `generate_content()` in forma base (`contents`, `safety_settings`, `max_output_tokens`) come fanno tutti i bot di questo progetto tramite `GeminiClient.generate()`.

**`requirements.txt` aggiornato:** `Pillow>=12.2.0` → `>=12.3.0`, `google-genai>=2.6.0` → `>=2.11.0`. Commento in testa al file esteso con la data e il ragionamento, incluso un promemoria: se un deploy si rompe dopo questo bump, controllare il changelog di 2.11.0 specificamente (non disponibile al momento del controllo). `pyTelegramBotAPI` e `flask` restano pinnati come prima, nessuna modifica.

**2. `Architect_301.py` → `Architect_302.py`.** Walter ha fatto notare che, essendo il prompt testuale sufficientemente breve (a differenza del JSON verboso della 3.0.0), non serve consegnarlo come file — coerente con Vogue/Atelier/Filtro/Surprise, che mandano tutti il risultato come testo diretto in chat. Aggiunta `send_prompt_text()`: stesso pattern di chunking a 3800 caratteri già usato in Vogue (senza bottoni post-prompt, non pertinenti qui). Rimossi `bot.send_document()`, `io.BytesIO`, la generazione del nome file per ogni foto, e l'import `io` (non più usato). `last_prompt` ora memorizza il testo puro invece della tupla `(testo, filename)` — semplificato. `/lastprompt` ora reinvia il testo in chat invece di un file.

`ast.parse()` superato per entrambi i punti. Diff verificato riga per riga contro la 301 — solo la logica di consegna toccata (file → testo inline), nessuna modifica al prompt di analisi (`ANALYSIS_PROMPT`) né alla logica di download della foto.

**Non ancora testato in produzione — nessuno dei due task.** Da verificare: (a) `requirements.txt` — che un rebuild Koyeb con le nuove versioni non rompa nulla (Pillow/google-genai non sono mai stati testati su queste versioni specifiche su questo stack, stesso tipo di cautela già usata per `pyTelegramBotAPI` 4.34.0); (b) Architect 302 — che il testo arrivi correttamente in chat, con chunk multipli se supera 3800 caratteri, e che `/lastprompt` funzioni come atteso.

---

## 2terdecies. SESSIONE 12/07/2026 — ARCHITECT 3.0.1, DA JSON A PROMPT TESTUALE

Walter ha testato Architect 3.0.0 (output JSON) e lo ha giudicato "ingestibile" e "non pubblicabile" — un JSON strutturato richiede una riformattazione manuale prima di poter essere usato come prompt per una nuova generazione, il che vanifica l'utilità pratica dello strumento.

**Richiesta di Walter:** output come file di testo, in formato prompt — non JSON.

**Modifiche applicate: `Architect_300.py` → `Architect_301.py`.**
- `ANALYSIS_PROMPT` riscritto da schema JSON a sezioni etichettate in chiaro (stesso stile di `_ANALYZE_PROMPT` in shared: `OUTFIT:`, `ACCESSORIES:`, `BACKGROUND:`, ecc.), con l'aggiunta di una sezione `SUBJECT:` che descrive per intero il soggetto reale (viso, capelli, espressione, corpo, posa) — assente da `_ANALYZE_PROMPT` di shared per design, ma necessaria qui dato che non c'è alcun DNA da iniettare al suo posto.
- Rimossa tutta la logica di parsing/validazione JSON: `_strip_json_fences()`, `json.loads()`, il retry su `JSONDecodeError`. Un testo libero non ha una sintassi da validare come un JSON — `analyze_image_full()` ora ritorna semplicemente il testo grezzo (`.strip()`) o un messaggio d'errore.
- Rimosso `import json` (non più usato).
- File consegnato come **.txt** invece di **.json** (`prompt_{file_unique_id}.txt`).
- Comando **`/lastjson` → di nuovo `/lastprompt`** (coerente con la convenzione degli altri bot del progetto) — stato `last_json` rinominato `last_prompt`.
- Aggiornati testi di `/start`, `/help`, `/info` per riflettere output testuale invece di JSON.
- `VERSION` 3.0.0 → 3.0.1 — patch all'interno della stessa riscrittura maggiore (10/07), non un nuovo cambio di scopo: la funzione resta "foto → descrizione completa, nessun DNA", cambia solo il formato di consegna.

`ast.parse()` superato. Diff verificato riga per riga contro la 300 — solo il prompt di analisi, la funzione `analyze_image_full()`, i testi dei comandi, e il nome/estensione del file toccati. Nessuna modifica alla logica di download/upload della foto né all'executor.

**Non ancora testato in produzione.** Da verificare su Koyeb: (a) foto normale → file `.txt` con le 10 sezioni etichettate, testo scorrevole e effettivamente incollabile in Flow; (b) foto di Valeria → conferma che SUBJECT descriva correttamente barba/occhiali/corpo; (c) `/lastprompt` → reinvia lo stesso file senza rianalizzare; (d) verificare a occhio che Gemini rispetti davvero il formato richiesto (10 sezioni, niente JSON/markdown residuo) — senza più un parser che lo validi automaticamente, un'eventuale deviazione dal formato passerebbe inosservata finché qualcuno non la legge.

---

## 2duodecies. SESSIONE 10/07/2026 (continua) — ARCHITECT RISCRITTO DA ZERO (v2.0.6 → v3.0.0)

Walter ha segnalato che il raddoppio del debounce (2.0.6, sezione 2undecies) non ha risolto nulla — "/generico non funziona, niente da fare" — e ha deciso di cambiare approccio radicalmente invece di continuare a inseguire il sintomo.

**Decisione di Walter, comunicata con 4 punti chiari:**
1. Rimozione totale del comando `/generico` così com'era.
2. Nuova funzione: JSON puro e dettagliato di una qualsiasi immagine, **senza alcun DNA Valeria**.
3. Rimozione della scelta Testo/Foto iniziale — Architect riceve solo foto, genera un'analisi ultra-dettagliata della scena da ogni punto di vista.
4. Motivazione esplicita: Atelier e Vogue coprono già il lavoro con DNA Valeria — non serve un terzo bot che fa la stessa cosa.

**Prima di scrivere codice, chiarite 4 cose con Walter (tutte confermate):**
1. Se l'immagine di riferimento è di Valeria, il JSON deve descriverla com'è (barba, occhiali, corpo) — non è un problema, anzi è corretto: nessuna sostituzione, descrizione fedele di qualunque soggetto sia nella foto.
2. Output come **file .json** scaricabile via Telegram (`bot.send_document()`), non testo in chat — elimina alla radice ogni problema di lunghezza messaggio che ha afflitto `/generico` per 6 versioni (201→206).
3. Rimozione totale, non solo di `/generico`: anche modalità testo, `generate_monolith_prompt()`, `GENERICO_SYSTEM_PROMPT`, tutto lo stato `pending_generico`/`_generico_state`.
4. Stesso servizio Koyeb (`homely-annabelle/thearchitect`), stesso token (`TELEGRAM_TOKEN_ARCHITECT`) — non un bot nuovo, lo stesso contenitore ripensato dentro.

**Perché questo risolve il problema alla radice, non solo il sintomo:** ogni fix precedente su `/generico` (201-206, sezioni 2ter/2octies/2undecies) ha inseguito un sintomo diverso senza mai toccare la causa strutturale — Architect faceva analisi e scrittura in un'**unica chiamata Gemini**, senza mai produrre un testo intermedio ispezionabile. Questo è anche il motivo per cui, in sezione 2decies, Architect non ha mai potuto avere la clausola BODY ART condizionale come Vogue/Atelier. Passando a "foto → JSON puro", quel problema strutturale semplicemente non esiste più: il JSON stesso È il testo intermedio ispezionabile, e non c'è più nessun DNA da forzare o da compensare.

**Riscrittura completa: `Architect_206.py` → `Architect_300.py`.** Dato il volume di codice rimosso rispetto a quello nuovo, il file è stato ricreato da zero invece di editato incrementalmente — un diff riga-per-riga contro la 206 non sarebbe stato significativo. Verificato invece: `ast.parse()` superato; nessun riferimento residuo a `VALERIA_*`, `generic`/`GENERICO`, `user_mode`, `get_mode_kb`/`get_after_prompt_kb`, `EDITORIAL_WRAPPER`, `review_and_fix`, `sanitize_user_input`, `analyze_scene`, `build_valeria_identity`, `BODY_ART_EXCEPTION` (verificato via grep, zero occorrenze fuori dai commenti che documentano cosa è stato rimosso); tutti gli import usati almeno una volta nel corpo del file (verificato via `ast.walk`); schema JSON di esempio validato con `json.loads()`.

**Cosa contiene la 207:**
- `ANALYSIS_PROMPT`: un unico prompt di analisi, autonomo — **non** riusa `analyze_scene()` di shared, perché quella funzione è deliberatamente cieca sul soggetto (per design, dato che negli altri bot il soggetto viene sempre sostituito dal DNA). Qui serve l'esatto opposto: descrizione letterale e completa del soggetto reale (viso, corpo, capelli, espressione, posa) oltre a outfit, accessori, body art, props, sfondo, luce, camera, palette colori, mood.
- `analyze_image_full(img_bytes)`: chiama Gemini con l'immagine, richiede JSON puro (no markdown fence), fa un secondo tentativo se il primo non produce JSON valido (`json.loads()` fallito), altrimenti ritorna l'errore.
- `handle_photo()`: unico handler di contenuto — scarica la foto, chiama `analyze_image_full()`, invia il risultato come file `.json` via `bot.send_document()` con `io.BytesIO`.
- `handle_text()`: risponde con un messaggio guida ("inviami una foto") per chi scrive per abitudine — nessuna modalità testo residua.
- `/lastjson` (sostituisce `/lastprompt`): reinvia l'ultimo file JSON generato senza rianalizzare la foto.
- `/start`, `/help`, `/info`, `/shared`: aggiornati al nuovo scopo. `/info` mostra correttamente `gemini-3.5-flash` (motore attuale) — a differenza degli altri 4 bot, qui non c'è nessuna stringa da disallineare perché il file è stato scritto da zero oggi.

**Non ancora testato in produzione.** Da verificare su Koyeb: (a) foto normale → JSON completo e valido ricevuto come file; (b) foto di Valeria → conferma che la descrizione del soggetto include correttamente barba/occhiali/corpo senza intervento di DNA; (c) `/lastjson` dopo una foto → reinvia lo stesso file senza rianalizzare; (d) caso limite — immagine che Gemini rifiuta di analizzare o restituisce JSON non valido anche al secondo tentativo → verificare che il messaggio d'errore sia chiaro all'utente.

**Nota per la prossima sessione:** con Architect ora completamente scollegato dal DNA Valeria, l'unico posto nel progetto dove ancora si menziona `/generico` come pattern di riferimento era la sezione "Nota tecnica importante" del README — corretto in questa sessione. Verificare che non restino altri riferimenti a `/generico` in HANDOFF sezioni precedenti (quelle storiche restano intenzionalmente invariate come registro, non vanno riscritte).

**Correzione (stesso giorno, post-consegna):** il file era stato consegnato inizialmente come `Architect_207.py` (incrementato meccanicamente da 206, seguendo l'abitudine di incrementare di 1 il numero nel nome a ogni modifica) invece di `Architect_300.py`. Walter ha fatto notare che il nome file ha **sempre** corrisposto esattamente alla VERSION interna in ogni bot di questo progetto (es. `Atelier_204.py` → `2.0.4`, `Architect_206.py` → `2.0.6`) — non è un contatore progressivo indipendente come inizialmente spiegato per errore, è una corrispondenza 1:1 nome↔versione. Il salto di versione 2.0.6 → 3.0.0 andava riflesso nel nome come `300`, non come "il prossimo numero della sequenza". Corretto: file rinominato `Architect_300.py`, stesso contenuto, nessuna modifica al codice. **Promemoria per ogni bump di versione futuro, specialmente su salti non incrementali (x.0.0):** il numero nel nome file deve sempre essere i tre cifre della VERSION senza punti, mai un semplice "+1" dal nome precedente.

---

## 2undecies. SESSIONE 10/07/2026 — ARCHITECT 2.0.6, DEBOUNCE /generico RADDOPPIATO (SUPERATO DA 2duodecies)

Walter ha segnalato che `/generico` continua a tagliare i prompt lunghi generati da Atelier, chiedendo di "raddoppiare il numero di caratteri".

**Verifica fatta prima di agire:** non esiste alcun limite di caratteri sul testo in ingresso nel codice. `full_text = "".join(st["chunks"])` in `_fire_generico()` ricostruisce tutti i chunk bufferizzati senza tagli; `make_generic()` chiama Gemini con `max_tokens=8192` (~32.000 caratteri), ampiamente sufficiente per qualunque prompt di Atelier. Segnalato esplicitamente a Walter che la sua richiesta letterale ("raddoppia i caratteri") non corrisponde a un parametro esistente nel codice.

**Ipotesi più probabile, non confermata da log:** i prompt mosaico di Atelier (4 scatti) possono superare gli 8-10.000 caratteri — Telegram li spezzerebbe quindi in 3 o più messaggi invece di 2. Con più pezzi in arrivo, è più facile che il debounce di 1.5s (introdotto in Architect 2.0.3, sezione 2octies) scatti prima che l'ultimo pezzo sia arrivato, tagliando la coda del testo per un problema di tempistica, non di caratteri.

**Fix applicato: `Architect_205.py` → `Architect_206.py`.** Raddoppiato `_GENERICO_DEBOUNCE` da 1.5 a 3.0 secondi — unico parametro del codice che mappa ragionevolmente sulla richiesta di Walter, dato che un vero limite di caratteri non esiste. `ast.parse()` superato, diff verificato riga per riga — solo changelog, version bump e la costante toccati.

**Non confermato con certezza — da monitorare.** Se il taglio persiste anche con 3 secondi di debounce, il prossimo passo NON è raddoppiare ulteriormente alla cieca, ma aggiungere un log con timestamp per ogni chunk ricevuto in `handle_text()`, per misurare il ritardo reale tra un pezzo e l'altro invece di ipotizzarlo. Testare con lo stesso prompt mosaico lungo che ha fatto emergere il problema.

---

## 2decies. SESSIONE 08/07/2026 (continua) — SHARED 2.3.18, CLAUSOLA BODY ART RESA CONDIZIONALE

Ripresa la discussione rimandata in sezione 2octies: la clausola "BODY ART EXCEPTION" (shared 2.3.17) compariva in ogni prompt generato, anche con `BODY ART: None`, come testo condizionale inerte nel caso comune.

**Analisi bot-per-bot (verificata leggendo il codice, non assunta) prima di agire:**
- **Atelier**: passa sempre da `analyze_scene()`, ha un vero campo BODY ART — candidato pulito.
- **Vogue**: passa da `analyze_scene()` solo sul percorso foto (`build_prompt()`, usa `VALERIA_DNA`); il percorso testo (`handle_text`) non ha un campo BODY ART, `body_art_clause()` restituirà sempre stringa vuota lì — comportamento invariato.
- **Architect**: fa analisi e scrittura in un'**unica chiamata Gemini** (`generate_from_image`/`generate_monolith_prompt`), senza mai produrre un campo BODY ART esterno ispezionabile — **non può avere una versione condizionale**, strutturalmente.
- **Filtro**: importa `VALERIA_DNA`/`build_valeria_identity`/`VALERIA_FACE`/`VALERIA_BODY_STRONG`/`VALERIA_BODY_SAFE`/`VALERIA_WATERMARK`/`VALERIA_NEGATIVE` ma **non li usa mai** nei prompt reali (`_run_generation`, `_run_mirror` costruiscono i prompt solo da `outfit_desc` + filtro, con istruzione esplicita all'utente di caricare anche la foto originale su Flow). Import morti, non pertinenti a questo problema — non toccato.
- **Surprise**: **non chiama mai `analyze_scene()`** — genera scenari casuali (location + outfit) senza analizzare alcuna foto. Costruisce l'identità **inline 3 volte** (non tramite `VALERIA_DNA`/`build_valeria_identity()`, duplicazione preesistente non toccata qui) usando `VALERIA_FACE + VALERIA_BODY_STRONG` direttamente. La clausola era quindi sempre e comunque morta lì — si risolve gratis togliendola dalla fonte comune, senza toccare il file di Surprise.

**Confermato con Walter:** procedere su shared + Vogue + Atelier. Su Architect (che non può essere condizionale): mantenere la clausola sempre presente, nessuna modifica di comportamento.

**Complicazione tecnica scoperta in fase di progettazione, segnalata a Walter prima di procedere:** `VALERIA_DNA` è la STESSA costante condivisa da Vogue e Architect. Ripulirla per risolvere Vogue avrebbe tolto la clausola anche ad Architect come effetto collaterale — in contraddizione con "lascialo com'è". Risolto isolando il testo della clausola in una costante dedicata (`BODY_ART_EXCEPTION_TEXT`) che Architect concatena esplicitamente, così da restare comportamentalmente identico pur cambiando la fonte.

**Modifiche applicate:**

1. **`C_shared100.py` 2.3.17 → 2.3.18.** Rimossa "BODY ART EXCEPTION" da `VALERIA_BODY_STRONG` e `VALERIA_BODY_SAFE` (tornano alla forma pre-2.3.17, formattazione `\n\n` finale ripristinata esattamente). Aggiunta `import re`. Aggiunta `BODY_ART_EXCEPTION_TEXT` (stesso testo, costante isolata) e `body_art_clause(scene_description)` — restituisce il testo solo se il campo `BODY ART:` nella scena non è "None"/assente (regex case-insensitive, testato su entrambi i casi), altrimenti stringa vuota. `ast.parse()` superato.
2. **`Vogue_200.py` → `Vogue_201.py`.** Import `body_art_clause`. In `build_prompt()`, inserito `body_art_clause(scene_description)` subito dopo `{VALERIA_DNA}`.
3. **`Atelier_203.py` → `Atelier_204.py`.** Import `body_art_clause`. Inserito `body_art_clause(outfit_description)`/`body_art_clause(outfit_desc)` dopo il blocco OUTFIT DETAIL LOCK in `build_full_prompt()` e in entrambi i rami (single/mosaic) di `build_shooting_prompt()` — posizione coerente in tutti e 3 i punti, subito prima di BACKGROUND LOCK/NEGATIVE PROMPT.
4. **`Architect_204.py` → `Architect_205.py`.** Import `BODY_ART_EXCEPTION_TEXT`. Concatenato direttamente dopo `{VALERIA_DNA}` in entrambi i punti di generazione (testo e immagine) — stesso comportamento di prima, solo la fonte del testo è cambiata da "dentro VALERIA_BODY_STRONG" a "costante dedicata concatenata esplicitamente qui".

Tutti e 4 i file verificati con `ast.parse()` e diff riga per riga contro la versione precedente — nessuna riga estranea toccata in nessuno dei 4.

**Non ancora testato in produzione da Walter** — nessuno dei 3 bot (Vogue 201, Atelier 204, Architect 205) è stato ancora provato dopo questa modifica. Da verificare: (a) Vogue/Atelier con foto senza tatuaggi → prompt più corto, nessuna clausola; (b) Vogue/Atelier con foto con tatuaggi (es. quella del 07/07) → clausola presente, generazione fedele come nella verifica già fatta su Atelier 203; (c) Architect → comportamento invariato, clausola sempre presente come prima.

---

## 2novies. SESSIONE 08/07/2026 — ARCHITECT 2.0.4, GENERICO_SYSTEM_PROMPT E BODY ART

Walter ha spiegato il vero scopo di `/generico`, mai documentato esplicitamente prima: workflow reale è foto → Atelier → prompt con DNA Valeria → Flow → immagine generata → pubblicazione su Threads → follower chiede "come ottengo quell'immagine" → Walter gli passa la versione `/generico` del prompt, pensata per essere riusabile con qualsiasi LLM e una foto di riferimento personale del follower. Questo eleva la posta in gioco su `/generico`: non deve solo "sembrare pulito", deve essere davvero riutilizzabile da uno sconosciuto.

**Osservazione emersa da questo contesto:** `GENERICO_SYSTEM_PROMPT` (introdotto prima dell'esistenza del campo BODY ART, shared 2.3.17) non menzionava tatuaggi/body art nella lista di elementi identitari da rimuovere. La descrizione dell'eventuale body art (nella sezione "Reference image analysis" del prompt, accanto a OUTFIT/COLOR PALETTE) rischiava quindi di essere mantenuta nella versione generica insieme al resto della scena, invece di essere trattata come marker identitario del soggetto specifico fotografato (alla pari di barba/corpo di Valeria).

**Decisione di Walter:** i tatuaggi vanno rimossi da `/generico` con lo stesso criterio della barba di Valeria — appartengono allo specifico soggetto nella foto di riferimento (che sia Valeria via DNA fisso, o una persona reale fotografata con tatuaggi veri), non alla ricetta outfit/scena che il follower deve poter riusare.

**Fix applicato: `Architect_203.py` → `Architect_204.py`.** Esteso `GENERICO_SYSTEM_PROMPT`: aggiunta esplicita di "body art or skin markings (tattoos, body paint...)" alla lista di elementi da rimuovere, con la stessa motivazione della barba; aggiunta istruzione esplicita di rimuovere/neutralizzare la riga `BODY ART:` nella sezione "Reference image analysis" se presente. Nessuna modifica alla logica di debounce introdotta in 2.0.3. `ast.parse()` superato, diff verificato riga per riga — solo il blocco `GENERICO_SYSTEM_PROMPT` toccato.

**Non ancora testato in produzione** — Walter deve verificarlo con un caso reale (foto di riferimento con tatuaggi visibili, come quella usata per lo step 2 del 07/07) prima di considerarlo definitivo.

**Nota per la prossima sessione:** questo NON risolve il TODO separato ancora aperto (sezione 2octies) sulla clausola "BODY ART EXCEPTION" che compare sempre in shared anche con `BODY ART: None` — sono due problemi distinti, uno in Architect (`/generico` non rimuoveva i tatuaggi) e uno in shared (la clausola condizionale è sempre presente anche quando inerte). Il secondo resta rimandato, discussione non ancora ripresa.

---

## 2sexies. SESSIONE 07/07/2026 — MODIFICHE

Sessione innescata da due test creativi di Walter su Atelier con foto di riferimento fuori dagli scenari standard: un centauro e un'immagine ad alta densità decorativa (tatuaggi/body paint elaborati + corsetto con filigrana e gemme).

**1. Test centauro — nessuna modifica al codice, solo diagnosi (vedi conversazione).** Nessuno dei 3 bot testati (Vogue, Architect, Atelier) ha riprodotto l'anatomia ibrida. Causa identificata: `_ANALYZE_PROMPT` non ha alcun campo per descrivere anatomia/struttura corporea (per design — "no wearer mentioned"), e `VALERIA_BODY_STRONG` impone "fianchi larghi, cosce piene" in modo tassativo ("OVERRIDE ALL DEFAULTS"), in contraddizione diretta con un'anatomia non bipede. **Walter ha confermato che era un test occasionale — nessuna modalità dedicata da costruire.** Nessun'azione richiesta.

**2. Test tatuaggi/body paint + outfit elaborato su Atelier — diagnosi che ha portato a un cambio di codice concordato in 2 step.** Confrontando l'originale (tatuaggi/body paint dettagliati su viso/collo/petto/braccia + corsetto con filigrana e gemme) con 2 output generati, sono emersi due problemi distinti:
   - **Tatuaggi/body paint completamente assenti** — stessa causa strutturale del centauro (nessun campo di analisi per decorazioni sulla pelle) più un secondo fattore: `VALERIA_BODY_STRONG`/`SAFE` impone esplicitamente "smooth porcelain skin... perfectly continuous from face → neck → shoulders → chest → arms" — le stesse identiche zone coperte dai tatuaggi nell'originale. Anche descrivendo bene il tatuaggio, questa istruzione lavorerebbe contro di esso.
   - **Corsetto semplificato/appiattito rispetto all'originale** — la descrizione outfit di `analyze_scene()` arriva per intero nel prompt finale (verificato in `build_full_prompt()`/`build_shooting_prompt()`), ma esisteva un blocco "COLOR LOCK — ABSOLUTE PRIORITY" dedicato al colore senza un equivalente per la complessità ornamentale — nulla impediva a Flow di semplificare filigrana/ricami/gemme in fase di generazione.

   **Decisione di Walter: procedere in 2 step, entrambi da fare, iniziando dal più contenuto.**

   **STEP 1 — FATTO in questa sessione: `Atelier_202.py` → `Atelier_203.py`.** Aggiunto blocco "⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY" (stessa forza/posizione del COLOR LOCK esistente) in tutti e 3 i punti dove viene costruito il prompt finale: `build_full_prompt()`, `build_shooting_prompt()` ramo `single`, `build_shooting_prompt()` ramo `mosaic`. Estesi i rispettivi NEGATIVE PROMPT con termini che penalizzano outfit semplificati/generici ("simplified outfit, missing embellishments, missing embroidery, missing gemstones, plain fabric replacing detailed pattern, flattened texture, generic garment reinterpretation"). Nessuna modifica al blocco identità/DNA, nessuna modifica agli altri bot. `ast.parse()` superato, diff verificato riga per riga contro l'originale — solo i 3 blocchi outfit-lock + changelog + version bump, nessun'altra riga toccata. **Verificato con prova pratica da Walter: netto miglioramento su filigrana/gemme del corsetto, zero drift su identità.** Walter ha giudicato il risultato sufficientemente fedele e ha esplicitamente chiesto di NON spingere oltre — una fedeltà troppo letterale rischia di somigliare troppo alla foto originale ("potrebbe passare per face swap"). Step 1 chiuso, nessuna ulteriore modifica prevista su questo fronte.

   **STEP 2 — FATTO nella sessione 2septies (stesso giorno, dopo verifica dello step 1).** Vedi sezione 2septies per il dettaglio completo.

---

## 2septies. SESSIONE 07/07/2026 (continua) — SHARED 2.3.17, STEP 2/2

Dopo che Walter ha verificato lo step 1 (Atelier 203, outfit lock) con esito positivo e ha dato "Vai" esplicito per lo step 2, modificato `C_shared100.py` 2.3.16 → 2.3.17:

**1. Nuovo campo `BODY ART` in `_ANALYZE_PROMPT`**, inserito subito dopo `PROPS & ACTIONS` e prima di `COLOR PALETTE`. Cattura tatuaggi/body paint/decorazioni sulla pelle come design visivo standalone (pattern, colore con HEX, posizione/copertura esatta sul corpo, densità delle linee) — stesso pattern di `PROPS & ACTIONS`, incluso il fallback esplicito `'None.'` se non presenti. Aggiunta anche una regola pratica per Gemini: non confondere body art con pattern stampati sui capi (quelli restano in OUTFIT).

**2. Nuova clausola "⚠️ BODY ART EXCEPTION — CONDITIONAL"** aggiunta sia a `VALERIA_BODY_STRONG` che a `VALERIA_BODY_SAFE`, subito dopo la COEXISTENCE RULE esistente (stesso pattern: una regola condizionale che risolve un'apparente contraddizione tra due istruzioni forti). Se la scena descrive body art nel campo BODY ART, questo sostituisce "smooth porcelain skin" **solo sulle zone indicate** — il resto della pelle resta liscia come da default. Se BODY ART è "None" o assente, la pelle resta liscia ovunque, **nessuna invenzione di tatuaggi non descritti** — clausola esplicita per evitare che i bot comincino a generare tatuaggi a caso su foto che non ne avevano.

**3. Verifica tecnica:** `ast.parse()` superato. Diff verificato riga per riga contro la 2.3.16 — solo i due punti sopra, più changelog e version bump. Nessun termine "tattoo"/"body art" presente nel NEGATIVE prompt esistente (`VALERIA_NEGATIVE`), quindi nessun conflitto residuo da rimuovere. Confermato via grep che tutti e 5 i bot importano `VALERIA_DNA` e/o `build_valeria_identity()` — quindi tutti ereditano la nuova clausola, coerente con la richiesta di Walter di avere le stesse istruzioni ovunque.

**Colta l'occasione per una correzione minore:** il changelog 2.3.16 nel file riportava ancora la data 02/07/2026 (rimasta indietro rispetto alla correzione fatta il 04/07 su HANDOFF/README/xlsx, che allora non aveva toccato il commento interno del file). Corretto a 04/07/2026 per coerenza.

**Verificato con prova pratica da Walter, esito positivo:** tatuaggi/body paint riprodotti fedelmente su collo, petto, braccia e schiena, densità e stile coerenti con l'originale; identità (viso, barba, occhiali) rimasta intatta nonostante il conflitto testuale con "PHOTOGRAPHIC UNITY" nello stesso paragrafo. Il meccanismo condizionale ha retto anche nel caso limite di pattern esteso fino al viso. Step 2 chiuso.

---

## 2octies. SESSIONE 07/07/2026 (continua) — ARCHITECT 2.0.3, CAUSA REALE DI "/generico"

Walter ha segnalato che `/generico` continuava a mostrare "Scegli prima la modalità" dopo l'invio del testo da generalizzare, E che con testi lunghi il bot genera due prompt separati invece di uno — sintomo mai osservato prima perché la diagnosi precedente (sessione 2quinquies punto 4) era stata fatta con testi brevi.

**Causa reale trovata — unifica entrambi i sintomi:** Telegram divide automaticamente i messaggi di testo oltre ~4096 caratteri in più invii separati e consecutivi (comportamento del client, non modificabile lato bot). Il codice precedente faceva `pending_generico.pop(uid, False)` al primo pezzo ricevuto — consumava subito il flag, generava un prompt basato solo sul primo pezzo (incompleto), e il secondo pezzo, arrivando pochi istanti dopo con il flag già consumato, cadeva nel ramo `if user_mode.get(uid) != "text":` producendo i pulsanti "Scegli la modalità" fuori contesto. Un'unica causa per entrambi i sintomi osservati, confermata leggendo il codice riga per riga (non per ipotesi).

**Fix applicato: `Architect_202.py` → `Architect_203.py`.** Aggiunto `_generico_state`: bufferizza i pezzi di testo per uid con un debounce di 1.5 secondi (`_GENERICO_DEBOUNCE`) — stesso pattern del timer `/caption` già usato in Vogue (`threading.Timer`). Se non arriva un altro pezzo entro la finestra, il testo bufferizzato viene concatenato e processato una sola volta. `cmd_generico()` e `/start` ripuliscono esplicitamente buffer/timer residui di richieste precedenti non completate, per evitare stati incrociati. `ast.parse()` superato, diff verificato riga per riga — solo il blocco `/generico` toccato, resto del file invariato.

**Non ancora testato in produzione** — Walter deve verificare su Koyeb con un testo abbastanza lungo da superare il limite di Telegram (lo stesso caso che ha fatto emergere il bug) prima di considerarlo chiuso.

**Secondo problema segnalato nella stessa sessione — NON ancora affrontato, discussione rimandata su richiesta di Walter:** la clausola "BODY ART EXCEPTION" (shared 2.3.17) compare in ogni prompt anche quando `BODY ART: None` — testo condizionale inerte nel caso comune, segnalato da Walter come "inutilmente aggiunta". Causa: `VALERIA_BODY_STRONG`/`SAFE` sono stringhe statiche concatenate a import-time, senza visibilità sul risultato reale di `analyze_scene()` per quella specifica generazione. Per renderla davvero condizionale servirebbe: (a) una funzione tipo `body_art_clause(scene_description)` in `C_shared100.py` che ispeziona il campo BODY ART e restituisce la clausola solo se non è "None"/assente, e (b) modificare il punto di assemblaggio del prompt finale in **tutti e 5 i bot** per chiamarla e inserirla condizionalmente. Scope più ampio di quanto sembrasse — non ancora discusso nel dettaglio con Walter, riprendere da qui.

---

## 2quinquies. SESSIONE 04/07/2026 — MODIFICHE

Sessione innescata da 503 diffusi e continui su tutti (o quasi tutti) i bot, oltre a un tentativo di diagnosi sul bug `/generico` di Architect (vedi nota sotto — non risolto).

**1. Diagnosi 503 e migrazione modello (C_shared100.py 2.3.15 → 2.3.16):** Walter ha riportato 503 costanti su praticamente tutti i bot, nonostante la rotazione chiavi già presente in `GeminiClient.generate()`. Ipotesi verificata via ricerca sulla pagina ufficiale delle deprecation Google: `gemini-3-flash-preview` (modello usato da tutti i 5 bot tramite l'unico `MODEL` in `C_shared100.py`) è un modello **preview**, con limiti di capacità/priorità documentati come più severi rispetto ai modelli GA — indipendentemente da quante chiavi si ruotano, perché il collo di bottiglia è sul backend del modello, non sulla singola chiave. Google raccomanda esplicitamente la migrazione a `gemini-3.5-flash` (GA, rilasciato 19/05/2026). Confrontati due candidati GA: `gemini-3.5-flash` (qualità/reasoning superiore, 3x il costo del preview attuale: $1,50/$9,00 per 1M token input/output) e `gemini-3.1-flash-lite` (più economico del preview stesso: $0,25/$1,50 per 1M, pensato per task leggeri ad alto volume, ma rischio di minore aderenza al prompt di sistema lungo e vincolante di `analyze_scene()` — DNA Valeria, campo PROPS & ACTIONS, safety disattivata). **Decisione di Walter: `gemini-3.5-flash`**, con piano di fallback esplicito su `gemini-3.1-flash-lite` o ritorno a `gemini-3-flash-preview` se emergono limiti di costo o rate limit. Cambiata una sola riga in `C_shared100.py` (`MODEL = "gemini-3.5-flash"`), verificato via grep che non ci fossero altre occorrenze del vecchio nome nel file. `ast.parse()` superato.

**2. TODO aperto lasciato esplicitamente per la prossima sessione — su richiesta di Walter, NON eseguito in questa sessione:** i comandi `/info` dei 5 bot mostrano ancora `gemini-3-flash-preview` in chat, perché sono stringhe/costanti locali ai singoli file bot, non lette da `C_shared100.py`:
   - `Vogue_200.py` riga 20 — `MODEL_TEXT = "gemini-3-flash-preview"`
   - `Filtro_200.py` riga 23 — `MODEL_TEXT_ID = "gemini-3-flash-preview"`
   - `Architect_202.py` riga ~120 — stringa inline `"Motore: <code>gemini-3-flash-preview</code> (Flow)"`
   - `Atelier_202.py` riga ~623 — stringa inline `"Modello: <code>gemini-3-flash-preview</code>"`
   - `Surprise_200.py` riga ~1149 — stringa inline `"Modello caption: <code>gemini-3-flash-preview</code>"`

   **Da fare nella prossima sessione in cui si toccano i bot:** aggiornare tutte e 5 le stringhe a `gemini-3.5-flash` (o al modello effettivo del momento, se nel frattempo si è passati al fallback flash-lite/preview). Va fatto **insieme** ai file che verranno creati in quell'update — cioè con l'incremento di versione file per ciascun bot toccato (`Vogue_200.py`→`_201`, `Filtro_200.py`→`_201`, `Architect_202.py`→`_203`, `Atelier_202.py`→`_203`, `Surprise_200.py`→`_201`, secondo convenzione), non come fix isolato — e con README/HANDOFF/Excel aggiornati in coda, come da regola.

**3. Audit chiavi Google — 3 assegnazioni errate trovate e corrette su Koyeb:** confrontando tutti e 10 i valori chiave visibili su Koyeb con i 10 progetti distinti in Google AI Studio, sono emersi 3 errori di assegnazione (probabile scivolamento in fase di distribuzione chiavi):
   - La chiave del progetto "Telegram Atelier" (`...x1DE`) era finita, per errore, condivisa su **Filtro e Surprise** invece che su Atelier.
   - La chiave del progetto "Telegram surprise" (`...-eOE`) era finita su **Atelier** invece che su Surprise.
   - La chiave del progetto "Telegram Filter" (`...kMPo`) non era mai stata usata da nessun bot — ferma dal 6/05/2026.

   Walter ha corretto le 3 assegnazioni su Koyeb (Atelier, Surprise, Filtro → ciascuno con la propria chiave dedicata). Risultato: le 10 chiavi sono ora su 10 progetti Google Cloud distinti, nessuna condivisione — dovrebbe alleggerire ulteriormente la pressione sui 503 per Filtro/Surprise, indipendentemente dal cambio modello.

   **Nota per prossima sessione:** il foglio `VERSIONI_BOT.xlsx` conteneva 2 celle contaminate (presunta 3ª chiave di Vogue e presunta 2ª chiave di Architect, in realtà copie della 4ª e 5ª chiave di Atelier) — segnalate ma **non ancora corrette su richiesta esplicita di Walter** ("non ancora"). Da correggere quando richiesto.

**4. Bug `/generico` di Architect — diagnosi avviata, NON conclusa.** Walter ha segnalato che i due pulsanti "✏️ Testo / 📸 Foto" compaiono ancora dopo l'invio del testo a `/generico`, nonostante il fix 2.0.2 (sezione 2ter) verificato corretto riga per riga. Prima ipotesi (riavvio Koyeb tra comando e testo, stato in-memory perso) esclusa — Walter ha confermato "pochi secondi, risposta immediata" tra `/generico` e l'invio del testo. Verificato che non ci sono handler duplicati (`content_types=['text']` registrato una sola volta, nessun `register_next_step_handler`, `TeleBot` istanziato senza `threaded=False` esplicito — quindi thread pool di default). **La diagnosi si è interrotta qui per passare alla questione più urgente dei 503** — riprendere da qui nella prossima sessione, verificando in particolare: comportamento sotto `threaded=True` di default di pyTelegramBotAPI con dispatch concorrente di updates ravvicinati, e se il problema è riproducibile in modo consistente o intermittente.

---

## 2quater. SESSIONE 01/07/2026 — MODIFICHE

Sessione breve, su richiesta esplicita di Walter, dopo audit di lettura completo di tutti i file (README, requirements.txt, HANDOFF, xlsx, i 5 bot, shared). Tre interventi, tutti con "Vai" esplicito:

1. **Allineamento dipendenze (README + xlsx):** `README.md` e la cella `REQUIREMENTS` (B36) del foglio `BOT` in `VERSIONI_BOT.xlsx` riportavano due elenchi diversi tra loro e diversi da `requirements.txt` — unico dei tre dichiarato "verificato contro PyPI" nella sessione del 20/06. Differenze trovate: README era fermo a `pyTelegramBotAPI==4.31.0`/`flask==3.0.0`/`Pillow>=10.0.0`/`google-genai>=1.66.0` e includeva `pilmoji>=2.0.4` (dipendenza fantasma — non importata in nessuno dei 5 bot, verificato via grep su tutti gli import); l'xlsx aveva `pyTelegramBotAPI==4.31.0` (vecchia) mischiata a `flask`/`Pillow`/`google-genai` già aggiornati e `openpyxl>=3.1.0` (terza variante di versione). Entrambi i file ora riportano esattamente il blocco di `requirements.txt`: `pyTelegramBotAPI==4.34.0`, `flask==3.1.3`, `Pillow>=12.2.0`, `google-genai>=2.6.0`, `openpyxl>=3.1.5`. `openpyxl` è confermato realmente in uso in `Filtro_200.py` (~riga 2585, export `.xlsx` del LEGO mosaic).
2. **C_shared100.py 2.3.14 → 2.3.15 (solo pulizia documentale, zero modifiche funzionali):** corretto un commento obsoleto in `_schedule_daily_reset()` — il docstring riportava ancora "08:00 UTC (= 09:00 Lisbona estate)", valore pre-fix 2.3.11 mai aggiornato dopo che il codice era stato corretto a `hour=7` (07:00 UTC = 08:00 Lisbona estate, coerente con README e con la sezione 4 di questo HANDOFF). Diff verificato riga per riga contro l'originale: solo header versione, voce changelog e il commento — nessuna riga di codice eseguibile toccata. `ast.parse()` superato.
3. **Bug `on_key_use` (contatore globale invece di per-chiave, sezione 2ter/TODO) lasciato volutamente intatto** — Walter ha richiesto esplicitamente solo la pulizia del commento, non l'audit completo né il fix funzionale. Resta aperto per una sessione futura, vedi sezione 4 e sezione 12.

**Nota modello:** prima sessione su Claude Sonnet 5 invece di Sonnet 4.6 (vedi sezione 0).

---

## 2ter. SESSIONE 25/06/2026 — MODIFICHE

**C_shared100.py 2.3.12 → 2.3.14:**
- **2.3.13:** `_ANALYZE_PROMPT` — aggiunto campo `PROPS & ACTIONS` dopo ACCESSORIES. Cattura oggetti fisici in contatto diretto col corpo (posizione, punto di contatto, azione). Prima, prop interattivi come "ice cube held between lips" venivano ignorati o descritti vagamente in BACKGROUND. Protezione NSFW invariata (analisi testuale mediata).
- **2.3.14:** `GeminiClient` — aggiunta `GOOGLE_API_KEY_5` alla lista variabili d'ambiente. Atelier passa da 4 a 5 chiavi.

**Architect_200.py → Architect_201.py → Architect_202.py:**
- **201 (v2.0.1, 25/06):** Fix preventivo: `/generico` nasconde i bottoni "Nuova foto/Nuovo testo" del prompt precedente tramite `edit_message_reply_markup`. Introdotto `last_prompt_msg[uid]`. `/start` pulisce anche `pending_generico` e `last_prompt_msg`.
- **202 (v2.0.2, 27/06): causa reale trovata e fixata.** `task_generico` chiamava `send_prompt()`, che allega SEMPRE `get_after_prompt_kb()` ("Nuova foto/Nuovo testo") — bottoni fuori contesto nel flusso `/generico`. Se premuti, il callback handler controlla `user_mode[uid]`, mai impostato in quel flusso, e cade nel branch che mostra "Scegli prima la modalità". Il fix 201 (nascondere i bottoni del messaggio precedente) non risolveva perché il problema erano i bottoni del messaggio APPENA generato da `/generico` stesso, non quelli del messaggio precedente. Fix 202: `task_generico` non usa più `send_prompt()` — invia il prompt direttamente senza alcun bottone post-prompt.
- **Lezione:** il fix 201 era una correzione preventiva ragionevole ma non centrata — il log Koyeb della sequenza non mostrava la causa perché il problema era strutturale (quale funzione genera la tastiera), non temporale (quando viene premuto un vecchio bottone). Quando un fix "plausibile" non risolve un bug ricorrente, ricontrollare se la diagnosi iniziale ha individuato la fonte ESATTA del messaggio incriminato, non solo una fonte plausibile.

**Atelier_200.py → Atelier_201.py → Atelier_202.py:**
- **201 (v2.0.1):**
  - Header prompt filtri singoli: rimossi `📐 ratio` e `🔢 conteggio` — informazioni ridondanti/fuori contesto
  - Corpo prompt `build_full_prompt()`: rimossa riga `FORMAT: {ratio}`
  - `ratio` e `count` rimossi da `user_settings`, firma `build_full_prompt`, tutti i reset, `/help` — dead state
  - Rimosso `FACE IDENTITY LOCK` duplicato hardcoded in `riviera_60` (già coperto da `build_valeria_identity()`)
- **202 (v2.0.2):**
  - `build_shooting_prompt()` (mode=single e mosaic): "Outfit" ora condizionale — se `OUTFIT: None`, Flow non inventa vestiti dalla palette cromatica
  - Aggiunto "Props and physical interactions" nel blocco "What MUST remain identical" — prop coerenti in tutti e 4 gli scatti
  - Aggiunto negative prompt `clothing added where none exists, garments invented from color palette`
  - **Nota trade-off:** 202 più fedele alla scena ma più vulnerabile al filtro NSFW su scene con nudità+studio+mood sensoriale (testato: 12 generazioni bloccate su scena ghiaccio/pelle bagnata). Atelier_201 disponibile come fallback. Su scene normali (es. spiaggia/rocce) 202 funziona bene.

**Redistribuzione chiavi API (25/06):**
- Una chiave spostata da Architect (2→1) ad Atelier (4→5)
- Motivazione: Atelier è il bot più pesante (2 call/foto) e ora ha il pool chiavi più grande

**TODO aperto (segnalato 27/06, non ancora fixato):** il callback `on_key_use` in `C_shared100.py` passa `self._total_calls` (contatore globale di tutte le chiavi sommate) invece di `self._call_counts[self._key_index]` (contatore per-chiave). Il messaggio `🔑 Key N · call #N` mostra quindi il totale globale, non le call di quella specifica chiave. Da correggere il codice (riga ~708, e il commento errato a riga ~632) e aggiornare README/HANDOFF di conseguenza.

---

## 2bis. AUDIT E FIX SESSIONE 20/06/2026

Su richiesta esplicita di Walter ("analizzare tutti i codici per trovare bug ed eventuali miglioramenti — solo bug reali/concreti"), è stato fatto un audit a profondità "bug concreti" (crash, race condition, logica rotta) su tutti e 6 i file. Trovati 9 bug, 6 fixati in questa sessione, 3 lasciati invariati su scelta esplicita di Walter (whitelist a singolo utente, nessuna concorrenza reale possibile oggi).

**Fixati:**
- **#2 (shared, 2.3.12):** `_schedule_daily_reset()` usava `datetime.utcnow()`, deprecato e naive — sostituito con `datetime.now(timezone.utc)`.
- **#3 (shared, 2.3.12):** `_reset_loop()` non aveva try/except — una qualsiasi eccezione interna terminava il thread di reset giornaliero per sempre, in modo silenzioso, senza log. Ora il loop è avvolto in try/except con retry a 60s in caso di errore.
- **#5 (Atelier, 2.0.0):** `_process()` dentro `executor.submit()` non aveva gestione eccezioni — un errore imprevisto lasciava l'utente bloccato su "Analisi in corso..." senza messaggio né log. Ora l'intero corpo è avvolto in try/except con messaggio di errore esplicito all'utente.
- **#6 (Architect, 2.0.0):** `analyze_scene()` veniva chiamata sincrona sul thread di polling Telegram in `handle_photo`, bloccando la ricezione di altri messaggi per i 20-30s della chiamata Gemini. Spostata dentro `task_single()` nell'executor.
- **#8 (Surprise, 2.0.0):** bug più grave trovato — `idx` nel `callback_data` di location/outfit era sempre risolto contro il pool COMPLETO non filtrato, ma la tastiera mostrata all'utente usa un pool FILTRATO (esclude voci già usate in sessione). Dal secondo giro in sessione in poi, il bot selezionava silenziosamente una location/outfit diversa da quella effettivamente cliccata — nessun crash, nessun errore visibile, solo output sbagliato. Fix: introdotto `shown_pool[uid][step]` che traccia il pool esatto mostrato, usato sia alla selezione che al cambio pagina (`pg_`). Aggiunto anche un guard esplicito contro `IndexError` su tastiere obsolete (messaggio "Scelta non più valida" invece di crash).
- **#9 (Filtro, 2.0.0):** in `handle_photo`, un secondo blocco `if uid in mosaic_collecting:` (commentato come "cleanup sessione zombie") era codice irraggiungibile, identico al check precedente che fa sempre `return`. Verificato che non serve comunque: ogni uscita da una sessione mosaic passa già da `_finalize_mosaic()` o `_start_mosaic_session()`, che ripuliscono correttamente lo stato. Blocco morto rimosso.

**Lasciati invariati (scelta esplicita di Walter — whitelist singolo utente, nessuna richiesta concorrente possibile):**
- **#1 (shared):** `GeminiClient.generate()` non è thread-safe — `_call_counts`/`_key_index` mutati senza lock attorno alla read-modify-write. Da riconsiderare se in futuro si aggiunge un secondo utente o un webhook al posto del polling.
- **#4 (Vogue, Atelier):** `_active_cid` è una singola variabile globale per processo, non per-utente — sotto concorrenza reale le notifiche "🔑 Key N · call #M" potrebbero finire nella chat sbagliata. **Nota:** la sezione storica 5 di questo HANDOFF afferma che `_active_cid` è stato "reso thread-safe con Lock" in Vogue v1.0.2-1.0.5 — verificato falso/parziale: il `Lock` esiste ed è usato in scrittura, ma mai in lettura. La protezione reale è minore di quanto documentato in precedenza.
- **#7 (Surprise):** `_is_duplicate_callback()` ha una finestra check-then-act senza lock tra `call_id in _seen_callbacks` e `.add(call_id)`. Rischio reale solo se Telegram recapita lo stesso callback su thread diversi in rapida successione.

**Non applicabile in questa sessione:**
- **Filtro_106.py → Filtro_108.py:** diff verificato minimo (solo bump versione + rimozione caption automatica da `from_filter` in `_run_generation`). L'analisi fatta su 106 resta valida su 108 a meno del fix #9, specifico di 108.

---

## 3. PROBLEMA "Key 2 · call #63" — CHIUSO (20/06/2026)

**Sintomo originale (17/06):** Atelier mostrò `Key 2 · call #63`, apparentemente impossibile con limite 20/giorno/chiave.

**Causa identificata da Walter (20/06):** Google applica anche un rate limit ORARIO oltre a quello giornaliero (fonte: documentazione ufficiale Google AI Studio/Gemini API, non rivalutata nel dettaglio in questa sessione). Combinato con la rotazione round-robin su più chiavi, il numero "#63" cumulativo non è di per sé anomalo. Limiti Gemini sono per progetto Google Cloud, non per account — confermato coerente con l'architettura a 10 progetti separati già in uso, quindi **nessuna modifica architetturale necessaria** (decisione esplicita di Walter).

**Fix tecnico applicato comunque (indipendente dalla causa sopra):** in questa sessione sono stati corretti due difetti reali e indipendenti dal rate limit nel meccanismo di reset stesso — vedi #2 e #3 in sezione 2bis. Prima del fix, `_reset_loop()` poteva morire silenziosamente alla prima eccezione interna (incluso un futuro `TypeError` da `datetime.utcnow()` deprecato), lasciando i contatori bloccati indefinitamente senza alcun log. Questo NON era la causa confermata del sintomo originale, ma era comunque un baco reale e ora è risolto.

**Verifica log Koyeb (06:55-07:10 UTC, riga `🔄 GeminiClient: contatori call azzerati`) non è stata fatta** — Walter ha scelto esplicitamente di non procedere con quella verifica, ritenendola non più necessaria dopo aver chiarito la causa del rate limit orario.

---

## 4. C_SHARED100.PY — STORICO COMPLETO FIX (v2.3.0 → v2.3.18)

- **v2.3.18 (08/07/2026):** "BODY ART EXCEPTION" tolta da `VALERIA_BODY_STRONG`/`SAFE` (compariva sempre, anche con BODY ART: None) e isolata in `BODY_ART_EXCEPTION_TEXT` + nuova `body_art_clause(scene_description)`, condizionale su un vero campo BODY ART. Applicata a Vogue/Atelier; Architect la mantiene sempre presente tramite import diretto della costante (non può essere condizionale). Vedi sezione 2decies.
- **v2.3.17 (07/07/2026):** nuovo campo `BODY ART` in `_ANALYZE_PROMPT` (dopo PROPS & ACTIONS) e clausola condizionale "BODY ART EXCEPTION" in `VALERIA_BODY_STRONG`/`SAFE` — permette a tatuaggi/body paint descritti di sostituire "smooth porcelain skin" solo sulle zone indicate, senza inventare markings non descritti. Tocca tutti e 5 i bot. Vedi sezione 2septies.
- **v2.3.16 (04/07/2026):** `MODEL` — `gemini-3-flash-preview` → `gemini-3.5-flash` (GA). Motivo: 503 diffusi riconducibili ai limiti di capacità del livello preview, non a esaurimento chiavi. Fallback concordato: `gemini-3.1-flash-lite` o ritorno al preview se emergono limiti di costo/rate. Vedi sezione 2quinquies per il dettaglio completo.
- **v2.3.15 (01/07/2026):** solo pulizia documentale — corretto commento obsoleto in `_schedule_daily_reset()` ("08:00 UTC" → "07:00 UTC", coerente col codice reale `hour=7` già corretto in 2.3.11). Zero modifiche funzionali, diff verificato riga per riga.
- **v2.3.14 (25/06):** `GeminiClient` — aggiunta `GOOGLE_API_KEY_5` alla lista variabili d'ambiente. Atelier passa da 4 a 5 chiavi.
- **v2.3.13 (25/06):** `_ANALYZE_PROMPT` — aggiunto campo `PROPS & ACTIONS` dopo ACCESSORIES. Cattura oggetti fisici in contatto diretto col corpo (posizione, punto di contatto, azione). Prima, prop interattivi come "ice cube held between lips" venivano ignorati o descritti vagamente in BACKGROUND — causando prompt Atelier privi degli elementi scenici più forti dell'immagine originale. Protezione NSFW invariata.
- **v2.3.12 (20/06):** Fix robustezza `GeminiCounterReset` — `datetime.utcnow()` (deprecato, naive) sostituito con `datetime.now(timezone.utc)`. `_reset_loop()` ora avvolto in try/except con retry a 60s: prima, una qualsiasi eccezione interna terminava il thread per sempre, in modo silenzioso, senza log, lasciando i contatori bloccati fino al riavvio del servizio.
- **v2.3.11:** Reset giornaliero corretto a 07:00 UTC (= 08:00 Lisbona estate). Era erroneamente impostato a 08:00 UTC.
- **v2.3.10:** Fix crash critico — `_schedule_daily_reset()` non era definita nel file (persa accidentalmente in una sostituzione precedente), causava `AttributeError` e crash di TUTTI i bot al boot. Ripristinata.
- **v2.3.9:** Introdotti `reset_counters()` + `_schedule_daily_reset()` (con bug v2.3.10, poi fixato).
- **v2.3.8:** Aggiunto supporto `GOOGLE_API_KEY_4` (4ª chiave, usata da Atelier).
- **v2.3.7:** Tentativo di contatore globale `_total_calls` — **scartato su richiesta esplicita di Walter**, che vuole il contatore PER CHIAVE (`_call_counts[key_index]`), non globale, per sapere esattamente quante call restano su ogni singola chiave prima di dover passare a un altro bot.
- **v2.3.6:** `CaptionGenerator.local()` rimossa — dopo test, qualità insufficiente (frasi con parole tecniche del prompt, es. "reference locked alter following description extracted"). Decisione finale: niente caption automatica, solo `/caption` on-demand via Gemini.
- **v2.3.5:** `CaptionGenerator.local()` introdotta (poi rimossa in v2.3.6).
- **v2.3.4:** `on_key_use(callback)` + `_call_counts` per chiave introdotti.
- **v2.3.3:** Retry estesi a TUTTI gli errori transitori (503/unavailable/timeout/connection), non solo 429.
- **v2.3.0-2.3.2:** Rotation loop su tutte le chiavi prima di arrendersi, safety block Gemini con messaggio chiaro, allineamenti versione.

**Funzioni esportate attuali:** `GeminiClient` (singleton, max 4 chiavi, rotation round-robin, retry su transitori, `on_key_use`/`on_key_rotation` callback, `reset_counters()`, `call_counts` property) · `HealthServer` · `is_allowed` · `analyze_scene` · `generate_caption` · `generate_mini_caption` · `generate_mini_prompt` · `review_and_fix` (⚠️ forza DNA Valeria — vedi regola 10) · `sanitize_user_input` · `detect_mime_type` · `CaptionGenerator` (solo `from_image`/`from_filter`, NO `local()`) · `VALERIA_DNA` · `EDITORIAL_WRAPPER` · `build_valeria_identity` · `VALERIA_FACE`/`BODY_STRONG`/`BODY_SAFE`/`WATERMARK`/`NEGATIVE` · `SHARED_VERSION` · `SHARED_DATE`

**Limite Google free tier (confermato da log reali):** 20 richieste/giorno per chiave per modello (`gemini-3-flash`). Quota condivisa per progetto Google Cloud — ogni chiave è su un progetto diverso (verificato via screenshot Google AI Studio: 10 progetti distinti, tutti free tier).

---

## 5. VOGUE — STORICO E STATO (v2.0.1)

- **v2.0.1 (08/07):** `build_prompt()` inserisce `body_art_clause(scene_description)` dopo `VALERIA_DNA` — la clausola BODY ART ora compare solo se la foto analizzata ha davvero body art, non più sempre. Percorso testo (senza foto) invariato: la funzione restituisce sempre stringa vuota lì. Vedi sezione 2decies. **Non ancora testato in produzione.**
- **v2.0.0 (20/06):** Bump di allineamento al nuovo ciclo versioni (5 bot → 2.0.0). Nessuna modifica funzionale in questa sessione — bug noto #4 (`_active_cid` globale, vedi sezione 2bis) lasciato invariato su scelta esplicita di Walter.
- **v1.0.8:** Rimossi pulsanti "Mini caption"/"Mini prompt" (mai usati), relativi callback, import inutilizzati. Keyboard post-prompt ora solo "📸 Nuova foto" / "🏠 Home".
- **v1.0.7:** `gemini.reset_counters()` chiamato su `/start`.
- **v1.0.6:** `on_key_use` attivo — mostra `🔑 Key N · call #N` ad ogni chiamata Gemini.
- **v1.0.2-1.0.5:** `_active_cid` reso thread-safe con `Lock`, messaggio di attesa per generazione da testo, `generate_caption()` automatica rimossa (era 1 call sprecata per foto), caption locale (introdotta poi rimossa, vedi shared v2.3.5/2.3.6).

**Pipeline:** foto/testo → `analyze_scene` (1 call) → `review_and_fix` (1 call) → prompt Flow-ready. 2 call totali per generazione. Caption SOLO on-demand via `/caption` (1 call extra).

**Comandi:** `/start` · `/info` · `/shared` · `/dna` · `/caption`

---

## 6. ARCHITECT — STORICO E STATO (v3.0.2)

- **v3.0.2 (11/07):** consegna cambiata da file `.txt` a testo diretto in chat, coerente con Vogue/Atelier/Filtro/Surprise — il prompt è sufficientemente breve da non richiedere un file, su osservazione di Walter. Aggiunta `send_prompt_text()` (chunking a 3800 caratteri, stesso pattern di Vogue). Rimossi `bot.send_document()`, `io.BytesIO`, import `io`. `/lastprompt` ora reinvia testo, non un file. Vedi sezione 2quaterdecies. **Non ancora testato in produzione.**
- **v3.0.1 (11/07) — SUPERATO da v3.0.2, storico:** Walter ha giudicato l'output JSON della 3.0.0 "ingestibile" e "non pubblicabile". Cambiato l'output da JSON a testo in formato prompt — sezioni etichettate in chiaro (`SUBJECT:`, `OUTFIT:`, `ACCESSORIES:`, `BODY ART:`, `PROPS & ACTIONS:`, `BACKGROUND:`, `LIGHTING:`, `CAMERA:`, `COLOR PALETTE:`, `MOOD:`), consegnato allora come file `.txt` (poi cambiato in 3.0.2, vedi sopra). Rimossa tutta la logica di parsing/validazione JSON. `/lastjson` → di nuovo `/lastprompt`. Vedi sezione 2terdecies.
- **v3.0.0 (10/07) — SUPERATO da v3.0.1, storico:** RISCRITTURA COMPLETA su richiesta di Walter — `/generico` rimosso interamente (mai stato affidabile in 6 versioni, 201→206, causa strutturale mai risolvibile con patch: analisi+scrittura in un'unica chiamata Gemini, nessun testo intermedio ispezionabile). Nuovo scopo: riceve una foto, restituisce analisi completa e fedele — soggetto reale incluso, **nessun DNA Valeria**. Output iniziale era JSON, corretto in 3.0.1 (vedi sopra). Vedi sezione 2duodecies per il dettaglio completo della riscrittura.
- **v2.0.6 (10/07) — SUPERATO da v3.0.0, storico:** raddoppiato `_GENERICO_DEBOUNCE` a 3.0s ipotizzando un problema di tempistica sui chunk Telegram. Non ha risolto — Walter ha deciso di riscrivere il bot invece di continuare a patchare. Vedi sezione 2undecies.
- **v2.0.5 (08/07) — storico, codice rimosso in v3.0.0:** Compensazione tecnica per shared 2.3.18 — la clausola BODY ART arrivava "gratis" tramite `VALERIA_DNA`, condivisa con Vogue. Vedi sezione 2decies.
- **v2.0.4 (08/07) — storico, codice rimosso in v3.0.0:** `GENERICO_SYSTEM_PROMPT` esteso per rimuovere body art/tattoo dalla sezione "Reference image analysis". Vedi sezione 2novies.
- **v2.0.3 (07/07) — storico, codice rimosso in v3.0.0:** Causa REALE #2 del bug "/generico" trovata — Telegram divide i testi lunghi in più messaggi; il bot consumava lo stato al primo pezzo. Fix: buffer con debounce. Vedi sezione 2octies.
- **v2.0.2 (27/06) — storico, codice rimosso in v3.0.0:** Causa REALE del bug "Scegli prima la modalità dopo /generico" — `task_generico` chiamava `send_prompt()` fuori contesto.
- **v2.0.1 (25/06) — storico:** Fix preventivo, poi rivelatosi NON la causa reale.
- **v2.0.0 (20/06) — storico:** Fix #6 — `analyze_scene()` spostata nell'executor.
- **v1.0.5-1.0.7 — storico:** introduzione e affinamento di `/generico`, ora completamente rimosso.

**Flusso attuale (v3.0.2):** utente invia una foto → Architect analizza con `analyze_image_full()` → invia il prompt completo come testo in chat (chunk da 3800 caratteri se necessario), in formato a sezioni etichettate, con la scena completa (soggetto reale, outfit, accessori, body art, sfondo, luce, palette, mood) — nessun DNA, nessuna sostituzione identitaria, nessun file da scaricare. Nessuna modalità da scegliere, nessun testo da inviare. `/lastprompt` reinvia l'ultimo testo senza rianalizzare.

**Comandi (v3.0.2):** `/start` · `/help` · `/info` · `/lastprompt` · `/shared`

---

## 7. ATELIER — STORICO E STATO (v2.0.4)

- **v2.0.4 (08/07):** `build_full_prompt()` e `build_shooting_prompt()` (entrambi i rami) inseriscono `body_art_clause(outfit_description)` dopo OUTFIT DETAIL LOCK — la clausola BODY ART ora compare solo se la foto ha davvero body art, non più sempre. Vedi sezione 2decies. **Non ancora testato in produzione.**
- **v2.0.3 (07/07):** aggiunto blocco "⚠️ OUTFIT DETAIL LOCK — ABSOLUTE PRIORITY" in `build_full_prompt()` e in entrambi i rami di `build_shooting_prompt()` (single/mosaic), stessa priorità del COLOR LOCK esistente — contrasta la semplificazione di outfit molto elaborati (filigrana, gemme, ricami densi). Negative prompt estesi di conseguenza. Vedi sezione 2sexies per il contesto completo (step 1 di 2 — step 2 riguarda i tatuaggi e tocca shared).
- **v2.0.2 (25/06):** `build_shooting_prompt()` (mode=single e mosaic) — outfit ora condizionale (se `OUTFIT: None`, Flow non inventa vestiti dalla palette); aggiunto "Props and physical interactions" nel blocco "What MUST remain identical"; aggiunto negative prompt anti-vestito-inventato. **Trade-off noto:** su scene con nudità+studio+mood sensoriale il filtro NSFW Flow può bloccare (testato: 12 generazioni bloccate su scena ghiaccio/pelle bagnata) — usare Atelier_201 come fallback in quei casi.
- **v2.0.1 (25/06):** Header prompt filtri singoli: rimossi `📐 ratio` e `🔢 conteggio`. Corpo prompt: rimossa riga `FORMAT: {ratio}`. `ratio` e `count` rimossi da `user_settings`, firma `build_full_prompt`, tutti i reset, `/help`. Rimosso `FACE IDENTITY LOCK` duplicato in `riviera_60`. **5 chiavi API** (aumentate da 4 a 5 il 25/06 — una spostata da Architect).
- **v2.0.0 (20/06):** Fix #5 — `_process()` dentro `executor.submit()` non aveva gestione eccezioni.
- **v1.1.3:** Rimosso messaggio "Procedere?", rimosso `pending_prompts` (dict morto).
- **v1.1.2:** `gemini.reset_counters()` su `/start`.
- **v1.1.1:** Filtro persistente tra sessioni.
- **v1.1.0:** `on_key_use` attivo.
- **v1.0.5-1.0.9:** Caption locale (introdotta poi rimossa), filtro "🖍️ Scarabocchio", mosaic zombie cleanup.

**Pipeline:** foto → `analyze_scene` (1 call) → `review_and_fix` (1 call) → prompt con filtro applicato. 2 call totali. Caption SOLO on-demand via `/caption` (timeout 60s).

**Comandi:** `/start` · `/help` · `/info` · `/lastprompt` · `/caption` · `/shared`

---

## 8. FILTRO — STATO (v2.0.0)

- **v2.0.0 (20/06):** Fix #9 — rimosso blocco "cleanup sessione mosaic zombie" in `handle_photo`, codice irraggiungibile (secondo `if uid in mosaic_collecting` identico al precedente che fa sempre `return`). Verificato non necessario: ogni uscita da sessione mosaic passa già da `_finalize_mosaic()`/`_start_mosaic_session()`.
- **v1.0.8 → 1.0.6 (diff minimo):** rimossa caption automatica da `from_filter()` in `_run_generation` (era residuo non più voluto).

7 categorie filtro + LEGO Mosaic/Galaxy + filtro "🖍️ Scarabocchio" (stile artistico). Pipeline: `analyze_scene` (1 call) → prompt locale per categoria. Caption SOLO on-demand via `/caption`.

**Comandi:** `/start` · `/filtro` · `/help` · `/info` · `/lastprompt` · `/caption` · `/mosaic` · `/done` · `/shared`

---

## 9. SURPRISE — STATO (v2.0.1)

- **v2.0.1 (12/07):** analisi location da foto (`handle_location_photo`) era limitata a un paragrafo di massimo 50 parole — troppo corta secondo Walter, che voleva lo stesso livello di dettaglio di Architect. Riscritto `location_prompt` con la stessa struttura a sezioni (BACKGROUND/LIGHTING/CAMERA/MOOD, senza SUBJECT/OUTFIT — esclusi di proposito, l'outfit lo genera Surprise altrove). Messaggio di conferma non più troncato a 200 caratteri. Colto anche un bug adiacente: `mime_type` hardcoded a `"image/jpeg"` → sostituito con `detect_mime_type()`. Vedi sezione 2quindecies. **Non ancora testato in produzione.**
- **v2.0.0 (20/06):** Fix #8, il bug più grave trovato in questa sessione di audit — `idx` nel `callback_data` di location/outfit era risolto contro il pool COMPLETO, ma la tastiera mostrata usa un pool FILTRATO (esclude voci già usate in sessione). Dal secondo giro in sessione, il bot selezionava silenziosamente una location/outfit diversa da quella cliccata — nessun crash, nessun errore visibile. Fix: introdotto `shown_pool[uid][step]`, applicato sia alla selezione che al cambio pagina (`pg_`). Aggiunto guard esplicito contro `IndexError` su tastiere obsolete.

Pool locale di location (~260) e outfit per la generazione principale (zero call Gemini per la selezione in sé). C'è anche una funzione opzionale per acquisire una location da foto (`handle_location_photo`, non `analyze_scene()` di shared — un prompt dedicato solo scena/ambiente, vedi v2.0.1) usata quando l'utente vuole una location specifica invece del pool random. `/pride` + `/flag` per mosaici Pride a 6 pannelli, zero call Gemini per quei comandi specifici. Pipeline normale: pool random → `review_and_fix` (1 call) → prompt.

**Comandi:** `/start` · `/flag` · `/pride` · `/help` · `/info` · `/shared` · `/lastprompt`

---

## 10. STRATEGIA CALL GEMINI — RIEPILOGO

| Bot | Call/operazione normale | Caption | Extra |
|-----|----|---------|-------|
| Atelier | 2 (analyze + review) | `/caption` on-demand — 1 call | — |
| Vogue | 2 (analyze + review) | `/caption` on-demand — 1 call | — |
| Architect | 1-2 (review ± analyze) | nessuna automatica | `/generico` — 1 call |
| Filtro | 1 (analyze, prompt locale) | `/caption` on-demand — 1 call | — |
| Surprise | 1 (review, pool locale) | nessuna | — |

**Principio guida (Walter, sessione 07/06):** "vorrei avere tutto su shared condiviso in modo che tutti i bot si comportino nello stesso identico modo, e le variazioni le faremo una volta per tutti solo su shared". Tendenza desiderata: centralizzare comportamento condiviso in C_shared, bot-specific solo per logica realmente specifica (filtri, pool location, ecc.).

---

## 11. ERRORI DA NON RIPETERE (lezioni da questa sessione lunga)

1. **Mai presumere conteggio chiavi/dati senza verificare** — Walter si è infuriato 2 volte per somme sbagliate (8 invece di 10, poi di nuovo errore simile). Contare sempre esplicitamente prima di affermare un totale.
2. **Mai bumpare una versione senza `grep "^VERSION"` preventivo sul file reale** — causò la consegna di "Atelier_110.py" con dentro ancora `VERSION = "1.0.7"`.
3. **Attenzione critica quando si rimuove codice con `.replace()` su blocchi con indentazione variabile** — un replace con count fisso ha lasciato righe orfane causando `IndentationError`. Preferire approcci con regex (`re.sub`) quando l'indentazione non è garantita identica in tutte le occorrenze, o verificare sempre con `ast.parse()` IMMEDIATAMENTE dopo ogni replace, non solo a fine sessione.
4. **`_schedule_daily_reset()` sparì dal file in una sostituzione precedente senza essere notato finché non ha causato un crash in produzione** — sempre verificare con `grep "def nome_funzione"` che una funzione richiamata esista davvero nel file finale, non solo che l'`ast.parse()` passi (l'AST check non rileva `AttributeError` a runtime su metodi mancanti).
5. **Orari: Walter è a Lisbona. Tutti i riferimenti a "le 8 del mattino" sono LISBONA, mai UTC, mai California, mai altro fuso.** Lisbona è UTC+0 in inverno, UTC+1 in estate (DST). Il reset Google quota è a mezzanotte Pacific Time, che corrisponde alle 08:00-09:00 Lisbona a seconda della stagione — verificare sempre la conversione stagionale corretta, non hardcodare un solo offset.
6. **review_and_fix() non è "neutralizzabile" passando solo testo diverso** — ha un wrapper di sistema interno che sovrascrive qualsiasi istruzione esterna riguardo al DNA Valeria. Per bypassare serve `gemini.generate()` diretto.
7. **Stile comunicativo:** Walter ha chiesto esplicitamente un tono da advisor diretto e critico, non accomodante. Questa preferenza è permanente e salvata in memoria — applicarla aumenta la qualità percepita dell'interazione, in particolare durante debug e revisioni di codice.
8. **Verificare sempre se un fix documentato come "completo" lo è davvero** — la sezione storica Vogue affermava `_active_cid` "reso thread-safe con Lock" (v1.0.2-1.0.5), ma il Lock era usato solo in scrittura, mai in lettura. La documentazione di sessioni precedenti può sovrastimare la protezione reale di un fix — non fidarsi ciecamente, controllare il codice.
9. **Quando si analizza una versione diversa da quella già documentata (es. Filtro_106 vs Filtro_108), fare sempre un diff esplicito prima di rianalizzare tutto da zero** — se il diff è minimo, l'analisi precedente resta valida per le parti invariate; risparmia tempo e riduce rischio di contraddirsi.
10. **Trade-off NSFW/fedeltà in Atelier (scoperto 25/06):** la pipeline mediata di Atelier (immagine → testo → prompt) è anche la sua protezione dal filtro NSFW di Flow. Rendere il prompt più fedele alla scena originale (es. aggiungendo PROPS & ACTIONS, rimuovendo outfit inventati) può aumentare i blocchi su scene con nudità+mood sensoriale. Mantenere versioni separate (201 fedele/permissiva, 202 più fedele ma più bloccata) è la strategia corretta — non cercare un'unica versione che ottimizzi entrambe.
11. **Contatori chiave: il numero nel nome file (es. Atelier_202) e la VERSION interna (es. 2.0.2) devono sempre coincidere.** Walter ha regola esplicita: mai riusare un nome file già deployato su Koyeb — anche per fix minimi, sempre incrementare il numero nel nome file E la VERSION interna in modo coordinato.
12. **Le dipendenze possono disallinearsi silenziosamente tra `requirements.txt`, README e xlsx se si bumpa una versione in un solo file.** Scoperto 01/07: il bump pyTelegramBotAPI 4.31.0→4.34.0 del 20/06 era stato fatto solo su `requirements.txt`; README e xlsx erano rimasti indietro, e per giunta diversi anche tra loro. Quando si tocca una dipendenza, aggiornare tutti e tre i punti insieme nello stesso passaggio — non solo `requirements.txt`.

---

## 12. COME RIPARTIRE NELLA PROSSIMA SESSIONE

1. Importa questo HANDOFF come primo messaggio/contesto
2. Se Walter fornisce nuovi file aggiornati, leggerli SEMPRE per intero con `view`/`bash_tool cat` prima di agire — non fidarsi della cronologia HANDOFF per i contenuti effettivi del codice, solo per il contesto storico
3. Mantenere stile comunicativo da advisor diretto fin dal primo messaggio
4. Mai agire senza "Vai" esplicito, anche per fix che sembrano banali
5. **Bug noti rimasti volutamente aperti** (vedi sezione 2bis): #1 (lock mancante su `_call_counts`/`_key_index` in `GeminiClient.generate()`), #4 (`_active_cid` globale non per-utente in Vogue/Atelier), #7 (`_is_duplicate_callback` non thread-safe in Surprise). Tutti e tre diventano rilevanti SOLO se in futuro si introduce un secondo utente in whitelist o si passa da polling a webhook — da riconsiderare se cambia quel contesto.
6. **TODO ancora aperto:** il callback `on_key_use` passa `self._total_calls` (contatore globale di tutte le chiavi sommate) invece di `self._call_counts[self._key_index]` (contatore per-chiave). Il messaggio `🔑 Key N · call #N` mostra quindi il totale globale, non le call di quella specifica chiave. Da correggere in `C_shared100.py` (riga ~708) e aggiornare il commento a riga ~632 (`"call_count cumulativo per quella chiave"` è sbagliato). Anche README e HANDOFF vanno aggiornati di conseguenza.
7. **TODO aperto (04/07), ridotto il 10/07 — priorità alta:** allineare le stringhe `/info` di Vogue, Filtro, Atelier, Surprise al modello reale (`gemini-3.5-flash`, o quello effettivo se nel frattempo si è passati al fallback). **Architect è già corretto** dal 10/07 (riscritto da zero, `/info` mostra `gemini-3.5-flash` di suo). Dettaglio righe da toccare per gli altri 4 in sezione 2quinquies, punto 2. Va fatto **insieme** all'incremento di versione file per ciascun bot toccato e al conseguente aggiornamento di README/HANDOFF/Excel — non come fix isolato.
8. **TODO aperto (04/07):** foglio `VERSIONI_BOT.xlsx` ha 2 celle contaminate (presunta 3ª chiave Vogue, presunta 2ª chiave Architect — in realtà copie della 4ª/5ª chiave di Atelier). Segnalato a Walter, correzione rimandata su sua richiesta esplicita — chiedere se procedere.
9. **Bug `/generico` Architect — SUPERATO il 10/07, non più rilevante.** Sei versioni di fix (201→206, sezioni 2ter/2octies/2undecies) non hanno mai risolto il problema alla radice — causa strutturale (analisi+scrittura in un'unica chiamata Gemini). Walter ha deciso di rimuovere `/generico` interamente e riscrivere Architect da zero come analizzatore JSON puro. Vedi sezione 2duodecies. Nessun'azione di follow-up su questo punto — è chiuso per rimozione, non per fix.
10. **Clausola "BODY ART EXCEPTION" — risolta (08/07) per shared/Vogue/Atelier; il punto su Architect è SUPERATO il 10/07.** Analisi bot-per-bot aveva confermato che Filtro/Surprise non erano toccati dal problema, mentre Vogue/Atelier la ricevono condizionalmente. Il compromesso trovato per Architect (mantenerla sempre presente tramite `BODY_ART_EXCEPTION_TEXT`, sezione 2decies) è stato rimosso insieme a tutto il resto del DNA nella riscrittura v3.0.0 — Architect ora non ha alcun concetto di DNA/body-art da gestire. Vedi sezione 2decies per il contesto storico e 2duodecies per la rimozione.
11. **TODO aperto (08/07) — test da fare per Vogue e Atelier, NON per Architect (superato):** nessuno dei 2 file toccati per la clausola BODY ART (`Vogue_201.py`, `Atelier_204.py`) è stato provato su Koyeb. Da verificare: (a) foto senza tatuaggi → prompt più corto, clausola assente; (b) foto con tatuaggi (es. quella del 07/07) → clausola presente, fedeltà come già vista su Atelier 203.
13. **TODO aperto (12/07) — SUPERATO nella stessa giornata dal cambio di consegna:** il punto sul file `.txt` di Architect 3.0.1 non è più rilevante — l'output ora è testo diretto in chat, non un file. Vedi punto 14.
14. **TODO aperto (12/07) — priorità alta, da fare prima di ogni altra cosa su Architect:** `Architect_302.py` (testo in chat invece di file, sezione 2quaterdecies) non è mai stato testato in produzione. Verificare su Koyeb: (a) foto normale → testo con le 10 sezioni etichettate ricevuto in chat, chunk multipli se >3800 caratteri; (b) foto di Valeria → conferma che SUBJECT descriva correttamente barba/occhiali/corpo senza intervento di DNA; (c) `/lastprompt` dopo una foto → reinvia lo stesso testo; (d) verificare a occhio che Gemini rispetti il formato richiesto — senza un parser che lo validi, una deviazione dal formato passerebbe inosservata finché qualcuno non legge il testo.
15. **TODO aperto (12/07):** `requirements.txt` aggiornato (Pillow→12.3.0, google-genai→2.11.0) non ancora testato con un deploy Koyeb reale — stesso tipo di cautela già in nota per `pyTelegramBotAPI` 4.34.0 (bump testato solo a livello di changelog, non su questo stack specifico). Se un deploy si rompe dopo questo bump, vedi il commento in testa a `requirements.txt` per il sospetto principale.
16. **TODO aperto (12/07):** `Surprise_201.py` (analisi location a sezioni, ex 50 parole) non ancora testato in produzione. Verificare su Koyeb: (a) foto location → le 4 sezioni (BACKGROUND/LIGHTING/CAMERA/MOOD) arrivano complete in chat, non più il paragrafo generico; (b) messaggio di conferma senza troncamento si comporta bene con testi lunghi; (c) foto PNG/WebP (non solo JPEG) → confermare che il fix `detect_mime_type()` funzioni. Vedi sezione 2quindecies.

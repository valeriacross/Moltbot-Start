"""
C_shared100.py — Valeria Cross AI · Oggetti comuni a tutti i bot
Versione: 2.4.21

REGOLA: questo file si aggiorna SEMPRE in-place con lo stesso nome C_shared100.py.
Non rinominare mai in C_shared101.py o simili — tutti i bot importano da C_shared100.
CHANGELOG 2.4.21 (13/11/2026): tre fix dalla revisione del codice del 13/11, chiesti da
  Walter (regola "una modifica al giorno per bot" saltata da lui in modo esplicito).
  Il DNA di Valeria NON è stato toccato. Nessun bot cambia chiamate: cambiano solo il
  controllo interno di review_and_fix(), la classificazione degli errori Gemini e
  l'escape di tre messaggi di errore.
  - _review_result_problem() (il controllo introdotto in 2.4.19) lasciava passare
    revisioni mutilate di Gemini. Provato con il prompt shooting mosaico reale:
    venivano accettate la revisione senza l'intera "Reference image analysis" (HEX
    compresi), senza il blocco MULTI-SUBJECT LOCK, avvolta in ``` , con un preambolo
    tipo "Here is the corrected prompt:" e troncata subito dopo l'intestazione
    "BACKGROUND LOCK:**" (i caratteri * e ` valevano come fine frase). Ora si scarta
    la revisione e si usa il prompt costruito dal codice se: (a) mancano
    MULTI-SUBJECT LOCK, "Reference image analysis" o "Technical:" e c'erano
    nell'originale; (b) manca un codice colore HEX presente nell'originale; (c) la
    risposta è avvolta in ``` o inizia con un preambolo e l'originale no; (d) finisce
    su un'intestazione che termina con ":" o ":**", oppure se l'originale chiude con la riga
    "Technical:" e la revisione no. Tutti i controlli valgono solo per
    ciò che l'originale contiene, quindi i prompt di Vogue, Surprise e Filtro non
    cambiano comportamento.
  - _classify_gemini_error(): il codice di stato si cerca come numero a sé stante, non
    come sottostringa (un 400 con "token count (1048503)" non è più un "503 overload").
    Gli errori INVALID_ARGUMENT / 400 non sono mai transitori. Ora sono transitori,
    quindi ritentati con la catena modelli e il backoff: 500, 502, 504, INTERNAL,
    DEADLINE_EXCEEDED, "disconnected", "remote protocol", "reset by peer".
    Prima un 500 o un "Server disconnected" davano errore al primo tentativo, senza
    fallback.
  - html.escape sul testo d'errore in generate_caption(), generate_mini_caption() e
    generate_mini_prompt(): un errore con "<" o "&" faceva rispondere 400 a Telegram
    (parse_mode HTML) e l'utente non riceveva nulla.
CHANGELOG 2.4.20 (12/11/2026): revisione del codice su richiesta di Walter. Il DNA
  di Valeria (volto, capelli, occhiali, barba, corpo) NON è stato toccato.
  - review_and_fix(): la regola 6 (togli "Valeria Cross") contraddiceva la regola 5
    (il watermark contiene "Valeria Cross") — ora il watermark è escluso
    esplicitamente. Regola 5 allineata al DNA: "bottom center" (prima
    "bottom center/left").
  - review_and_fix(): nuovo face_mode="described" — regole su capelli, occhiali e
    subject bleed che rimandano all'identità GIÀ descritta nel prompt, senza
    rimandi a una foto allegata e senza imporre un testo di DNA. Serve a Vogue,
    il cui volto video è descritto a parole (prima la revisione in modalità
    "photo" poteva reinserire "attached reference photo" nel prompt video).
  - body_art_clause()/has_multiple_figures(): riconoscono anche le varianti di
    Gemini ("No visible tattoos", "Single figure", "Only one person", ...) —
    prima aggiungevano per errore ~1.800 caratteri di clausole inutili.
  - analyze_scene(): max_tokens 3000 → 8192. Con risposte troncate (finish_reason
    MAX_TOKENS) le ultime sezioni dell'analisi potevano mancare senza avviso.
  - Reset contatori: alle 08:00 ora di Lisbona tutto l'anno (Europe/Lisbon), non
    più alle 07:00 UTC fisse (in inverno erano le 07:00 di Lisbona). Log corretto.
  - Contatori chiamate: contano anche i tentativi ripetuti dentro generate()
    (prima un generate() con 5 tentativi contava 1). La notifica 🔑 resta una
    sola per richiesta. Rotazione chiave e contatori protetti da un lock.
  - Messaggio quota in analyze_scene(): non dice più "le 20 richieste di questa
    chiave" (generate() prova tutte le chiavi prima di arrendersi).
  - Rimossa sanitize_user_input() — non usata da nessun bot dalla Vogue 4.2.
    __all__: tolto il doppione di is_allowed, aggiunti body_art_clause,
    BODY_ART_EXCEPTION_TEXT e MODEL_LITE.

CHANGELOG 2.4.19 (07/11/2026):
  - FIX 1 (difetto verificato nel codice): body_art_clause() e has_multiple_figures()
    leggono i campi "BODY ART:" e "FIGURES:" dell'analisi con una regex che si
    aspetta il testo subito dopo i due punti. Se analyze_scene() restituisce i
    nomi dei campi in grassetto markdown ("**BODY ART:** None.", "**FIGURES:** One
    figure."), la regex legge "** None." / "** One figure." come contenuto reale:
    BODY ART EXCEPTION e MULTI-SUBJECT LOCK (e la frase "if multiple figures are
    present" nel checklist del mosaico) venivano aggiunti anche con zero tatuaggi
    e una sola figura — circa 1.800 caratteri inutili per prompt, solo quando
    Gemini formatta in grassetto (varianza dell'analisi, non una scelta del
    codice). Ora il markdown "**" e i punti elenco iniziali ("* ", "- ") vengono
    ignorati prima del controllo; per input senza grassetto né elenchi il
    comportamento è identico a prima.
  - FIX 2 (difetto verificato): review_and_fix() accettava qualunque testo
    restituito da Gemini senza controllare che fosse completo. Il 07/11 /lastprompt
    ha mostrato un prompt finito a metà frase ("...and the same body identity
    described") — mancavano IDENTITY LOCK, HAIR LOCK, BACKGROUND LOCK e la riga
    Technical; il 23/10 un 503 sul modello lite aveva prodotto un prompt riscritto
    e accorciato, senza COEXISTENCE/BUST VOLUME. Ora dopo la revisione si controlla
    (_review_result_problem): lunghezza non inferiore al 60% dell'originale, fine
    di frase se l'originale finisce in modo chiuso, presenza dei blocchi
    obbligatori presenti nell'originale (COLOR/OUTFIT DETAIL/TEXTURE LOCK,
    COEXISTENCE, BUST VOLUME, IDENTITY/HAIR/BACKGROUND LOCK locali, liste pose/
    framing). Se un controllo fallisce si usa il prompt originale costruito dal
    codice (sempre completo) e il motivo va nel log. Costo accettato: in quei
    casi si perdono le correzioni di Gemini su capelli/occhiali/subject bleed,
    già coperte dai blocchi del codice.
  - DIAGNOSI (nessun cambio di comportamento): GeminiClient._call_model() ora
    scrive nel log un warning se il finish_reason non è STOP (es. MAX_TOKENS,
    SAFETY, ...), così al prossimo taglio si saprà perché Gemini si è fermato.
    La causa del taglio del 07/11 NON è nota: un limite di token è solo
    un'ipotesi, e Walter segnala che prompt completi in 4 blocchi sono arrivati
    in passato, quindi il solo limite di lunghezza non basta a spiegarlo.
  - Non toccati: Atelier (2.8.0 invariato), costanti DNA, max_tokens=8192.
    Non ancora testato in produzione. Rollback: ridistribuire la 2.4.18.

CHANGELOG 2.4.18 (23/10/2026):
  - Nuova modalità volto "testo" per i bot che costruiscono l'identità via
    build_valeria_identity() (oggi solo Atelier). Motivo (Walter): con la foto
    reale del volto allegata in Flow le scene più spinte vengono bloccate; senza
    foto il volto esce generico, perché dal 25/07 VALERIA_FACE rimanda alla
    foto allegata invece di descrivere occhiali/barba/capelli. Nuove costanti
    VALERIA_HAIR_TEXT, VALERIA_GLASSES_TEXT, VALERIA_FACE_TEXT — testo messo a
    punto con Walter in 5 versioni provate a mano su Flow il 23/10 (v2-v6, 8
    generazioni per variante, senza foto allegata): età 60, volto ovale di pienezza media,
    barba piena bianco-argento, occhiali spessi verde petrolio di forma
    geometrica tondeggiante (l'asimmetria reale non viene resa da Flow in
    nessuna variante, quindi non richiesta), capelli pettinati all'indietro
    come nella foto scelta da Walter. Esito del test: ~2 volti su 8 molto
    simili senza foto, ~80% con foto + testo (stima di Walter) — il testo
    avvicina il tipo di volto, non l'identità.
  - DEVIAZIONI dal testo v6 testato, dichiarate: "male face" invece di "man"
    (coerenza col DNA esistente "male face" e col corpo femminile, per non
    spingere un torso maschile); tolto "warm wide smile" (l'espressione la
    decide la scena, il mosaico Atelier varia già le espressioni); aggiunto
    "ending well above the collar" ai capelli (limite superiore contro la
    deriva a capelli lunghi già vista il 14/07). Questi tre punti NON sono
    stati provati su Flow così come scritti.
  - build_valeria_identity(safe=False, face_mode="photo"): nuovo parametro,
    default invariato — Vogue e ogni chiamata esistente producono lo stesso
    identico testo della 2.4.17 (verificato a runtime confrontando l'output).
  - review_and_fix(prompt, client, face_mode="photo"): in modalità testo le
    regole 1 (capelli), 2 (occhiali) e 4 (subject bleed) usano il testo
    dettagliato invece di "short Italian cut, nape exposed" e "attached
    reference photo" — senza questa modifica avrebbero riscritto capelli e
    occhiali come ultimo step prima di Flow (stesso schema del 25/07,
    lezione #17). Default invariato, verificato.
  - Non toccati: VALERIA_FACE, VALERIA_DNA (Vogue), sanitize_user_input.
    Non ancora testato in produzione. Rollback: ridistribuire la 2.4.17.

CHANGELOG 2.4.17 (03/10/2026):
  - Aggiornamento DNA Valeria su richiesta esplicita di Walter: peso 85kg →
    75kg in VALERIA_BODY_STRONG e VALERIA_BODY_SAFE (unica coppia trovata
    nello shared — grep mirato su "85" vicino a kg/bust/hourglass prima di
    considerare il fix completo, lezione delle sessioni precedenti).
    Altezza (180cm) e resto della descrizione invariati, nessun'altra
    modifica. Stessa correzione necessaria in Surprise_210.py (non importa
    il DNA da shared, ha una riga locale duplicata in due punti) — vedi
    changelog di quel file. Atelier_272.py, Vogue_432.py, Architect_311.py
    verificati: nessun riferimento hardcoded al peso, ereditano tutto da
    shared via import. Non ancora testato in produzione.

CHANGELOG 2.4.16 (01/10/2026):
  - Walter ha inoltrato un suggerimento di Gemini: un retry loop generico con
    backoff esponenziale (2,4,8,16,32s) su un singolo `genai.Client()` senza
    chiave esplicita. Valutato e NON adottato come sostituto di generate():
    usa una sola chiave (incompatibile con la rotazione a 5 chiavi/progetti
    di GeminiClient), riprova solo sullo stesso modello (nessun fallback su
    MODEL_FALLBACKS), e perde messaggio Telegram amichevole/logging/
    distinzione 429 vs 503 già presenti. L'unica idea utile — attendere di
    più prima di arrendersi — è stata applicata direttamente ai parametri
    già introdotti in 2.4.15, invece di sostituire la logica.
  - Verificato prima di allungare l'attesa (rischio: bloccare un worker a
    lungo) che tutti i bot che chiamano generate() girano su
    infinity_polling (mai webhook, nessun rischio di timeout Telegram) con
    pool di thread dedicato: Atelier e Surprise un ThreadPoolExecutor
    esplicito (max_workers=4), Vogue il pool interno di telebot
    (threaded=True, num_threads=2 di default, mai sovrascritto). Architect e
    Filtro non più in uso da Walter (Vogue solo ~1 volta/mese, uso
    prevalentemente solo-utente) — contesa sul pool di thread non è un
    rischio pratico.
  - GEMINI_RETRY_PASSES: default 2 → 4, reso configurabile via env (prima
    hardcoded). GEMINI_BACKOFF_BASE: default 3.0 → 4.0, reso configurabile
    via env. Con i default: fino a 3 attese tra i 4 giri (~4-5.5s, ~8-9.5s,
    ~16-17.5s con jitter) prima di arrendersi, oltre al tempo delle chiamate
    stesse — che durante un vero sovraccarico varia molto: nel log del 28/09
    alcune risposte 503 sono arrivate in ~1s, una in ~12.5s. Nessuna
    garanzia contro un episodio sostenuto di minuti come quello del 28/09 —
    solo più occasioni di incrociare una schiarita, non una soluzione al
    sovraccarico lato Google.
  - Nessuna modifica alla logica di generate() stessa (identica a 2.4.15).

CHANGELOG 2.4.15 (28/09/2026):
  - Walter ha mandato il log di un fallimento reale (Atelier, ore di
    "Servizio Gemini non disponibile"): 503 UNAVAILABLE "high demand" sia su
    gemini-3.8-flash sia su gemini-3.1-flash-lite, identico su tutte e 5 le
    chiavi (5 progetti Google separati, tutti free tier). Diagnosi: overload
    lato Google, per MODELLO — non dipende dalla chiave né dal progetto. Il
    vecchio generate() però reagiva male: dopo il fallback su lite ruotava
    tutte le altre 4 chiavi sullo stesso modello (4 chiamate su 6 identiche e
    inutili), senza alcun backoff, con fino a ~20s di attesa per l'utente e
    catena di due soli modelli entrambi colpiti. Riscritta solo la strategia
    di retry in generate() (firma e valore di ritorno invariati):
      * 503/overload → si scorre la catena modelli [richiesto, *MODEL_FALLBACKS]
        sulla STESSA chiave, SENZA ruotare chiavi. Se tutta la catena fallisce:
        backoff con jitter (GEMINI_BACKOFF_BASE, ~3-4.5s) e un secondo giro
        (GEMINI_RETRY_PASSES = 2). Massimo 4 chiamate invece di 6.
      * 429/quota → la coppia (chiave, modello) è segnata esaurita per quella
        chiamata; si prova il modello successivo sulla stessa chiave e, se una
        coppia della chiave è esaurita, si ruota alla chiave successiva (le
        quote sono per progetto+modello, quindi qui la rotazione ha senso).
        Se l'errore è solo quota ovunque non si ripete il giro né si dorme.
      * errori non transitori (SAFETY, parametri, ecc.) → sollevati subito.
      * tetto di sicurezza GEMINI_MAX_ATTEMPTS = 16 tentativi per chiamata.
  - NUOVO: variabile d'ambiente opzionale GEMINI_FALLBACK_MODELS (elenco
    separato da virgole) per aggiungere modelli in coda alla catena
    (MODEL_FALLBACKS = [MODEL_LITE] + elenco) senza toccare il codice.
    NESSUN terzo modello è hardcoded: non ho potuto verificare quale
    risponda ora sul free tier, e le segnalazioni utente indicano 503 su
    tutta la famiglia flash 3.x. Va provato prima di configurarlo.
  - Cambi di comportamento collaterali, tutti voluti:
      * last_fallback_code (2.4.12) viene ora impostato solo quando un
        modello di fallback ha DAVVERO risposto, non appena il modello
        richiesto fallisce: prima poteva restare impostato anche se il
        modello richiesto riusciva al tentativo successivo.
      * una risposta vuota da MODEL_LITE ora solleva (con il motivo
        SAFETY/finish_reason) invece di essere ignorata in silenzio.
      * gli errori transitori non stampano più il traceback completo a ogni
        tentativo (logger.warning, riga corta); il traceback resta solo per
        gli errori non transitori.
      * le chiamate usano self._clients[idx] invece di self._client, per non
        cambiare chiave a metà chiamata se un altro thread ruota.
      * la rotazione chiave non scatta più su 503, quindi le callback
        on_key_rotation si attivano solo su 429/quota e sul round-robin.
  - Classificazione errori estratta in _classify_gemini_error() (stessi
    criteri di prima: 503/unavailable/overloaded, 429/quota/exhausted,
    timeout/connection). Non aggiunti 500/504.
  - Non ancora testato in produzione. Testato in locale con client finti
    (10 scenari: 503 ovunque, fallback riuscito, 429 con rotazione, quota
    ovunque, successo al secondo giro, errore non transitorio, risposta
    vuota, catena estesa da env).

CHANGELOG 2.4.14 (26/09/2026):
  - Walter ha chiesto di aggiornare i bot al nuovo modello gemini-3.8-flash,
    dopo aver segnalato 503 persistenti su gemini-3.5-flash (ormai tre
    generazioni indietro: 3.6/3.7/3.8 già rilasciati). Verificato prima di
    cambiare nulla: (1) l'ID modello esatto è "gemini-3.8-flash", confermato
    su più fonti ufficiali Google; (2) il requisito SDK per l'intera
    famiglia Gemini 3.x (incluso 3.8) è google-genai >=2.0.0 — il pin
    attuale (>=2.11.0) lo soddisfa ampiamente, nessun aggiornamento
    requirements.txt necessario; (3) Gemini 3.x rimuove/deprecca
    temperature/top_p/top_k/candidate_count e sostituisce thinking_budget
    con thinking_level — verificato che generate() (qui sotto) passa solo
    safety_settings e max_output_tokens a GenerateContentConfig, nessuno
    dei parametri deprecati è in uso, quindi nessuna modifica di codice
    necessaria per compatibilità. Cambiato solo MODEL. MODEL_LITE
    ("gemini-3.1-flash-lite") NON toccato — fuori dallo scope di questa
    richiesta, ma segnalato a Walter che esiste anche un
    "gemini-3.5-flash-lite" più recente, da valutare separatamente se
    interessa. Non ancora testato in produzione — resta da vedere se il
    modello più recente riduce davvero i 503 come sperato, oppure se (come
    successo con gemini-3-flash-preview a suo tempo) un modello nuovo porta
    con sé i suoi problemi di capacità nelle prime settimane.

CHANGELOG 2.4.13 (21/09/2026):
  - Walter ha ricevuto un errore Telegram grezzo invece del messaggio amichevole
    atteso: "Bad Request: can't parse entities: Unsupported start tag
    'blockedreason.prohibited_content:'". Causa isolata in analyze_scene():
    quando Gemini blocca l'analisi per PROHIBITED_CONTENT (prompt_feedback,
    non finish_reason SAFETY), il testo grezzo dell'errore Python contiene
    parentesi angolari (repr di un enum, es. "<BlockedReason.
    PROHIBITED_CONTENT: 'PROHIBITED_CONTENT'>") — la classificazione errori
    non riconosceva PROHIBITED_CONTENT come equivalente a SAFETY, quindi
    cadeva nel ramo else finale, che mandava il testo grezzo a Telegram in
    parse_mode HTML SENZA html.escape() — Telegram lo interpretava come un
    tag HTML non valido e rifiutava l'intero messaggio (l'utente non vedeva
    nessun errore leggibile, solo il 400 grezzo dell'API Telegram). Fix
    doppio: (1) PROHIBITED_CONTENT aggiunto alla classificazione SAFETY, ora
    restituisce il messaggio amichevole già esistente "Immagine bloccata dai
    filtri Gemini" invece di cadere nel ramo generico; (2) html.escape()
    aggiunto anche al ramo else finale, come difesa in profondità per
    qualunque futuro testo di errore non classificato che contenga
    caratteri HTML speciali. Stesso identico bug e stessa correzione
    applicata anche a analyze_video() (Vogue, locale). Non ancora testato
    in produzione.

CHANGELOG 2.4.12 (03/08/2026):
  - Walter ha chiesto che, quando scatta il fallback su MODEL_LITE (503 o
    429), l'utente veda anche il codice errore nell'etichetta del prompt —
    per capire se conviene riprovare a breve (503, transitorio, il modello
    può tornare disponibile) o se resterà su lite fino al reset delle 08:00
    (429, quota esaurita per la giornata, riprovare prima non cambia
    nulla). Aggiunto GeminiClient.last_fallback_code ("503"/"429"/
    "transient"/None) impostato dentro generate() nello stesso punto in cui
    scatta già il fallback (2.4.8) — non si azzera da solo dentro
    generate(), perché una richiesta utente può fare più chiamate generate()
    (analisi + review_and_fix) e vogliamo che l'informazione sopravviva a
    entrambe. Nuovo metodo reset_fallback(), stesso pattern di
    reset_counters() — il chiamante lo invoca esplicitamente a inizio
    richiesta. Non ancora testato in produzione.

CHANGELOG 2.4.11 (03/08/2026):
  - Walter ha notato che la riga "Subject identity" del checklist mosaico
    (corretta in 2.4.10 per menzionare ogni figura) era scritta come testo
    STATICO, sempre identica in ogni prompt — anche quando FIGURES dice
    "One figure.", cioè quando la frase "if multiple figures are present"
    non ha alcun senso, testo morto. A differenza di multi_subject_clause(),
    che è correttamente condizionale. Estratta la logica di rilevamento in
    una nuova funzione has_multiple_figures() (usata internamente anche da
    multi_subject_clause(), stessa regex non più duplicata) — usata da
    Atelier per costruire quella riga del checklist condizionalmente: con
    una sola figura torna al testo originale senza la parentesi. Non
    ancora testato in produzione.

CHANGELOG 2.4.10 (01/08/2026):
  - Walter ha testato in produzione il multi-soggetto di 2.4.9: Vogue e
    Atelier modalità singola hanno funzionato bene (identità Valeria su
    entrambe le figure), il MOSAICO Atelier no — la figura secondaria ha
    mantenuto il volto reale della foto originale invece del volto di
    Valeria. Riscritto VALERIA_MULTI_SUBJECT_LOCK per essere esplicito
    quanto gli altri LOCK (FACE IDENTITY LOCK, HAIR LOCK, ecc.) invece di
    un rimando indiretto — dice direttamente che la sostituzione vale per
    OGNI figura, non solo la principale, e che nessun volto originale
    sopravvive per nessuna figura. Fix di parte 2 in Atelier (2.6.1, vedi
    changelog lì) sulla riga "Subject identity" del mosaico. Non ancora
    testato in produzione.

CHANGELOG 2.4.9 (01/08/2026):
  - Walter ha chiesto di gestire foto di riferimento con 2+ soggetti distinti
    (m+f, m+m, f+f...): il prompt generato deve presentare una figura
    multipla, tutte con la stessa identità Valeria (stesso volto/DNA),
    posizionate/interagenti come nell'originale, ciascuna con il proprio
    outfit separato (non un outfit unico condiviso). Rilevamento automatico,
    non un comando esplicito. Aggiunto campo FIGURES a _ANALYZE_PROMPT
    (conta le persone, posa/posizione/interazione fisica di ciascuna, cieco
    sull'identità come OUTFIT/PROPS & ACTIONS) e reso OUTFIT/ACCESSORIES/BODY
    ART strutturabili per figura quando FIGURES rileva 2+ persone (stessa
    label breve usata in FIGURES). Nuova costante VALERIA_MULTI_SUBJECT_LOCK
    + funzione multi_subject_clause() — stesso identico pattern di
    body_art_clause(): nessun impatto sul caso comune (una sola figura).
    Applicata a Vogue e Atelier (unici bot in scope su richiesta di Walter).
    Non ancora testato in produzione.

CHANGELOG 2.4.8 (30/07/2026):
  - Walter ha mandato il log di un fallimento reale: non era un 503/overload
    come nei casi precedenti, ma un 429 RESOURCE_EXHAUSTED — quota free tier
    (20 richieste/giorno per chiave per modello su gemini-3.5-flash) esaurita
    su tutte e 5 le chiavi nello stesso giro. Il fallback reattivo su
    MODEL_LITE, introdotto in 2.4.7 solo per il 503, ora scatta per
    QUALSIASI errore transitorio (503/overload, 429/quota, timeout,
    connessione) — non solo il 503. Stessa logica: ritenta SUBITO con
    MODEL_LITE sulla chiave corrente prima di ruotare, perché MODEL_LITE ha
    una quota separata da gemini-3.5-flash, non ancora toccata. Non ancora
    testato in produzione.

CHANGELOG 2.4.7 (30/07/2026):
  - Walter ha chiesto di cambiare approccio rispetto alla 2.4.6: niente più
    soglia di consumo (75 call) per passare a MODEL_LITE — rimossa
    LITE_FALLBACK_AT. Ora il fallback è reattivo: su un 503/overload si
    ritenta SUBITO con gemini-3.1-flash-lite sulla stessa chiave, prima
    ancora di ruotare chiave (la rotazione chiave non serve contro un
    overload lato server, condiviso da tutte le chiavi). Se anche
    MODEL_LITE fallisce sulla chiave corrente, si prosegue con la
    rotazione chiavi esistente ma restando su MODEL_LITE per il resto dei
    tentativi di quella chiamata. Non ancora testato in produzione.

CHANGELOG 2.4.6 (30/07/2026):
  - Walter segnala errori "Servizio Gemini non disponibile — Sovraccarico
    temporaneo" ricorrenti da due settimane, tipicamente dalle 12/13 di
    Lisbona fino a sera tardi. Il retry esistente in generate() ruota le
    chiavi ma non aiuta contro un vero overload lato server (503) — il
    modello è saturo per tutte le chiavi contemporaneamente, non è un
    problema di quota della singola chiave. Attivato il piano di fallback
    già scritto (ma mai implementato) nel changelog 2.3.16: oltre
    LITE_FALLBACK_AT (75) call totali giornaliere, le chiamate sul modello
    di default passano automaticamente a MODEL_LITE
    ("gemini-3.1-flash-lite"). Non tocca le chiamate con model esplicito
    diverso (es. MODEL_TEXT_ID per le caption). Non ancora testato in
    produzione — da verificare se la soglia 75 è quella giusta una volta
    osservato il comportamento reale.

CHANGELOG 2.4.5 (28/07/2026):
  - Walter ha segnalato un pattern ricorrente su scene a pelle scoperta
    (torso nudo/scoperto: piscina, spiaggia, doccia, ecc.): il corpo generato
    torna maschile (peloso, senza seno) nonostante FULL D-CUP BUST e
    COEXISTENCE già presenti — non un caso isolato, confermato ricorrente.
    Segnalata anche una correlazione con la variante Gemini usata in Flow:
    capita molto più spesso con "nano pro" che con "nano 2" o "nano light" —
    annotato per riferimento, ma è una scelta manuale di Walter dentro Flow
    al momento di incollare il prompt, non un parametro del codice dei bot:
    nessuna leva qui lato codice per quella parte. Aggiunto un rinforzo
    INCONDIZIONATO (vale in ogni immagine, non solo a pelle scoperta, su
    richiesta esplicita di Walter — niente di legato a una scena specifica)
    dopo la clausola COEXISTENCE sia in VALERIA_BODY_STRONG ("BUST VOLUME —
    ALWAYS VISIBLE") sia in VALERIA_BODY_SAFE ("SILHOUETTE — ALWAYS
    VISIBLE"), ereditato automaticamente ovunque questi due blocchi sono già
    usati (Vogue via VALERIA_DNA, Atelier via build_valeria_identity()).
    Non garantito al 100%: nota permanente già in HANDOFF, questi rinforzi
    riducono ma non eliminano la variabilità di Flow. Non ancora ritestato
    in produzione dopo questo fix.

CHANGELOG 2.4.4 (27/07/2026):
  - Walter ha segnalato scostamento tra un mosaico generato da Atelier e la
    foto originale: il pattern del bodysuit (mosaico a frammenti fini, tipo
    specchio infranto) era diventato nel generato un pattern "arlecchino" a
    grandi rombi piatti — la scala/densità del pattern non teneva. Prima
    ipotesi (negative prompt sul pattern arlecchino) scartata su richiesta
    esplicita di Walter: Gemini non considera i negative prompt in
    generazione (confermato anche dall'audit 2.4.0/2septendecies). Aggiunta
    una nuova costante generica VALERIA_TEXTURE_LOCK — non legata a questa
    scena/foto specifica, vale per qualsiasi pattern/texture/sfondo/
    abbigliamento — interamente in positivo (nessun "not/never"), che
    richiede granularità fine (decine/centinaia di unità piccole) per
    qualunque pattern descritto nella scena. Inserita sia in VALERIA_DNA
    (usato da Vogue) sia dentro build_valeria_identity() (usato da Atelier)
    — verificato che Atelier NON passa mai da VALERIA_DNA nonostante lo
    importi, quindi mettere il fix solo lì non sarebbe arrivato ad Atelier.
    Non ancora testato in produzione.

CHANGELOG 2.4.3 (25/07/2026):
  - Il fix 2.4.2 sul campo BACKGROUND aveva un solo esempio illustrativo
    ("e.g. 'approximately a dozen vintage clocks...'"), specifico dello
    scenario di test (stanza tea-party con orologi) usato per diagnosticare
    il problema — a differenza di OUTFIT, che non ha esempi e resta
    puramente definizionale. Walter ha chiesto se il fix generalizza a
    scene non fatte di oggetti discreti (es. una giungla) — risposta: il
    meccanismo sì (nessun riferimento hardcoded al caso specifico), ma
    l'unico esempio presente era sbilanciato verso scene "da collezione di
    oggetti", rischio concreto di bias sottile su scene organiche. Aggiunto
    un secondo esempio parallelo per contenuto naturale/organico (fogliame,
    fauna) accanto a quello originale per contenuto man-made, così
    l'istruzione resta domain-agnostic invece di implicitamente orientata
    verso interni con oggetti numerabili. Non ancora testato in produzione
    su nessuno dei due tipi di scena.

CHANGELOG 2.4.2 (25/07/2026):
  - Campo BACKGROUND di _ANALYZE_PROMPT era una singola riga generica
    ("Exact location, architecture, surfaces, props, environment — be
    specific"), l'unico campo del prompt di analisi senza richiesta di
    enumerazione oggetto-per-oggetto — a differenza di OUTFIT/ACCESSORIES/
    BODY ART/PROPS & ACTIONS, tutti esplicitamente "every X as a standalone
    object" con HEX. Causa trovata confrontando un mosaico Atelier reale
    con la foto originale (Walter, sfondo tea-party surrealista denso di
    orologi/lanterne/porcellane sospese): l'analisi generata riassumeva
    tutto in poche frasi di categoria ("shelves packed with...", "numerous
    vintage clocks...") invece di elencare quantità/densità reali — nessun
    lock in fase di generazione può recuperare un dettaglio mai catturato
    nel testo. Riscritto BACKGROUND con lo stesso trattamento esaustivo di
    OUTFIT: enumerazione per oggetto, conteggio/densità approssimativa per
    elementi ripetuti, HEX dove rilevante, profondità spaziale
    (foreground/midground/background). Vedi anche Atelier 2.5.2 per la
    seconda metà del fix (BACKGROUND LOCK lato generazione).
    Non ancora testato in produzione.

CHANGELOG 2.4.1 (25/07/2026):
  - VALERIA_FACE conteneva descrizioni hardcoded di occhiali ("Thin octagonal
    Vogue Havana dark tortoiseshell frame") e barba ("approximately 6-7cm,
    perfectly groomed, dense and uniform") che confermate in contraddizione
    diretta con la foto di riferimento reale che Walter allega di volta in
    volta al prompt in Flow (occhiali rotondi/spessi/scuri nella foto vs.
    ottagonali/sottili/tartarugato nel testo; barba visibilmente più lunga e
    meno uniforme nella foto vs. 6-7cm curata nel testo). Su conferma
    esplicita di Walter, la foto allegata è sempre autorevole su questi due
    punti — il testo non deve più specificare forma/lunghezza, deve rimandare
    alla foto. Aggiunta anche una riga di priorità esplicita in apertura del
    blocco ("the photo wins" in caso di conflitto) — prima non esisteva
    alcun riferimento testuale all'immagine allegata, il modello non aveva
    modo di sapere che la foto va trattata come autorità sopra il testo.
    Non toccato: sezione Hair (nessuna contraddizione accertata, solo un
    dubbio dovuto a una foto di riferimento particolarmente ventosa) e
    VALERIA_BODY_STRONG/SAFE (fuori scope, non discussi in questa sessione).

    Il fix su VALERIA_FACE da solo era inutile: review_and_fix() (usata da
    Vogue 2x e Atelier 3x, ultimo step prima di Flow) e sanitize_user_input()
    (usata da Vogue sul testo utente) avevano la STESSA specifica hardcoded
    ("thin octagonal Vogue Havana dark tortoiseshell", "beard 6-7cm") in
    punti indipendenti — regola 2 (GLASSES MANDATORY) e regola 4 (SUBJECT
    BLEED) di review_and_fix(), più la lista "IMMUTABLE traits" di
    sanitize_user_input(). Reiniettavano la vecchia specifica anche dopo la
    correzione di VALERIA_FACE. Corrette anche queste tre, stessa logica di
    rimando alla foto allegata. Non toccati in questa sessione (su richiesta
    esplicita di Walter, rimandati): i 3 blocchi "IDENTITY LOCK" locali di
    Atelier (build_full_prompt, build_shooting_prompt singolo e mosaico) con
    lo stesso testo "tortoiseshell glasses" hardcoded indipendentemente da
    shared — stesso fix, stessa sessione di lavoro del 17/07 che ha
    introdotto quei blocchi. TODO aperto per la prossima sessione. WALTER_DNA
    in Surprise (feature Pride) e il testo LEGO in Filtro: esplicitamente
    fuori scope, Walter non usa questi due bot al momento.

    Ipotesi di lavoro, non certezza: questo fix riduce ma non elimina la
    percentuale di generazioni che ignorano il volto — resta un limite
    architetturale del modello (sampling probabilistico), non risolvibile
    al 100% solo col prompt.

CHANGELOG 2.4.0 (17/07/2026):
  - Fix generale, non un patch puntuale. Verificato sulla documentazione
    ufficiale Google Cloud (prompting guide Nano Banana) che il modello
    dietro Flow NON ha un campo negativePrompt indipendente — architettura
    multimodale end-to-end, non diffusion con sottrazione vettoriale come
    Stable Diffusion/Midjourney/Imagen. Google raccomanda esplicitamente
    "positive framing, not negative" per questo modello. Causa scatenante:
    HAIR LOCK v2.0.7 e v2.0.8 su Atelier (basati su negative prompt, vedi
    HANDOFF) non hanno retto a test successivi — calvizie ricomparsa
    nonostante due round di negative prompt via via più estesi. Rimosso
    l'intero meccanismo negative prompt dall'impianto DNA condiviso:
    VALERIA_FACE e VALERIA_BODY_STRONG/SAFE riscritte in positivo puro
    (tolte le frasi "DO NOT shave it", "DO NOT GENERATE A MALE PHYSIQUE",
    ecc. — il contenuto informativo resta identico, cambia solo il framing).
    VALERIA_NEGATIVE eliminata interamente (era usata da Vogue via
    VALERIA_DNA e 3 volte in Surprise) — le due garanzie generiche che
    portava (mani corrette, nessun testo sovrapposto) spostate in positivo
    dentro VALERIA_DNA. review_and_fix(): punto 3 (scansione sezione
    negative) rimosso perché non più applicabile; punto 8 (BODY HAIR
    ENFORCEMENT) riscritto per richiedere solo l'affermazione positiva,
    tolta la riga che reiniettava "NEGATIVE PROMPT — BODY" nel testo
    finale — prima questo passaggio avrebbe vanificato qualunque pulizia
    fatta a monte nei singoli bot, dato che è l'ultimo step prima
    dell'invio a Flow. Vogue (203) e Surprise (203) aggiornati in
    parallelo per rimuovere i loro negative prompt locali — vedi
    changelog di ciascun bot. Atelier (209, sessione precedente) già
    allineato. Filtro (202) aveva import morti di VALERIA_FACE/BODY_STRONG/
    BODY_SAFE/NEGATIVE mai usati nei suoi prompt (confermato via grep —
    Filtro non inietta mai il DNA Valeria), ma aveva 3 negative prompt
    locali propri (editorial underwater, LEGO, wrapper "DO NOT ALTER")
    non collegati al DNA — corretti anche quelli nello stesso giro.
    Vedi HANDOFF sezione 2septendecies per il dettaglio completo.

CHANGELOG 2.3.18 (08/07/2026):
  - Risolto: la clausola "BODY ART EXCEPTION" (2.3.17) compariva in OGNI
    prompt generato da tutti i bot, anche con BODY ART: None — testo
    condizionale inerte nel caso comune. Analisi bot-per-bot (non assunta)
    ha rivelato che solo Vogue e Atelier passano davvero da analyze_scene()
    con un campo BODY ART ispezionabile; Filtro ha import morti (VALERIA_DNA
    mai usato nei suoi prompt); Surprise non analizza mai una foto di
    riferimento (clausola sempre morta lì, si risolve gratis); Architect fa
    analisi+scrittura in un'unica chiamata Gemini, senza produrre un campo
    esterno da controllare — non può avere una versione condizionale.
    Rimossa la clausola da VALERIA_BODY_STRONG/SAFE (tornano alla forma
    pre-2.3.17). Aggiunta BODY_ART_EXCEPTION_TEXT (stesso testo, costante
    isolata) e body_art_clause(scene_description) — quest'ultima restituisce
    il testo solo se BODY ART nella scena non è "None"/assente, altrimenti
    stringa vuota. Vogue e Atelier chiamano body_art_clause() dopo
    l'identità. Architect, su scelta esplicita di Walter, concatena
    BODY_ART_EXCEPTION_TEXT direttamente e sempre — stesso comportamento
    che aveva dal 07/07, solo spostato da VALERIA_BODY_STRONG a questa
    costante dedicata (compensazione necessaria per non perdere la
    capacità di preservare body art lì come effetto collaterale di questo
    fix, dato che Architect condivide VALERIA_DNA con Vogue). Filtro e
    Surprise non toccati — non ne avevano bisogno.

CHANGELOG 2.3.17 (07/07/2026):
  - Step 2/2 concordato con Walter dopo test su Atelier con foto di riferimento
    a body art elaborato (vedi HANDOFF sezione 2sexies/2septies). Aggiunto
    campo "BODY ART" a _ANALYZE_PROMPT (dopo PROPS & ACTIONS) — cattura
    tatuaggi/body paint/decorazioni sulla pelle come design visivo standalone,
    con fallback esplicito 'None.' se assenti (stesso pattern di PROPS &
    ACTIONS). Aggiunta clausola "BODY ART EXCEPTION — CONDITIONAL" sia a
    VALERIA_BODY_STRONG che VALERIA_BODY_SAFE: se la scena descrive body art,
    questo sostituisce "smooth porcelain skin" SOLO sulle zone indicate;
    altrimenti la pelle resta liscia ovunque come da default — nessuna
    invenzione di tatuaggi non descritti. Tocca tutti e 5 i bot (tutti
    importano VALERIA_DNA e/o build_valeria_identity, verificato via grep).
    Nessuna modifica a _ANALYZE_PROMPT oltre l'aggiunta del campo — ordine
    delle altre sezioni invariato. Nessun termine body-art nel NEGATIVE
    prompt esistente, quindi nessun conflitto da rimuovere.

CHANGELOG 2.3.16 (04/07/2026):
  - MODEL: "gemini-3-flash-preview" → "gemini-3.5-flash". Motivo: 503 diffusi
    su tutti i bot nonostante il retry/rotazione chiavi già presente in
    generate() — riconducibile al fatto che gemini-3-flash-preview è
    modello preview, con limiti di capacità/priorità più severi per
    definizione rispetto ai modelli GA (fonte: pagina ufficiale deprecation
    Google, che raccomanda esplicitamente la migrazione a gemini-3.5-flash).
    gemini-3.5-flash è GA/stabile, costa 3x il preview attuale ma non ha
    le restrizioni di capacità del livello preview. Scelta di Valeria tra
    gemini-3.5-flash (qualità superiore) e gemini-3.1-flash-lite (più
    economico, alto volume) — se emergono limiti (costo o rate limit) il
    piano di fallback concordato è passare a gemini-3.1-flash-lite o
    tornare a gemini-3-flash-preview. Nessun'altra occorrenza del vecchio
    nome modello nel file (verificato via grep) — tutti i bot ereditano
    MODEL da qui, nessuna modifica ai singoli bot in questo cambio.
    NOTA: i comandi /info di Vogue (MODEL_TEXT), Filtro (MODEL_TEXT_ID),
    Architect/Atelier/Surprise (stringa inline) mostrano ancora
    "gemini-3-flash-preview" in chat — sono costanti locali ai singoli
    bot, non lette da qui, quindi restano disallineate finché non
    vengono aggiornate separatamente nei singoli file bot.

CHANGELOG 2.3.15 (01/07/2026):
  - Solo pulizia documentale, nessuna modifica funzionale. Corretto commento
    obsoleto in _schedule_daily_reset(): il docstring riportava ancora
    "08:00 UTC (= 09:00 Lisbona estate)", residuo del fix 2.3.11 mai
    aggiornato dopo che il codice era stato corretto a hour=7 (07:00 UTC
    = 08:00 Lisbona estate). Il comportamento a runtime non cambia — era
    solo il commento a essere disallineato dal codice reale.

CHANGELOG 2.3.14 (25/06/2026):
  - GeminiClient: aggiunta GOOGLE_API_KEY_5 alla lista variabili d'ambiente.
    Atelier passa da 4 a 5 chiavi (una spostata da Architect, che ora ne ha 1).
    Architect non modificato — GeminiClient usa automaticamente solo le chiavi
    effettivamente presenti nell'environment.

CHANGELOG 2.3.13 (25/06/2026):
  - _ANALYZE_PROMPT: aggiunto campo PROPS & ACTIONS dopo ACCESSORIES.
    Cattura oggetti fisici in contatto diretto col corpo del soggetto (posizione,
    punto di contatto, azione). Prima, prop interattivi come "ice cube held between
    lips" venivano ignorati o descritti vagamente in BACKGROUND — causando prompt
    Atelier privi degli elementi scenici più forti dell'immagine originale.
    Nessuna altra modifica alla pipeline: protezione NSFW (analisi testuale mediata,
    senza visione diretta dell'immagine nei passaggi successivi) invariata.

CHANGELOG 2.3.12 (20/06/2026):
  - Fix robustezza GeminiCounterReset: datetime.utcnow() (deprecato) sostituito con
    datetime.now(timezone.utc). _reset_loop() ora avvolto in try/except — prima,
    una qualsiasi eccezione interna terminava il thread di reset giornaliero per
    sempre, in modo silenzioso, senza log e senza che i contatori si azzerassero più.

CHANGELOG 2.2.0 (31/05/2026):
  - GeminiClient: property current_key_num (1-based) e metodo on_key_rotation(callback).
    Permette ai bot di ricevere notifica immediata del cambio chiave API.

CHANGELOG 2.0.0 (26/05/2026):
  - Fix critico in review_and_fix(): client._model → MODEL.
    GeminiClient non espone _model come attributo pubblico.
    Causava crash silenzioso su tutti i bot che usano review_and_fix.

CHANGELOG 1.8.0 (25/05/2026):
  - Classificazione errore 503 UNAVAILABLE in analyze_scene(), generate_caption(),
    generate_mini_caption(), generate_mini_prompt() e tutti i classificatori.
    Messaggio differenziato: 503 → "Servizio non disponibile, riprova",
    429 → "Quota esaurita, reset 08:00".

CHANGELOG 1.7.0 (25/05/2026):
  - sanitize_user_input(text, client): pre-processa testo utente rimuovendo
    elementi incompatibili con DNA Valeria. Usata da Vogue e Architect.

CHANGELOG 1.6.0 (25/05/2026):
  - review_and_fix(prompt, client): revisione contraddizioni DNA (capelli, occhiali,
    body hair, watermark, subject bleed). Usata da Vogue, Architect e Atelier.

CHANGELOG 1.5.0 (24/05/2026):
  - generate_mini_prompt(text, client): estrae dal prompt Flow un mini-prompt
    strutturato formato Nosurprise (Location/Sky/Outfit/Style/Pose/Mood/Body).

CHANGELOG 1.4.0 (24/05/2026):
  - generate_mini_caption(text, client): genera caption da testo prompt,
    5 emoji + frase no-gender. Usata da Vogue, Architect, Atelier, Nosurprise/Pride.

CHANGELOG 1.3.0 (11/05/2026):
  - CaptionGenerator.extract_caption(): filtro ragionamento interno Gemini.

CHANGELOG 1.2.0 (10/05/2026):
  - GeminiClient.generate(): finish_reason reale su risposta vuota.
  - analyze_scene(): classificazione errori 429/SAFETY/timeout/generico.

CHANGELOG 1.1.0 (10/05/2026):
  - detect_mime_type(): JPEG/PNG/WebP da magic bytes.
  - SHARED_VERSION e SHARED_DATE esportate.

CHANGELOG 1.0.x (09/05/2026):
  - Versioni iniziali: GeminiClient, HealthServer, analyze_scene(),
    generate_caption(), CaptionGenerator, VALERIA_DNA, EDITORIAL_WRAPPER.
"""

import os, html, logging, threading, flask, re, time, random
from google import genai
from google.genai import types as genai_types

# Esportati per uso nei bot
__all__ = [
    'GeminiClient', 'CaptionGenerator', 'HealthServer', 'is_allowed',
    'VALERIA_FACE', 'VALERIA_BODY_STRONG', 'VALERIA_BODY_SAFE',
    'VALERIA_WATERMARK', 'VALERIA_TEXTURE_LOCK', 'VALERIA_MULTI_SUBJECT_LOCK',
    'VALERIA_DNA', 'EDITORIAL_WRAPPER',
    'VALERIA_FACE_TEXT', 'VALERIA_HAIR_TEXT', 'VALERIA_GLASSES_TEXT',
    'build_valeria_identity', 'generate_caption', 'generate_mini_caption', 'generate_mini_prompt',
    'review_and_fix', 'multi_subject_clause', 'has_multiple_figures',
    'body_art_clause', 'BODY_ART_EXCEPTION_TEXT',
    'analyze_scene', 'genai_types', 'MODEL', 'MODEL_LITE', 'detect_mime_type',
    'SHARED_VERSION', 'SHARED_DATE',
]

logger = logging.getLogger(__name__)

MODEL = "gemini-3.8-flash"
# Fallback automatico — introdotto in 2.4.6 (soglia 75 call/giorno), reso
# REATTIVO in 2.4.7 su richiesta di Walter: niente più soglia di consumo —
# su un 503/overload si ritenta SUBITO con MODEL_LITE, in ogni caso, prima
# ancora di ruotare chiave (vedi generate()). Piano di fallback originale
# concordato nel changelog 2.3.16. Non tocca le chiamate che passano
# esplicitamente un modello diverso (es. MODEL_TEXT_ID per le caption,
# definito nei singoli bot) — solo quelle sul default MODEL.
MODEL_LITE = "gemini-3.1-flash-lite"

# FIX 2.4.15 — catena di fallback modelli e parametri di retry (vedi changelog).
# MODEL_FALLBACKS: modelli provati in ordine dopo quello richiesto. Si estende
# senza toccare il codice con la variabile d'ambiente GEMINI_FALLBACK_MODELS
# (elenco separato da virgole, es. "modello-a,modello-b").
MODEL_FALLBACKS = [MODEL_LITE] + [
    _m.strip()
    for _m in os.environ.get("GEMINI_FALLBACK_MODELS", "").split(",")
    if _m.strip() and _m.strip() != MODEL_LITE
]
GEMINI_RETRY_PASSES = int(os.environ.get("GEMINI_RETRY_PASSES", "4"))   # giri sulla catena modelli in overload (503)
GEMINI_BACKOFF_BASE = float(os.environ.get("GEMINI_BACKOFF_BASE", "4.0"))  # secondi; attesa = base * 2**giro + jitter 0-1.5s
GEMINI_MAX_ATTEMPTS = 16     # tetto assoluto di chiamate API per singolo generate()

# Versione
VERSION = "2.4.21"
SHARED_VERSION = "2.4.21"   # aggiornare ad ogni modifica
SHARED_DATE    = "13/11/2026"  # aggiornare ad ogni modifica

logger.info(f"📦 C_shared100.py v{VERSION} ({SHARED_DATE}) caricato — MODEL={MODEL} fallback={MODEL_FALLBACKS}")

# ============================================================
# WHITELIST — SICUREZZA
# ============================================================

def _load_allowed() -> set[int]:
    """
    Carica la whitelist da env ALLOWED_USERS (CSV di user ID interi).
    Fallback hardcoded: solo Walter Caponi (273003890).
    """
    raw = os.environ.get("ALLOWED_USERS", "273003890")
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

_ALLOWED_USERS: set[int] = _load_allowed()

def is_allowed(uid: int) -> bool:
    """Ritorna True se l'utente è in whitelist. Loggare i tentativi non autorizzati nel bot."""
    return uid in _ALLOWED_USERS

# ============================================================
# VALERIA CROSS — DNA IDENTITÀ
# ============================================================

VALERIA_FACE = (
    "**⚠️ FACE IDENTITY LOCK — ABSOLUTE PRIORITY:** The attached reference photo shows the exact face "
    "to reproduce. The reference photo is authoritative for the face, eyeglasses and beard — if anything "
    "below conflicts with it, the photo wins.\n"
    "60-year-old Italian male face, oval-rectangular shape. "
    "Ultra-detailed mature skin with visible pores, deep character wrinkles, crow's feet. "
    "Calm half-smile, no teeth shown.\n"
    "**Eyeglasses:** Exactly as shown in the attached reference photo — same shape, color and frame "
    "thickness. Always present.\n"
    "**Hair:** Short silver-grey Italian cut, slightly voluminous top, nape exposed.\n"
    "**⚠️ BEARD — MANDATORY — NON-NEGOTIABLE:** Exactly as shown in the attached reference photo — same "
    "length, density, texture and shape, clearly visible in every shot. The beard is a permanent part of "
    "the identity lock, matching the reference image precisely.\n"
    "**Rendering:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200.\n\n"
)

# FACE TEXT MODE — introdotta in 2.4.18 (vedi changelog). Alternativa a
# VALERIA_FACE per quando in Flow NON si allega la foto reale del volto:
# descrive il volto per intero, senza rimandi a una foto allegata.
# Interamente in positivo (coerente con l'audit 2.4.0). Il default dei bot
# resta VALERIA_FACE (face_mode="photo"); questa si attiva solo su richiesta
# esplicita dell'utente (Atelier: /volto testo). HAIR e GLASSES sono costanti
# separate perché servono anche a review_and_fix() e ai blocchi HAIR LOCK /
# IDENTITY LOCK locali di Atelier — un'unica fonte, mai copiate a mano.
VALERIA_HAIR_TEXT = (
    "silver-grey hair swept back from the recessed hairline in a natural quiff, about 8\u201310 cm on top, "
    "sides combed back above the ears, reaching the nape and ending well above the collar, "
    "fine slightly wavy texture"
)
VALERIA_GLASSES_TEXT = (
    "glasses with a thick translucent deep-teal acetate frame in a rounded geometric shape, always worn"
)
VALERIA_FACE_TEXT = (
    "**\u26a0\ufe0f FACE IDENTITY \u2014 ABSOLUTE PRIORITY:** The face is described completely below and is "
    "reproduced exactly as written, identically in every image.\n"
    "Mature male face of about 60, oval with average fullness, a tall wide forehead with moderate horizontal "
    "lines, hairline receding at the temples. Warm dark-brown eyes with slightly hooded lids and light crow's "
    "feet; bushy, untamed silver-white eyebrows. Medium nose with a rounded tip, in proportion to the face. "
    "Ruddy, rosy complexion with light freckling, natural skin texture. "
    "Full, wide, bushy silver-white beard with a rounded lower edge sitting just below the chin, voluminous "
    "along the cheeks and jaw, loose curling strands, a darker steel-grey patch at the centre of the chin, "
    "thick darker-grey moustache over the upper lip. "
    + VALERIA_HAIR_TEXT[:1].upper() + VALERIA_HAIR_TEXT[1:] + ". "
    + VALERIA_GLASSES_TEXT[:1].upper() + VALERIA_GLASSES_TEXT[1:] + ". "
    "Soft expression lines around the eyes and mouth.\n"
    "**Rendering:** Subsurface Scattering, Global Illumination, Ambient Occlusion, Fresnel Effect. "
    "8K, cinematic, 85mm, f/2.8, ISO 200.\n\n"
)

VALERIA_BODY_STRONG = (
    "**MANDATORY BODY — FEMININE SILHOUETTE, HELD EXACTLY AS DESCRIBED:**\n"
    "**Feminine hourglass proportions, 180cm, 75kg. FULL D-CUP BUST — prominent, natural, clearly visible. "
    "Wide rounded hips, defined waist, full thighs.**\n"
    "Completely smooth, hairless skin on the torso, arms and legs. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE — CRITICAL:** The silver-grey beard on the face and the feminine body coexist "
    "together in the same image, exactly as described — the beard stays exactly as specified above, "
    "the body stays exactly as specified here, both simultaneously, unchanged.\n"
    "**⚠️ BUST VOLUME — ALWAYS VISIBLE:** The full D-cup bust stays fully three-dimensional, rounded and "
    "clearly visible in every image, under any clothing, framing or pose — never flattened, minimized or "
    "omitted, identically whether the skin is bare or covered.\n\n"
)

VALERIA_BODY_SAFE = (
    "**MANDATORY BODY — FEMININE SILHOUETTE, HELD EXACTLY AS DESCRIBED:**\n"
    "**Feminine hourglass silhouette, 180cm, 75kg. Soft feminine proportions — defined waist, "
    "wide rounded hips, full figure.**\n"
    "Completely smooth, hairless skin on the torso, arms and legs. "
    "Smooth porcelain skin. PHOTOGRAPHIC UNITY: skin tone, warmth and texture perfectly continuous "
    "from face → neck → shoulders → chest → arms.\n"
    "**⚠️ COEXISTENCE — CRITICAL:** The silver-grey beard on the face and the feminine body coexist "
    "together in the same image, exactly as described — the beard stays exactly as specified above, "
    "the body stays exactly as specified here, both simultaneously, unchanged.\n"
    "**⚠️ SILHOUETTE — ALWAYS VISIBLE:** The soft feminine chest and waist silhouette stays fully "
    "visible in every image, under any clothing, framing or pose — never flattened, minimized or "
    "omitted, identically whether the skin is bare or covered.\n\n"
)

VALERIA_WATERMARK = "feat. Valeria Cross 👠"

# BODY ART EXCEPTION — introdotta in 2.3.17, spostata fuori dai blocchi BODY
# statici in 2.3.18. Testo unico condiviso, usato in due modi diversi:
# 1) SEMPRE presente in Architect (che non ha un campo BODY ART esterno da
#    controllare — analisi e scrittura avvengono in un'unica chiamata Gemini,
#    senza produrre un testo intermedio ispezionabile). Architect importa
#    questa costante e la concatena direttamente dopo VALERIA_DNA.
# 2) CONDIZIONALMENTE presente in Vogue e Atelier tramite body_art_clause()
#    sotto — questi bot passano da analyze_scene(), che produce un vero
#    campo "BODY ART: ..." da poter ispezionare prima di decidere se la
#    clausola serve o è testo morto (caso comune: BODY ART: None).
BODY_ART_EXCEPTION_TEXT = (
    "**⚠️ BODY ART EXCEPTION — CONDITIONAL:** If the scene reference includes a BODY ART section describing "
    "tattoos, body paint or decorative skin markings, these OVERRIDE 'smooth porcelain skin' ONLY on the "
    "areas described — reproduce the pattern, colors and placement exactly as given. Skin NOT covered by "
    "described markings stays smooth and porcelain as specified above. If BODY ART states 'None' or is "
    "absent, skin remains fully smooth and unmarked everywhere — do NOT invent tattoos or markings that "
    "were not explicitly described.\n\n"
)

def body_art_clause(scene_description: str) -> str:
    """Restituisce BODY_ART_EXCEPTION_TEXT SOLO se scene_description contiene
    un campo BODY ART con contenuto reale (non 'None'/assente) — altrimenti
    stringa vuota, per non appesantire il prompt nel caso comune (nessun
    tatuaggio nella foto). Usare dopo l'identità (VALERIA_DNA o
    build_valeria_identity()) nei bot che passano da analyze_scene()
    (Vogue, Atelier). NON usare in Architect — vedi nota sopra."""
    if not scene_description:
        return ""
    scene_description = scene_description.replace("**", "")  # 2.4.19: tollera i nomi campo in grassetto
    m = re.search(r'BODY ART:\s*(.+?)(?:\n\n|\Z)', scene_description, re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    val = m.group(1).strip().lstrip("*-\u2022\u00b7 \t").strip()  # 2.4.19: tollera anche gli elenchi puntati
    if not val or _BODY_ART_EMPTY_RE.match(val):
        return ""
    return BODY_ART_EXCEPTION_TEXT

# 2.4.20 \u2014 varianti con cui Gemini dice "nessun segno sulla pelle" oltre a "None."
# (es. "No visible tattoos.", "No body art.", "N/A", "Not visible", "Nothing").
_BODY_ART_EMPTY_RE = re.compile(
    r"^(none\b|no\b|n/?a\b|nothing\b|not\s+(visible|present|applicable)\b|absent\b)",
    re.IGNORECASE,
)
# 2.4.20 \u2014 varianti con cui Gemini descrive UNA sola persona oltre a "One figure."
# (es. "Single figure.", "Only one person.", "Exactly one figure.", "1 figure", "A single woman").
_ONE_FIGURE_RE = re.compile(
    r"^((there\s+is\s+)?(exactly|only|just)\s+)?(one|1|a\s+single|single|a\s+lone|lone|solo|no|none|zero)\b",
    re.IGNORECASE,
)

# MULTI-SUBJECT LOCK — introdotta in 2.4.9, rafforzata in 2.4.10 dopo test
# reali di Walter: Vogue e Atelier in modalità singola hanno funzionato bene
# (identità Valeria su entrambe le figure), il MOSAICO Atelier no — la
# figura secondaria ha mantenuto il volto reale della foto originale.
# Ipotesi: il wording precedente era un rimando indiretto ("sharing the
# identical face... described above"), una singola frase debole a
# confronto con FACE IDENTITY LOCK/IDENTITY LOCK/HAIR LOCK/BEARD MANDATORY
# che nel resto del prompt ribadiscono l'identità della figura principale
# più volte — sproporzionato contro il prior visivo forte della foto
# allegata per la figura secondaria. Riscritta per essere esplicita quanto
# gli altri LOCK: dice direttamente che la sostituzione è totale e vale per
# OGNI figura, non solo la principale — non un rimando implicito.
# Generica, non legata a una scena specifica: se la foto di riferimento
# mostra 2+ persone distinte (rilevato dal campo FIGURES di
# _ANALYZE_PROMPT), il prompt finale deve generare lo stesso numero di
# figure, tutte con l'identica identità Valeria — non persone diverse. Ogni
# figura mantiene il proprio outfit/accessori/body art come descritti
# separatamente per quella figura in OUTFIT/ACCESSORIES/BODY ART (vedi
# _ANALYZE_PROMPT — quelle sezioni ora si strutturano per figura quando
# FIGURES ne rileva 2+). Stesso pattern di body_art_clause(): nessun
# impatto sul caso comune (una sola figura), nessuna riga aggiunta al
# prompt in quel caso.
VALERIA_MULTI_SUBJECT_LOCK = (
    "**\u26a0\ufe0f MULTI-SUBJECT LOCK — ABSOLUTE PRIORITY:** If the FIGURES section above describes two or "
    "more distinct people, EVERY one of those figures — not just the primary one — is replaced by the "
    "exact same identity: the mature face with full beard, eyeglasses, and hairstyle described above, and "
    "the same body identity described above. This replacement is total and applies identically to each "
    "figure — none of the original people's faces, hair, or body types survive in the output, for any "
    "figure, including secondary or background figures. All figures are the same person, repeated — zero "
    "variation in identity between them. Each figure wears the outfit, accessories and body art "
    "individually described for them in the OUTFIT/ACCESSORIES/BODY ART sections above — do not mix "
    "garments between figures. Position, pose and physical interaction between the figures follow FIGURES "
    "exactly as described. If FIGURES describes only one person, this does not apply — render a single "
    "figure as normal.\n\n"
)

def has_multiple_figures(scene_description: str) -> bool:
    """Restituisce True se scene_description contiene un campo FIGURES che descrive 2+
    persone (non 'One figure.' o assente/vuoto) — False altrimenti. Introdotta in 2.4.11,
    estratta da multi_subject_clause() perché serve anche altrove (checklist mosaico
    Atelier "What stays identical") per evitare di duplicare la stessa regex in più punti —
    vedi lezione #21 HANDOFF."""
    if not scene_description:
        return False
    scene_description = scene_description.replace("**", "")  # 2.4.19: tollera i nomi campo in grassetto
    m = re.search(r'FIGURES:\s*(.+?)(?:\n\n|\Z)', scene_description, re.IGNORECASE | re.DOTALL)
    if not m:
        return False
    val = m.group(1).strip().lstrip("*-\u2022\u00b7 \t").strip()  # 2.4.19: tollera anche gli elenchi puntati
    return bool(val) and not _ONE_FIGURE_RE.match(val)

def multi_subject_clause(scene_description: str) -> str:
    """Restituisce VALERIA_MULTI_SUBJECT_LOCK SOLO se has_multiple_figures() è True —
    altrimenti stringa vuota, per non appesantire il prompt nel caso comune (una sola
    persona nella foto). Usare dopo l'identità (VALERIA_DNA o build_valeria_identity())
    nei bot che passano da analyze_scene() (Vogue, Atelier). NON usare in Architect — non
    inietta DNA."""
    if not has_multiple_figures(scene_description):
        return ""
    return VALERIA_MULTI_SUBJECT_LOCK

# TEXTURE & PATTERN FIDELITY LOCK — introdotta in 2.4.4. Generica, non legata
# a una scena/foto specifica: si applica a qualunque pattern, texture o
# superficie descritta (mosaico, tessuto, marmo, stampa, ecc.), su qualunque
# bot. Interamente in positivo — nessun "not/never" — coerente con l'audit
# negative-prompt di 2.4.0 (Flow/Gemini non considera i negative prompt in
# generazione). Va SEMPRE inserita sia in VALERIA_DNA (Vogue) sia dentro
# build_valeria_identity() (Atelier) — Atelier importa VALERIA_DNA ma non lo
# usa mai nel codice, quindi va aggiunta esplicitamente in entrambi i punti.
VALERIA_TEXTURE_LOCK = (
    "**⚠️ TEXTURE & PATTERN FIDELITY LOCK — ABSOLUTE PRIORITY:** Any pattern, texture, print, weave, "
    "marbling or faceted surface described in the scene reference must be reproduced at fine, "
    "small-scale granularity — dozens to hundreds of individual small units (tiles, facets, threads, "
    "scales) visible across any single limb, panel or surface, matching the density and fragmentation "
    "shown in the reference photograph. Each unit follows the contours of the body or object "
    "continuously, exactly as a real photographed material would.\n\n"
)

# DNA completo assemblato — usato da Vogue. NOTA 2.4.0: Architect non lo
# usa più dalla riscrittura v3.0.0 (10/07) — nessun DNA, analisi pura del
# soggetto reale. Il commento precedente ("usato da Vogue e Architect") era
# rimasto stale da prima di quella riscrittura, corretto qui. NOTA 2.3.18:
# non include più BODY_ART_EXCEPTION_TEXT (era qui via VALERIA_BODY_STRONG
# fino alla 2.3.17). Vogue aggiunge body_art_clause(scene_description) dopo
# questa costante. NOTA 2.4.0: rimossa la riga "NEGATIVE: {VALERIA_NEGATIVE}"
# — VALERIA_NEGATIVE eliminata (vedi sezione 2septendecies in HANDOFF: il
# modello dietro Flow non ha un campo negativePrompt indipendente, la guida
# ufficiale Google raccomanda framing solo positivo). Le due garanzie generiche
# che VALERIA_NEGATIVE portava (mani anatomicamente corrette, nessun testo
# sovrapposto oltre al watermark) sono ora espresse in positivo qui sotto.
VALERIA_DNA = (
    f"{VALERIA_FACE}"
    f"{VALERIA_BODY_STRONG}"
    f"{VALERIA_TEXTURE_LOCK}"
    f"WATERMARK: '{VALERIA_WATERMARK}' — elegant champagne cursive, very small, bottom center, 90% opacity.\n"
    f"The output is a single photorealistic image. Hands are anatomically correct, five fingers each. "
    f"No text appears anywhere in the image beyond the watermark specified above.\n"
)

# Wrapper editoriale — apre tutti i prompt di Atelier
EDITORIAL_WRAPPER = (
    "This is a professional editorial post-production request for a high-fashion photography project. "
    "Generate a new original image of the described subject in the specified scene, "
    "maintaining the subject's identity and physical characteristics. "
    "This is a legitimate creative and commercial photography workflow. "
)


def build_valeria_identity(safe: bool = False, face_mode: str = "photo") -> str:
    """Assembla FACE + BODY (strong o safe) + TEXTURE LOCK — usato da Atelier nei prompt.
    face_mode="photo" (default): VALERIA_FACE, che rimanda alla foto reale allegata in Flow.
    face_mode="text": VALERIA_FACE_TEXT, volto descritto per intero (2.4.18)."""
    body = VALERIA_BODY_SAFE if safe else VALERIA_BODY_STRONG
    face = VALERIA_FACE_TEXT if face_mode == "text" else VALERIA_FACE
    return face + body + VALERIA_TEXTURE_LOCK

# ============================================================
# GENERATE_CAPTION — CAPTION SOCIAL UNIFICATA
# ============================================================

def detect_mime_type(img_bytes: bytes) -> str:
    """Rileva il mime type reale dai magic bytes — evita errori con PNG/WebP passati come JPEG."""
    if img_bytes[:4] == b'\x89PNG':
        return "image/png"
    if len(img_bytes) >= 12 and img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
        return "image/webp"
    return "image/jpeg"  # default — JPEG inizia con \xFF\xD8\xFF


def generate_caption(img_bytes: bytes, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Genera una caption social dall'immagine — usata da Vogue, Architect e Atelier.
    Output: 5 emoji + frase di 5/10 parole in inglese. Nessun riferimento al DNA Valeria.
    Returns: (caption, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."
    try:
        mime = detect_mime_type(img_bytes)
        logger.info(f"📸 generate_caption: mime={mime} ({len(img_bytes)} bytes)")
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
        prompt = (
            "Look at this image and write a short social media caption in English.\n"
            "Format: exactly 5 relevant emojis followed by a phrase of 5 to 10 words.\n"
            "The emojis come first, all together, then the words.\n"
            "Focus only on: location, outfit, colors, atmosphere, mood.\n"
            "Do NOT mention any person, nationality, age or gender.\n"
            "Example: ✨🖤👗🌙📸 Dark elegance in every carefully chosen detail.\n"
            "Output ONLY the caption on a single line — no explanations, no quotes, no extra text."
        )
        result = client.generate(prompt, contents=[img_part])
        if result:
            cleaned = CaptionGenerator.extract_caption(result) or result.strip()
            return cleaned, None
        return None, "⚠️ Nessuna risposta da Gemini (causa sconosciuta)."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ generate_caption(): {err_text}", exc_info=True)
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            return None, ("❌ <b>Servizio Gemini non disponibile.</b> Sovraccarico temporaneo. Riprova tra qualche minuto." if "503" in err_text or "unavailable" in err_text.lower() else "❌ <b>Quota API esaurita.</b> Reset alle 08:00 ora Lisbona.")
        elif "SAFETY" in err_text:
            return None, "❌ <b>Safety block di Gemini.</b> Prova con un'immagine diversa."
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            return None, "❌ <b>Timeout Gemini.</b> Riprova tra qualche secondo."
        else:
            return None, f"❌ <b>Errore caption:</b>\n<code>{html.escape(err_text)}</code>"


def generate_mini_caption(text: str, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Genera una mini caption social da un testo (prompt Flow, descrizione scena, scenario).
    Output: 5 emoji + frase di 5/10 parole in inglese. No gender, no DNA Valeria.
    Usata da Vogue, Architect, Atelier come caption alternativa testuale al prompt Flow.
    Returns: (caption, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."
    try:
        prompt = (
            "Read the following image generation prompt and extract its visual essence.\n"
            "Write a short social media caption in English.\n"
            "Format: exactly 5 relevant emojis followed by a phrase of 5 to 10 words.\n"
            "The emojis come first, all together, then the words.\n"
            "Focus only on: location, outfit, colors, atmosphere, mood, artistic style.\n"
            "Do NOT mention any person, name, nationality, age or gender.\n"
            "Do NOT reference the fact that this is an AI prompt.\n"
            "Example: ✨🖤👗🌙📸 Dark elegance in every carefully chosen detail.\n"
            "Output ONLY the caption on a single line — no explanations, no quotes.\n\n"
            f"PROMPT:\n{text[:2000]}"
        )
        logger.info("📝 generate_mini_caption: chiamata API testo")
        result = client.generate(prompt)
        if result:
            cleaned = CaptionGenerator.extract_caption(result) or result.strip()
            return cleaned, None
        return None, "⚠️ Nessuna risposta da Gemini."
    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ generate_mini_caption(): {err_text}", exc_info=True)
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            return None, ("❌ <b>Servizio Gemini non disponibile.</b> Sovraccarico temporaneo. Riprova tra qualche minuto." if "503" in err_text or "unavailable" in err_text.lower() else "❌ <b>Quota API esaurita.</b> Reset alle 08:00 ora Lisbona.")
        elif "SAFETY" in err_text:
            return None, "❌ <b>Safety block di Gemini.</b> Riprova."
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            return None, "❌ <b>Timeout Gemini.</b> Riprova tra qualche secondo."
        else:
            return None, f"❌ <b>Errore mini caption:</b>\n<code>{html.escape(err_text)}</code>"


def generate_mini_prompt(text: str, client=None) -> tuple:
    """
    Estrae dal prompt Flow un mini-prompt strutturato — stesso schema di Nosurprise format_scenario.
    Parser locale: zero chiamate Gemini. Estrae sezioni dal testo del prompt.
    Returns: (mini_prompt, error)
    """
    import re as _re

    def _extract(patterns, default='[not specified]'):
        for pattern in patterns:
            m = _re.search(pattern, text, _re.IGNORECASE)
            if m:
                val = m.group(1).strip().strip('.-–—*')
                if len(val) > 4:
                    return val[:120]
        return default

    try:
        location = _extract([
            r'(?:Scene|Location|Setting|Environment)[:\s—-]+([^\n]{10,})',
            r'(?:LOCATION|SCENE)[:\s—-]+([^\n]{10,})',
        ])
        if len(location) > 80:
            location = location.split(',')[0].strip()[:80]

        sky = _extract([
            r'(?:Lighting(?:\s+and\s+camera)?|Sky|Light(?:ing)?|Time of day)[:\s—-]+([^\n]{5,})',
            r'(?:LIGHTING|SKY)[:\s—-]+([^\n]{5,})',
        ])

        outfit = _extract([
            r'(?:Outfit|Clothing|Garments?)[:\s—-]+([^\n]{10,})',
            r'(?:OUTFIT)[:\s—-]+([^\n]{10,})',
            r'(?:wearing|dressed in)\s+([^\n]{10,})',
        ])

        style = _extract([
            r'(?:Style|Photographic style|Rendering)[:\s—-]+([^\n]{5,})',
            r'(?:STYLE|RENDERING)[:\s—-]+([^\n]{5,})',
            r'((?:cinematic|editorial|fashion|documentary|portrait)\s+[^\n]{5,})',
        ])

        pose = _extract([
            r'(?:Pose|Position|Framing|Camera angle)[:\s—-]+([^\n]{5,})',
            r'(?:POSE|COMPOSITION)[:\s—-]+([^\n]{5,})',
        ])

        mood = _extract([
            r'(?:Mood|Atmosphere|Emotional\s+tone)[:\s—-]+([^\n]{5,})',
            r'(?:MOOD|ATMOSPHERE)[:\s—-]+([^\n]{5,})',
        ])

        body = _extract([
            r'(?:Subject\s+body|Body|Physical\s+description)[:\s—-]+([^\n]{5,})',
            r'(?:BODY|SUBJECT BODY)[:\s—-]+([^\n]{5,})',
        ])

        result = (
            f"📍 <b>Location:</b> {location}\n"
            f"🌤 <b>Sky:</b> {sky}\n"
            f"👗 <b>Outfit:</b> {outfit}\n"
            f"🎨 <b>Style:</b> {style}\n"
            f"💃 <b>Pose:</b> {pose}\n"
            f"✨ <b>Mood:</b> {mood}\n"
            f"🏛 <b>Body:</b> {body}"
        )
        return result, None

    except Exception as e:
        return None, f"❌ <b>Errore mini prompt:</b> <code>{html.escape(str(e))}</code>"


_REVIEW_MIN_RATIO = 0.6
_REVIEW_END_CHARS = '.!?)"\'\u201d\u00bb*`'
_REVIEW_REQUIRED = (
    ("COLOR LOCK", r"COLOR LOCK"),
    ("OUTFIT DETAIL LOCK", r"OUTFIT DETAIL LOCK"),
    ("TEXTURE & PATTERN", r"TEXTURE & PATTERN"),
    ("COEXISTENCE", r"COEXISTENCE"),
    ("BUST VOLUME", r"BUST VOLUME"),
    ("IDENTITY LOCK locale", r"(?<!FACE )IDENTITY LOCK"),
    ("HAIR LOCK", r"HAIR LOCK"),
    ("BACKGROUND LOCK", r"BACKGROUND LOCK"),
    ("Pose options", r"Pose options"),
    ("Framing options", r"Framing options"),
    ("MULTI-SUBJECT LOCK", r"MULTI-SUBJECT LOCK"),            # 2.4.21
    ("Reference image analysis", r"Reference image analysis"),  # 2.4.21
    ("Technical", r"Technical:"),                             # 2.4.21
)
# 2.4.21 — un preambolo tipo "Here is the corrected prompt:" e le intestazioni che finiscono
# con ":" o ":**" (troncamento subito dopo il titolo di un blocco) non sono revisioni valide.
_REVIEW_PREAMBLE = re.compile(
    r"^\W*(here(?:'s| is| are)\b|sure\b|certainly\b|of course\b|below is\b|"
    r"the (?:corrected|revised)\b|corrected prompt\b|revised prompt\b|ecco\b)", re.I)
_REVIEW_HEADING_END = re.compile(r":\**\s*$")
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")


def _review_result_problem(original: str, reviewed: str):
    """2.4.19 — controlla che la revisione di Gemini sia utilizzabile. Ritorna None se ok,
    altrimenti una stringa col motivo. Vale solo per i blocchi presenti nell'originale:
    un bot il cui prompt non li contiene non viene toccato. In caso di problema
    review_and_fix() usa il prompt originale costruito dal codice."""
    o, r = original.rstrip(), (reviewed or "").rstrip()
    if not r:
        return "risposta vuota"
    if len(r) < _REVIEW_MIN_RATIO * len(o):
        return f"accorciata troppo ({len(r)} contro {len(o)} caratteri)"
    if o and o[-1] in _REVIEW_END_CHARS and r[-1] not in _REVIEW_END_CHARS:
        return f"finisce a meta' frase (...{r[-40:]!r})"
    missing = [name for name, pat in _REVIEW_REQUIRED
               if re.search(pat, o) and not re.search(pat, r)]
    if missing:
        return "blocchi mancanti: " + ", ".join(missing)
    # 2.4.21 — i codici colore HEX dell'originale devono esserci ancora tutti
    lost = sorted({h.upper() for h in _HEX_RE.findall(o)} - {h.upper() for h in _HEX_RE.findall(r)})
    if lost:
        return "codici colore persi: " + ", ".join(lost[:4]) + ("..." if len(lost) > 4 else "")
    if "```" in r and "```" not in o:
        return "avvolta in un blocco di codice"
    if _REVIEW_PREAMBLE.match(r) and not _REVIEW_PREAMBLE.match(o):
        return f"inizia con un preambolo ({r[:40]!r})"
    _o_last = o.splitlines()[-1] if o else ""
    if _REVIEW_HEADING_END.search(r.splitlines()[-1]) and not _REVIEW_HEADING_END.search(_o_last):
        return f"finisce su un'intestazione (...{r[-40:]!r})"
    # se l'originale chiude con la riga "**Technical:** ...", la revisione deve chiudere allo stesso
    # modo (in alcuni filtri "Technical:" compare anche prima, nel testo della scena)
    if re.match(r"\W*Technical:", _o_last) and "Technical:" not in r.splitlines()[-1]:
        return f"manca la riga finale Technical (...{r[-40:]!r})"
    return None


def _review_rules(face_mode: str = "photo"):
    """Regole 1 (capelli), 2 (occhiali) e 4 (subject bleed) di review_and_fix().
    face_mode="photo": testo identico alla 2.4.17. face_mode="text" (2.4.18): usano
    VALERIA_HAIR_TEXT / VALERIA_GLASSES_TEXT, senza rimandi a una foto allegata."""
    if face_mode == "text":
        r1 = (
            f"1. HAIR: Valeria Cross has {VALERIA_HAIR_TEXT}. "
            "Remove or replace ANY mention of: long hair, brown hair, dark hair, black hair, curly hair, "
            "flowing hair, loose waves, wet long hair, hair falling on shoulders, "
            "hair spread around head, hair fanned out, dark flowing locks, wavy dark hair, hair against background. "
            f"Replace with: {VALERIA_HAIR_TEXT}.\n\n"
        )
        r2 = (
            f"2. GLASSES MANDATORY: Valeria Cross ALWAYS wears {VALERIA_GLASSES_TEXT}. "
            "If the prompt does NOT mention glasses or eyeglasses, ADD this phrase in the "
            f"Facial identity section: '{VALERIA_GLASSES_TEXT}'. "
            "Also ensure 'no glasses' does NOT appear anywhere in the prompt.\n\n"
        )
        r4 = (
            "4. SUBJECT BLEED: Remove any physical description belonging to the original reference subject. "
            "Valeria Cross DNA: Male face 60yo, full silver-white beard, "
            f"{VALERIA_GLASSES_TEXT}, {VALERIA_HAIR_TEXT}, hourglass body, smooth skin.\n\n"
        )
    elif face_mode == "described":
        # 2.4.20 — per prompt il cui volto è GIÀ descritto per intero nel blocco di
        # identità (es. Vogue video). Nessun rimando a foto allegate e nessun testo di
        # DNA imposto qui: Gemini mantiene quello che il prompt stesso dice.
        r1 = (
            "1. HAIR: Keep the hairstyle exactly as described in the face identity section at the top "
            "of the prompt. Remove or replace ANY other hair description that conflicts with it "
            "(for example hair coming from the scene reference). Do not add a different hairstyle.\n\n"
        )
        r2 = (
            "2. GLASSES MANDATORY: The subject ALWAYS wears the eyeglasses described in the face identity "
            "section. Keep that description exactly as written. Ensure 'no glasses' does NOT appear "
            "anywhere in the prompt. Do NOT add any reference to an attached or reference photo.\n\n"
        )
        r4 = (
            "4. SUBJECT BLEED: Remove any physical description belonging to the original reference subject "
            "(face, hair, beard, body type) that contradicts the identity and body described at the top of "
            "the prompt. The identity sections at the top stay exactly as written.\n\n"
        )
    else:
        r1 = (
            "1. HAIR: Valeria Cross has SHORT silver/grey hair (sides 1-2cm, top max 15cm, nape exposed). "
            "Remove or replace ANY mention of: long hair, brown hair, dark hair, black hair, curly hair, "
            "flowing hair, loose waves, slicked back long hair, wet long hair, hair falling on shoulders, "
            "hair spread around head, hair fanned out, dark flowing locks, wavy dark hair, hair against background. "
            "Replace with: short silver Italian cut, slightly voluminous top, nape exposed.\n\n"
        )
        r2 = (
            "2. GLASSES MANDATORY: Valeria Cross ALWAYS wears eyeglasses, exactly as shown in the attached "
            "reference photo. If the prompt does NOT mention glasses or eyeglasses, ADD this phrase in the "
            "Facial identity section: 'eyeglasses exactly as shown in the attached reference photo "
            "(MANDATORY, always present)'. Also ensure 'no glasses' does NOT appear anywhere in the prompt.\n\n"
        )
        r4 = (
            "4. SUBJECT BLEED: Remove any physical description belonging to the original reference subject. "
            "Valeria Cross DNA: Male Italian face 60yo, beard and eyeglasses exactly as shown in the attached "
            "reference photo, silver short hair, hourglass body, smooth skin.\n\n"
        )
    return r1, r2, r4


def review_and_fix(prompt: str, client: 'GeminiClient', face_mode: str = "photo") -> str:
    """
    Revisione e correzione contraddizioni nel prompt generato.
    Corregge capelli, occhiali, body hair, watermark, subject bleed.
    In caso di errore ritorna il prompt originale invariato.
    face_mode="photo" (default, comportamento storico) o "text" (2.4.18: le regole
    1/2/4 usano il volto descritto a parole invece del rimando alla foto allegata)
    o "described" (2.4.20: le regole 1/2/4 rimandano all'identità già scritta nel
    prompt, senza imporre un testo di DNA — usato da Vogue per il prompt video).
    """
    try:
        _r1, _r2, _r4 = _review_rules(face_mode)
        review_instr = (
            "You are a prompt quality reviewer. Carefully read the following image generation prompt "
            "and fix ALL contradictions, inconsistencies and conflicts. Return ONLY the corrected prompt, "
            "no explanations, no preamble.\n\n"
            "MANDATORY FIXES — apply all of these:\n\n"
            + _r1 + _r2 +
            "2b. GLASSES POSE REMOVAL: Remove ANY description of hands or fingers touching, adjusting, holding or "
            "raising to the glasses or temple area. The glasses are simply worn — no hand interaction with them.\n\n"
            "3. MIRROR SELFIE RULE: ONLY if the prompt explicitly contains 'mirror selfie' or both 'selfie' AND 'mirror' together — "
            "then smartphone held in hand IS a required prop. "
            "Do NOT add smartphone for decorative mirrors, antique mirrors, historical scenes, artistic reflections, "
            "or any mirror that is not a selfie context.\n\n"
            + _r4 +
            "5. WATERMARK TEXT: Must read exactly: 'feat. Valeria Cross 👠' "
            "in elegant champagne cursive, very small, bottom center, 90% opacity. "
            "Replace any other watermark text with the exact text above.\n\n"
            "6. NAME REMOVAL: Remove any occurrence of 'Valeria Cross' or 'DNA of Valeria Cross' from the prompt body, "
            "EXCEPT inside the watermark text of rule 5, which stays exactly 'feat. Valeria Cross 👠'.\n\n"
            "7. KEEP INTACT: scene, outfit, lighting, environment, pose, mood, camera settings, "
            "photographic style, watermark spec, all creative elements not related to the subject's identity.\n\n"
            "8. BODY STATEMENT: Ensure the Subject body section explicitly states, in positive terms: "
            "'completely smooth, hairless skin on the torso, arms and legs', "
            "'soft feminine hourglass silhouette'.\n\n"
            f"PROMPT TO REVIEW:\n\n{prompt}"
        )
        logger.info("🔍 review_and_fix: avviata")
        result = client.generate(review_instr, max_tokens=8192)
        if result:
            _problem = _review_result_problem(prompt, result)
            if _problem:
                logger.warning(f"⚠️ review_and_fix: risposta non utilizzabile ({_problem}) — uso prompt originale")
                return prompt
            logger.info(f"✅ review_and_fix: completata ({len(result)} chars)")
            return result
        logger.warning("⚠️ review_and_fix: risposta vuota — uso prompt originale")
        return prompt
    except Exception as e:
        logger.warning(f"⚠️ review_and_fix: fallita, uso prompt originale: {e}")
        return prompt


# ============================================================
# ANALYZE_SCENE — ANALISI IMMAGINE CENTRALIZZATA
# ============================================================

# Prompt unico — un solo tentativo, nessun retry
_ANALYZE_PROMPT = (
    "Analyze this image. "
    "Return a structured description with these exact sections:\n\n"
    "FIGURES: [How many distinct people are in the frame — exactly one, or two or more. "
    "If two or more: describe each one's individual pose, position in the frame (e.g. "
    "'left figure', 'kneeling figure in front', 'figure standing behind'), and how they "
    "physically interact with each other — literal and specific, the same way PROPS & "
    "ACTIONS is described below. Do not describe any physical identity trait of the "
    "people themselves (no face, gender, hair, body-type details) — only count, position "
    "and physical interaction. Give each figure a short consistent label (e.g. 'left "
    "figure', 'right figure', 'kneeling figure') to be reused in OUTFIT/ACCESSORIES/BODY "
    "ART below. If only one person is present, write 'One figure.']\n\n"
    "OUTFIT: [Every garment as a standalone object — exact name, color with HEX code, fabric, "
    "cut, fit, coverage, embellishments, details. "
    "Describe the garment as if it exists independently — no wearer mentioned.]\n\n"
    "ACCESSORIES: [Every accessory as a standalone object — jewelry, footwear, headwear, bags, "
    "with color+HEX.]\n\n"
    "PROPS & ACTIONS: [Physical objects interacting directly with the subject's body — "
    "exact position, contact point, and action being performed. "
    "Be specific and literal: describe where the object is, how it contacts the body, and what is happening. "
    "Examples: 'single clear ice cube held between lips, partially inserted in mouth', "
    "'four translucent ice cubes stacked vertically on upper chest between collarbones, "
    "melting water running in rivulets down torso', "
    "'liquid dripping from chin onto chest'. "
    "If no props interact with the body: 'None.']\n\n"
    "BODY ART: [Any tattoos, henna, body paint, or decorative markings directly on the skin — "
    "pattern style, color(s) with HEX, exact placement and coverage area on the body (e.g. 'left forearm', "
    "'neck and collarbone', 'covering both shoulders and upper back'), line density and level of detail. "
    "Describe it as a standalone visual design, independent of the wearer. "
    "If no markings are present on the skin: 'None.']\n\n"
    "COLOR PALETTE: [Dominant HEX codes with label.]\n\n"
    "BACKGROUND: [Every distinct background element as a standalone object — furniture, wall decor, "
    "hanging or suspended objects, shelved or displayed items, architectural features, natural elements "
    "(plants, foliage, terrain, animals) — with approximate count or density where multiple similar "
    "elements repeat, for man-made scenes (e.g. 'approximately a dozen vintage clocks of varying sizes, "
    "mounted on the wall and suspended from the ceiling on cords') as well as organic/natural scenes "
    "(e.g. 'dense fern undergrowth filling the foreground, a dozen orchid clusters scattered through the "
    "mid-ground, three birds perched at different heights and depths'), color with HEX where relevant, "
    "and spatial layering (foreground/midground/background). Do not summarize repeated elements into a "
    "single category — enumerate their approximate quantity and variety.]\n\n"
    "LIGHTING: [Light source, direction, quality, color temperature, mood — 1-2 sentences.]\n\n"
    "CAMERA: [Framing. Describe how the subjects/garments are positioned in frame.]\n\n"
    "MOOD: [Overall atmosphere, color grade, cinematic style — 1 sentence.]\n\n"
    "Rules:\n"
    "— Describe garments and accessories as standalone objects\n"
    "— Be precise and detailed on fabrics, colors and environment\n"
    "— For PROPS & ACTIONS: describe physical contact and actions literally, not metaphorically\n"
    "— For BODY ART: describe only markings actually visible on the skin — do not confuse with printed "
    "patterns on garments (those belong in OUTFIT)\n"
    "— If FIGURES describes two or more people: within OUTFIT, ACCESSORIES and BODY ART, describe each "
    "figure's garments/accessories/markings SEPARATELY, labeled with the same short label used in FIGURES "
    "(e.g. 'Left figure: ... Right figure: ...') — never merge different figures' garments into one "
    "generic description. If FIGURES says 'One figure', describe these sections exactly as before, with "
    "no figure labeling."
)


def analyze_scene(img_bytes: bytes, client: 'GeminiClient') -> tuple[str | None, str | None]:
    """
    Analisi immagine centralizzata — singolo tentativo, nessun retry.
    Returns: (result, error)
    """
    if not client.available:
        return None, "⚠️ API key non configurata."

    try:
        mime = detect_mime_type(img_bytes)
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
        logger.info(f"🔍 analyze_scene: mime={mime} ({len(img_bytes)} bytes)")
        result = client.generate(_ANALYZE_PROMPT, contents=[img_part], max_tokens=8192)
        if result:
            logger.info(f"✅ analyze_scene: completato ({len(result)} chars)")
            return result, None
        # Non dovrebbe mai arrivare qui — generate() ora rilancia invece di ritornare None
        return None, "⚠️ Nessuna risposta da Gemini (causa sconosciuta)."

    except Exception as e:
        err_text = str(e)
        logger.error(f"❌ analyze_scene: {err_text}")
        # Classifica l'errore per un messaggio utente chiaro
        if "429" in err_text or "503" in err_text or "quota" in err_text.lower() or "exhausted" in err_text.lower() or "unavailable" in err_text.lower():
            if "503" in err_text or "unavailable" in err_text.lower():
                friendly = (
                    "❌ <b>Servizio Gemini non disponibile.</b>\n"
                    "Sovraccarico temporaneo. Riprova tra qualche minuto."
                )
            else:
                friendly = (
                    "❌ <b>Quota API esaurita.</b>\n"
                    "Quota giornaliera finita su tutte le chiavi disponibili.\n"
                    "Reset alle 08:00 ora Lisbona."
                )
        elif "SAFETY" in err_text or "SAFETY BLOCK" in err_text or "PROHIBITED_CONTENT" in err_text or "sconosciuto" in err_text:
            friendly = (
                "⚠️ <b>Immagine bloccata dai filtri Gemini.</b>\n"
                "Gemini rifiuta questa foto (contenuto sensibile).\n"
                "Prova con un'immagine diversa."
            )
        elif "API key" in err_text or "API_KEY" in err_text or "credentials" in err_text.lower():
            friendly = (
                "❌ <b>Errore chiave API.</b>\n"
                "La chiave Google non è valida o non è configurata correttamente."
            )
        elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
            friendly = (
                "❌ <b>Timeout Gemini.</b>\n"
                "La risposta ha impiegato troppo tempo. Riprova tra qualche secondo."
            )
        else:
            friendly = f"❌ <b>Errore API Gemini:</b>\n<code>{html.escape(err_text)}</code>"
        return None, friendly


def _classify_gemini_error(err_text: str):
    """Classifica un errore Gemini dal suo testo (FIX 2.4.15, stessi criteri di prima).
    Ritorna "overload" (503/unavailable/overloaded), "quota" (429/quota/exhausted),
    "transient" (timeout/connessione) oppure None se non transitorio."""
    low = err_text.lower()
    # 2.4.21 — richiesta sbagliata: mai transitoria (anche se il testo contiene un numero tipo 503)
    if "INVALID_ARGUMENT" in err_text or re.match(r"\s*400\b", err_text):
        return None
    def _has(code):   # il codice come numero a sé stante, non come parte di un numero più lungo
        return re.search(r"(?<!\d)" + code + r"(?!\d)", err_text) is not None
    if _has("503") or "unavailable" in low or "overloaded" in low:
        return "overload"
    if _has("429") or "quota" in low or "exhausted" in low:
        return "quota"
    if (_has("500") or _has("502") or _has("504")
            or re.search(r"\b(INTERNAL|DEADLINE_EXCEEDED|BAD_GATEWAY)\b", err_text)
            or any(x in low for x in ("timeout", "timed out", "connection", "disconnected",
                                      "remote protocol", "reset by peer"))):
        return "transient"
    return None


# ============================================================
# GeminiClient
# ============================================================

class GeminiClient:
    """
    Wrapper Singleton attorno a genai.Client con rotation automatica multi-chiave.
    Legge GOOGLE_API_KEY, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, GOOGLE_API_KEY_4, GOOGLE_API_KEY_5 dall'environment.
    Su 429/quota esaurita ruota automaticamente alla chiave successiva.
    Su 503/overload ruota i MODELLI (MODEL_FALLBACKS), non le chiavi (2.4.15).
    """
    _instance = None
    _lock = threading.Lock()
    _state_lock = threading.RLock()   # 2.4.20 — rotazione chiave e contatori (più thread per bot)

    def __new__(cls, api_key: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, api_key: str = None):
        if self._initialized:
            return
        # Raccoglie tutte le chiavi disponibili
        keys = []
        for env_var in ["GOOGLE_API_KEY", "GOOGLE_API_KEY_2", "GOOGLE_API_KEY_3", "GOOGLE_API_KEY_4", "GOOGLE_API_KEY_5"]:
            k = os.environ.get(env_var)
            if k:
                keys.append(k)
        if api_key and api_key not in keys:
            keys.insert(0, api_key)

        self._keys = keys
        self._key_index = 0
        self._clients = [genai.Client(api_key=k) for k in keys] if keys else []
        self._client = self._clients[0] if self._clients else None
        self._rotation_callbacks = []
        self._key_use_callbacks = []        # callback ad ogni chiamata (chiave, count)
        self._call_counts = [0] * len(keys)  # contatore per chiave — si azzera al riavvio
        self._total_calls = 0               # contatore globale — tutte le chiavi sommate
        # last_fallback_code — introdotto in 2.4.12 su richiesta di Walter: quale errore
        # ha fatto scattare l'ultimo fallback su MODEL_LITE ("503", "429", "transient") o
        # None se nessun fallback è avvenuto. NON si azzera da solo dentro generate() —
        # accumula attraverso più chiamate generate() della stessa richiesta (es. analisi +
        # review_and_fix), altrimenti una seconda chiamata pulita cancellerebbe l'informazione
        # della prima. Il chiamante deve azzerarlo esplicitamente con reset_fallback() prima
        # di iniziare una nuova richiesta utente, stesso pattern di reset_counters().
        self.last_fallback_code: str | None = None

        if not self._clients:
            logger.warning("⚠️ GeminiClient: nessuna GOOGLE_API_KEY configurata.")
        else:
            logger.info(f"🔑 GeminiClient: {len(self._clients)} chiave/i disponibile/i")
        self._initialized = True
        if self._clients:
            self._schedule_daily_reset()

    def _rotate_key(self):
        """Ruota alla chiave successiva — chiamato su 429/quota."""
        if len(self._clients) <= 1:
            return False
        with self._state_lock:
            self._key_index = (self._key_index + 1) % len(self._clients)
            self._client = self._clients[self._key_index]
            new_num = self._key_index + 1
        logger.warning(f"🔄 GeminiClient: rotazione chiave → indice {new_num}/{len(self._clients)}")
        # Notifica tutti i callback registrati
        for cb in self._rotation_callbacks:
            try:
                cb(new_num)
            except Exception as cb_err:
                logger.warning(f"⚠️ on_key_rotation callback error: {cb_err}")
        return True

    @property
    def current_key_num(self) -> int:
        """Ritorna il numero (1-based) della chiave API attualmente in uso."""
        return self._key_index + 1

    def on_key_rotation(self, callback):
        """
        Registra una callback chiamata ogni volta che la chiave ruota.
        callback(new_key_num: int) — new_key_num è 1-based.
        Permette ai bot di notificare l'utente del cambio chiave.
        """
        self._rotation_callbacks.append(callback)

    def on_key_use(self, callback):
        """
        Registra una callback chiamata ad OGNI chiamata generate().
        callback(key_num: int, call_count: int) — key_num 1-based, call_count cumulativo per quella chiave.
        Utile per mostrare quale chiave è in uso e quante call ha fatto oggi.
        """
        self._key_use_callbacks.append(callback)

    def reset_counters(self):
        """Azzera tutti i contatori call — chiamare su /start e automaticamente alle 08:00 ora di Lisbona."""
        with self._state_lock:
            self._call_counts = [0] * len(self._clients)
            self._total_calls = 0
        logger.info("🔄 GeminiClient: contatori call azzerati")

    def reset_fallback(self):
        """Azzera last_fallback_code — chiamare all'inizio di ogni nuova richiesta utente
        (es. inizio _process() su una foto), prima delle chiamate generate() di quella
        richiesta, così last_fallback_code riflette solo i fallback di QUESTA richiesta."""
        self.last_fallback_code = None

    def _schedule_daily_reset(self):
        """Pianifica reset automatico ogni giorno alle 08:00 ora di Lisbona (Europe/Lisbon),
        cioè quando si azzera la quota Gemini (mezzanotte del Pacifico). FIX 2.4.20: prima
        era alle 07:00 UTC fisse, che in inverno sono le 07:00 di Lisbona — un'ora prima.
        Se il fuso Europe/Lisbon non è disponibile nel container si usa 07:00 UTC.
        FIX 2.3.12: datetime.utcnow() (deprecato, naive) sostituito con
        datetime.now(timezone.utc) (aware) — evita TypeError silenziosi futuri su
        confronti naive/aware. Il loop è inoltre avvolto in try/except: prima, una
        qualsiasi eccezione interna terminava il thread per sempre senza alcun log,
        e i contatori restavano bloccati fino al riavvio del servizio senza che
        nessuno se ne accorgesse.
        """
        import threading as _t
        import datetime as _dt

        try:
            from zoneinfo import ZoneInfo
            _tz, _hour, _label = ZoneInfo("Europe/Lisbon"), 8, "08:00 Lisbona"
        except Exception:
            _tz, _hour, _label = _dt.timezone.utc, 7, "07:00 UTC (fuso Lisbona non disponibile)"

        def _reset_loop():
            while True:
                try:
                    now = _dt.datetime.now(_tz)
                    next_reset = now.replace(hour=_hour, minute=0, second=0, microsecond=0)
                    if now >= next_reset:
                        next_reset = (next_reset + _dt.timedelta(days=1)).replace(hour=_hour)
                    # differenza calcolata in UTC: corretta anche nei giorni di cambio ora
                    wait_secs = (next_reset.astimezone(_dt.timezone.utc)
                                 - now.astimezone(_dt.timezone.utc)).total_seconds()
                    logger.info(f"⏰ Prossimo reset contatori in {int(wait_secs//3600)}h {int((wait_secs%3600)//60)}m ({_label})")
                    _t.Event().wait(timeout=wait_secs)
                    self.reset_counters()
                except Exception as e:
                    logger.error(f"❌ GeminiCounterReset: errore nel loop, ritento tra 60s: {e}", exc_info=True)
                    _t.Event().wait(timeout=60)

        t = _t.Thread(target=_reset_loop, daemon=True, name="GeminiCounterReset")
        t.start()

    @property
    def call_counts(self) -> list[int]:
        """Ritorna la lista dei contatori per chiave (0-based index)."""
        return list(self._call_counts)

    @property
    def available(self) -> bool:
        return bool(self._clients)

    @staticmethod
    def _empty_reason(response) -> str:
        """Motivo leggibile di una risposta senza testo (finish_reason / prompt_feedback).
        Estratto da generate() in 2.4.15 — logica invariata."""
        reason = "sconosciuto"
        try:
            candidate = response.candidates[0] if response.candidates else None
            if candidate:
                fr = str(candidate.finish_reason)
                if "SAFETY" in fr:
                    reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                elif "RECITATION" in fr:
                    reason = "RECITATION — Gemini ha bloccato per potenziale riproduzione di contenuto protetto"
                elif "MAX_TOKENS" in fr:
                    reason = "MAX_TOKENS — risposta troncata, output troppo lungo"
                elif "STOP" in fr:
                    reason = "STOP — risposta terminata normalmente ma testo vuoto"
                else:
                    reason = f"finish_reason: {fr}"
            else:
                # Nessun candidato — Gemini ha bloccato l'intera richiesta
                # Controlla prompt_feedback per il motivo
                try:
                    pf = str(response.prompt_feedback) if hasattr(response, "prompt_feedback") else ""
                    if "SAFETY" in pf or "BLOCK" in pf:
                        reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                    elif pf:
                        reason = f"prompt_feedback: {pf[:80]}"
                    else:
                        reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
                except Exception:
                    reason = "SAFETY BLOCK — immagine bloccata dai filtri di sicurezza Gemini"
        except Exception as fe:
            reason = f"impossibile leggere finish_reason: {fe}"
        return reason

    def _call_model(self, idx: int, model: str, payload, safety, max_tokens: int) -> str:
        """Singola chiamata a (chiave idx, modello). Ritorna il testo oppure solleva.
        Usa self._clients[idx] direttamente (non self._client) così una rotazione
        fatta da un altro thread a metà chiamata non cambia la chiave sotto i piedi."""
        response = self._clients[idx].models.generate_content(
            model=model,
            contents=payload,
            config=genai_types.GenerateContentConfig(
                safety_settings=safety,
                max_output_tokens=max_tokens,
            )
        )
        try:  # 2.4.19 — solo diagnostica: segnala risposte non concluse normalmente
            _cands = getattr(response, "candidates", None) or []
            _fr = getattr(_cands[0], "finish_reason", None) if _cands else None
            _fr_name = getattr(_fr, "name", str(_fr)) if _fr is not None else None
            if _fr_name and _fr_name not in ("STOP", "FINISH_REASON_UNSPECIFIED"):
                logger.warning(f"⚠️ GeminiClient: finish_reason={_fr_name} su {model} (chiave #{idx + 1}, "
                               f"max_tokens={max_tokens}) — la risposta può essere parziale")
        except Exception:
            pass
        if response.text:
            return response.text.strip()
        # Risposta vuota — estrai il motivo reale da finish_reason
        raise RuntimeError(f"Gemini ha risposto senza testo — {self._empty_reason(response)}")

    def generate(self, prompt: str, contents: list = None, model: str = MODEL, max_tokens: int = 3000) -> str | None:
        """
        Genera testo con Gemini.
        contents: lista di Part aggiuntivi (immagini, ecc.) — vengono messi PRIMA del testo.
        Ritorna il testo generato; su errore solleva l'ultima eccezione.

        FIX 1.2.0: quando contents non è vuoto (es. immagini), il prompt testuale
        viene wrappato come genai_types.Part per garantire compatibilità con l'API.
        Passare una stringa nuda in una lista mista Part+str causa il fallimento
        silenziosa dell'analisi immagine (Gemini ignora la parte visiva).
        FIX 1.6.0: safety_settings disabilitati — necessario per analisi outfit
        su immagini fashion che altrimenti vengono bloccate dai filtri Gemini.

        FIX 2.4.15 — strategia di retry riscritta (vedi changelog):
          - 503/overload (capacità del MODELLO, uguale per tutte le chiavi): si
            scorre la catena [model, *MODEL_FALLBACKS] sulla STESSA chiave, senza
            ruotare chiavi; se l'intera catena fallisce, backoff con jitter e
            un secondo giro (GEMINI_RETRY_PASSES).
          - 429/quota (per progetto+modello): la coppia (chiave, modello) è
            segnata esaurita per questa chiamata; si prova il modello successivo
            sulla stessa chiave e, se una qualunque coppia della chiave è in
            quota esaurita, si ruota alla chiave successiva.
          - Errori non transitori (SAFETY, parametri, ...): sollevati subito.
        """
        if not self._client:
            logger.error("❌ GeminiClient non disponibile.")
            return None
        # Round-robin: ruota la chiave PRIMA di ogni chiamata
        with self._state_lock:
            if len(self._clients) > 1:
                self._rotate_key()
            _cur_key = self._key_index + 1
            _cur_total = self._total_calls + 1   # la prima chiamata viene contata nel ciclo sotto
        # Notifica on_key_use callbacks — una sola volta per richiesta
        for _cb in self._key_use_callbacks:
            try:
                _cb(_cur_key, _cur_total)
            except Exception as _cb_err:
                logger.warning(f"\u26a0\ufe0f on_key_use callback error: {_cb_err}")

        if contents:
            text_part = genai_types.Part.from_text(text=prompt)
            payload = list(contents) + [text_part]
        else:
            payload = prompt
        safety = [
            genai_types.SafetySetting(
                category=genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
            ),
            genai_types.SafetySetting(
                category=genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
            ),
            genai_types.SafetySetting(
                category=genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
            ),
            genai_types.SafetySetting(
                category=genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=genai_types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

        chain = [model] + [m for m in MODEL_FALLBACKS if m != model]
        n_keys = len(self._clients)
        dead = set()            # coppie (indice chiave, modello) in quota esaurita, per QUESTA chiamata
        last_exc = None
        req_fail_code = None    # codice con cui è fallito il modello richiesto ("503"/"429"/"transient")
        attempts = 0

        for pass_no in range(GEMINI_RETRY_PASSES):
            saw_overload = False
            for key_step in range(n_keys):
                with self._state_lock:
                    idx = self._key_index
                for m in chain:
                    if (idx, m) in dead:
                        continue
                    if attempts >= GEMINI_MAX_ATTEMPTS:
                        break
                    attempts += 1
                    with self._state_lock:   # 2.4.20 — conta OGNI chiamata API reale, anche i retry
                        self._total_calls += 1
                        if idx < len(self._call_counts):
                            self._call_counts[idx] += 1
                    try:
                        text = self._call_model(idx, m, payload, safety, max_tokens)
                        if m != model:
                            # Fallback realmente usato: solo ora si imposta il codice
                            # mostrato all'utente (2.4.12), così non resta impostato
                            # se il modello richiesto riesce al giro successivo.
                            self.last_fallback_code = req_fail_code or "transient"
                            logger.info(f"✅ GeminiClient: risposta da fallback {m} (chiave #{idx + 1}, {req_fail_code or 'transient'} su {model})")
                        return text
                    except Exception as e:
                        err_text = str(e)
                        kind = _classify_gemini_error(err_text)
                        if kind is None:
                            # Errore non transitorio (SAFETY, parametro errato, ecc.) — stop
                            logger.error(f"❌ GeminiClient.generate() [{m}, chiave #{idx + 1}]: {e}", exc_info=True)
                            raise
                        last_exc = e
                        code = "503" if kind == "overload" else ("429" if kind == "quota" else "transient")
                        if m == model:
                            req_fail_code = code
                        if kind == "quota":
                            dead.add((idx, m))
                        else:
                            saw_overload = True
                        logger.warning(f"⚠️ GeminiClient: {code} su {m} (chiave #{idx + 1}, giro {pass_no + 1}/{GEMINI_RETRY_PASSES}): {err_text[:160]}")
                if attempts >= GEMINI_MAX_ATTEMPTS:
                    break
                # Fine catena sulla chiave corrente. Si ruota chiave SOLO se almeno
                # una coppia di questa chiave è in quota esaurita (429): su un
                # 503 un'altra chiave non cambia nulla, l'overload è del modello.
                if (any((idx, m) in dead for m in chain)
                        and key_step < n_keys - 1
                        and self._rotate_key()):
                    continue
                break
            if attempts >= GEMINI_MAX_ATTEMPTS or not saw_overload:
                # Solo quota esaurita ovunque (o budget tentativi finito): ripetere il giro non serve
                break
            if pass_no < GEMINI_RETRY_PASSES - 1:
                delay = GEMINI_BACKOFF_BASE * (2 ** pass_no) + random.uniform(0, 1.5)
                logger.info(f"⏳ GeminiClient: catena {chain} in overload, attendo {delay:.1f}s e ritento")
                time.sleep(delay)

        logger.error(f"❌ GeminiClient.generate(): catena {chain} esaurita dopo {attempts} tentativi")
        if last_exc is None:
            raise RuntimeError("GeminiClient.generate(): nessun tentativo eseguito")
        raise last_exc


# ============================================================
# CaptionGenerator
# ============================================================

class CaptionGenerator:
    """
    Genera caption social in stile Valeria Cross.
    Tre varianti di tono:
      - from_scenario()  → Surprise (scena da pool)
      - from_image()     → Vogue / Architect (foto originale)
      - from_filter()    → Filtro (effetto artistico applicato)
    """

    EXAMPLES = (
        "🩰🍷🕊️🎞️🌑 dramatic white layers against a deep burgundy backdrop\n"
        "🌊✨💎🎤🌃 shimmering turquoise beads under the stage lights\n"
        "🌸🪨🩰🕯️✨ delicate pink lace within ancient stone alcove\n"
        "💖🐱🤳✨ pretty in pink and feline fine"
    )

    RULES = (
        "Rules:\n"
        "- Start with 4 or 5 emoji that match the style, setting, mood, colors and fashion\n"
        "- Follow with a short evocative phrase of maximum 10 words\n"
        "- Focus ONLY on: location, outfit, colors, atmosphere, fashion, mood, artistic effect\n"
        "- Do NOT mention any person, nationality, ethnicity, age, gender or physical traits\n"
        "- No hashtags, no punctuation at the end\n"
        "- Return ONLY the caption on a single line, nothing else\n"
    )

    @staticmethod
    def extract_caption(text: str) -> str | None:
        """
        Estrae la caption finale dal testo di Gemini.
        Gemini a volte ragiona ad alta voce prima di rispondere —
        cerca l'ultima riga non vuota che inizia con uno o più emoji.
        Se non trovata, ritorna l'ultima riga non vuota.
        """
        import unicodedata
        def starts_with_emoji(line):
            return line and unicodedata.category(line[0]) in ('So', 'Sm') or (
                len(line) > 1 and ord(line[0]) > 0x1F000)
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        # Cerca l'ultima riga che inizia con emoji
        for line in reversed(lines):
            if starts_with_emoji(line):
                return line
        # Fallback: ultima riga non vuota
        return lines[-1] if lines else None

    def __init__(self, client: GeminiClient):
        self.client = client

    def from_scenario(self, scenario: dict) -> tuple[str | None, str | None]:
        """
        Caption da scenario Surprise (pool).
        scenario: dict con keys location, sky, outfit, style, pose, mood
        """
        context = (
            f"Location: {scenario.get('location', '')}\n"
            f"Sky/Lighting: {scenario.get('sky', '')}\n"
            f"Outfit: {scenario.get('outfit', '')}\n"
            f"Style: {scenario.get('style', '')}\n"
            f"Pose: {scenario.get('pose', '')}\n"
            f"Mood: {scenario.get('mood', '')}"
        )
        prompt = (
            f"Based on this fashion editorial scene, write a social media caption.\n\n"
            f"SCENE:\n{context}\n\n"
            f"{self.RULES}"
            f"Examples:\n{self.EXAMPLES}"
        )
        result = self.client.generate(prompt)
        if result:
            return self.extract_caption(result) or result, None
        return None, "⚠️ Caption non disponibile."

    def from_image(self, img_bytes: bytes) -> tuple[str | None, str | None]:
        """
        Caption da foto originale (Vogue / Architect).
        Legge soggetto, atmosfera e outfit dall'immagine.
        """
        if not self.client.available:
            return None, "⚠️ API non configurata."
        try:
            mime = detect_mime_type(img_bytes)
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
            prompt = (
                "Look at this fashion photo and write a social media caption.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return self.extract_caption(result) or result, None
            return None, "⚠️ Caption non disponibile."
        except Exception as e:
            logger.error(f"❌ CaptionGenerator.from_image(): {e}", exc_info=True)
            return None, f"❌ Errore: {html.escape(str(e))}"

    def from_filter(self, img_bytes: bytes, filter_label: str) -> tuple[str | None, str | None]:
        """
        Caption per Filtro — descrive l'effetto artistico applicato all'immagine.
        filter_label: es. "🌊 Dissolve" o "🌀 Dalì"
        """
        if not self.client.available:
            return None, "⚠️ API non configurata."
        try:
            mime = detect_mime_type(img_bytes)
            img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type=mime)
            prompt = (
                f"This image has been processed with the artistic filter: {filter_label}\n\n"
                f"Write a social media caption that evokes the artistic effect and atmosphere "
                f"of the filtered result — not the original photo.\n\n"
                f"{self.RULES}"
                f"Examples:\n{self.EXAMPLES}"
            )
            result = self.client.generate(prompt, contents=[img_part])
            if result:
                return self.extract_caption(result) or result, None
            return None, "⚠️ Caption non disponibile."
        except Exception as e:
            logger.error(f"❌ CaptionGenerator.from_filter(): {e}", exc_info=True)
            return None, f"❌ Errore: {html.escape(str(e))}"



# ============================================================
# HealthServer
# ============================================================

class HealthServer:
    """
    Flask health check server — porta 10000 (default Koyeb).
    Avvia in thread daemon, non blocca il bot.
    """

    def __init__(self, bot_name: str, version: str, port: int = 10000):
        self.bot_name = bot_name
        self.version  = version
        self.port     = port
        self.app      = flask.Flask(bot_name)

        @self.app.route('/')
        def health():
            return f"{self.bot_name} v{self.version} ok", 200

        @self.app.route('/health')
        def health_detail():
            return {"bot": self.bot_name, "version": self.version, "status": "ok"}, 200

    def start(self):
        """Avvia Flask in thread daemon."""
        t = threading.Thread(
            target=lambda: self.app.run(
                host='0.0.0.0',
                port=int(os.environ.get("PORT", self.port)),
                debug=False,
                use_reloader=False,   # evita fork bomb di Werkzeug in thread daemon
                threaded=True,        # gestisce richieste concurrent senza bloccare
            ),
            daemon=True
        )
        t.start()
        logger.info(f"🌐 HealthServer avviato su porta {self.port}")

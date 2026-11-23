# CLAUDE.md — Moltbot

Progetto di bot Telegram che generano prompt di fotografia editoriale di moda per il personaggio fittizio Valeria Cross, con il modello Nano Banana di Flow. Unico sviluppatore e unico operatore: Walter. Rispondi sempre in italiano.

## Come lavorare

- Non creare, modificare o generare nulla che non sia stato chiesto esplicitamente.
- Le modifiche si fanno direttamente su `main`, senza ramo separato né pull request (decisione di Walter, 13/11/2026). Ogni push su `main` può far partire da solo il deploy su Koyeb: ricordalo a Walter quando cambia un file di bot.
- Niente patch temporanee.
- A fine lavoro elenca i file modificati e, per ogni bot, la versione prima e dopo.

## Versioni

- Prima di cambiare qualsiasi `VERSION`, leggi il valore reale nel file con `grep "^VERSION"`. Non fidarti di README, HANDOFF o cronologia.
- Il nome del file corrisponde alla `VERSION` senza punti (esempio: 2.0.9 diventa `_209`).
- Prima di scrivere una data in changelog, stringhe di versione, nomi di file o intestazioni, controlla la data reale del giorno con il comando `date`. Non riusare mai una data di un passaggio precedente.
- Aggiorna README e HANDOFF a ogni modifica.
- Ogni bot ha un lanciatore fisso (`atelier.py`, `vogue.py`, `architect.py`, `filtro.py`, `surprise.py`) che avvia il file versionato indicato in `BOT_FILE`. A ogni nuova versione di un bot aggiorna `BOT_FILE` nel suo lanciatore. Ogni bot ha anche `VERSION_DATE` (gg/mm/aaaa, da `date`) accanto a `VERSION`: aggiornala a ogni nuova versione, il `/start` la mostra. Il modulo comune è `shared300.py`, sempre in-place con nome fisso. Il Run command su Koyeb è `python <bot>.py` e non cambia più.

## Regole sul codice

- Quando correggi i dati del volto o del DNA di Valeria, esegui `grep -rn` su tutto il progetto prima di considerare il lavoro finito. Le specifiche possono essere duplicate in `review_and_fix()` e nei blocchi locali `IDENTITY LOCK`.
- I conteggi dei pool (per esempio `LOCATION_POOL`) si verificano nel codice, non nelle etichette di un foglio Excel.
- Nano Banana non ha un campo `negativePrompt` indipendente: i prompt di tutti i bot sono scritti solo in positivo. Non reintrodurre negative prompt senza una richiesta esplicita.

## Segreti

- Mai token, chiavi API o credenziali nel codice, nei commit o nei messaggi. Vanno nelle variabili d'ambiente di Koyeb.
- Se trovi un segreto nel repository o nella cronologia, segnalalo subito senza copiarlo.
- Non leggere, non modificare e non aggiungere al repository i file Excel di tracciamento (`VERSIONI_BOT_*.xlsx`): contengono credenziali e li gestisce Walter.

# token diet
most of my usage is you re-reading this chat. keep it short.
wait for background jobs to ping you. never check on them in a loop.
never wake an idle agent to ask for status. send it a real next step.
when a job is done, tell me to run /compact or write a handoff for a fresh chat.
max 2 helper agents at a time. use a cheaper model for jobs that only read files.

# CLAUDE.md — Moltbot

Progetto di bot Telegram che generano prompt di fotografia editoriale di moda per il personaggio fittizio Valeria Cross, con il modello Nano Banana di Flow. Unico sviluppatore e unico operatore: Walter. Rispondi sempre in italiano.

## Come lavorare

- Non creare, modificare o generare nulla che non sia stato chiesto esplicitamente.
- Lavora sempre su un ramo separato e apri una pull request. Non fare push né merge sul ramo principale: il deploy su Koyeb potrebbe partire da solo.
- Una sola modifica al giorno per bot. Niente patch temporanee.
- A fine lavoro elenca i file modificati e, per ogni bot, la versione prima e dopo.

## Versioni

- Prima di cambiare qualsiasi `VERSION`, leggi il valore reale nel file con `grep "^VERSION"`. Non fidarti di README, HANDOFF o cronologia.
- Il nome del file corrisponde alla `VERSION` senza punti (esempio: 2.0.9 diventa `_209`).
- Prima di scrivere una data in changelog, stringhe di versione, nomi di file o intestazioni, controlla la data reale del giorno con il comando `date`. Non riusare mai una data di un passaggio precedente.
- Aggiorna README e HANDOFF a ogni modifica.

## Regole sul codice

- Quando correggi i dati del volto o del DNA di Valeria, esegui `grep -rn` su tutto il progetto prima di considerare il lavoro finito. Le specifiche possono essere duplicate in `review_and_fix()` e nei blocchi locali `IDENTITY LOCK`.
- I conteggi dei pool (per esempio `LOCATION_POOL`) si verificano nel codice, non nelle etichette di un foglio Excel.
- Nano Banana non ha un campo `negativePrompt` indipendente: i prompt di tutti i bot sono scritti solo in positivo. Non reintrodurre negative prompt senza una richiesta esplicita.

## Segreti

- Mai token, chiavi API o credenziali nel codice, nei commit o nei messaggi. Vanno nelle variabili d'ambiente di Koyeb.
- Se trovi un segreto nel repository o nella cronologia, segnalalo subito senza copiarlo.
- Non leggere, non modificare e non aggiungere al repository i file Excel di tracciamento (`VERSIONI_BOT_*.xlsx`): contengono credenziali e li gestisce Walter.

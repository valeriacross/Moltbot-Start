# README — Ecosistema Bot Valeria Cross
**Aggiornato:** 18 Marzo 2026

---

## ECOSISTEMA BOT

```
ARCHITECT (A) = 🖼️/T → Prompt ottimizzato (T2T)
VOGUE (B)     = T/Prompt + A → {Immagine generata} (T2I)
FX (D)        = {Immagine generata} + Filtro → {Immagine filtrata} (I2I)
CABINA (C)    = 🖼️ costume + Filtro → {Valeria in costume} (pipeline neutra)
SORPRESA (E)  = 🎲 Random 14 variabili → {Immagine generata} (T2I)
```

---

## VERSIONI DEPLOYATE

| Bot | Versione | File | Note |
|-----|----------|------|------|
| SorpresaBot | 2.0.0 | sorpresa-200.py | ✅ |
| CabinaBot | 2.0.0 | cabina-200.py | ✅ |
| ValeriaFX | 4.0.0 | valeriafx-400.py | ✅ |
| VogueBot | 6.0.0 | vogue-600.py | ✅ |
| ArchitectBot | 8.0.0 | architect-800.py | ✅ |

**Token env:** TELEGRAM_TOKEN_SORPRESA, TELEGRAM_TOKEN_CLOSET, TELEGRAM_TOKEN_FX, TELEGRAM_TOKEN_VOGUE, TELEGRAM_TOKEN_ARCHITECT

**Deploy:** tutti su Koyeb — Flask health check obbligatorio su porta 10000

---

## HASHTAG FISSI (tutti i bot)

Aggiunti su seconda riga dopo ogni caption:
#genderfluid #selfexpression #bodypositivity

---

## IDENTITÀ VALERIA CROSS

- 60 anni, uomo italiano, viso ovale-rettangolare
- Occhiali Vogue Havana tartaruga scura ottagonali (SEMPRE presenti, mai toccati con le mani)
- Barba argento 6-7cm, capelli corti argento
- Corpo femminile: 180cm, 85kg, seno D-cup, hourglass
- Pelle liscia (zero peli su tutto il corpo)
- Watermark: feat. Valeria Cross 👠 — corsivo champagne, piccolo, bottom center
- Tutti i bot usano masterface.png (non master_face.png)
- Architect non usa master face (genera solo prompt testuali)

---

## REGOLE OPERATIVE

- Ogni modifica = bump versione; file precedente resta vivo (non sovrascrivere)
- NON applicare modifiche senza esplicito ok di Walter ("Vai" = ok)
- File di lavoro: /home/claude/ — Output finali: /mnt/user-data/outputs/
- Quota Gemini: 50 immagini/giorno (piano gratuito)
- Versione nel filename E versione dentro il file devono essere aggiornate insieme
- 409 Conflict = due istanze in parallelo → restart manuale sul deploy nuovo
- Excel e README: consegnare solo su richiesta esplicita
- HANDOFF: inviare su richiesta o a fine sessione
- Nomenclatura: nomebot-X00.py per versioni major (es. architect-800.py)

---

## SORPRESA BOT v2.0.0

Stili artistici: Magritte, Dalì, De Chirico, Mondrian, Banksy (con overrides asse 11)
Flow: estrazione silenziosamente filtrata (11 assi) → generazione → caption Threads + hashtag
Comandi: /start /reset /lastprompt

---

## VOGUE BOT v6.0.0

Flow: testo/prompt → ottimizzazione → generazione → immagine + caption + hashtag
Faceswap: hint /lastprompt nel messaggio di conferma
Comandi: /lastprompt /help /info /settings

---

## VALERIAFX v4.0.0

Mosaic: tile basato su ratio prima foto, minimo 1024px per lato
Comandi: /start /reset /filtro /help /info /lastprompt /mosaic /done

---

## CABINA BOT v2.0.0

VALERIA_FACE aggiunto come blocco testuale — fallback quando masterface.png non viene letta
Flow: foto outfit → analisi → generazione → immagine + caption + hashtag
Comandi: /start /reset /formato /settings /info /help /lastprompt

---

## ARCHITECT BOT v8.0.0

Menu motori: prima riga GEMINI+GROK, seconda riga QWEN+CHATGPT+META
/movie: collage 2x2 con DIRECTOR_PROFILES hardcodati
Anti-mani-occhiali: doppio blocco DNA+STEPS + review_and_fix
/lastprompt: implementato, salva sia prompt singolo che album
Comandi: /start /reset /motore /movie /lastprompt /help /info

---

## LEZIONI APPRESE

- Hashtag fissi: #genderfluid #selfexpression #bodypositivity — seconda riga dopo caption
- Cabina senza face: VALERIA_FACE testuale necessario come fallback
- Chunking obbligatorio: prompt superano spesso 4096 chars — chunks da 3800
- Glasses pose: doppio blocco DNA+STEPS più efficace del solo post-processing
- Stili artistici Sorpresa: 5 artisti con overrides coerenza palette/sfondo/pattern
- Menu Architect: Gemini e Grok in prima riga per accesso rapido

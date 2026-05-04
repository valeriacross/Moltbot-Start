# Valeria Cross AI — Ecosistema Bot Telegram

> Ecosistema di bot Telegram per la generazione di prompt editoriali per **Valeria Cross AI** — alter ego femminile di Walter Caponi, generato interamente con AI.
> I bot non generano immagini direttamente: producono prompt ottimizzati da incollare su **Flow (Google Labs)**.

---

## Struttura del repository

```
Moltbot-Start/
├── C_shared100.py        # Libreria comune — importata da tutti i bot
├── C_vogue100.py         # VogueBot — analisi foto → prompt Flow-ready
├── C_architect100.py     # ArchitectBot — prompt avanzati + Director's Cut
├── C_atelier100.py       # Atelier — prompt da outfit di riferimento
├── C_filtro100.py        # Filtro — effetti stilistici su foto
├── C_surprise100.py      # Surprise — scenari editoriali random
└── masterface.png        # Foto DNA Valeria (richiesta da Atelier e Filtro)
```

---

## Bot attivi

| Bot | File | Token env | Deploy Koyeb |
|-----|------|-----------|--------------|
| VogueBot | `C_vogue100.py` | `TELEGRAM_TOKEN` | colossal-giselle/vogue |
| ArchitectBot | `C_architect100.py` | `TELEGRAM_TOKEN_ARCHITECT` | homely-annabelle/thearchitect |
| Atelier | `C_atelier100.py` | `TELEGRAM_TOKEN_CLOSET` | flexible-denna/atelier |
| Filtro | `C_filtro100.py` | `TELEGRAM_TOKEN_FX` | screeching-jobina/filtro |
| Surprise | `C_surprise100.py` | `TELEGRAM_TOKEN_SORPRESA` | near-damara/sorpresa |

---

## Variabili d'ambiente (Koyeb)

```
TELEGRAM_TOKEN_*    Token del bot specifico (vedi tabella sopra)
GOOGLE_API_KEY      Chiave API Google AI Studio (gemini-3-flash-preview)
ALLOWED_USERS       Whitelist user ID Telegram, separati da virgola (es. 273003890)
PORT                10000 (default Koyeb)
```

> `GOOGLE_API_KEY` e `ALLOWED_USERS` vanno impostate su ogni servizio.
> Filtro non usa `GOOGLE_API_KEY`.

---

## Requisiti Python

```
pyTelegramBotAPI==4.14.0
flask==3.0.0
Pillow>=10.0.0
google-genai>=1.16.0
python-dotenv>=1.0.0
requests>=2.31.0
pytz
```

---

## C_shared100.py — Libreria comune

Tutti i bot importano da questo file:

```python
from C_shared100 import GeminiClient, CaptionGenerator, HealthServer, is_allowed, genai_types
from C_shared100 import VALERIA_FACE, VALERIA_BODY_STRONG, VALERIA_WATERMARK, VALERIA_NEGATIVE
```

**Componenti:**

- `GeminiClient` — Singleton thread-safe che wrappa `genai.Client`. Il prompt testuale viene wrappato come `Part.from_text()` nei payload misti immagine+testo.
- `CaptionGenerator` — Genera caption social in stile Valeria Cross. Tre modalità: `from_scenario()`, `from_image()`, `from_filter()`.
- `HealthServer` — Flask health check su porta 10000. Avvia in thread daemon con `use_reloader=False`.
- `is_allowed(uid)` — Whitelist utenti via env `ALLOWED_USERS`, fallback `273003890`.
- Costanti DNA: `VALERIA_FACE`, `VALERIA_BODY_STRONG`, `VALERIA_BODY_SAFE`, `VALERIA_WATERMARK`, `VALERIA_NEGATIVE`.

---

## C_vogue100.py — VogueBot

Analizza foto o testo e genera un prompt Flow-ready con il DNA di Valeria Cross.

**Flusso:** foto o testo → analisi Gemini → prompt → keyboard (Nuova foto / Riusa prompt / Home)

**Comandi:** `/start` · `/info` · `/dna`

---

## C_architect100.py — ArchitectBot

Genera prompt avanzati. Supporta foto singola, album multi-foto e Director's Cut (collage 2×2).

**Flusso:** scegli modalità → foto o testo → VisionStruct parallelo + generazione → review → prompt certificato

**Comandi:** `/start` · `/reset` · `/movie` · `/caption` · `/lastprompt` · `/info` · `/help`

**Director's Cut — 15 registi:**
Sergio Leone · Alfred Hitchcock · Stanley Kubrick · Akira Kurosawa · David Lynch · Christopher Nolan · Wes Anderson · Martin Scorsese · Francis Ford Coppola · Ridley Scott · Darren Aronofsky · Quentin Tarantino · Guillermo del Toro · Joel & Ethan Coen · Wong Kar-wai

---

## C_atelier100.py — Atelier

Genera prompt editoriali da una foto outfit di riferimento.

**Flusso:** scegli filtro → formato → quantità → foto outfit → prompt + caption

**Filtri:** 🎨 Canvas Swimsuit · 🤳 Selfie Spiaggia · 🛌 Letto · 🌅 Spiaggia Editoriale · 🍹 Beach Club · ⛵ Yacht · 🏄 Surf · 🎞️ Riviera '60 · 🌊 Pool Party · 🤿 Underwater · 🎬 Shooting Editorial

**Comandi:** `/start` · `/reset` · `/caption` · `/lastprompt` · `/settings` · `/info` · `/help`

---

## C_filtro100.py — Filtro

Applica filtri stilistici a foto. Supporta foto singola e mosaico fino a 9 foto.

**Categorie:** Cinematografico · Glam & Shine · Decorativo · 3D & Synthetic · Street Art · Effetti temporali · Scale & Fantasy · Stile Artistico (Magritte, Dalì, De Chirico, Mondrian, Banksy — casuale)

**Comandi:** `/start` · `/filtro` · `/caption` · `/mosaic` · `/lastprompt` · `/info` · `/help`

---

## C_surprise100.py — Surprise

Genera scenari editoriali da pool fissi. Modalità automatica o manuale passo-passo (6 passi).

**Pool — 481 voci totali:**

| Pool | Voci |
|------|------|
| Location | 197 |
| Outfit | 100 |
| Sky / Lighting | 41 |
| Pose | 43 |
| Mood | 50 |
| Stile fotografico | 50 |

**Comandi:** `/start` · `/lastprompt` · `/info` · `/help`

---

## Identità Valeria Cross

- **Viso:** maschile italiano 60 anni, barba argento 6-7 cm — obbligatoria
- **Occhiali:** Vogue Havana ottagonali — sempre presenti
- **Capelli:** taglio corto argento, nuca scoperta
- **Corpo:** femminile hourglass, 180 cm, 85 kg, D-cup, pelle liscia
- **Watermark:** `feat. Valeria Cross 👠` — corsivo champagne, bottom center
- **Regola coesistenza:** barba maschile + corpo femminile coesistono obbligatoriamente

---

## Infrastruttura

- **Deploy:** Koyeb — un servizio per bot, branch `main`
- **AI:** `gemini-3-flash-preview` — Google AI Studio, tier gratuito
- **Generazione immagini:** Flow (Google Labs) + NanoBanana 2
- **Health check:** `GET /` e `GET /health` su porta 10000

---

## Regole operative

1. Mai modificare file senza conferma esplicita
2. Ogni modifica = nuovo file con versione incrementata (es. `C_vogue100.py` → `C_vogue101.py`)
3. Testare sempre prima di consegnare
4. Mai produrre versioni multiple senza test intermedi
5. Presentare sempre il file dopo averlo prodotto

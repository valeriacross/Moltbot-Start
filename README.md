# 📸 VogueBot & 🏛️ ArchitectBot — README

> Aggiornato: Marzo 2026

---

## 📸 VogueBot v5.2.0

### Cosa fa
Genera scatti fotografici di Valeria Cross a partire da una descrizione testuale (e opzionalmente una foto di riferimento stile). Ottimizza automaticamente il prompt prima della generazione.

### Flusso standard
```
Utente scrive idea → Traduzione EN → Ottimizzazione Gemini → Preview prompt → Conferma → Genera
```

### Flusso Architect Certified (bypass)
```
Prompt con tag [MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]
→ Vogue riconosce tag → Rimuove tag → Preview diretta → Conferma → Genera
```
Il bypass salta traduzione e ottimizzazione — il prompt arriva intatto da Architect.

### Comandi
| Comando | Funzione |
|---|---|
| `/start` | Avvia il bot |
| `/ar` | Sceglie aspect ratio (2:3, 1:1, 9:16…) |
| `/qty` | Imposta numero di scatti (1–4) |
| `/lastprompt` | Mostra l'ultimo prompt usato |
| `/info` | Versione e stato |

### Bottone 🔁 Riprova
Appare sotto ogni scatto (successo o fallimento). Rilancia esattamente lo stesso prompt + immagine riferimento senza rielaborare. Utile per IMAGE_SAFETY non deterministica.

### Note tecniche
- Motore: `gemini-3-pro-image-preview`
- Ottimizzatore: `gemini-3-flash-preview`
- Safety: BLOCK_NONE
- `user_last_prompt` salvato come dict `{full_p, img}`
- Keep-alive: cron-job esterno (Flask presente ma non necessario)

---

## 🏛️ ArchitectBot v7.5.0

### Cosa fa
Genera Master Prompt professionali ottimizzati per diversi motori di image generation, partendo da un'idea testuale o da una foto di riferimento stile.

### Motori supportati
| Motore | Formato output |
|---|---|
| Gemini | Strutturato con sezioni labeled + 4 blocchi NEGATIVE separati |
| ChatGPT | Monolitico, linguaggio editoriale fashion, no anatomical terms |
| Grok | Monolitico, cinematico |
| Qwen | Monolitico, descrittivo |
| Meta | Monolitico, artistico |

### Pipeline di generazione
```
Input utente
  → Step 0: sanitize_user_input() — rimuove makeup, capelli conflittuali, watermark estranei
  → [se foto] VisionStruct scan — JSON strutturato (colori HEX, materiali, texture, angolo camera)
  → generate_monolith_prompt() / generate_from_image()
  → review_and_fix() — corregge contraddizioni nel prompt generato
  → adapt_to_engine() — adatta al motore target
  → Aggiunge tag [MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]
  → Output al'utente
```

### review_and_fix — controlli automatici
| Check | Azione |
|---|---|
| Capelli conflittuali (dark/long/curly/brown…) | Sostituisce con short silver Italian cut |
| Occhiali assenti | Inietta octagonal Vogue glasses (MANDATORY) |
| Watermark errato | Sostituisce con `feat. Valeria Cross 👠` |
| Brand reali (VOGUE logo…) | Sostituisce con generic luxury typography |
| Name bleeding (Valeria Cross nel body) | Rimuove e sostituisce con descrizione fisica |
| Conflitti nei negativi | Rimuove termini negativi che contraddicono i positivi |

### sanitize_user_input — filtri su input utente
- Makeup (smoky eyes, eyeliner, lipstick, contour…) → RIMOSSO
- Capelli conflittuali (lunghi, castani, biondi, melena…) → RIMOSSO
- Watermark estranei (non "feat. Valeria Cross") → RIMOSSO
- Tratti femminili giovani → RIMOSSO
- Scena, outfit, pose, luci, camera → PRESERVATI intatti

### VisionStruct
Pre-analisi dell'immagine di riferimento che produce un JSON strutturato con:
`meta, global_context, lighting, optics, color_palette, composition, entity_catalog` (con HEX, materiali, texture, micro-dettagli), `spatial_logic`

Il JSON viene iniettato come "ground truth" nel prompt di generazione. Se fallisce → fallback silenzioso.

### Tag Architect Certified
Ogni prompt in output include in testa:
```
[MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]
```
Vogue riconosce questo tag e bypassa l'intera catena di ottimizzazione.

### Note tecniche
- Generatore: `gemini-3-flash-preview`
- Safety: BLOCK_NONE
- Keep-alive: cron-job esterno (Flask presente ma non necessario)

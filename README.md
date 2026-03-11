# 📸 VogueBot · 🏛️ ArchitectBot · 🎲 SorpresaBot — README

> Aggiornato: Marzo 2026

---

## 📸 VogueBot v5.12.6

### Cosa fa
Genera scatti fotografici di Valeria Cross a partire da una descrizione testuale (e opzionalmente una foto di riferimento stile). Ottimizza automaticamente il prompt prima della generazione.

### Flusso standard
```
Utente scrive idea → Traduzione EN → Ottimizzazione Gemini → Preview prompt → Conferma → Genera
```

### Flusso Faceswap editoriale
```
Utente invia foto → Gemini analizza scena → Ricostruisce prompt con Valeria → Conferma → Genera
```
La foto viene analizzata testualmente da Flash. Il prompt completo (scena + identità Valeria) viene passato a Pro Image **senza troncare**. L'immagine originale non viene passata alla generazione.

### Flusso Architect Certified (bypass)
```
Prompt con tag [MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]
→ Vogue riconosce tag → Rimuove tag → Preview diretta → Conferma → Genera
```
Il bypass salta traduzione e ottimizzazione — il prompt arriva intatto da Architect.

### Flusso Reply Handler
```
Utente fa reply a un messaggio del bot con testo → run_refine() con ultima immagine come reference visiva
```
Usa `user_last_image[uid]` (bytes immagine generata) come reference. `refine_prompt` salvato in `user_last_prompt[uid]` prima di generare.

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
- Timeout: 120s con retry automatico (1 tentativo aggiuntivo dopo 15s)
- Troncamento prompt: **rimosso** — il prompt passa intero a Gemini
- `user_last_prompt` salvato come dict `{full_p, img}`
- `user_last_image` salvato come bytes dell'ultima immagine generata
- Master face: `masterface.png`
- Deploy: Koyeb, Flask health check porta 10000
- Token env: `TELEGRAM_TOKEN_VOGUE`

---

## 🏛️ ArchitectBot v7.11.5

### Cosa fa
Genera Master Prompt professionali ottimizzati per diversi motori di image generation, partendo da un'idea testuale o da una foto di riferimento stile (singola o album fino a 4 foto).

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
  → [se foto singola] VisionStruct scan — JSON strutturato (colori HEX, materiali, texture, angolo camera)
  → [se album 2-4 foto] generate_from_album() — Gemini analizza tutte le foto → posa NUOVA diversa da tutte le reference
  → generate_monolith_prompt() / generate_from_image()
  → review_and_fix() — corregge contraddizioni nel prompt generato
  → adapt_to_engine() — adatta al motore target
  → hard_cap_prompt() — tronca al limite caratteri sul boundary dell'ultima riga completa
  → Aggiunge tag [MASTER PROMPT — ARCHITECT CERTIFIED — SKIP OPTIMIZATION]
  → Output all'utente
```

### Flusso foto
```
Utente manda foto → pulsanti ✅ Genera prompt (1 foto) e ➕ Aggiungi foto
Premi ➕ → altra foto → contatore aggiornato (max 4)
✅ Genera prompt → processa
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

### Bug noto (da fixare)
`hard_cap_prompt` definita dopo `bot.infinity_polling` → `NameError` negli handler. Fix: spostare la funzione in cima al file, subito dopo gli import. Versione fix: `architect-7116.py`.

### Note tecniche
- Generatore: `gemini-3-flash-preview`
- Safety: BLOCK_NONE
- `user_last_input[uid]` aggiornato dopo `generate_from_album` (fix v7.11.5)
- Deploy: Koyeb, Flask health check porta 10000
- Token env: `TELEGRAM_TOKEN_ARCHITECT`

---

## 🎲 SorpresaBot v1.0.5

### Cosa fa
Estrae casualmente **13 variabili** e genera un'immagine unica di Valeria Cross. Ogni combinazione è praticamente irripetibile (~2 trilioni di possibilità).

### Flusso
```
/start → 🎲 Tira i dadi! → Mostra 13 variabili estratte
→ ✅ Conferma — Genera! oppure 🎲 Ritira i dadi
→ Genera immagine
→ Invia immagine + prompt generico separato (copiabile)
→ 🎲 Nuova sorpresa oppure 🔁 Riprova questa
```

### Variabili (13 × 15-16 opzioni)
| Variabile | Emoji | Opzioni |
|---|---|---|
| Sfondo | 🏛️ | 15 |
| Cielo | 🌤️ | 15 |
| Posa | 🧍 | 15 |
| Espressione | 😏 | 15 |
| Outfit Top | 👚 | 15 |
| Outfit Bottom | 👗 | 15 |
| Scarpe | 👠 | 15 |
| Colore | 🎨 | 15 |
| Accessori | 💍 | 15 |
| Stile | ✨ | 15 |
| Luce | 💡 | 15 |
| Inquadratura | 📷 | 15 |
| Filtro FX | ✨ | 16 |

### Filtri FX disponibili
Cinematic High-Angle, Dramatic Low-Angle, Glossy Opal, Iridescent, Rainbow Neon, Galaxy Couture, Neon HDR, Ghost Temporal, Dissolvence, Stained Glass, 3D Synthetic, Graffiti Artist, Cloud Sculpture, Action Figure, Art Doll Exhibition + `none` (photorealistic puro).

### Prompt generico
Dopo ogni immagine generata, il bot invia automaticamente un secondo messaggio con il prompt generico (senza identità Valeria) in formato copiabile — da condividere con i followers.

### Comandi
| Comando | Funzione |
|---|---|
| `/start` | Avvia il bot |
| `/info` | Mostra tutte le variabili con conteggio e totale combinazioni |

### Note tecniche
- Motore: `gemini-3-pro-image-preview`
- Safety: BLOCK_NONE
- Timeout: 120s con retry automatico (1 tentativo aggiuntivo dopo 15s)
- Master face: `masterface.png`
- Deploy: Koyeb, Flask health check porta 10000
- Token env: `TELEGRAM_TOKEN_SORPRESA`
- Repository: stesso di Vogue (requirements già presenti)

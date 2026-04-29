# README — Valeria Cross AI · Ecosistema Bot Telegram
**Aggiornato:** 29/04/2026

---

## Versioni attive

| Bot | Versione | File | Deploy |
|-----|----------|------|--------|
| ATELIER | **3.4.3** | `atelier-343.py` | flexible-denna/cabina |
| **SURPRISE** | **4.2.5** | `surprise-425.py` | near-damara/sorpresa |
| Filtro | **5.0.1** | `filtro-501.py` | screeching-jobina/filtro |
| VogueBot | **6.7.2** | `vogue-672.py` | colossal-giselle/vogue |
| ArchitectBot | **8.2.2** | `architect-822.py` | homely-annabelle/thearchitect |

---

## SURPRISE 4.2.5
Genera scenari editoriali con o senza foto di riferimento.

**Flow:**
```
/start → Hai una foto? [📷 Sì] [🎲 No]
  Con foto → analisi Gemini (7 elementi, 60-80 parole)
           → [Auto usa foto] [Manuale senza step location]
  Senza foto → [Auto] [Manuale completo]
→ Riepilogo + [📋 Prompt Flow] + [✅ Genera]
→ [🎲 Nuova scena] [🔁 Riprova]
```

**Prompt Flow:** descrizione estesa Gemini Vision (con foto) o value pool (senza foto). Include identity lock completo, beard MANDATORY, body PRIORITY 1.

**Pool:** 200 location · 100 outfit · 50 sky · 50 pose · 50 mood · 50 stili
**No-repeat:** location e outfit non si ripetono per sessione
**Comandi:** `/start` `/info` `/lastprompt`

---

## ATELIER 3.4.3
⚠️ BEARD MANDATORY + COEXISTENCE RULE. Caption da `outfit_desc` · COLOR LOCK HEX · Shooting Editorial + Mosaico 4 foto.

## Filtro 5.0.1
💧 Dissolvence · 👻 Ghost Temporal · 📸 Long Exposure · scenografici · `/mosaic` 2-9 foto

## VogueBot 6.7.2
⚠️ BEARD MANDATORY + COEXISTENCE RULE. Genera da testo o foto. Faceswap, batch.

## ArchitectBot 8.2.2
Prompt ottimizzati per Flow/ChatGPT/Grok/Qwen/Meta. Non usa masterface.

---

## Infrastruttura
- **Deploy:** Koyeb · Flask porta 10000
- **Modello immagini:** `gemini-3-pro-image-preview`
- **Modello testo:** `gemini-3-flash-preview`
- **masterface.png:** sempre primo in `contents` Gemini (tranne ArchitectBot)
- **Repository:** `github.com/valeriacross/Moltbot-Start` · `github.com/valeriacross/il-mio-moltbot`
- ⚠️ **Gemini 2.0 Flash shutdown 1/6/2026** — tutti già su 3.x

---

## Workflow UPDATE
`UPDATE` → handoff + README + XLSX pronti da salvare. Base: `Telegram_Bot_27-04-26.xlsx`

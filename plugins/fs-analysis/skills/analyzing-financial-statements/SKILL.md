---
name: analyzing-financial-statements
description: Analizza un bilancio italiano (Stato Patrimoniale e Conto Economico, uno o piu' esercizi) da PDF o XLSX. Lo riclassifica secondo lo schema CEE (artt. 2424/2425 c.c.), verifica la quadratura al centesimo, calcola indici, un punteggio sintetico e l'Altman Z'' con un engine deterministico, presenta insight e grafici in chat, risponde a domande e simulazioni e produce un report PDF a layout fisso. Usare quando l'utente carica o cita un bilancio, una visura, uno stato patrimoniale o un conto economico, oppure chiede un'analisi di bilancio, una riclassificazione, indici finanziari, un rating o un report di bilancio.
---

# Analisi di bilancio conversazionale → report PDF

Trasforma un bilancio "sporco" (PDF digitale, scansione o XLSX, con 2 o piu' esercizi)
in un'**analisi in chat**, con insight, grafici e risposte alle domande, e in un
**report PDF** a layout fisso.

**Separazione dei compiti (chiave della riproducibilita'):**
- Tu (agente) fai le parti che richiedono ragionamento: **leggere** il bilancio (anche
  scansioni), **mappare** le voci sulle chiavi canoniche, **spiegare** i risultati in
  chat, scrivere i grafici interattivi e i 4 testi del PDF.
- L'**engine Python** fa tutto il resto in modo deterministico: quadratura al
  centesimo, indici, punteggio, Altman Z'', grafici PNG e PDF. I numeri vengono **solo**
  da `metrics.json`.

## Percorsi e dipendenze
- Gli script stanno in `scripts/` **accanto a questo SKILL.md**. Imposta `SKILL_DIR`:
  - **Plugin Claude Code**: `SKILL_DIR="$CLAUDE_PLUGIN_ROOT/skills/analyzing-financial-statements"`.
  - **Skill su claude.ai o uso locale** (nessun `CLAUDE_PLUGIN_ROOT`): la cartella da
    cui hai letto questo SKILL.md.
- Python 3.10+: `pip install openpyxl reportlab matplotlib` (obbligatori);
  `pip install pdfplumber` (opzionale, per estrarre testo e tabelle dai PDF digitali).
- Riferimenti, da leggere quando servono:
  - [references/mapping.md](references/mapping.md): voci → chiavi canoniche, regole IT GAAP, vincoli di quadratura.
  - [references/indices.md](references/indices.md): indici, punteggio, rating, Altman Z'', dimensione, struttura di `metrics.json`.
  - [references/conversation.md](references/conversation.md): come presentare insight e grafici in chat, domande e simulazioni.
  - [references/narrative.md](references/narrative.md): contenuto dei 4 testi del PDF.
  - [references/output-format.md](references/output-format.md): layout del PDF e lunghezza dei testi.

## Workflow
Copia questa checklist e aggiornala mentre procedi:

```
Analisi di bilancio:
- [ ] 1. Identifica il file e il tipo (xlsx / pdf digitale / pdf scansione)
- [ ] 2. Estrai voci + metadati di tutti gli esercizi (min. 2)
- [ ] 3. Riclassifica → normalized.json
- [ ] 4. analyze.py: quadratura al centesimo + metriche + grafici
- [ ] 5. Presenta in chat quadratura, giudizio, KPI, insight e grafici
- [ ] 6. Rispondi a domande e simulazioni
- [ ] 7. Su richiesta: analysis.json → render_pdf.py → consegna il PDF
```

### 1–2. Estrazione
```bash
python "$SKILL_DIR/scripts/ingest.py" BILANCIO.(xlsx|pdf) \
    --skeleton normalized.json --anno <ULTIMO_ANNO> --esercizi <N>
```
- **XLSX / PDF digitale**: leggi il dump di `ingest.py`.
- **PDF scansione**: leggi direttamente le pagine con le tue capacita' multimodali.

Raccogli **tutti gli esercizi disponibili** (almeno 2; con un export pluriennale o piu'
bilanci anche 3 o piu', senza un limite fisso) e i metadati: ragione sociale, anno,
P.IVA, ATECO, forma giuridica, sede, numero medio dei dipendenti, capitale sociale,
debiti verso fornitori, crediti verso clienti.

### 3. Riclassifica → `normalized.json`
Compila lo schema seguendo [references/mapping.md](references/mapping.md), con
ESATTAMENTE le chiavi canoniche. Usa i **totali ufficiali** del bilancio come ancore
della quadratura.

### 4. Quadratura e metriche
```bash
python "$SKILL_DIR/scripts/analyze.py" normalized.json --out-dir fsa-output
```
- Codice di uscita **2** = NON quadra: leggi `fsa-output/verification.json`, correggi
  la mappatura (di norma una voce mancante o un totale sbagliato) e ripeti. I residui
  di arrotondamento fino a 0,05 € vengono assorbiti e segnalati.
- Successo: `fsa-output/metrics.json` (tutti i numeri, un elemento per esercizio),
  `verification.json` e i grafici in `fsa-output/charts/`.

### 5–6. Conversazione
Segui [references/conversation.md](references/conversation.md):
- primo messaggio con quadratura, giudizio sintetico, KPI, 3-5 insight e grafici;
- **grafici interattivi** se la superficie li supporta (artifact, widget o pagina HTML),
  altrimenti i PNG di `fsa-output/charts/`;
- domande e simulazioni: per ogni scenario si copia `normalized.json`, lo si modifica e
  si rilancia `analyze.py` in una cartella separata. Non ricalcolare mai a mente.

### 7. Report PDF (su richiesta o a fine analisi)
Scrivi `analysis.json` con le chiavi `economico`, `finanziario_patrimoniale`,
`sintesi`, `valutazione`, seguendo [references/narrative.md](references/narrative.md).
Con 3 o piu' esercizi ogni blocco apre con l'**andamento pluriennale** e si chiude sugli
**ultimi due anni**.
```bash
python "$SKILL_DIR/scripts/render_pdf.py" fsa-output/metrics.json --analysis analysis.json
```
Gli avvisi `[avviso capienza]` indicano testo troppo lungo: accorcia e ripeti.
Consegna `fsa-output/<azienda>_<anno>_report.pdf`.

## Regole non negoziabili
- Il bilancio **deve quadrare al centesimo**: se `analyze.py` esce con codice 2, NON
  proseguire; correggi la mappatura.
- I numeri (indici, punteggio, rating, Z'') vengono **solo** da `metrics.json` o da
  codice eseguito su di esso: non inventarli e non ricalcolarli a mente.
- Il **layout del PDF non cambia**: si scrive solo tramite `render_pdf.py`.
- Analisi descrittiva e valutativa: niente raccomandazioni di investimento o di affidamento.

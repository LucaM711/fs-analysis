---
name: analyzing-financial-statements
description: Riclassifica un bilancio italiano (Stato Patrimoniale e Conto Economico) da PDF o XLSX secondo i principi contabili italiani (schema CEE artt. 2424/2425 c.c.), verifica la quadratura al centesimo, calcola indici, grade e fido con un modello Excel deterministico e produce un report a layout fisso in XLSX e in PDF. Usare quando l'utente carica o cita un bilancio, una visura, uno stato patrimoniale o un conto economico, oppure chiede analisi di bilancio, riclassificazione, indici finanziari, rating, fido o un report di bilancio.
---

# Analisi di bilancio → report a layout fisso

Trasforma UN bilancio "sporco" (PDF export, PDF scansione, o XLSX) in un report
sempre con lo **stesso formato**: il foglio `Report` del modello, popolato e
esportato in PDF, piu' l'XLSX editabile per gli aggiustamenti dell'operatore.

**Separazione dei compiti (chiave della riproducibilita'):**
- Tu (agente) fai le parti che richiedono ragionamento: **leggere** il bilancio
  (anche scansioni) e **mappare** le voci sporche sulle voci canoniche; **scrivere**
  le 4 analisi testuali entro un formato fisso.
- L'**engine Python** fa tutto il resto in modo deterministico: popola il modello,
  **verifica la quadratura al centesimo**, ricalcola e legge indici/grade/fido dal
  modello (unica fonte di verita'), inietta i testi ed esporta il PDF.

Il layout del report **non cambia mai**: l'engine scrive solo celle predefinite.

## Percorsi e dipendenze
- Script: `${CLAUDE_PLUGIN_ROOT}/skills/analyzing-financial-statements/scripts/`
  (in sviluppo locale: la cartella `scripts/` di questa skill). Comodo: imposta
  `SKILL_DIR="${CLAUDE_PLUGIN_ROOT}/skills/analyzing-financial-statements"`.
- Python: `pip install openpyxl` (obbligatorio); `pip install pdfplumber` (opzionale,
  per estrarre testo/tabelle da PDF digitali).
- Rendering PDF: **LibreOffice** (`soffice`). Se manca in locale:
  `brew install --cask libreoffice` (macOS) o `apt-get install -y libreoffice-calc`.
  Fallback automatico su macOS con Microsoft Excel.
- Documenti di riferimento (leggere alla bisogna):
  - [references/mapping.md](references/mapping.md) — voci sporche → chiavi canoniche, regole IT GAAP, vincoli di quadratura.
  - [references/indices.md](references/indices.md) — indici, grade, fido, rating, bande interpretative.
  - [references/output-format.md](references/output-format.md) — celle scritte e budget dei testi.

## Workflow
Copia questa checklist e aggiornala mentre procedi:

```
Analisi di bilancio:
- [ ] 1. Identifica il file e il tipo (xlsx / pdf digitale / pdf scansione)
- [ ] 2. Estrai voci + metadati dei 2 esercizi
- [ ] 3. Riclassifica → normalized.json
- [ ] 4. Quadratura al centesimo (build_report.py) — checkpoint operatore
- [ ] 5. Leggi metrics.json (indici/grade/fido) + budget testi
- [ ] 6. Scrivi le 4 analisi → analysis.json
- [ ] 7. Esporta (render_pdf.py)
- [ ] 8. Consegna PDF + XLSX
```

### 1–2. Estrazione
Genera anche lo schema vuoto e dumpa il contenuto grezzo:
```bash
python "$SKILL_DIR/scripts/ingest.py" BILANCIO.(xlsx|pdf) \
    --skeleton normalized.json --anno <ULTIMO_ANNO>
```
- **XLSX / PDF digitale**: leggi il dump di `ingest.py`.
- **PDF scansione**: leggi direttamente le pagine con le tue capacita' multimodali
  (l'OCR automatico potrebbe non bastare).
Raccogli i **2 esercizi** (ultimo + precedente) e i metadati: ragione sociale, anno,
P.IVA, ATECO, forma giuridica, sede, numero medio dipendenti, debiti v/fornitori,
crediti v/clienti.

### 3. Riclassifica → `normalized.json`
Compila lo schema mappando ogni voce secondo
[references/mapping.md](references/mapping.md). Usa ESATTAMENTE le chiavi canoniche.
Rispetta i 5 vincoli di coerenza (i totali devono tornare). Usa i **totali ufficiali**
del bilancio come ancore della quadratura.

### 4. Quadratura (checkpoint operatore)
```bash
python "$SKILL_DIR/scripts/build_report.py" normalized.json --out-dir fsa-output
```
- Codice di uscita **2** = NON quadra: leggi `fsa-output/verification.json`, correggi
  la mappatura in `normalized.json` (di norma una voce mancante o un totale errato) e
  ripeti. Piccoli residui di arrotondamento (≤ 0,05 €) sono assorbiti e segnalati.
- Successo: vengono prodotti l'XLSX editabile, `metrics.json` e `verification.json`.
  **Mostra all'operatore** il riepilogo (quadratura + eventuali aggiustamenti) per il
  suo controllo.

### 5. Leggi le metriche
Leggi `fsa-output/metrics.json`: indici (economico, finanziario/patrimoniale),
`grade_fido` (dimensione, grade, fido), `ratings`, e `text_budgets` (limiti di
lunghezza per blocco). NON ricalcolare nulla: i numeri vengono dal modello.

### 6. Scrivi le 4 analisi → `analysis.json`
Scrivi un JSON con le chiavi `economico`, `finanziario_patrimoniale`, `sintesi`,
`grade_fido`, rispettando i budget di
[references/output-format.md](references/output-format.md) e ancorando ogni
affermazione ai numeri di `metrics.json`. Esempio:
```json
{
  "economico": "...",
  "finanziario_patrimoniale": "...",
  "sintesi": "...",
  "grade_fido": "..."
}
```

### 7. Esporta
```bash
python "$SKILL_DIR/scripts/render_pdf.py" \
    fsa-output/<azienda>_<anno>_report.xlsx --analysis analysis.json
```
Gli avvisi `[avviso capienza]` indicano testo troppo lungo: accorcia e ripeti.

### 8. Consegna
- `fsa-output/<azienda>_<anno>_report.pdf` — il report (output finale).
- `fsa-output/<azienda>_<anno>_report.xlsx` — workbook editabile per aggiustamenti
  (formule vive: l'operatore puo' correggere e rilanciare `render_pdf.py`).

## Regole non negoziabili
- Il **formato del report non cambia mai**: scrivi solo via gli script, mai
  modificare il layout, gli stili o le formule del modello.
- Il bilancio **deve quadrare al centesimo**: se `build_report.py` fallisce, NON
  proseguire — correggi la mappatura.
- I numeri (indici, grade, fido) provengono **solo** dal modello (`metrics.json`):
  non inventarli e non ricalcolarli nel testo.

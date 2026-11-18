# fs-analysis — Analisi di bilancio (plugin Claude Code)

Plugin Claude Code che trasforma un bilancio "sporco" (Stato Patrimoniale + Conto
Economico, in **PDF** o **XLSX**, anche scansione, con **2 o piu' esercizi**) in
un'**analisi conversazionale**, con insight, grafici e risposte alle domande in chat, e in
un **report PDF a layout fisso**.

La skill ragiona cosi':

1. carica il bilancio (qualunque formato) e ne estrae tutti gli esercizi disponibili;
2. **riclassifica** le voci secondo i principi contabili italiani (schema CEE, artt.
   2424/2425 c.c.);
3. **verifica la quadratura al centesimo** di Attivo e Passivo per ogni esercizio
   (assorbendo solo i residui di arrotondamento);
4. calcola per ogni esercizio **indici**, un **punteggio sintetico** con i rating per
   area e l'**Altman Z''**;
5. presenta in chat quadratura, giudizio, KPI, insight e **grafici** (interattivi dove
   la superficie lo permette) e risponde a domande e **simulazioni**;
6. su richiesta scrive le 4 analisi testuali e genera il **PDF**.

## Architettura (perche' l'output e' riproducibile)

| Parte | Chi la fa | Garanzia |
|---|---|---|
| Lettura del bilancio, mappatura delle voci, spiegazioni in chat, testi | Agente (Claude) | ragionamento, anche su scansioni |
| Quadratura, indici, punteggio, Altman Z'', grafici PNG, PDF | Engine Python deterministico (`scripts/fsa/`) | stessi input → stessi numeri |
| Layout del report | `fsa/report.py` | formato sempre identico |

Tutti i numeri finiscono in `metrics.json`: la chat, i grafici e il PDF leggono solo
quello. Le soglie e i pesi del punteggio sono tabelle leggibili in `fsa/scoring.py`.

## Struttura della repository

```
.claude-plugin/marketplace.json        # marketplace (un plugin)
plugins/fs-analysis/
  .claude-plugin/plugin.json           # manifest del plugin (versione SemVer)
  skills/analyzing-financial-statements/
    SKILL.md                           # workflow della skill
    references/                        # mappatura IT GAAP, indici e punteggio, chat, testi, PDF
    scripts/                           # CLI (ingest, analyze, render_pdf) + engine `fsa/`
tests/                                 # test dell'engine
pyproject.toml  release.config.mjs  sync-version.mjs  .github/workflows/
```

## Installazione come plugin

```text
/plugin marketplace add LucaM711/fs-analysis
/plugin install fs-analysis@fs-analysis-marketplace
```

Poi basta caricare un bilancio e chiedere l'analisi: la skill si attiva da sola.

### Dipendenze d'esecuzione
- Python 3.10+: `openpyxl`, `reportlab`, `matplotlib` (obbligatori), `pdfplumber`
  (opzionale, PDF digitali).
- Nessun programma esterno: niente LibreOffice o Excel.

## Uso manuale degli script (debug / pipeline)

```bash
SKILL=plugins/fs-analysis/skills/analyzing-financial-statements
# 1) assist estrazione + schema
python $SKILL/scripts/ingest.py BILANCIO.pdf --skeleton normalized.json --anno 2024 --esercizi 3
# 2) compila normalized.json, poi quadratura + metriche + grafici
python $SKILL/scripts/analyze.py normalized.json --out-dir fsa-output
# 3) scrivi analysis.json (4 blocchi) e genera il PDF
python $SKILL/scripts/render_pdf.py fsa-output/metrics.json --analysis analysis.json
```

`analyze.py` esce con codice **2** se il bilancio non quadra al centesimo: si corregge
la mappatura e si ripete.

## Sviluppo

```bash
pip install -r requirements.txt   # installa Poetry
poetry install                    # ambiente di sviluppo
poetry run poe test               # test
poetry run poe static-checks      # ruff + mypy
poetry run poe format             # formattazione
```

## Versionamento e release

Versione **SemVer** derivata dai **Conventional Commits** via `semantic-release`:
al merge su `master` aggiorna `CHANGELOG.md`, crea la release GitHub e sincronizza la
versione in `pyproject.toml`, `plugin.json` e `marketplace.json`. **Nessuna**
pubblicazione su PyPI. Le altre branch eseguono un dry-run.

## Licenza
[Apache 2.0](LICENSE).

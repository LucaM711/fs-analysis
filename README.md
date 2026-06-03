# fs-analysis — Analisi di bilancio (plugin Claude Code)

Plugin Claude Code che trasforma **un** bilancio "sporco" (Stato Patrimoniale +
Conto Economico, in **PDF** o **XLSX**, anche scansione) in un **report a layout
fisso** — esportato in **PDF** e disponibile come **XLSX editabile** per gli
aggiustamenti dell'operatore.

La skill ragiona cosi':

1. carica il bilancio (un solo upload, qualunque formato);
2. **riclassifica** le voci secondo i principi contabili italiani (schema CEE, artt.
   2424/2425 c.c.) mappandole sulle tabelle del modello;
3. **verifica la quadratura al centesimo** di Attivo e Passivo (con riconciliazione
   dei soli residui di arrotondamento);
4. calcola **indici, grade e fido** con il modello Excel (unica fonte di verita') e
   redige le **4 analisi** (Economico, Finanziario e Patrimoniale, Sintesi, Grade e
   Fido);
5. inietta i testi nelle celle predefinite ed esporta il **PDF**; il **formato del
   report non cambia mai**.

## Architettura (perche' l'output e' riproducibile)

| Parte | Chi la fa | Garanzia |
|---|---|---|
| Lettura del bilancio + mappatura voci | Agente (Claude) | ragionamento, anche su scansioni |
| Popolamento modello, quadratura, indici/grade/fido, PDF | Engine Python deterministico | stessi input → stessi numeri |
| Layout del report | Modello `template.xlsx` (mai modificato) | formato sempre identico |

L'engine non duplica le formule: **valorizza** il modello e ne **rilegge** i risultati.

## Struttura della repository

```
.claude-plugin/marketplace.json        # marketplace (un plugin)
plugins/fs-analysis/
  .claude-plugin/plugin.json           # manifest del plugin (versione SemVer)
  skills/analyzing-financial-statements/
    SKILL.md                           # workflow della skill
    references/                        # mapping IT GAAP, indici/grade/fido, formato output
    assets/                            # template.xlsx + font Syne (OFL)
    scripts/                           # CLI + engine `fsa/`
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
- Python: `openpyxl` (obbligatorio), `pdfplumber` (opzionale, PDF digitali).
- **LibreOffice** (`soffice`) per ricalcolo ed export PDF. In locale:
  `brew install --cask libreoffice` (macOS) / `apt-get install -y libreoffice-calc`.
  Su macOS con Microsoft Excel il fallback e' automatico. Nel sandbox di Claude
  (web) LibreOffice e' gia' disponibile.
- Il font **Syne** (OFL) e' incluso e viene installato automaticamente al rendering.

## Uso manuale degli script (debug / pipeline)

```bash
SKILL=plugins/fs-analysis/skills/analyzing-financial-statements
# 1) assist estrazione + schema
python $SKILL/scripts/ingest.py BILANCIO.pdf --skeleton normalized.json --anno 2024
# 2) compila normalized.json (mappatura) e verifica + popola + metriche
python $SKILL/scripts/build_report.py normalized.json --out-dir fsa-output
# 3) scrivi analysis.json (4 blocchi) ed esporta il PDF
python $SKILL/scripts/render_pdf.py fsa-output/<azienda>_<anno>_report.xlsx --analysis analysis.json
```

`build_report.py` esce con codice **2** se il bilancio non quadra al centesimo:
si corregge la mappatura e si ripete.

## Sviluppo

```bash
pip install -r requirements.txt   # installa Poetry
poetry install                    # ambiente di sviluppo
poetry run poe test               # test (i casi che richiedono LibreOffice si saltano se assente)
poetry run poe static-checks      # ruff + mypy
poetry run poe format             # formattazione
```

## Versionamento e release

Versione **SemVer** derivata dai **Conventional Commits** via `semantic-release`:
al merge su `master` aggiorna `CHANGELOG.md`, crea la release GitHub e sincronizza la
versione in `pyproject.toml`, `plugin.json` e `marketplace.json`. **Nessuna**
pubblicazione su PyPI. Le altre branch eseguono un dry-run.

## Licenza
[Apache 2.0](LICENSE). Font Syne: [SIL Open Font License](plugins/fs-analysis/skills/analyzing-financial-statements/assets/fonts/OFL.txt).

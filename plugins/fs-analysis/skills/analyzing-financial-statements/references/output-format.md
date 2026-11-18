# Il report PDF

`render_pdf.py` produce **un PDF A4 di 4 pagine a layout fisso** da `metrics.json` e
`analysis.json`. Il layout non cambia: cambiano solo numeri e testi.

| Pagina | Contenuto |
|---|---|
| 1 | Intestazione (ragione sociale, periodo), profilo (P.IVA, ATECO, forma giuridica, sede, dimensione UE, dipendenti), **valutazione sintetica** (punteggio 1-10, rating per area, Altman Z'' con zona), 8 KPI con variazione %, blocchi `economico` e `finanziario_patrimoniale` |
| 2 | Blocchi `sintesi` e `valutazione`; 4 grafici: andamento economico, struttura patrimoniale, redditivita', solidita' (Z'') |
| 3 | Stato patrimoniale riclassificato e conto economico, con la variazione % dell'ultimo anno; importi in euro, o in migliaia di euro (indicato nell'intestazione) quando superano i 10 milioni |
| 4 | Indici per anno; punteggio, rating e componenti dello Z'' per anno |

Le tabelle mostrano i **5 esercizi piu' recenti**; i grafici li mostrano tutti.

## Blocchi testuali (`analysis.json`)
| Chiave | Pagina | Sezione |
|---|---|---|
| `economico` | 1, a sinistra | Ambito economico |
| `finanziario_patrimoniale` | 1, a destra | Ambito finanziario e patrimoniale |
| `sintesi` | 2, a sinistra | Sintesi |
| `valutazione` | 2, a destra | Valutazione |

Altre chiavi vengono rifiutate (`render_pdf.py` esce con codice 1). Un blocco mancante
resta vuoto.

## Lunghezza dei testi
Ogni blocco ha un riquadro fisso (DejaVu Sans 9,5 pt). `render_pdf.py` **misura** ogni
testo: se non ci sta lo rimpicciolisce per non coprire il resto e stampa un
`[avviso capienza]`, quindi va accorciato e il PDF rigenerato. `metrics.json.text_budgets`
indica la capienza approssimativa (`max_chars`, `lines`): circa 1.550 caratteri per i
blocchi di pagina 1 e 1.350 per quelli di pagina 2. Testi piu' brevi rendono meglio:
puntare a 600-1.000 caratteri.

## Stile
- Prosa in italiano, registro professionale di analisi di bilancio.
- Frasi brevi; a capo (`\n`) per separare 2-3 micro-paragrafi.
- Ogni affermazione ancorata a un numero di `metrics.json`.
- Niente markdown, niente elenchi con simboli.

## Output
- `fsa-output/<azienda>_<anno>_report.pdf` (oppure il percorso di `--out`).

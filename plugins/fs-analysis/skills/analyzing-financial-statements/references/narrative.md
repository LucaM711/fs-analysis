# Struttura delle 4 analisi testuali (`analysis.json`)

Questa pagina dice **cosa scrivere** in ciascuno dei 4 blocchi. Per *dove* scriverli
e i *limiti di lunghezza* vedi [output-format.md](output-format.md); per il
*significato* di indici/grade/fido vedi [indices.md](indices.md).

## Regole di ferro (valgono per tutti i blocchi)
- **Numeri solo da `metrics.json`**: ogni cifra (valore, variazione %, indice, grade,
  fido) e' letta dal modello. Mai inventarli ne' ricalcolarli nel testo.
- **Prosa semplice in italiano**, registro di merito creditizio. Niente markdown,
  niente elenchi puntati con simboli: gli elenchi qui sotto sono **guida editoriale**,
  non il formato di output. Si possono usare a capo (`\n`) per separare 2-3 micro-paragrafi.
- **Rispettare i budget** di caratteri/righe (vedi `text_budgets` in `metrics.json`).
  I limiti "una riga / due righe" indicati sotto sono indicativi: prevale sempre il budget.
- **Ancorare ogni affermazione a un numero** e mantenere coerenza con il rating mostrato
  nelle celle B11/B14/B17 (campo `ratings` di `metrics.json`).

---

## 1. `economico` — Ambito Economico (cella `A34:B43`)
Andamento della gestione operativa. Ogni elemento ~1 frase:
- **Fatturato**: valore della produzione dell'ultimo esercizio (`economico.valore_produzione.y0`),
  valore assoluto dell'anno precedente (`.y1`) e variazione % (`valore_produzione_var`); breve commento.
- **Redditivita' operativa**: EBITDA (`ebitda`), EBIT (`ebit`, `ebit_var`, `ebit_pct`) e
  utile netto (`utile`, `utile_var`) confrontati con l'anno precedente, in valore assoluto e %;
  breve commento. Eventualmente richiamare ROS/ROE/ROI.
- **Sintesi**: redditivita' complessiva e sostenibilita' del modello economico nel medio-lungo termine.

## 2. `finanziario_patrimoniale` — Ambito Finanziario e Patrimoniale (cella `C34:D43`)
Solidita' patrimoniale, indebitamento e stabilita' finanziaria. E' il blocco con il
**budget piu' stretto**: massima sintesi, ~1-2 frasi per elemento.
- **Patrimonio netto**: valore attuale (`patrimonio_netto.y0`), precedente (`.y1`) e variazione %; breve commento.
- **Indebitamento finanziario**: distinzione breve/lungo termine, valori assoluti e variazioni %
  (`debiti_finanziari`, `debiti_finanziari_pct`, `rapporto_indebitamento`, `pfn`, `pfn_ebitda`); breve commento.
- **Disponibilita' liquide**: valore attuale (`disponibilita_liquide`), variazione assoluta e % vs esercizio precedente; breve commento.
- **Sintesi**: equilibrio patrimoniale, situazione delle disponibilita' liquide e stabilita' finanziaria.

## 3. `sintesi` — Sintesi Generale (cella `A46:B55`)
Raccoglie i principali elementi emersi (economici e finanziari):
- **Punti di forza**: evidenze positive (es. calo dell'indebitamento, solidita' patrimoniale, buona liquidita').
- **Punti di attenzione**: criticita' da monitorare (es. calo dei margini, perdita d'esercizio, contrazione dei ricavi).
- **Conclusione complessiva**: valutazione integrata, anche in ottica prospettica, della solidita' economico-finanziaria.

Il tono complessivo segue la banda di grade (vedi *Bande interpretative* in [indices.md](indices.md)).

## 4. `grade_fido` — Grade e Fido (cella `C46:D55`)
Valutazione sintetica e prudenziale sull'assegnazione di Grade e Fido commerciale:
- Tenere conto dell'equilibrio tra redditivita' e struttura finanziaria.
- Valutare la solvibilita' a breve termine e la sostenibilita' del business.
- Esprimere un giudizio sintetico ma motivato. Usare il **grade finale** (`grade_fido.grade_finale`,
  scala 1-10, 1 = migliore), il **fido** (`fido_massimo` / `fido_label`) e la
  `dimensione_impresa` **cosi' come sono in `metrics.json`** — senza alterarli.
- Coerenza con i rating delle tre aree (Reddituale/Finanziaria/Patrimoniale).

---

## Mappa rapida blocco → metriche principali
| Blocco | Chiavi `metrics.json` di riferimento |
|---|---|
| `economico` | `economico.*` (valore_produzione, ebit, ebitda, utile, ros, roe, roi, *_var, *_pct) |
| `finanziario_patrimoniale` | `finanziario_patrimoniale.*` (patrimonio_netto, debiti_finanziari, disponibilita_liquide, rapporto_indebitamento, pfn, pfn_ebitda) |
| `sintesi` | sintesi trasversale dei due blocchi precedenti + `grade_fido` |
| `grade_fido` | `grade_fido.*` (grade_finale, fido_massimo, fido_label, dimensione_impresa), `ratings.*` |

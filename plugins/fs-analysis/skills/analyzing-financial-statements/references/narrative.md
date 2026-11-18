# Le 4 analisi testuali del PDF (`analysis.json`)

Questa pagina dice **cosa scrivere** in ciascuno dei 4 blocchi del report PDF. Per i
riquadri e i limiti di lunghezza vedi [output-format.md](output-format.md); per il
significato dei numeri vedi [indices.md](indices.md). In chat valgono le stesse regole
sui numeri, con una forma piu' libera: vedi [conversation.md](conversation.md).

## Regole di ferro (valgono per tutti i blocchi)
- **Numeri solo da `metrics.json`**: ogni cifra (valore, variazione %, indice,
  punteggio, Z'') e' letta da li'. Mai inventarla o ricalcolarla nel testo.
- **Prosa semplice in italiano**, registro di analisi di bilancio: descrivere e
  valutare la situazione dell'azienda, senza raccomandazioni di investimento o di
  affidamento. Niente markdown ne' elenchi con simboli; si possono usare a capo (`\n`)
  per separare 2-3 micro-paragrafi.
- **Rispettare i riquadri**: `render_pdf.py` segnala i testi che non ci stanno
  (`[avviso capienza]`); in quel caso accorciare e rigenerare. `text_budgets` in
  `metrics.json` da' la capienza indicativa.
- **Ancorare ogni affermazione a un numero** ed essere coerenti con i rating
  (`esercizi[0].punteggio.aree.*.rating`).

## Andamento pluriennale (3 o piu' esercizi)
`metrics.json.esercizi` ha un elemento per anno, dal piu' recente al piu' vecchio. Con
3 o piu' esercizi **ogni blocco segue lo stesso ordine**:
1. **Andamento** (circa 1/4 del blocco): la traiettoria dal primo all'ultimo anno,
   citando gli estremi e le svolte (anni di picco, inversioni, perdite). Usare solo
   valori e `variazioni` presenti in `esercizi`: **non** calcolare medie o tassi di
   crescita pluriennali.
2. **Ultimi due anni** (il resto): l'analisi di dettaglio dell'ultimo esercizio sul
   precedente descritta qui sotto, letta alla luce dell'andamento.

Con 2 soli esercizi scrivere solo la parte 2. Con molti anni citare solo i passaggi che
contano, non ogni anno.

---

## 1. `economico` — Ambito economico
Andamento della gestione operativa. Circa una frase per elemento:
- **Fatturato**: valore della produzione dell'ultimo esercizio, del precedente e
  variazione % (`valori.valore_della_produzione`, `variazioni.valore_della_produzione`).
- **Redditivita' operativa**: EBITDA, EBIT e utile netto confrontati con l'anno
  precedente, in valore e in % (`valori.ebitda|ebit|utile_perdita_esercizio`,
  `indici.ebitda_pct|ebit_pct`); se utile, ROS, ROE e ROI.
- **Sintesi**: redditivita' complessiva e sostenibilita' del modello economico.

## 2. `finanziario_patrimoniale` — Ambito finanziario e patrimoniale
Solidita' patrimoniale, indebitamento e liquidita':
- **Patrimonio netto**: valore, variazione % e peso sull'attivo
  (`composizione.totale_patrimonio_netto_su_attivo`).
- **Indebitamento finanziario**: breve e lungo termine, PFN, PFN/EBITDA, rapporto di
  indebitamento, copertura degli interessi.
- **Liquidita'**: disponibilita' liquide, variazione, test acido e current ratio.
- **Sintesi**: equilibrio patrimoniale e stabilita' finanziaria.

## 3. `sintesi` — Sintesi
- **Punti di forza**: le evidenze positive principali.
- **Punti di attenzione**: le criticita' da monitorare.
- **Conclusione**: valutazione complessiva della solidita' economico-finanziaria.

## 4. `valutazione` — Valutazione
Lettura del giudizio sintetico calcolato dall'engine:
- **Punteggio complessivo** (`punteggio.complessivo`, scala 1-10, 1 = migliore) e
  `grade`, con la banda di lettura di [indices.md](indices.md#bande-di-lettura).
- **Rating per area** (reddituale, finanziaria, patrimoniale): quale area sostiene e
  quale pesa sul giudizio.
- **Altman Z''** (`altman.z`, `altman.zona`) e, con piu' esercizi, la sua evoluzione.
- Riportare punteggio, rating e Z'' **cosi' come sono**, senza alterarli.

---

## Mappa rapida blocco → campi di `esercizi[i]`
| Blocco | Campi principali |
|---|---|
| `economico` | `valori` (valore_della_produzione, ebitda, ebit, utile_perdita_esercizio), `variazioni`, `indici` (ros, roe, roi, *_pct) |
| `finanziario_patrimoniale` | `valori` (totale_patrimonio_netto, totale_debiti_finanziari, disponibilita_liquide), `composizione`, `indici` (pfn, pfn_ebitda, rapporto_indebitamento, test_acido, current_ratio) |
| `sintesi` | i due blocchi precedenti + `punteggio` |
| `valutazione` | `punteggio` (complessivo, grade, aree), `altman` |

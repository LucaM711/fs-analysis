# Analisi conversazionale: insight e grafici in chat

Dopo `analyze.py` l'analisi si svolge **in chat**: l'agente presenta i risultati, mostra
i grafici e risponde alle domande dell'utente. Il PDF e' il documento finale, prodotto
su richiesta o a fine conversazione.

## Regole
- **Numeri solo da `metrics.json`** (e da `verification.json` per la quadratura). Se
  serve un dato che non c'e', calcolarlo **con codice** a partire da `metrics.json`
  (o da `normalized.json`) e dire come e' stato ottenuto; mai stimarlo a mente.
- Prima l'**andamento** su tutti gli esercizi, poi il **dettaglio degli ultimi due anni**.
- Frasi brevi; tabelle markdown e grafici sono benvenuti in chat (non nel PDF).
- Registro di analisi di bilancio: niente raccomandazioni di investimento o di affidamento.

## Primo messaggio dopo `analyze.py`
1. **Quadratura**: esito per esercizio ed eventuali residui assorbiti o avvisi.
2. **Giudizio sintetico**: punteggio 1-10 e grade, rating per area, Altman Z'' con zona,
   dimensione UE.
3. **KPI** dell'ultimo esercizio con variazione: valore della produzione, EBITDA, EBIT,
   utile, patrimonio netto, PFN, liquidita'.
4. **3-5 insight**: le cose piu' rilevanti (svolte nell'andamento, punti di forza,
   segnali di attenzione), ognuna con il suo numero.
5. **Grafici**: almeno andamento economico e solidita' (vedi sotto).
6. Proporre i passi successivi: approfondimenti, simulazioni, PDF.

## Grafici
**Interattivi dove la superficie lo permette.** Se l'ambiente offre artifact, widget
o pagine HTML (per esempio claude.ai o l'app desktop), creare un grafico interattivo
con i dati di `metrics.json`: un file HTML unico con Chart.js da CDN, oppure il
componente grafico della superficie. Etichette in italiano, anni in ordine cronologico,
importi in migliaia o milioni di euro, tooltip con il valore esatto.

**Altrimenti PNG.** `analyze.py` scrive in `fsa-output/charts/` gli stessi 4 grafici
del PDF:
- `andamento_economico.png`: valore della produzione, EBITDA e utile per anno;
- `struttura_patrimoniale.png`: composizione di attivo e passivo dell'ultimo anno;
- `redditivita.png`: ROE, ROI e ROS per anno;
- `solidita.png`: Altman Z'' per anno con le zone.

Mostrarli o allegarli. Per un grafico che non c'e' (per esempio il ciclo monetario o
la composizione dei costi), scriverlo con matplotlib a partire da `metrics.json`.

Dati utili per i grafici: `anni` (dal piu' recente), `esercizi[i].valori`,
`.composizione`, `.indici`, `.punteggio`, `.altman`.

## Domande e simulazioni
- **Domande sui numeri** ("perche' scende il ROE?", "come si e' mosso il circolante?"):
  rispondere scomponendo l'indice nei suoi fattori con i valori di `metrics.json`
  (per esempio ROE = utile / PN, ROI = ROS × asset turnover).
- **Simulazioni** ("e se i debiti finanziari salissero di 100 mila euro?"):
  1. copiare `normalized.json` in `scenario.json` e modificarne le voci, mantenendo la
     quadratura (ogni variazione dell'attivo ha la sua contropartita nel passivo);
  2. `python analyze.py scenario.json --out-dir fsa-output/scenario`;
  3. confrontare le metriche dello scenario con quelle originali in una tabella e
     spiegare cosa cambia nel punteggio e nello Z''.
  Dire chiaramente che si tratta di una simulazione, non del bilancio reale.
- **Correzioni della mappatura** segnalate dall'utente: correggere `normalized.json`,
  rilanciare `analyze.py` e riassumere cosa e' cambiato.

## Verso il PDF
Quando l'utente vuole il documento: scrivere `analysis.json` seguendo
[narrative.md](narrative.md), lanciare `render_pdf.py` e risolvere eventuali
`[avviso capienza]`. I testi del PDF devono essere coerenti con quanto detto in chat.

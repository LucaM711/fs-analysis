# Indici, Grade e Fido — definizioni e lettura per la narrativa

I valori numerici di indici, grade e fido sono calcolati dal **modello** (foglio
`Input`/`Report`) e letti da `metrics.json`. NON ricalcolarli a mano: questa pagina
serve solo a interpretarli correttamente nel testo.

## Indice
- [Indici (foglio Report)](#indici-foglio-report)
- [Grade complessivo e dimensione impresa](#grade-complessivo-e-dimensione-impresa)
- [Sotto-grade e rating (Reddituale/Finanziaria/Patrimoniale)](#sotto-grade-e-rating)
- [Fido massimo](#fido-massimo)
- [Bande interpretative (PLACEHOLDER MVP)](#bande-interpretative-placeholder-mvp)

## Indici (foglio Report)
- **Liquidita'**: Test Acido `(Crediti+Disp.Liq.+Ratei att.)/Debiti a breve` ---> Prova più severa rispetto al Current Ratio. Si ottiene sottraendo le rimanenze dal numeratore del current
  ratio, scelta derivante dalla considerazione delle ovvie problematiche inerenti alla loro liquidabilità senza perdite del loro valore. Con Test Acido > 1 le attività correnti al netto delle scorte (denaro in cassa più gli incassi attesi dai crediti) sono sufficienti a coprire i debiti — commerciali e/o finanziari — scadenti nel breve periodo, senza dover smobilizzare il magazzino. ;
  Current Ratio `(Rimanenze+...)/Debiti a breve` ---> Rappresenta la nozione del capitale circolante netto, 
  non più considerando qui le attività correnti come misura di un fabbisogno di finanziamento, ma evidenziandone la complementare funzione di insieme di risorse più, o meno, pronte a far fronte ai debiti correntemente esigibili. Per ottenere un buon livello di solvibilità le attività correnti `(Rimanenze+Crediti+Disp.Liq.+Ratei att.)` devono superare le passività correnti `(Debiti a breve)`, e quindi Current Ratio > 1: l'impresa fa fronte ai debiti — commerciali e/o finanziari — scadenti nel breve periodo utilizzando l'intero insieme delle attività correnti, incluso il valore contabile delle scorte.
  Nel caso in cui test Acido < 1 e Current Ratio > 1 = Situazione pericolosa, da cui al netto delle scorte, le attività correnti non sono sufficienti a coprire quanto esigibile dalle passività correnti.
- **Indebitamento/sostenibilita'**: Rapporto Indebitamento `Debiti Fin./PN`
  (o `Debiti/PN` se Deb.Fin.=0) ---> nel caso in cui `Debiti Fin.`=0, si parla di Indice di leva finanziaria e misura quanto pesa l'indebitamento a fronte del capitale di rischio. Più risulta alto il valore dell'indice di leva finanziaria, maggiore è il livello di indebitamento dell'azienda. Il numeratore può comprendere sia tutti i debiti, sia soltanto quelli finanziari, caso in cui si parla di Leva finanziaria netta. ; PFN `Disp.Liq.+Att.Fin.−Debiti Fin.` (positiva = posizione di cassa netta;
  negativa = indebitamento finanziario netto) ---> La posizione finanziaria netta (PFN) è un indice di bilancio, cioè un indicatore che serve ad analizzare il bilancio d’esercizio di un’azienda. È data dalla differenza tra la somma di liquidità e crediti finanziari da una parte e i debiti finanziari verso banche o altri finanziatori dall’altra. La liquidità comprende ad esempio depositi bancari e denaro in cassa. La PFN si può calcolare a breve termine (considerando i crediti e i debiti finanziari a breve termine) o a medio-lungo termine (considerando invece i crediti e i debiti finanziari a medio-lungo termine). Se è positiva l’impresa ha disponibilità finanziaria, se è negativa è in una situazione di indebitamento. Esprime quindi la capacità/incapacità dell'azienda di generare la liquidità sufficiente a coprire le proprie esigenze di gestione e di far fronte ai debiti (solvibilità); PFN/EBITDA  esprime in “quanti anni” un’azienda è in grado di ripagare i debiti finanziari contratti ove utilizzasse la totalità dei suoi flussi operativi “potenziali” (EBITDA) per tale finalità; esso indica anche in quanto tempo la società potrà saldare il suo debito. Nota sul segno: in questo modello la PFN positiva = cassa netta, quindi la lettura "anni per ripagare" vale quando la PFN e' negativa (indebitamento netto); una PFN/EBITDA positiva segnala invece posizione di cassa netta.
- **Redditivita'**: ROS `EBIT/Ricavi` Rappresenta il cardine della misura dell'efficienza della gestione aziendale, nonché condizione per generare redditività, a prescindere dalla copertura degli eventuali risultati negativi emergenti dalla gestione finanziaria, straordinaria e fiscale. Il Return on Sales (ROS) misura l'efficienza operativa dell'impresa e consente di effettuare comparazioni nel tempo per una stessa impresa e fra imprese operanti nello stesso settore. Un indice elevato è sintomo di buona salute operativa e commerciale dell'impresa. ;
  ROE `Utile/PN` ---> rendimento contabile del capitale di rischio conferito dai soci. Va confrontato col costo-opportunita' del capitale; attenzione: un ROE elevato puo' derivare da un PN molto basso (alta leva) piu' che da redditivita' reale, quindi va letto insieme a ROI e rapporto di indebitamento. ;
  ROI `EBIT/Totale Attivo` ---> redditivita' del capitale investito nella gestione operativa, a prescindere dalla struttura finanziaria. Confronto chiave col costo medio del debito: se ROI > costo del debito la leva amplifica il ROE (effetto leva positivo), se ROI < costo del debito lo erode. ;
  EBITDA `EBIT+Ammortamenti` ---> margine operativo lordo (qui EBIT piu' i soli ammortamenti): proxy della cassa generata dalla gestione caratteristica prima di ammortamenti, oneri finanziari e imposte. E' la base di PFN/EBITDA e della valutazione di sostenibilita' del debito. ;
  EBIT% `EBIT/Valore Produzione` ---> incidenza del reddito operativo sul valore della produzione; marginalita' operativa al lordo della gestione finanziaria, straordinaria e fiscale (complementare al ROS, che rapporta l'EBIT ai ricavi di vendita).
- **Efficienza** (i tempi del ciclo usano il valore della produzione per gli incassi, i costi della produzione per pagamenti e magazzino):
  Asset Turnover `Ricavi/Totale Attivo` ---> rotazione del capitale investito: euro di ricavi per ogni euro di attivo. Vale la scomposizione DuPont: ROI = ROS x Asset Turnover. ;
  DSO `Crediti v/clienti / Valore Produzione x 365` (giorni) ---> giorni medi di incasso dei crediti commerciali. Piu' basso = incassi piu' rapidi. ;
  DPO `Debiti v/fornitori / Costi Produzione x 365` (giorni) ---> giorni medi di pagamento ai fornitori. Piu' alto = maggiore dilazione ottenuta, ma valori molto elevati possono segnalare tensioni di liquidita'. ;
  DIO `Rimanenze / Costi Produzione x 365` (giorni) ---> giorni medi di giacenza del magazzino. Piu' basso = scorte che ruotano piu' velocemente. ;
  CCC `DSO + DIO - DPO` (giorni) ---> ciclo monetario: giorni tra l'uscita di cassa per gli acquisti e l'incasso dalle vendite. Piu' basso (o negativo) = minor fabbisogno di circolante; un CCC negativo indica che i fornitori finanziano il ciclo operativo.

Per ciascun indice il modello assegna un **grade 1..10** (1 = migliore) tramite
soglie e pesi predefiniti; la loro media pesata e' il grade complessivo.

## Grade complessivo e dimensione impresa
- `grade_pesato` = media pesata dei grade 1..10 dei singoli indici (`Input!E75`).
- `dimensione_impresa` ∈ {Microimpresa, Piccola impresa, Media impresa, Grande
  impresa}, classificata su Totale Attivo, Ricavi e numero dipendenti.
- `grade_finale` (`Input!C83`) = arrotondamento del grade pesato con correzione per
  dimensione (le imprese piu' piccole ricevono un piccolo aggravio prudenziale).
  **1 = profilo migliore, 10 = peggiore.**

## Sotto-grade e rating
Tre aree con punteggio **1..5** (1 = migliore) e relativa etichetta:

| Punteggio | Rating |
|---|---|
| 1 | Eccellente |
| 2 | Positiva |
| 3 | Adeguata |
| 4 | Critica |
| 5 | Molto Critica |

- **Reddituale** (`sub_grade_reddituale`) → cella Report `B11`.
- **Finanziaria** (`sub_grade_finanziaria`) → cella `B14`.
- **Patrimoniale** (`sub_grade_patrimoniale`) → cella `B17`.

`build_report.py` scrive automaticamente `B11`/`B14`/`B17` dai sotto-grade calcolati: nel
testo usare le etichette coerenti (campo `ratings` di `metrics.json`).

## Fido massimo
`fido_massimo` (`Input!D83`) = importo massimo di affidamento proposto, funzione del
`grade_finale` e della `dimensione_impresa`; `fido_label` e' la fascia formattata
(es. `"0 € - 70.000 €"`). Riportare nel testo il valore del modello, senza alterarlo.

## Bande interpretative (PLACEHOLDER MVP)
> Logica provvisoria per dare un tono coerente alla prosa. Da rivedere quando
> saranno definite le logiche di rating definitive. NON cambia i numeri del modello.

Grade finale (1..10):
- **1–3**: profilo solido / rischio basso — tono positivo, evidenziare i punti di forza.
- **4–6**: profilo adeguato / rischio medio — tono equilibrato, segnalare aree di attenzione.
- **7–8**: profilo debole / rischio medio-alto — tono prudente, indicare le criticita'.
- **9–10**: profilo critico / rischio alto — tono cauto, raccomandazioni di monitoraggio.

Linee guida per la narrativa:
- Ancorare ogni affermazione a un numero di `metrics.json` (indice, variazione %, grade).
- Coerenza fra rating mostrato (B11/B14/B17) e testo dell'area corrispondente.
- Niente raccomandazioni di investimento; analisi descrittiva e di merito creditizio.

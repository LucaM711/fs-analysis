# Indici, punteggio e Altman Z'' — definizioni e lettura

Tutti i valori sono calcolati dall'engine (`fsa/metrics.py`, `fsa/scoring.py`) e si
leggono da `metrics.json`, sotto `esercizi[i]` (`i = 0` e' l'ultimo esercizio). **Non
ricalcolarli a mano**: questa pagina serve a interpretarli. Un valore `null` vuol dire
"non calcolabile" (denominatore zero, dato `n.d.`, nessun debito finanziario per la PFN).

## Indice
- [Dove sono i numeri](#dove-sono-i-numeri)
- [Indici](#indici)
- [Punteggio complessivo](#punteggio-complessivo)
- [Rating per area](#rating-per-area)
- [Altman Z''](#altman-z)
- [Dimensione d'impresa](#dimensione-dimpresa)
- [Bande di lettura](#bande-di-lettura)

## Dove sono i numeri
| Campo di `esercizi[i]` | Contenuto |
|---|---|
| `anno` | esercizio |
| `valori` | voci di `normalized.json` + `ebitda`, `debiti_non_finanziari` (+ `_breve`/`_oltre`), `attivo_corrente` |
| `composizione` | `<voce>_su_attivo` (SP sul totale attivo), `<costo>_su_costi` (sui costi della produzione) |
| `variazioni` | variazione % di ogni voce di `valori` sull'anno prima (`null` per l'esercizio piu' vecchio) |
| `indici` | gli indici qui sotto |
| `punteggio` | `complessivo` (1-10), `grade`, `indici.<nome>.grade/peso`, `aree` |
| `altman` | `x1`..`x4`, `z`, `zona` |

Le variazioni dividono per il **valore assoluto** dell'anno prima: da una perdita a un
utile la variazione e' positiva.

## Indici
| Chiave | Formula | Lettura |
|---|---|---|
| `test_acido` | (crediti + liquidita' + ratei att.) / debiti a breve | > 1: le attivita' correnti senza magazzino coprono i debiti a breve. Piu' severo del current ratio |
| `current_ratio` | attivo corrente / debiti a breve | > 1: buona solvibilita' usando anche le scorte. Test acido < 1 con current ratio > 1 = dipendenza dal magazzino |
| `rapporto_indebitamento` | debiti finanziari / PN (debiti non finanziari / PN se i finanziari sono 0) | peso del debito sul capitale di rischio: piu' alto = piu' leva |
| `pfn` | liquidita' + attivita' fin. − debiti finanziari | **positiva = cassa netta**, negativa = indebitamento netto |
| `pfn_ebitda` | PFN / EBITDA | con PFN negativa: quanti anni di EBITDA servono a ripagare il debito netto. Con PFN positiva segnala cassa netta |
| `ims` | PN / immobilizzazioni | margine di struttura: ≥ 1 = immobilizzazioni coperte dal capitale proprio |
| `interest_coverage` | EBITDA / oneri finanziari | quante volte il margine copre gli interessi |
| `ros` | EBIT / ricavi | efficienza operativa, confrontabile nel tempo e nel settore |
| `roe` | utile / PN | rendimento del capitale di rischio. Un ROE alto con PN basso puo' venire dalla leva: leggerlo con ROI e indebitamento |
| `roi` | EBIT / totale attivo | redditivita' del capitale investito. ROI > costo del debito = leva favorevole |
| `ebitda_pct`, `ebit_pct`, `risultato_pct` | EBITDA, EBIT, utile / valore della produzione | marginalita' lorda, operativa e netta |
| `asset_turnover` | ricavi / totale attivo | euro di ricavi per euro investito (ROI = ROS × asset turnover) |
| `dso` | crediti v/clienti / valore produzione × 365 | giorni medi di incasso: piu' basso e' meglio |
| `dpo` | debiti v/fornitori / costi produzione × 365 | giorni medi di pagamento: piu' alto = piu' dilazione, ma valori estremi segnalano tensione |
| `dio` | rimanenze / costi produzione × 365 | giorni di magazzino |
| `ccc` | DSO + DIO − DPO | ciclo monetario: piu' basso (o negativo) = meno capitale circolante da finanziare |

EBITDA = EBIT + ammortamenti (`valori.ebitda`).

## Punteggio complessivo
Ogni indice riceve un **grade da 1 (migliore) a 10** tramite soglie fisse
(`INDEX_GRADES` in `fsa/scoring.py`). Il `complessivo` e' la **media pesata** dei grade
calcolabili; i pesi degli indici non calcolabili vengono ridistribuiti. Il `grade` e'
il complessivo arrotondato.

| Area | Indici (peso) |
|---|---|
| Liquidita' | test acido (10%), current ratio (10%) |
| Indebitamento | rapporto di indebitamento (10%), PFN/EBITDA (15%), IMS (5%), copertura interessi (10%) |
| Redditivita' | ROS (10%), ROE (5%), ROI (5%), EBITDA% (10%), EBIT% (5%), risultato% (2,5%) |
| Efficienza | asset turnover (2,5%) |

Casi speciali: con PFN in cassa netta ed EBITDA positivo il grade PFN/EBITDA e' 3; con
debito netto ed EBITDA negativo e' 8; senza debiti finanziari e' 5, oppure e' escluso
se non ci sono nemmeno oneri finanziari. Senza oneri finanziari la copertura interessi
ha grade 1.

## Rating per area
`punteggio.aree.<area>` ha `punteggio` da **1 (migliore) a 5**, `rating` e il dettaglio
`componenti`. Richiede l'esercizio precedente, quindi e' `null` per il piu' vecchio.

| Punteggio | Rating |
|---|---|
| 1 | Eccellente |
| 2 | Positiva |
| 3 | Adeguata |
| 4 | Critica |
| 5 | Molto Critica |

- **Reddituale**: crescita del valore della produzione, dell'EBIT e dell'utile,
  variazione dell'incidenza di EBIT e utile, ROS.
- **Finanziaria**: peso e crescita della liquidita', liquidita' oltre il debito
  finanziario a breve e totale, crescita dell'EBITDA.
- **Patrimoniale**: peso del patrimonio netto sull'attivo, rapporto di indebitamento.

## Altman Z''
Modello di Altman (1995) per le imprese non quotate:
`Z'' = 6,56·X1 + 3,26·X2 + 6,72·X3 + 1,05·X4`.

| Componente | Formula |
|---|---|
| `x1` | (attivo corrente − debiti a breve) / totale attivo |
| `x2` | (PN − capitale sociale) / totale attivo, una stima degli utili non distribuiti che include anche le altre riserve |
| `x3` | EBIT / totale attivo |
| `x4` | PN / (totale attivo − PN) |

Zone (`zona`): **sicurezza** oltre 2,60; **grigia** da 1,10 a 2,60 compresi; **rischio** sotto 1,10.
La zona si decide sullo Z'' arrotondato a 2 decimali, cioe' sul valore mostrato.
E' un indicatore statistico di rischio, non una previsione: citarlo come tale.

## Dimensione d'impresa
`dimensione_impresa` (ultimo esercizio) segue la Raccomandazione UE 2003/361:

| Dimensione | Dipendenti | e fatturato oppure attivo |
|---|---|---|
| Microimpresa | < 10 | ≤ 2 mln oppure ≤ 2 mln |
| Piccola impresa | < 50 | ≤ 10 mln oppure ≤ 10 mln |
| Media impresa | < 250 | ≤ 50 mln oppure ≤ 43 mln |
| Grande impresa | oltre | |

E' solo descrittiva: non modifica il punteggio.

## Bande di lettura
Per il tono del testo, in base al `grade` (1..10):
- **1–3**: profilo solido; evidenziare i punti di forza.
- **4–6**: profilo adeguato; equilibrio fra punti di forza e di attenzione.
- **7–8**: profilo debole; indicare le criticita'.
- **9–10**: profilo critico; tono cauto, indicare cosa monitorare.

Il punteggio, i rating e lo Z'' sono strumenti di analisi: niente raccomandazioni di
investimento o di affidamento.

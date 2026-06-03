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
- **Liquidita'**: Test Acido `(Crediti+Disp.Liq.+Ratei att.)/Debiti a breve`;
  Current Ratio `(Rimanenze+...)/Debiti a breve`.
- **Indebitamento/sostenibilita'**: Rapporto Indebitamento `Debiti Fin./PN`
  (o `Debiti/PN` se Deb.Fin.=0); PFN `Disp.Liq.+Att.Fin.−Debiti Fin.` (negativa =
  posizione di cassa netta positiva); PFN/EBITDA.
- **Redditivita'**: ROS `EBIT/Ricavi`; ROE `Utile/PN`; ROI `EBIT/Totale Attivo`;
  EBITDA `EBIT+Ammortamenti`; EBIT% `EBIT/Valore Produzione`.
- **Efficienza**: Asset Turnover `Ricavi/Totale Attivo`; DSO, DPO, DIO, CCC (giorni).

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
- **Finanziaria** (`sub_grade_finanziaria`) → cella `B14` (gia' formula nel modello).
- **Patrimoniale** (`sub_grade_patrimoniale`) → cella `B17`.

`build_report.py` scrive automaticamente `B11`/`B17` dai sotto-grade calcolati: nel
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

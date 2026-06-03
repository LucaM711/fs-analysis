# Riclassificazione e mappatura delle voci (principi contabili italiani)

Guida per mappare un bilancio "sporco" (schema CEE, artt. 2424/2425 c.c.) sulle
**chiavi canoniche** del `normalized.json`. Le chiavi sono fisse: usare ESATTAMENTE
quelle elencate qui.

## Indice
- [Regole generali](#regole-generali)
- [Conto Economico (art. 2425 c.c.)](#conto-economico-art-2425-cc)
- [Stato Patrimoniale (art. 2424 c.c.)](#stato-patrimoniale-art-2424-cc)
- [Vincoli di coerenza (obbligatori per la quadratura)](#vincoli-di-coerenza-obbligatori-per-la-quadratura)
- [Casi particolari](#casi-particolari)

## Regole generali
- Importi in **euro a 2 decimali**, segno positivo per costi e ricavi (i costi NON
  vanno messi negativi: il modello li sottrae da solo).
- `y0` = ultimo esercizio, `y1` = precedente. Servono **2 esercizi**.
- Se una voce di dettaglio non esiste nel bilancio, impostarla a `0` (non lasciarla
  nulla), assicurandosi che i totali tornino.
- Non inventare numeri: usare i totali di bilancio come ancore e mappare i dettagli
  dentro quei totali.

## Conto Economico (art. 2425 c.c.)
| Chiave canonica | Voce CEE | Note |
|---|---|---|
| `valore_della_produzione` | Totale A) | Valore della produzione |
| `ricavi_di_vendita` | A.1) | Ricavi delle vendite e delle prestazioni |
| `costi_della_produzione` | Totale B) | Costi della produzione |
| `costi_per_materie` | B.6) (± B.11 var. rimanenze materie) | Materie prime, sussidiarie, di consumo |
| `costi_per_servizi` | B.7) | Per servizi |
| `costi_godimento_beni_terzi` | B.8) | Godimento beni di terzi |
| `costi_personale` | B.9) | Totale costi del personale |
| `ammortamenti` | B.10) | Ammortamenti e svalutazioni (a+b+c; d se classificata qui) |
| `accantonamenti_per_rischi` | B.12) + B.13) | Accantonamenti per rischi e altri |
| `oneri_diversi_di_gestione` | B.14) | Oneri diversi di gestione |
| `ebit` | A − B | **Differenza tra valore e costi della produzione** (risultato operativo) |
| `proventi_finanziari` | C.15) + C.16) | Proventi finanziari |
| `oneri_finanziari` | C.17) (± C.17-bis) | Interessi e altri oneri finanziari |
| `utile_perdita_esercizio` | voce 21) | Utile (perdita) dell'esercizio, dopo le imposte |
| `dipendenti` | Nota integrativa | Numero medio dei dipendenti (intero) |

Coerenza CE attesa: `valore_della_produzione − costi_della_produzione = ebit`
(verificare; piccoli scostamenti indicano voci B non mappate).

## Stato Patrimoniale (art. 2424 c.c.)

### Attivo
| Chiave canonica | Voce CEE | Note |
|---|---|---|
| `immobilizzazioni` | B) (I + II + III) | Immateriali + materiali + finanziarie **immobilizzate** |
| `rimanenze` | C.I) | Rimanenze |
| `crediti` | C.II) | Crediti dell'attivo circolante (entro + oltre) + A) crediti v/soci |
| `attivita_finanziarie` | C.III) | Attivita' finanziarie **non** immobilizzate |
| `disponibilita_liquide` | C.IV) | Disponibilita' liquide |
| `ratei_risconti_attivi` | D) | Ratei e risconti attivi |
| `totale_attivo` | Totale attivo | Ancora della quadratura attivo |

### Passivo
| Chiave canonica | Voce CEE | Note |
|---|---|---|
| `totale_patrimonio_netto` | A) | Patrimonio netto (incl. utile d'esercizio) |
| `fondi_rischi_oneri` | B) | Fondi per rischi e oneri |
| `tfr` | C) | Trattamento di fine rapporto |
| `totale_debiti` | D) | Totale debiti (commerciali + finanziari + altri) |
| `debiti_esigibili_breve` | D) entro 12 mesi | Quota di **tutti** i debiti esigibile entro l'esercizio |
| `debiti_esigibili_oltre` | D) oltre 12 mesi | Quota di **tutti** i debiti esigibile oltre |
| `totale_debiti_finanziari` | D.1-D.5 | Obbligazioni, v/soci finanziamenti, v/banche, altri finanziatori |
| `debiti_finanziari_breve` | D.1-D.5 entro | Quota finanziaria a breve |
| `debiti_finanziari_oltre` | D.1-D.5 oltre | Quota finanziaria oltre |
| `ratei_risconti_passivi` | E) | Ratei e risconti passivi |
| `debiti_verso_fornitori` | D.7) | Per DPO; `"n.d."` se non separabile |
| `crediti_verso_clienti` | C.II.1) | Per DSO; `"n.d."` se non separabile |

## Vincoli di coerenza (obbligatori per la quadratura)
Devono valere al centesimo, altrimenti `build_report.py` esce con errore:

1. `immobilizzazioni + rimanenze + crediti + attivita_finanziarie + disponibilita_liquide + ratei_risconti_attivi = totale_attivo`
2. `debiti_esigibili_breve + debiti_esigibili_oltre = totale_debiti`
3. `debiti_finanziari_breve + debiti_finanziari_oltre = totale_debiti_finanziari`
4. `totale_debiti_finanziari ≤ totale_debiti` (i debiti commerciali = totale − finanziari ≥ 0)
5. Passivo: `totale_debiti + fondi_rischi_oneri + tfr + totale_patrimonio_netto + ratei_risconti_passivi = totale_attivo`

I debiti **commerciali/altri** non hanno una chiave propria: sono calcolati dal
modello come `totale_debiti − totale_debiti_finanziari` (suddivisi per scadenza).

## Casi particolari
- **Bilancio abbreviato/micro**: spesso mancano dettagli (es. ripartizione
  breve/oltre dei debiti). Stimare in modo prudente o, se impossibile separare i
  debiti finanziari, impostare `totale_debiti_finanziari` e le sue quote a `0`
  (l'indebitamento sara' valutato sui debiti totali). Mantenere comunque i 5 vincoli.
- **Debiti finanziari non distinti**: se non si distingue breve/oltre, attribuire
  tutto a `debiti_finanziari_oltre` (o `breve`) coerentemente con la natura del debito.
- **DSO/DPO non calcolabili**: usare `"n.d."` (stringa) per
  `crediti_verso_clienti`/`debiti_verso_fornitori`.
- **Segni**: l'`utile_perdita_esercizio` puo' essere negativo (perdita). Tutte le
  altre voci sono importi assoluti positivi.
- **Scansioni/PDF**: leggere i prospetti direttamente (anche via OCR/vision),
  privilegiando i **totali ufficiali** del bilancio come riferimento di quadratura.

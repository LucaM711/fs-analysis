# Formato dell'output — celle del Report (NON modificare il layout)

Il foglio `Report` ha un **layout fisso** (area di stampa `A1:D185`, portrait, scala
80, font Syne). L'output e' SEMPRE lo stesso formato. L'engine scrive solo le celle
qui sotto; ogni altra cella e' calcolata da formule e non va toccata.

## Celle scritte dall'engine

### Blocchi testuali (analysis.json → celle merge)
| Chiave `analysis.json` | Cella (merge) | Sezione |
|---|---|---|
| `economico` | `A34:B43` | Ambito Economico |
| `finanziario_patrimoniale` | `C34:D43` | Ambito Finanziario e Patrimoniale |
| `sintesi` | `A46:B55` | Sintesi |
| `grade_fido` | `C46:D55` | Grade e Fido |

### Rating (scritti automaticamente da build_report.py)
| Cella | Origine |
|---|---|
| `B11` | rating Reddituale (da `sub_grade_reddituale`) |
| `B14` | rating Finanziaria — **formula del modello, non si scrive** |
| `B17` | rating Patrimoniale (da `sub_grade_patrimoniale`) |

## Budget di lunghezza
Le celle merge hanno spazio limitato (font Syne 12, a capo automatico). `build_report.py`
stampa e salva in `metrics.json` (`text_budgets`) il **massimo di caratteri** e il
numero di righe per ciascun blocco. Tenersi entro il budget: testo piu' lungo viene
troncato nel PDF. Valori tipici (dipendono dalle larghezze colonna del modello):

| Blocco | Indicativo |
|---|---|
| `economico` (A:B) | ~550–600 caratteri, ~10 righe |
| `finanziario_patrimoniale` (C:D) | ~360–400 caratteri, ~10 righe |
| `sintesi` (A:B) | ~550–600 caratteri, ~10 righe |
| `grade_fido` (C:D) | ~360–400 caratteri, ~10 righe |

## Stile dei testi
- Prosa discorsiva in italiano, registro professionale (merito creditizio).
- Frasi brevi; si possono usare a capo (`\n`) per separare 2–3 micro-paragrafi.
- Ogni affermazione ancorata a un numero di `metrics.json`.
- Niente markdown, niente elenchi puntati con simboli: solo testo semplice.
- Coerenza fra il rating mostrato e il contenuto della sezione.

## Output finali
- `<azienda>_<anno>_report.xlsx` — workbook **editabile** (formule vive, testi e
  rating inseriti): l'operatore puo' rivederlo e correggerlo.
- `<azienda>_<anno>_report.pdf` — il report a layout fisso, da consegnare.

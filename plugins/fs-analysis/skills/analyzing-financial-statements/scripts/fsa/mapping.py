"""Mappa fra le voci canoniche e le celle del foglio ``Input`` del modello.

Queste sono le UNICHE celle che l'engine scrive nel foglio ``Input``. Ogni altra
cella (formule di indici, grade, fido, verifiche ``B52``/``B53``) e' calcolata dal
foglio di calcolo e non va mai toccata.

Le colonne degli anni nel foglio ``Input`` sono:
    y0 -> colonna B (ultimo esercizio, ``Input!B2``)
    y1 -> colonna C (esercizio precedente)
    y2 -> colonna D (due esercizi prima, opzionale)
"""

from __future__ import annotations

# Colonna del foglio Input per ciascun "slot" anno.
YEAR_COLUMNS: dict[str, str] = {"y0": "B", "y1": "C", "y2": "D"}

# --- Conto Economico: chiave canonica -> riga del foglio Input -------------------
CONTO_ECONOMICO_ROWS: dict[str, int] = {
    "valore_della_produzione": 7,
    "ricavi_di_vendita": 8,
    "costi_della_produzione": 9,
    "costi_per_materie": 10,
    "costi_per_servizi": 11,
    "costi_godimento_beni_terzi": 12,
    "costi_personale": 13,
    "ammortamenti": 14,
    "accantonamenti_per_rischi": 15,
    "oneri_diversi_di_gestione": 16,
    "ebit": 17,
    "proventi_finanziari": 18,
    "oneri_finanziari": 19,
    "utile_perdita_esercizio": 20,
    "dipendenti": 21,
}

# --- Stato Patrimoniale: chiave canonica -> riga del foglio Input ----------------
STATO_PATRIMONIALE_ROWS: dict[str, int] = {
    "immobilizzazioni": 27,
    "rimanenze": 28,
    "crediti": 29,
    "attivita_finanziarie": 30,
    "disponibilita_liquide": 31,
    "ratei_risconti_attivi": 32,
    "totale_attivo": 33,
    "totale_patrimonio_netto": 34,
    "fondi_rischi_oneri": 35,
    "tfr": 36,
    "totale_debiti": 37,
    "debiti_esigibili_breve": 38,
    "debiti_esigibili_oltre": 39,
    "totale_debiti_finanziari": 40,
    "debiti_finanziari_breve": 41,
    "debiti_finanziari_oltre": 42,
    "ratei_risconti_passivi": 43,
    "debiti_verso_fornitori": 44,
    "crediti_verso_clienti": 45,
}

# --- Metadati: chiave canonica -> cella assoluta del foglio Input ----------------
META_CELLS: dict[str, str] = {
    "nome_azienda": "B1",
    "anno": "B2",
    "tipologia": "C2",
    "ateco": "B46",
    "partita_iva": "B47",
    "forma_giuridica": "B48",
    "sede": "B49",
}

# Etichette leggibili (come compaiono nel foglio Input/Report), utili per i report
# di verifica e per la documentazione di mappatura.
LABELS: dict[str, str] = {
    "valore_della_produzione": "Valore della Produzione",
    "ricavi_di_vendita": "Ricavi di vendita",
    "costi_della_produzione": "Costi della Produzione",
    "costi_per_materie": "Costi per Materie",
    "costi_per_servizi": "Costi per Servizi",
    "costi_godimento_beni_terzi": "Costi per godimento beni di terzi",
    "costi_personale": "Costi Personale",
    "ammortamenti": "Ammortamenti",
    "accantonamenti_per_rischi": "Accantonamenti per rischi",
    "oneri_diversi_di_gestione": "Oneri diversi di gestione",
    "ebit": "EBIT",
    "proventi_finanziari": "Proventi Finanziari",
    "oneri_finanziari": "Oneri Finanziari",
    "utile_perdita_esercizio": "Utile (Perdita) dell'esercizio",
    "dipendenti": "Dipendenti",
    "immobilizzazioni": "Immobilizzazioni",
    "rimanenze": "Rimanenze",
    "crediti": "Crediti",
    "attivita_finanziarie": "Attivita' Finanziarie",
    "disponibilita_liquide": "Disponibilita' Liquide",
    "ratei_risconti_attivi": "Ratei e Risconti Attivi",
    "totale_attivo": "Totale Attivo",
    "totale_patrimonio_netto": "Totale Patrimonio Netto",
    "fondi_rischi_oneri": "Fondi per rischi e oneri",
    "tfr": "Trattamento di fine rapporto (TFR)",
    "totale_debiti": "Totale Debiti",
    "debiti_esigibili_breve": "Debiti esigibili a breve",
    "debiti_esigibili_oltre": "Debiti esigibili oltre l'esercizio successivo",
    "totale_debiti_finanziari": "Totale Debiti Finanziari",
    "debiti_finanziari_breve": "Debiti Finanziari esigibili a breve",
    "debiti_finanziari_oltre": "Debiti Finanziari esigibili oltre l'esercizio",
    "ratei_risconti_passivi": "Ratei e Risconti Passivi",
    "debiti_verso_fornitori": "Debiti verso fornitori",
    "crediti_verso_clienti": "Crediti verso clienti",
}

# Voci di importo (servono valori numerici). I metadati sono testuali.
CE_KEYS: tuple[str, ...] = tuple(CONTO_ECONOMICO_ROWS)
SP_KEYS: tuple[str, ...] = tuple(STATO_PATRIMONIALE_ROWS)

# Sheet name del modello.
INPUT_SHEET = "Input"
REPORT_SHEET = "Report"

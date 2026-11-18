"""Voci canoniche del bilancio riclassificato e loro etichette.

Sono le chiavi di ``normalized.json``: l'agente mappa le voci "sporche" del bilancio
su queste, l'engine calcola tutto il resto.
"""

from __future__ import annotations

LABELS: dict[str, str] = {
    # --- Conto Economico ---
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
    # --- Stato Patrimoniale ---
    "immobilizzazioni": "Immobilizzazioni",
    "rimanenze": "Rimanenze",
    "crediti": "Crediti",
    "attivita_finanziarie": "Attivita' Finanziarie",
    "disponibilita_liquide": "Disponibilita' Liquide",
    "ratei_risconti_attivi": "Ratei e Risconti Attivi",
    "totale_attivo": "Totale Attivo",
    "totale_patrimonio_netto": "Totale Patrimonio Netto",
    "capitale_sociale": "Capitale sociale",
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

CE_KEYS: tuple[str, ...] = tuple(LABELS)[: tuple(LABELS).index("dipendenti") + 1]
SP_KEYS: tuple[str, ...] = tuple(LABELS)[len(CE_KEYS) :]

# Metadati testuali dell'azienda (tutti facoltativi tranne nome e anno).
META_KEYS: tuple[str, ...] = ("nome_azienda", "anno", "ateco", "partita_iva", "forma_giuridica", "sede")

"""Voci canoniche del bilancio riclassificato (chiavi di ``normalized.json``).

L'agente mappa le voci "sporche" del bilancio su queste chiavi seguendo
``references/mapping.md``; l'engine calcola tutto il resto.
"""

from __future__ import annotations

CE_KEYS: tuple[str, ...] = (
    "valore_della_produzione",
    "ricavi_di_vendita",
    "costi_della_produzione",
    "costi_per_materie",
    "costi_per_servizi",
    "costi_godimento_beni_terzi",
    "costi_personale",
    "ammortamenti",
    "accantonamenti_per_rischi",
    "oneri_diversi_di_gestione",
    "ebit",
    "proventi_finanziari",
    "oneri_finanziari",
    "utile_perdita_esercizio",
    "dipendenti",
)

SP_KEYS: tuple[str, ...] = (
    "immobilizzazioni",
    "rimanenze",
    "crediti",
    "attivita_finanziarie",
    "disponibilita_liquide",
    "ratei_risconti_attivi",
    "totale_attivo",
    "totale_patrimonio_netto",
    "capitale_sociale",
    "fondi_rischi_oneri",
    "tfr",
    "totale_debiti",
    "debiti_esigibili_breve",
    "debiti_esigibili_oltre",
    "totale_debiti_finanziari",
    "debiti_finanziari_breve",
    "debiti_finanziari_oltre",
    "ratei_risconti_passivi",
    "debiti_verso_fornitori",
    "crediti_verso_clienti",
)

# Metadati testuali dell'azienda (tutti facoltativi tranne nome e anno).
META_KEYS: tuple[str, ...] = ("nome_azienda", "anno", "ateco", "partita_iva", "forma_giuridica", "sede")

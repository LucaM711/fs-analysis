"""Riclassificazione, composizione e indici di ogni esercizio.

Le formule sono quelle del vecchio modello Excel (foglio ``Report``, righe 61-142),
portate 1:1 e verificate dai test contro i valori che il modello produceva. Un
indice non calcolabile (denominatore zero, dato "n.d.", assenza di debiti
finanziari per la PFN) vale ``None``.

``compute`` restituisce il contenuto di ``metrics.json``: unica fonte dei numeri
per la conversazione, i grafici e il PDF.
"""

from __future__ import annotations

from typing import Any

from . import mapping, scoring
from .model import ND, CanonicalBalance

Values = dict[str, Any]


def _num(x: Any) -> float | None:
    return None if x is None or x == ND else float(x)


def div(a: Any, b: Any) -> float | None:
    a, b = _num(a), _num(b)
    if a is None or b is None or b == 0:
        return None
    return a / b


def var(new: Any, old: Any) -> float | None:
    """Variazione rispetto all'anno prima, sul valore assoluto del precedente.

    Il vecchio modello divideva per il valore con segno: da una perdita a un utile
    la "crescita" risultava negativa.
    """
    new, old = _num(new), _num(old)
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old)


def values(balance: CanonicalBalance, year: str) -> Values:
    """Voci di un esercizio piu' gli aggregati usati dal Report."""
    v: Values = {k: balance.ce(k, year) for k in mapping.CE_KEYS}
    v.update({k: balance.sp(k, year) for k in mapping.SP_KEYS})
    v["ebitda"] = v["ebit"] + v["ammortamenti"]
    v["debiti_non_finanziari"] = v["totale_debiti"] - v["totale_debiti_finanziari"]
    v["debiti_non_finanziari_breve"] = v["debiti_esigibili_breve"] - v["debiti_finanziari_breve"]
    v["debiti_non_finanziari_oltre"] = v["debiti_esigibili_oltre"] - v["debiti_finanziari_oltre"]
    v["attivo_corrente"] = (
        v["rimanenze"] + v["crediti"] + v["disponibilita_liquide"] + v["ratei_risconti_attivi"]
    )
    return v


def _days(amount: Any, base: Any) -> float | None:
    ratio = div(amount, base)
    return None if ratio is None else ratio * 365


def indices(v: Values) -> dict[str, float | None]:
    fin = v["totale_debiti_finanziari"]
    pfn = None if fin == 0 else v["disponibilita_liquide"] + v["attivita_finanziarie"] - fin
    out: dict[str, float | None] = {
        # Liquidita'
        "test_acido": div(
            v["crediti"] + v["disponibilita_liquide"] + v["ratei_risconti_attivi"],
            v["debiti_esigibili_breve"],
        ),
        "current_ratio": div(v["attivo_corrente"], v["debiti_esigibili_breve"]),
        # Indebitamento e sostenibilita' del debito
        "rapporto_indebitamento": div(
            v["debiti_non_finanziari"] if fin == 0 else fin, v["totale_patrimonio_netto"]
        ),
        "pfn": pfn,
        "pfn_ebitda": div(pfn, v["ebitda"]),
        "ims": div(v["totale_patrimonio_netto"], v["immobilizzazioni"]),
        "interest_coverage": div(v["ebitda"], v["oneri_finanziari"]),
        # Redditivita'
        "ros": div(v["ebit"], v["ricavi_di_vendita"]),
        "roe": div(v["utile_perdita_esercizio"], v["totale_patrimonio_netto"]),
        "roi": div(v["ebit"], v["totale_attivo"]),
        "ebitda_pct": div(v["ebitda"], v["valore_della_produzione"]),
        "ebit_pct": div(v["ebit"], v["valore_della_produzione"]),
        "risultato_pct": div(v["utile_perdita_esercizio"], v["valore_della_produzione"]),
        # Efficienza (incassi sul valore della produzione, pagamenti e magazzino sui costi)
        "asset_turnover": div(v["ricavi_di_vendita"], v["totale_attivo"]),
        "dso": _days(v["crediti_verso_clienti"], v["valore_della_produzione"]),
        "dpo": _days(v["debiti_verso_fornitori"], v["costi_della_produzione"]),
        "dio": _days(v["rimanenze"], v["costi_della_produzione"]),
    }
    dso, dio, dpo = out["dso"], out["dio"], out["dpo"]
    out["ccc"] = None if None in (dso, dio, dpo) else dso + dio - dpo  # type: ignore[operator]
    return out


_ON_ASSETS = (
    "immobilizzazioni",
    "rimanenze",
    "crediti",
    "attivita_finanziarie",
    "disponibilita_liquide",
    "ratei_risconti_attivi",
    "totale_patrimonio_netto",
    "fondi_rischi_oneri",
    "tfr",
    "debiti_non_finanziari",
    "totale_debiti_finanziari",
    "ratei_risconti_passivi",
)
_ON_COSTS = (
    "costi_per_materie",
    "costi_per_servizi",
    "costi_godimento_beni_terzi",
    "costi_personale",
    "ammortamenti",
    "accantonamenti_per_rischi",
    "oneri_diversi_di_gestione",
)


def composition(v: Values) -> dict[str, float | None]:
    """Peso delle voci: SP sul totale attivo, costi sui costi della produzione."""
    out = {f"{k}_su_attivo": div(v[k], v["totale_attivo"]) for k in _ON_ASSETS}
    out.update({f"{k}_su_costi": div(v[k], v["costi_della_produzione"]) for k in _ON_COSTS})
    return out


def compute(balance: CanonicalBalance) -> dict[str, Any]:
    """Tutte le metriche, un elemento per esercizio dal piu' recente."""
    anno = int(balance.meta["anno"])
    vals = [values(balance, y) for y in balance.years]
    idx = [indices(v) for v in vals]
    esercizi = []
    for k, (v, ind) in enumerate(zip(vals, idx)):
        prev = (vals[k + 1], idx[k + 1]) if k + 1 < len(vals) else None
        esercizi.append(
            {
                "anno": anno - k,
                "valori": v,
                "composizione": composition(v),
                "variazioni": {key: var(v[key], prev[0][key]) for key in v} if prev else None,
                "indici": ind,
                "punteggio": scoring.score(v, ind, prev),
                "altman": scoring.altman(v),
            }
        )
    return {
        "meta": {k: balance.meta.get(k) for k in mapping.META_KEYS},
        "anni": [e["anno"] for e in esercizi],
        "dimensione_impresa": scoring.firm_size(vals[0]),
        "esercizi": esercizi,
    }

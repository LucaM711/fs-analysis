"""Giudizio sintetico: punteggio complessivo, rating d'area, dimensione, Altman Z''.

Soglie e pesi vengono dal vecchio modello Excel (``Input!H56:Q72`` e ``D119:H139``)
e stanno qui in tabelle leggibili, cosi' si possono rivedere e cambiare in un posto
solo. Rispetto al vecchio modello cambia di proposito quanto segue:
- i pesi vengono applicati davvero (il vecchio "grade pesato" era una media semplice);
- nessuna penalita' per dimensione d'impresa e nessun fido commerciale;
- se non ci sono oneri finanziari la copertura degli interessi ha grade 1 (prima: #DIV/0!).
"""

from __future__ import annotations

import math
from typing import Any

# Indice -> (soglie per i grade 1..9, "alto" = meglio se piu' alto, peso).
# Grade = prima soglia superata (1 = migliore); nessuna soglia superata = 10.
INDEX_GRADES: dict[str, tuple[tuple[float, ...], str, float]] = {
    "test_acido": ((1.5, 1.3, 1.1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4), "alto", 0.10),
    "current_ratio": ((2, 1.8, 1.6, 1.4, 1.2, 1, 0.9, 0.8, 0.7), "alto", 0.10),
    "rapporto_indebitamento": ((0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.5, 1.8, 2), "basso", 0.10),
    "pfn_ebitda": ((2, 1.5, 1, 0.5, 0, -0.5, -1, -1.5, -2), "alto", 0.15),
    "ims": ((1.5, 1.3, 1.1, 1, 0.9, 0.8, 0.7, 0.6, 0.5), "alto", 0.05),
    "interest_coverage": ((10, 8, 6, 4, 2.5, 1.5, 1.2, 1, 0.8), "alto", 0.10),
    "ros": ((0.2, 0.13, 0.11, 0.09, 0.07, 0.05, 0.03, 0.01, 0), "alto", 0.10),
    "roe": ((0.25, 0.2, 0.15, 0.12, 0.1, 0.08, 0.06, 0.04, 0.02), "alto", 0.05),
    "roi": ((0.25, 0.2, 0.15, 0.12, 0.1, 0.08, 0.06, 0.04, 0.02), "alto", 0.05),
    "ebitda_pct": ((0.15, 0.13, 0.1, 0.08, 0.06, 0.04, 0.02, 0.01, 0), "alto", 0.10),
    "ebit_pct": ((0.13, 0.11, 0.1, 0.08, 0.06, 0.04, 0.02, 0, -0.02), "alto", 0.05),
    "risultato_pct": ((0.1, 0.08, 0.06, 0.04, 0.02, 0.01, 0, -0.03, -0.05), "alto", 0.025),
    "asset_turnover": ((2, 1.8, 1.6, 1.4, 1.2, 1, 0.9, 0.8, 0.7), "alto", 0.025),
}

# Componenti dei rating d'area -> (soglie per i punteggi 5,4,3,2; "alto" = meglio se piu' alto).
# Punteggio = 5 se valore <= prima soglia, poi 4, 3, 2; oltre l'ultima = 1 (1 = migliore).
# Per "basso" il confronto e' rovesciato (valore >= soglia).
AREA_COMPONENTS: dict[str, dict[str, tuple[tuple[float, ...], str]]] = {
    "reddituale": {
        "crescita_fatturato": ((-0.1, -0.05, 0, 0.05), "alto"),
        "crescita_ebit": ((-0.07, -0.03, 0, 0.03), "alto"),
        "crescita_peso_ebit": ((-0.05, -0.03, 0, 0.03), "alto"),
        "crescita_utile": ((-0.03, -0.01, 0, 0.03), "alto"),
        "crescita_peso_utile": ((-0.03, -0.01, 0, 0.02), "alto"),
        "ros": ((-0.05, 0, 0.05, 0.15), "alto"),
    },
    "finanziaria": {
        "peso_liquidita": ((0.05, 0.1, 0.2, 0.3), "alto"),
        "crescita_liquidita": ((-0.35, -0.15, 0, 0.15), "alto"),
        "crescita_ebitda": ((-0.1, -0.05, 0, 0.05), "alto"),
    },
    "patrimoniale": {
        "peso_patrimonio_netto": ((0.15, 0.25, 0.35, 0.45), "alto"),
        "rapporto_indebitamento": ((2, 1.5, 1, 0.6), "basso"),
    },
}

RATING_BY_SCORE = {1: "Eccellente", 2: "Positiva", 3: "Adeguata", 4: "Critica", 5: "Molto Critica"}

# Raccomandazione UE 2003/361: dipendenti < soglia e (fatturato <= X oppure attivo <= Y).
FIRM_SIZES = (
    ("Microimpresa", 10, 2_000_000, 2_000_000),
    ("Piccola impresa", 50, 10_000_000, 10_000_000),
    ("Media impresa", 250, 50_000_000, 43_000_000),
)

# Altman Z'' (1995, imprese non quotate e non manifatturiere) e zone.
ALTMAN_WEIGHTS = (6.56, 3.26, 6.72, 1.05)
ALTMAN_SAFE, ALTMAN_DISTRESS = 2.60, 1.10


def round_half_up(x: float) -> int:
    """Come ROUND(x; 0) di Excel per i valori positivi (Python arrotonda al pari)."""
    return math.floor(x + 0.5)


def _ladder(value: float, thresholds: tuple[float, ...], direction: str) -> int:
    for i, t in enumerate(thresholds):
        if (value > t) if direction == "alto" else (value < t):
            return i + 1
    return len(thresholds) + 1


def index_grade(name: str, v: dict[str, Any], ind: dict[str, Any]) -> int | None:
    """Grade 1..10 di un indice; ``None`` se non entra nel punteggio."""
    if name == "pfn_ebitda":
        pfn, ratio = ind["pfn"], ind["pfn_ebitda"]
        if pfn is None:  # nessun debito finanziario
            return None if v["oneri_finanziari"] == 0 else 5
        if ratio is None:  # EBITDA nullo
            return None
        if ratio > 0 and pfn > 0:  # cassa netta ed EBITDA positivo: rapporto non significativo
            return 3
        if ratio > 0 and pfn < 0:  # debito netto ed EBITDA negativo
            return 8
    if name == "interest_coverage" and v["oneri_finanziari"] == 0:
        return 1
    value = ind[name]
    if value is None:
        return None
    thresholds, direction, _ = INDEX_GRADES[name]
    return _ladder(value, thresholds, direction)


def _component_score(value: float, thresholds: tuple[float, ...], direction: str) -> int:
    for score, t in zip((5, 4, 3, 2), thresholds):
        if (value <= t) if direction == "alto" else (value >= t):
            return score
    return 1


def _components(v: dict[str, Any], ind: dict[str, Any], prev: tuple[dict, dict]) -> dict[str, Any]:
    from .metrics import div, var  # import locale: metrics importa questo modulo

    pv, pind = prev
    peso = None if ind["ebit_pct"] is None or pind["ebit_pct"] is None else ind["ebit_pct"] - pind["ebit_pct"]
    peso_utile = (
        None
        if ind["risultato_pct"] is None or pind["risultato_pct"] is None
        else ind["risultato_pct"] - pind["risultato_pct"]
    )
    return {
        "crescita_fatturato": var(v["valore_della_produzione"], pv["valore_della_produzione"]),
        "crescita_ebit": var(v["ebit"], pv["ebit"]),
        "crescita_peso_ebit": peso,
        "crescita_utile": var(v["utile_perdita_esercizio"], pv["utile_perdita_esercizio"]),
        "crescita_peso_utile": peso_utile,
        "ros": ind["ros"],
        "peso_liquidita": div(v["disponibilita_liquide"], v["totale_attivo"]),
        "crescita_liquidita": var(v["disponibilita_liquide"], pv["disponibilita_liquide"]),
        "crescita_ebitda": var(v["ebitda"], pv["ebitda"]),
        "peso_patrimonio_netto": div(v["totale_patrimonio_netto"], v["totale_attivo"]),
        "rapporto_indebitamento": ind["rapporto_indebitamento"],
    }


def areas(v: dict[str, Any], ind: dict[str, Any], prev: tuple[dict, dict]) -> dict[str, Any]:
    """Rating 1..5 per area. Serve l'esercizio precedente (le crescite)."""
    comp = _components(v, ind, prev)
    out: dict[str, Any] = {}
    for area, rules in AREA_COMPONENTS.items():
        scores = {k: _component_score(comp[k], th, d) for k, (th, d) in rules.items() if comp[k] is not None}
        if area == "finanziaria":
            cash = v["disponibilita_liquide"]
            scores["liquidita_oltre_debito_fin_breve"] = 3 if cash - v["debiti_finanziari_breve"] > 0 else 4
            scores["liquidita_oltre_debito_fin_totale"] = 2 if cash - v["totale_debiti_finanziari"] > 0 else 3
        score = round_half_up(sum(scores.values()) / len(scores)) if scores else None
        out[area] = {
            "punteggio": score,
            "rating": RATING_BY_SCORE.get(score) if score else None,
            "componenti": {k: {"valore": comp.get(k), "punteggio": s} for k, s in scores.items()},
        }
    return out


def score(v: dict[str, Any], ind: dict[str, Any], prev: tuple[dict, dict] | None) -> dict[str, Any]:
    grades = {n: g for n in INDEX_GRADES if (g := index_grade(n, v, ind)) is not None}
    weight = sum(INDEX_GRADES[n][2] for n in grades)
    weighted = sum(g * INDEX_GRADES[n][2] for n, g in grades.items()) / weight if weight else None
    return {
        "indici": {n: {"grade": grades.get(n), "peso": INDEX_GRADES[n][2]} for n in INDEX_GRADES},
        "complessivo": weighted,
        "grade": round_half_up(weighted) if weighted is not None else None,
        "aree": areas(v, ind, prev) if prev else None,
    }


def firm_size(v: dict[str, Any]) -> str:
    for name, staff, turnover, assets in FIRM_SIZES:
        if v["dipendenti"] < staff and (v["ricavi_di_vendita"] <= turnover or v["totale_attivo"] <= assets):
            return name
    return "Grande impresa"


def altman(v: dict[str, Any]) -> dict[str, Any] | None:
    """Z'' = 6.56 X1 + 3.26 X2 + 6.72 X3 + 1.05 X4.

    X2 usa PN - capitale sociale come stima degli utili non distribuiti (include le
    riserve non di utili, come sovrapprezzo e rivalutazione).
    """
    ta, pn = v["totale_attivo"], v["totale_patrimonio_netto"]
    if not ta or ta == pn:
        return None
    x = (
        (v["attivo_corrente"] - v["debiti_esigibili_breve"]) / ta,
        (pn - v["capitale_sociale"]) / ta,
        v["ebit"] / ta,
        pn / (ta - pn),
    )
    z = sum(w * xi for w, xi in zip(ALTMAN_WEIGHTS, x))
    zone = "sicurezza" if z > ALTMAN_SAFE else "grigia" if z >= ALTMAN_DISTRESS else "rischio"
    return {"x1": x[0], "x2": x[1], "x3": x[2], "x4": x[3], "z": z, "zona": zone}

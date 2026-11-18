"""Regole del punteggio: soglie, casi speciali, pesi, Altman Z'', dimensione UE."""

from __future__ import annotations

import pytest
from fsa import metrics, scoring
from fsa.model import CanonicalBalance


@pytest.fixture
def last(sample_data):
    m = metrics.compute(CanonicalBalance.from_dict(sample_data))
    return m["esercizi"][0]


@pytest.mark.parametrize(
    ("value", "grade"),
    [(1.51, 1), (1.5, 2), (1.0, 4), (0.4, 10), (0.39, 10)],  # "alto": soglia superata strettamente
)
def test_ladder_high_is_better(value, grade):
    assert scoring._ladder(value, scoring.INDEX_GRADES["test_acido"][0], "alto") == grade


def test_ladder_low_is_better():
    th = scoring.INDEX_GRADES["rapporto_indebitamento"][0]
    assert scoring._ladder(0.1, th, "basso") == 1
    assert scoring._ladder(2.5, th, "basso") == 10


def test_weights_sum_to_one():
    assert sum(w for _, _, w in scoring.INDEX_GRADES.values()) == pytest.approx(1.0)


def test_weighted_score_uses_weights(last):
    p = last["punteggio"]
    grades = {k: g["grade"] for k, g in p["indici"].items()}
    expected = sum(grades[k] * scoring.INDEX_GRADES[k][2] for k in grades)
    assert p["complessivo"] == pytest.approx(expected)  # tutti calcolabili: pesi pieni
    assert p["grade"] == scoring.round_half_up(expected)


def test_missing_index_spreads_its_weight(last):
    v, ind = last["valori"], dict(last["indici"])
    ind["ims"] = None
    p = scoring.score(v, ind, None)
    used = {k: g["grade"] for k, g in p["indici"].items() if g["grade"] is not None}
    assert "ims" not in used
    w = sum(scoring.INDEX_GRADES[k][2] for k in used)
    assert p["complessivo"] == pytest.approx(sum(used[k] * scoring.INDEX_GRADES[k][2] for k in used) / w)


def test_no_financial_charges_gives_best_coverage(last):
    v = {**last["valori"], "oneri_finanziari": 0}
    assert scoring.index_grade("interest_coverage", v, last["indici"]) == 1


def test_pfn_ebitda_special_cases(last):
    v, ind = last["valori"], last["indici"]
    no_debt = {**ind, "pfn": None, "pfn_ebitda": None}
    assert scoring.index_grade("pfn_ebitda", {**v, "oneri_finanziari": 0}, no_debt) is None
    assert scoring.index_grade("pfn_ebitda", v, no_debt) == 5
    assert scoring.index_grade("pfn_ebitda", v, {**ind, "pfn": 100.0, "pfn_ebitda": 0.5}) == 3
    assert scoring.index_grade("pfn_ebitda", v, {**ind, "pfn": -100.0, "pfn_ebitda": 0.5}) == 8


@pytest.mark.parametrize(
    ("z", "zone"), [(2.61, "sicurezza"), (2.6, "grigia"), (1.1, "grigia"), (1.09, "rischio")]
)
def test_altman_zones(last, z, zone):
    v = dict(last["valori"])
    a = scoring.altman(v)
    # sposta solo X3 (EBIT/attivo) per ottenere lo Z'' voluto
    v["ebit"] += (z - a["z"]) / 6.72 * v["totale_attivo"]
    assert scoring.altman(v)["zona"] == zone


def test_altman_formula(last):
    a = last["altman"]
    assert a["z"] == pytest.approx(6.56 * a["x1"] + 3.26 * a["x2"] + 6.72 * a["x3"] + 1.05 * a["x4"])
    v = last["valori"]
    assert a["x2"] == pytest.approx(
        (v["totale_patrimonio_netto"] - v["capitale_sociale"]) / v["totale_attivo"]
    )


@pytest.mark.parametrize(
    ("staff", "turnover", "assets", "size"),
    [
        (9, 1_900_000, 5_000_000, "Microimpresa"),
        (9, 3_000_000, 3_000_000, "Piccola impresa"),
        (49, 12_000_000, 9_000_000, "Piccola impresa"),
        (60, 40_000_000, 60_000_000, "Media impresa"),
        (250, 1_000_000, 1_000_000, "Grande impresa"),
    ],
)
def test_firm_size_eu(staff, turnover, assets, size):
    assert (
        scoring.firm_size({"dipendenti": staff, "ricavi_di_vendita": turnover, "totale_attivo": assets})
        == size
    )

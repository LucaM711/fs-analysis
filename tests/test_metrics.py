"""Indici e punteggi: parita' con il vecchio modello Excel e casi limite."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fsa import metrics
from fsa.model import CanonicalBalance

from tests.conftest import with_years

# Valori prodotti dal vecchio template Excel (LibreOffice) su 6 casi, compresi:
# nessun debito finanziario, perdita con EBITDA negativo, cassa netta, dati "n.d.".
GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "expected_template.json").read_text("utf-8"))

VALUE_ROWS = {
    "82": "debiti_non_finanziari",
    "83": "debiti_non_finanziari_breve",
    "84": "debiti_non_finanziari_oltre",
}
INDEX_ROWS = {
    "116": "ebit_pct", "126": "test_acido", "127": "current_ratio", "129": "rapporto_indebitamento",
    "130": "pfn", "131": "pfn_ebitda", "133": "ros", "134": "roe", "135": "roi", "136": "ebitda",
    "138": "asset_turnover", "139": "dso", "140": "dpo", "141": "dio", "142": "ccc",
}  # fmt: skip
GRADE_ROWS = {
    "57": "test_acido", "58": "current_ratio", "60": "rapporto_indebitamento", "61": "pfn_ebitda",
    "62": "ims", "63": "interest_coverage", "65": "ros", "66": "roe", "67": "roi",
    "68": "ebitda_pct", "69": "ebit_pct", "70": "risultato_pct", "72": "asset_turnover",
}  # fmt: skip
AREA_ROWS = {
    "121": ("reddituale", "crescita_fatturato"), "122": ("reddituale", "crescita_ebit"),
    "123": ("reddituale", "crescita_peso_ebit"), "124": ("reddituale", "crescita_utile"),
    "125": ("reddituale", "crescita_peso_utile"), "126": ("reddituale", "ros"),
    "130": ("finanziaria", "peso_liquidita"), "131": ("finanziaria", "crescita_liquidita"),
    "132": ("finanziaria", "liquidita_oltre_debito_fin_breve"),
    "133": ("finanziaria", "liquidita_oltre_debito_fin_totale"),
    "134": ("finanziaria", "crescita_ebitda"),
    "138": ("patrimoniale", "peso_patrimonio_netto"), "139": ("patrimoniale", "rapporto_indebitamento"),
}  # fmt: skip


def _missing(x):
    return x in (None, "Non Calcolabile", "", "0")


def _computed(case: str) -> dict:
    data = copy.deepcopy(GOLDEN[case]["balance"])
    data["stato_patrimoniale"]["capitale_sociale"] = {"y0": 1, "y1": 1}
    return metrics.compute(CanonicalBalance.from_dict(data))


@pytest.mark.parametrize("case", sorted(GOLDEN))
def test_indices_match_template(case):
    m, expected = _computed(case), GOLDEN[case]["report"]
    for i, y in enumerate(("y0", "y1")):
        e = m["esercizi"][i]
        for row, key in {**VALUE_ROWS, **INDEX_ROWS}.items():
            want, got = expected[row][y], e["valori"].get(key, e["indici"].get(key))
            if _missing(want):
                assert got is None, (case, y, key)
            else:
                assert got == pytest.approx(want), (case, y, key)


@pytest.mark.parametrize("case", sorted(GOLDEN))
def test_grades_and_area_scores_match_template(case):
    p = _computed(case)["esercizi"][0]["punteggio"]
    for row, key in GRADE_ROWS.items():
        want = GOLDEN[case]["index_grades"][row]["grade"]
        if str(want).startswith("#"):  # errore del vecchio modello (#DIV/0!): vedi test_scoring
            continue
        assert p["indici"][key]["grade"] == (None if _missing(want) else want), (case, key)
    for row, (area, key) in AREA_ROWS.items():
        assert p["aree"][area]["componenti"][key]["punteggio"] == GOLDEN[case]["area_scores"][row]["score"]


def test_one_entry_per_year_newest_first(sample_data):
    m = metrics.compute(CanonicalBalance.from_dict(with_years(sample_data, 4)))
    assert m["anni"] == [2024, 2023, 2022, 2021]
    oldest = m["esercizi"][-1]
    # l'esercizio piu' vecchio non ha un anno prima: niente variazioni ne' rating d'area
    assert oldest["variazioni"] is None and oldest["punteggio"]["aree"] is None
    assert oldest["punteggio"]["complessivo"] is not None and oldest["altman"] is not None


def test_growth_from_loss_to_profit_is_positive():
    assert metrics.var(50, -100) == pytest.approx(1.5)
    assert metrics.var(10, 0) is None

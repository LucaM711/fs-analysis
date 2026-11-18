"""Serie storica costruita dalle letture delle coppie di esercizi."""

from __future__ import annotations

from fsa.metrics import storico


def _window(anno: int, ebit0: float, ebit1: float) -> dict:
    return {
        "meta": {"anno": anno},
        "economico": {"ebit": {"y0": ebit0, "y1": ebit1}, "ebit_var": ebit0 / ebit1 - 1},
        "finanziario_patrimoniale": {"pfn": {"y0": -ebit0, "y1": -ebit1}},
        "grade_fido": {"grade_finale": anno - 2020},
        "ratings": {"reddituale": "Adeguata"},
    }


def test_storico_one_entry_per_year_newest_first():
    s = storico([_window(2024, 300, 200), _window(2023, 200, 100)])
    assert [e["anno"] for e in s] == [2024, 2023, 2022]
    assert [e["economico"]["ebit"] for e in s] == [300, 200, 100]
    assert s[0]["economico"]["ebit_var"] == 0.5
    assert s[1]["grade_fido"]["grade_finale"] == 3
    # l'anno piu' vecchio non ha esercizio precedente: niente variazioni ne' grade
    assert "ebit_var" not in s[2]["economico"] and "grade_fido" not in s[2]
    assert s[2]["finanziario_patrimoniale"]["pfn"] == -100


def test_storico_two_years():
    s = storico([_window(2024, 300, 200)])
    assert [e["anno"] for e in s] == [2024, 2023]

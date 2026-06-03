"""Iniezione testi/rating e calcolo dei budget di capienza."""

from __future__ import annotations

from openpyxl import load_workbook

from fsa import narrative
from fsa.model import CanonicalBalance
from fsa.populate import build_populated


def _wb(tmp_path, template_path, sample_data):
    bal = CanonicalBalance.from_dict(sample_data)
    out = build_populated(template_path, bal, tmp_path / "out.xlsx")
    return load_workbook(out, data_only=False)


def test_budgets_four_blocks(tmp_path, template_path, sample_data):
    wb = _wb(tmp_path, template_path, sample_data)
    b = narrative.budgets(wb)
    assert set(b) == {"economico", "finanziario_patrimoniale", "sintesi", "grade_fido"}
    for block in b.values():
        assert block["max_chars"] > 0 and block["lines"] > 0


def test_inject_texts_and_ratings(tmp_path, template_path, sample_data):
    wb = _wb(tmp_path, template_path, sample_data)
    warnings = narrative.inject(
        wb,
        texts={"economico": "Testo breve.", "sintesi": "Sintesi breve."},
        ratings={"reddituale": "Positiva", "patrimoniale": "Adeguata"},
    )
    rep = wb[narrative.mapping.REPORT_SHEET]
    assert rep["A34"].value == "Testo breve."
    assert rep["A46"].value == "Sintesi breve."
    assert rep["B11"].value == "Positiva"
    assert rep["B17"].value == "Adeguata"
    assert warnings == []


def test_overflow_warning(tmp_path, template_path, sample_data):
    wb = _wb(tmp_path, template_path, sample_data)
    warnings = narrative.inject(wb, texts={"finanziario_patrimoniale": "X" * 5000})
    assert any("finanziario_patrimoniale" in w for w in warnings)


def test_unknown_block_raises(tmp_path, template_path, sample_data):
    wb = _wb(tmp_path, template_path, sample_data)
    try:
        narrative.inject(wb, texts={"non_esiste": "y"})
    except KeyError:
        return
    raise AssertionError("atteso KeyError per blocco sconosciuto")

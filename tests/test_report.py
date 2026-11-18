"""PDF: 4 pagine, testi misurati, nessun riferimento a marchi."""

from __future__ import annotations

import copy

import pdfplumber
from fsa import metrics, report
from fsa.model import CanonicalBalance

from tests.conftest import with_years

TEXTS = {block: f"Analisi {block}." for block in report.TEXT_BLOCKS}


def _metrics(sample_data, years=4):
    return metrics.compute(CanonicalBalance.from_dict(with_years(sample_data, years)))


def test_pdf_has_four_pages_and_texts(tmp_path, sample_data):
    pdf = tmp_path / "r.pdf"
    assert report.render(_metrics(sample_data), TEXTS, pdf) == []
    with pdfplumber.open(pdf) as doc:
        assert len(doc.pages) == 4
        text = "\n".join(p.extract_text() or "" for p in doc.pages)
    assert "Acme S.r.l." in text and "Analisi sintesi." in text and "2021" in text
    assert "fido" not in text.lower()  # niente logica di credito commerciale


def test_symbols_survive_in_pdf(tmp_path, sample_data):
    text = "ROE ≥ 10% → buono, ≈ 2 volte; perché è già così: “citazione” – fine."
    pdf = tmp_path / "r.pdf"
    report.render(_metrics(sample_data, 2), {"economico": text}, pdf)
    with pdfplumber.open(pdf) as doc:
        extracted = " ".join((doc.pages[0].extract_text() or "").split())
    assert "ROE ≥ 10% → buono, ≈ 2 volte" in extracted


def test_text_too_long_is_reported(tmp_path, sample_data):
    long = "parola " * 2000
    warnings = report.render(_metrics(sample_data, 2), {**TEXTS, "valutazione": long}, tmp_path / "r.pdf")
    assert len(warnings) == 1 and "valutazione" in warnings[0]
    assert not report.fits("valutazione", long) and report.fits("valutazione", "breve")


def test_budgets_cover_every_block():
    b = report.budgets()
    assert set(b) == set(report.TEXT_BLOCKS)
    assert all(v["max_chars"] > 300 and v["lines"] > 10 for v in b.values())


def test_italian_formatting():
    assert report.eur(1234567.4) == "1.234.567 €"
    assert report.pct(0.1234) == "12,3%"
    assert report.change(-0.05) == "−5,0%"
    assert report.eur_short(1_950_000) == "1,95 mln €"


def test_large_amounts_switch_tables_to_thousands(sample_data):
    small = _metrics(sample_data, 2)
    assert report._money_unit(small["esercizi"], report.SP_ROWS) == (1.0, "€")
    big = copy.deepcopy(small)
    big["esercizi"][0]["valori"]["totale_attivo"] = 1_268_153_000
    assert report._money_unit(big["esercizi"], report.SP_ROWS) == (1000.0, "migliaia di €")
    body, _, _ = report._year_table(big, report.SP_ROWS, with_var=True)
    assert body[0][0] == "Voce (migliaia di €)"
    assert body[7][:2] == ["Totale attivo", "1.268.153"]

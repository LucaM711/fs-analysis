"""PDF: 4 pagine, testi misurati, nessun riferimento a marchi."""

from __future__ import annotations

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

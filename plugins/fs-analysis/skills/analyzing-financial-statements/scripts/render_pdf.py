#!/usr/bin/env python3
"""Inietta le analisi testuali e esporta il foglio ``Report`` in PDF.

Uso:
    python render_pdf.py REPORT_EDITABILE.xlsx [--analysis analysis.json] [--out report.pdf]

Pipeline:
    1. (se --analysis) scrive i 4 blocchi testuali nelle celle del Report
       (l'xlsx editabile viene aggiornato cosi' l'operatore vede anche il testo)
    2. ricalcola con LibreOffice (rating-bar, fido, B14, ...)
    3. genera la copia di rendering (solo Report, formule -> valori)
    4. esporta in PDF a layout fisso

analysis.json: {"economico": "...", "finanziario_patrimoniale": "...",
                "sintesi": "...", "grade_fido": "..."}
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsa import flatten, narrative, soffice  # noqa: E402

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def main() -> int:
    ap = argparse.ArgumentParser(description="Inietta i testi ed esporta il Report in PDF.")
    ap.add_argument("xlsx", type=Path, help="workbook editabile prodotto da build_report.py")
    ap.add_argument("--analysis", type=Path, help="analysis.json con i 4 blocchi testuali")
    ap.add_argument("--out", type=Path, help="path del PDF (default: accanto all'xlsx)")
    ap.add_argument("--no-fonts", action="store_true", help="non installare i font bundlati")
    args = ap.parse_args()

    if not args.xlsx.exists():
        print(f"File non trovato: {args.xlsx}", file=sys.stderr)
        return 1

    pdf_path = args.out or args.xlsx.with_suffix(".pdf")

    if not args.no_fonts:
        copied = soffice.ensure_fonts(FONTS_DIR)
        if copied:
            print(f"Font installati per il rendering: {copied}")

    # --- 1. iniezione testi --------------------------------------------------------
    if args.analysis:
        from openpyxl import load_workbook

        texts = json.loads(args.analysis.read_text(encoding="utf-8"))
        wb = load_workbook(filename=str(args.xlsx), data_only=False)
        warnings = narrative.inject(wb, texts=texts)
        wb.save(str(args.xlsx))
        for w in warnings:
            print(f"[avviso capienza] {w}", file=sys.stderr)

    # --- 2. ricalcolo --------------------------------------------------------------
    try:
        soffice.recalc(args.xlsx)
        # --- 3. flatten (solo Report, valori statici) ------------------------------
        with tempfile.TemporaryDirectory() as tmp:
            render = flatten.flatten_report(args.xlsx, Path(tmp) / "render.xlsx")
            # --- 4. PDF ------------------------------------------------------------
            soffice.to_pdf(render, pdf_path)
    except soffice.RenderError as exc:
        print(f"[render] {exc}", file=sys.stderr)
        return 3

    print(f"PDF generato: {pdf_path}")
    print(f"XLSX editabile (con testi): {args.xlsx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

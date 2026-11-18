#!/usr/bin/env python3
"""Report PDF a layout fisso da ``metrics.json`` + le 4 analisi testuali.

Uso:
    python render_pdf.py fsa-output/metrics.json --analysis analysis.json [--out report.pdf]

analysis.json: {"economico": "...", "finanziario_patrimoniale": "...",
                "sintesi": "...", "valutazione": "..."}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsa import report  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera il report PDF.")
    ap.add_argument("metrics", type=Path, help="metrics.json prodotto da analyze.py")
    ap.add_argument("--analysis", type=Path, required=True, help="analysis.json con i 4 blocchi testuali")
    ap.add_argument("--out", type=Path, help="path del PDF (default: accanto a metrics.json)")
    args = ap.parse_args()

    for path in (args.metrics, args.analysis):
        if not path.exists():
            print(f"File non trovato: {path}", file=sys.stderr)
            return 1
    m = json.loads(args.metrics.read_text(encoding="utf-8"))
    try:
        texts = json.loads(args.analysis.read_text(encoding="utf-8"))
        if not isinstance(texts, dict):
            raise ValueError("deve contenere un oggetto JSON con i 4 blocchi.")
        unknown = set(texts) - set(report.TEXT_BLOCKS)
        if unknown:
            raise ValueError(f"blocchi sconosciuti {sorted(unknown)}. Ammessi: {list(report.TEXT_BLOCKS)}")
    except ValueError as exc:  # JSONDecodeError e' un ValueError
        print(f"[analysis.json NON valido] {exc}", file=sys.stderr)
        return 1

    pdf = args.out or args.metrics.parent / report.default_filename(m["meta"])
    for w in report.render(m, texts, pdf):
        print(f"[avviso capienza] {w}", file=sys.stderr)
    print(f"PDF generato: {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

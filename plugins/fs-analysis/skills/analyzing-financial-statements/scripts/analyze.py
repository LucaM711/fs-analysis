#!/usr/bin/env python3
"""Da ``normalized.json`` a quadratura + metriche + grafici, pronti per la chat.

Uso:
    python analyze.py normalized.json [--out-dir fsa-output] [--reconcile-tolerance 0.05]

Pipeline:
    1. carica e valida normalized.json
    2. VERIFICA la quadratura al centesimo di ogni esercizio
       -> se non quadra: dettaglio in verification.json ed esce con codice 2
    3. calcola riclassificazione, indici, punteggio e Altman Z'' di ogni esercizio
    4. scrive metrics.json (+ text_budgets per il PDF) e i grafici PNG in charts/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsa import charts, metrics, report, verify  # noqa: E402
from fsa.model import CanonicalBalance, ValidationError  # noqa: E402


def _fmt(x, f) -> str:
    return "n.d." if x is None else f(x)


def main() -> int:
    ap = argparse.ArgumentParser(description="Quadratura, indici e punteggio di un bilancio.")
    ap.add_argument("normalized", type=Path, help="normalized.json prodotto dall'agente")
    ap.add_argument("--out-dir", type=Path, default=Path("fsa-output"))
    ap.add_argument(
        "--reconcile-tolerance",
        type=float,
        default=verify.DEFAULT_RECONCILE_EUR,
        help="residuo (EUR) di arrotondamento assorbito automaticamente",
    )
    args = ap.parse_args()

    try:
        balance = CanonicalBalance.load(args.normalized)
    except ValidationError as exc:
        print(f"[normalized.json NON valido] {exc}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    result = verify.verify(balance, reconcile_eur=args.reconcile_tolerance)
    (args.out_dir / "verification.json").write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(result.summary())
    if not result.ok:
        print(
            "\nLa quadratura al centesimo NON e' soddisfatta: rivedere la mappatura "
            "delle voci (vedi verification.json) e rigenerare normalized.json.",
            file=sys.stderr,
        )
        return 2

    m = metrics.compute(balance)
    m["text_budgets"] = report.budgets()
    out = args.out_dir / "metrics.json"
    out.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    paths = charts.render_all(m, args.out_dir / "charts")

    last, p = m["esercizi"][0], m["esercizi"][0]["punteggio"]
    aree = p["aree"] or {}
    z = last["altman"]
    print(
        f"\n== SINTESI {m['meta'].get('nome_azienda')} ({m['anni'][0]}; esercizi {m['anni'][-1]}..{m['anni'][0]}) =="
    )
    print(f"  Dimensione (UE)      : {m['dimensione_impresa']}")
    print(f"  Punteggio (1-10)     : {_fmt(p['complessivo'], lambda x: f'{x:.2f}')}  grade {p['grade']}")
    for area in ("reddituale", "finanziaria", "patrimoniale"):
        print(f"  Rating {area:13s} : {(aree.get(area) or {}).get('rating')}")
    print(f"  Altman Z''           : {_fmt(z and z['z'], lambda x: f'{x:.2f}')}  ({z and z['zona']})")
    print(f"\nmetrics.json : {out}")
    print(f"grafici PNG  : {', '.join(str(p) for p in paths.values())}")
    print(
        "\nProssimo passo: presentare in chat quadratura, sintesi, insight e grafici "
        "(references/conversation.md). Per il PDF: scrivere analysis.json con "
        "{economico, finanziario_patrimoniale, sintesi, valutazione} e lanciare\n"
        f"  python render_pdf.py {out} --analysis analysis.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

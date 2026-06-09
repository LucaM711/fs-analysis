#!/usr/bin/env python3
"""Da ``normalized.json`` al workbook popolato + verifica quadratura + metriche.

Uso:
    python build_report.py normalized.json [--out-dir DIR] [--template T.xlsx]
                           [--reconcile-tolerance 0.05] [--no-recalc]

Pipeline:
    1. carica e valida normalized.json
    2. VERIFICA la quadratura al centesimo (Attivo/Passivo, replica di B52/B53)
       -> se non quadra: stampa il dettaglio ed esce con codice 2 (l'operatore
          corregge la mappatura). Piccoli residui di arrotondamento sono assorbiti.
    3. popola il foglio Input del modello e salva l'xlsx editabile
    4. ricalcola con LibreOffice e LEGGE indici/grade/fido (fonte di verita': il modello)
    5. scrive i rating Reddituale/Patrimoniale (B11/B17) e salva
    6. emette metrics.json + verification.json e stampa il riepilogo per l'agente
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fsa import metrics as metrics_mod  # noqa: E402
from fsa import narrative, populate, soffice, verify  # noqa: E402
from fsa.model import CanonicalBalance, ValidationError  # noqa: E402

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.xlsx"


def _slug(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", str(text or "azienda")).strip("_").lower()
    return s or "azienda"


def main() -> int:
    ap = argparse.ArgumentParser(description="Popola il modello e verifica la quadratura.")
    ap.add_argument("normalized", type=Path, help="normalized.json prodotto dall'agente")
    ap.add_argument("--out-dir", type=Path, default=Path("fsa-output"))
    ap.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    ap.add_argument(
        "--reconcile-tolerance",
        type=float,
        default=verify.DEFAULT_RECONCILE_EUR,
        help="residuo (EUR) di arrotondamento assorbito automaticamente",
    )
    ap.add_argument(
        "--no-recalc", action="store_true", help="salta LibreOffice (solo popolamento+verifica; per test)"
    )
    args = ap.parse_args()

    try:
        balance = CanonicalBalance.load(args.normalized)
    except ValidationError as exc:
        print(f"[normalized.json NON valido] {exc}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(balance.meta.get("nome_azienda"))
    anno = balance.meta.get("anno")
    editable = args.out_dir / f"{slug}_{anno}_report.xlsx"

    # --- 2. verifica quadratura ----------------------------------------------------
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

    # --- 3. popolamento ------------------------------------------------------------
    populate.build_populated(args.template, balance, editable)
    print(f"\nWorkbook popolato: {editable}")

    if args.no_recalc:
        print("(--no-recalc) Salto ricalcolo e lettura metriche.")
        return 0

    # --- 4. ricalcolo + lettura metriche ------------------------------------------
    try:
        soffice.recalc(editable)
    except soffice.RenderError as exc:
        print(f"[ricalcolo] {exc}", file=sys.stderr)
        return 3
    metrics = metrics_mod.read_back(editable)

    # --- 5. rating B11/B14/B17 (coerenti con i sotto-grade calcolati) -----------------
    from openpyxl import load_workbook

    ratings = {
        "reddituale": metrics["ratings"].get("reddituale"),
        "finanziaria": metrics["ratings"].get("finanziaria"),
        "patrimoniale": metrics["ratings"].get("patrimoniale"),
    }
    wb = load_workbook(filename=str(editable), data_only=False)
    narrative.inject(wb, ratings=ratings)
    budgets = narrative.budgets(wb)
    wb.save(str(editable))

    # --- 6. output -----------------------------------------------------------------
    metrics["text_budgets"] = budgets
    (args.out_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    gf = metrics["grade_fido"]
    print("\n== METRICHE CHIAVE (fonte: modello ricalcolato) ==")
    print(f"  Dimensione impresa : {gf.get('dimensione_impresa')}")
    print(f"  Grade (pesato)     : {gf.get('grade_pesato')}")
    print(f"  Grade finale       : {gf.get('grade_finale')}")
    print(f"  Fido massimo       : {gf.get('fido_massimo')}  ({gf.get('fido_label')})")
    print(f"  Rating Reddituale  : {ratings['reddituale']}")
    print(f"  Rating Finanziaria : {metrics['ratings'].get('finanziaria')}")
    print(f"  Rating Patrimoniale: {ratings['patrimoniale']}")
    print("\n== BUDGET TESTI (caratteri massimi per blocco) ==")
    for block, b in budgets.items():
        print(f"  {block:28s}: max ~{b['max_chars']} char, {b['lines']} righe")
    print(f"\nmetrics.json: {args.out_dir / 'metrics.json'}")
    print(
        "\nProssimo passo: scrivere le 4 analisi (rispettando i budget) in analysis.json "
        "con chiavi {economico, finanziario_patrimoniale, sintesi, grade_fido}, poi:\n"
        f"  python render_pdf.py {editable} --analysis analysis.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Comandi end-to-end: ingest -> analyze -> render_pdf."""

from __future__ import annotations

import json
import subprocess
import sys

from tests.conftest import ENGINE_SCRIPTS, with_years


def _run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def test_analyze_then_render(tmp_path, sample_data):
    src = tmp_path / "n.json"
    src.write_text(json.dumps(with_years(sample_data, 4)))
    out = tmp_path / "out"
    r = _run(ENGINE_SCRIPTS / "analyze.py", src, "--out-dir", out)
    assert r.returncode == 0, r.stderr
    m = json.loads((out / "metrics.json").read_text())
    assert m["anni"] == [2024, 2023, 2022, 2021] and "text_budgets" in m
    assert sorted(p.name for p in (out / "charts").iterdir()) == [
        "andamento_economico.png", "redditivita.png", "solidita.png", "struttura_patrimoniale.png",
    ]  # fmt: skip

    analysis = tmp_path / "analysis.json"
    analysis.write_text(json.dumps({"economico": "x", "sintesi": "y"}))
    r = _run(ENGINE_SCRIPTS / "render_pdf.py", out / "metrics.json", "--analysis", analysis)
    assert r.returncode == 0, r.stderr
    assert (out / "acme_s_r_l_2024_report.pdf").stat().st_size > 10_000

    for bad, key in (({"grade_fido": "vecchio blocco"}, "grade_fido"), ({"sintesi": ["a", "b"]}, "sintesi")):
        analysis.write_text(json.dumps(bad))
        r = _run(ENGINE_SCRIPTS / "render_pdf.py", out / "metrics.json", "--analysis", analysis)
        assert r.returncode == 1 and key in r.stderr and "Traceback" not in r.stderr


def test_unbalanced_exits_2(tmp_path, sample_data):
    sample_data["stato_patrimoniale"]["crediti"]["y0"] += 1000
    src = tmp_path / "n.json"
    src.write_text(json.dumps(sample_data))
    r = _run(ENGINE_SCRIPTS / "analyze.py", src, "--out-dir", tmp_path / "out")
    assert r.returncode == 2 and not (tmp_path / "out" / "metrics.json").exists()


def test_skeleton_has_every_key(sample_data):
    from fsa import model

    s = model.skeleton(2024, esercizi=3)
    assert set(s["stato_patrimoniale"]) == set(sample_data["stato_patrimoniale"])
    assert set(s["conto_economico"]) == set(sample_data["conto_economico"])
    assert s["conto_economico"]["ebit"] == {"y0": None, "y1": None, "y2": None}

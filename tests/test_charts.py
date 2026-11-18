"""Grafici: dati corretti anche nei casi limite."""

from __future__ import annotations

import copy

import matplotlib.pyplot as plt
from fsa import charts, metrics
from fsa.model import CanonicalBalance

from tests.conftest import with_years


def test_negative_equity_is_drawn_below_zero(sample_data):
    data = copy.deepcopy(sample_data)
    sp = data["stato_patrimoniale"]
    sp["totale_patrimonio_netto"]["y0"] = -100000  # patrimonio netto negativo...
    sp["totale_debiti"]["y0"] += 500000  # ...compensato da piu' debiti a breve
    sp["debiti_esigibili_breve"]["y0"] += 500000
    m = metrics.compute(CanonicalBalance.from_dict(data))
    fig, ax = plt.subplots()
    charts.struttura_patrimoniale(m, ax)
    low, high = ax.get_ylim()
    plt.close(fig)
    pn_share = -100000 / sp["totale_attivo"]["y0"] * 100
    assert low <= pn_share < 0  # la fetta negativa resta visibile
    assert high >= 100 - pn_share - 1e-9  # il resto del passivo (oltre il 100%) non viene tagliato
    assert any(abs(p.get_height() - pn_share) < 1e-9 for p in ax.patches)


def test_all_charts_render(tmp_path, sample_data):
    m = metrics.compute(CanonicalBalance.from_dict(with_years(sample_data, 3)))
    paths = charts.render_all(m, tmp_path)
    assert set(paths) == set(charts.CHARTS) and all(p.stat().st_size > 5_000 for p in paths.values())

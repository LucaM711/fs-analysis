"""Quadratura al centesimo: replica di Input!B52/B53 + riconciliazione."""

from __future__ import annotations

import copy

from fsa.model import CanonicalBalance
from fsa.verify import verify


def test_balanced_sample_ok(sample_data):
    bal = CanonicalBalance.from_dict(sample_data)
    res = verify(bal)
    assert res.ok
    assert all(y.attivo_ok and y.passivo_ok for y in res.years)


def test_small_rounding_residual_reconciled(sample_data):
    # Totale Attivo piu' alto di 3 centesimi: residuo assorbito sui Ratei attivi.
    data = copy.deepcopy(sample_data)
    data["stato_patrimoniale"]["totale_attivo"]["y0"] = 1160000.03
    # mantieni il passivo coerente col nuovo totale (PN +0,03)
    data["stato_patrimoniale"]["totale_patrimonio_netto"]["y0"] = 400000.03
    bal = CanonicalBalance.from_dict(data)
    res = verify(bal)
    assert res.ok
    y0 = next(y for y in res.years if y.year == "y0")
    assert y0.adjustments  # registrato l'aggiustamento
    # dopo la riconciliazione la somma dell'attivo torna esatta
    assert bal.sp("ratei_risconti_attivi", "y0") == 10000.03


def test_large_imbalance_fails(sample_data):
    data = copy.deepcopy(sample_data)
    data["stato_patrimoniale"]["crediti"]["y0"] = 300000 + 5000  # 5.000 in piu'
    bal = CanonicalBalance.from_dict(data)
    res = verify(bal)
    assert not res.ok
    y0 = next(y for y in res.years if y.year == "y0")
    assert y0.errors


def test_internal_consistency_warning(sample_data):
    data = copy.deepcopy(sample_data)
    # Totale Debiti incoerente con breve+oltre -> warning, ma quadratura su B53 ok
    data["stato_patrimoniale"]["totale_debiti"]["y0"] = 999999
    bal = CanonicalBalance.from_dict(data)
    res = verify(bal)
    y0 = next(y for y in res.years if y.year == "y0")
    assert any("Totale Debiti" in w for w in y0.warnings)
    # B53 non usa Totale Debiti: la quadratura resta soddisfatta
    assert y0.passivo_ok

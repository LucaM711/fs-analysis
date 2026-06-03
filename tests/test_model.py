"""Validazione e caricamento di normalized.json."""

from __future__ import annotations

import copy

import pytest
from fsa.model import CanonicalBalance, ValidationError


def test_load_sample(sample_data):
    bal = CanonicalBalance.from_dict(sample_data)
    assert bal.meta["nome_azienda"] == "Acme S.r.l."
    assert bal.years == ("y0", "y1")
    assert bal.ce("ebit", "y0") == 200000.0
    assert bal.sp("totale_attivo", "y0") == 1160000.0


def test_missing_meta(sample_data):
    data = copy.deepcopy(sample_data)
    data["meta"].pop("nome_azienda")
    with pytest.raises(ValidationError):
        CanonicalBalance.from_dict(data)


def test_unknown_key_rejected(sample_data):
    data = copy.deepcopy(sample_data)
    data["conto_economico"]["voce_inventata"] = {"y0": 1, "y1": 1}
    with pytest.raises(ValidationError):
        CanonicalBalance.from_dict(data)


def test_missing_value_rejected(sample_data):
    data = copy.deepcopy(sample_data)
    data["stato_patrimoniale"]["crediti"].pop("y0")
    with pytest.raises(ValidationError):
        CanonicalBalance.from_dict(data)


def test_non_numeric_rejected(sample_data):
    data = copy.deepcopy(sample_data)
    data["conto_economico"]["ebit"]["y0"] = "tanti"
    with pytest.raises(ValidationError):
        CanonicalBalance.from_dict(data)


def test_nd_allowed_for_trade_keys(sample_data):
    data = copy.deepcopy(sample_data)
    data["stato_patrimoniale"]["debiti_verso_fornitori"]["y0"] = "n.d."
    data["stato_patrimoniale"]["crediti_verso_clienti"]["y0"] = "N.D."
    bal = CanonicalBalance.from_dict(data)
    assert bal.sp("debiti_verso_fornitori", "y0") == "n.d."
    assert bal.sp("crediti_verso_clienti", "y0") == "n.d."


def test_rounding_to_cents(sample_data):
    data = copy.deepcopy(sample_data)
    data["conto_economico"]["ebit"]["y0"] = 200000.12345
    bal = CanonicalBalance.from_dict(data)
    assert bal.ce("ebit", "y0") == 200000.12

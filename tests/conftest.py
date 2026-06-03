"""Configurazione pytest: rende importabile l'engine `fsa` (che vive dentro il
plugin) e fornisce fixture comuni."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "fs-analysis" / "skills" / "analyzing-financial-statements"
ENGINE_SCRIPTS = SKILL / "scripts"
TEMPLATE = SKILL / "assets" / "template.xlsx"
SAMPLE = ROOT / "tests" / "fixtures" / "sample_normalized.json"

# L'engine self-contained nel plugin va in sys.path per i test.
sys.path.insert(0, str(ENGINE_SCRIPTS))


@pytest.fixture
def template_path() -> Path:
    return TEMPLATE


@pytest.fixture
def sample_data() -> dict:
    return json.loads(SAMPLE.read_text(encoding="utf-8"))

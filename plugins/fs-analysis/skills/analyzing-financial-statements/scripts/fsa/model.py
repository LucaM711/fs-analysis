"""Modello dati canonico del bilancio riclassificato e (de)serializzazione JSON.

``normalized.json`` e' il contratto fra l'agente (che mappa le voci sporche) e
l'engine. Struttura attesa::

    {
      "meta": {"nome_azienda": str, "anno": int, "tipologia": str|null,
               "ateco": str|null, "partita_iva": str|null,
               "forma_giuridica": str|null, "sede": str|null},
      "conto_economico":   {"<chiave>": {"y0": num, "y1": num, "y2": num?}, ...},
      "stato_patrimoniale":{"<chiave>": {"y0": num, "y1": num, "y2": num?}, ...}
    }

``y0`` = ultimo esercizio, ``y1`` = precedente, ``y2`` = due esercizi prima (opz.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import mapping

REQUIRED_YEARS = ("y0", "y1")
OPTIONAL_YEARS = ("y2",)
ALL_YEARS = REQUIRED_YEARS + OPTIONAL_YEARS

# Voci non incluse nella quadratura per cui, se il dato non e' separabile dal
# bilancio (es. abbreviato), e' ammesso il valore letterale "n.d.": il modello
# marchera' DSO/DPO come "Non Calcolabile".
ND = "n.d."
NON_NUMERIC_OK = ("debiti_verso_fornitori", "crediti_verso_clienti")


class ValidationError(ValueError):
    """Errore di validazione del ``normalized.json``: messaggio per l'operatore."""


def _round2(value: Any, where: str) -> float:
    try:
        return round(float(value) + 0.0, 2)
    except (TypeError, ValueError):
        raise ValidationError(f"{where}: valore non numerico ({value!r})") from None


@dataclass
class CanonicalBalance:
    """Bilancio riclassificato pronto per essere scritto nel foglio Input."""

    meta: dict[str, Any] = field(default_factory=dict)
    conto_economico: dict[str, dict[str, float]] = field(default_factory=dict)
    stato_patrimoniale: dict[str, dict[str, float]] = field(default_factory=dict)
    years: tuple[str, ...] = REQUIRED_YEARS

    # -- costruzione / validazione -------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalBalance":
        if not isinstance(data, dict):
            raise ValidationError("Il file deve contenere un oggetto JSON.")
        meta = dict(data.get("meta") or {})
        if not meta.get("nome_azienda"):
            raise ValidationError("meta.nome_azienda mancante.")
        if not meta.get("anno"):
            raise ValidationError("meta.anno mancante (ultimo esercizio).")

        ce_in = data.get("conto_economico") or {}
        sp_in = data.get("stato_patrimoniale") or {}

        # Determina quali anni sono presenti (y0,y1 obbligatori; y2 opzionale).
        present = set(REQUIRED_YEARS)
        for section in (ce_in, sp_in):
            for cell in section.values():
                if isinstance(cell, dict) and cell.get("y2") is not None:
                    present.add("y2")
        years = tuple(y for y in ALL_YEARS if y in present)

        ce = cls._read_section(ce_in, mapping.CE_KEYS, "conto_economico", years)
        sp = cls._read_section(sp_in, mapping.SP_KEYS, "stato_patrimoniale", years)
        return cls(meta=meta, conto_economico=ce, stato_patrimoniale=sp, years=years)

    @staticmethod
    def _read_section(
        section: dict[str, Any],
        keys: tuple[str, ...],
        name: str,
        years: tuple[str, ...],
    ) -> dict[str, dict[str, float]]:
        if not isinstance(section, dict):
            raise ValidationError(f"{name} deve essere un oggetto.")
        unknown = set(section) - set(keys)
        if unknown:
            raise ValidationError(
                f"{name}: chiavi non riconosciute {sorted(unknown)}. Chiavi ammesse: {list(keys)}"
            )
        out: dict[str, dict[str, float]] = {}
        for key in keys:
            cell = section.get(key)
            if cell is None:
                raise ValidationError(f"{name}.{key} mancante.")
            if not isinstance(cell, dict):
                raise ValidationError(f"{name}.{key} deve essere un oggetto con y0/y1 (e y2 opz.).")
            allow_nd = key in NON_NUMERIC_OK
            values: dict[str, float] = {}
            for y in REQUIRED_YEARS:
                raw = cell.get(y)
                if raw is None:
                    raise ValidationError(f"{name}.{key}.{y} mancante.")
                if allow_nd and isinstance(raw, str) and raw.strip().lower() == ND:
                    values[y] = ND  # type: ignore[assignment]
                else:
                    values[y] = _round2(raw, f"{name}.{key}.{y}")
            if "y2" in years and cell.get("y2") is not None:
                raw = cell["y2"]
                if allow_nd and isinstance(raw, str) and raw.strip().lower() == ND:
                    values["y2"] = ND  # type: ignore[assignment]
                else:
                    values["y2"] = _round2(raw, f"{name}.{key}.y2")
            out[key] = values
        return out

    @classmethod
    def load(cls, path: str | Path) -> "CanonicalBalance":
        raw = Path(path).read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"JSON non valido: {exc}") from None
        return cls.from_dict(data)

    # -- accesso comodo ------------------------------------------------------------
    def ce(self, key: str, year: str) -> float:
        return self.conto_economico[key].get(year, 0.0)

    def sp(self, key: str, year: str) -> float:
        return self.stato_patrimoniale[key].get(year, 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "conto_economico": self.conto_economico,
            "stato_patrimoniale": self.stato_patrimoniale,
        }


def skeleton(anno: int | None = None) -> dict[str, Any]:
    """Schema vuoto di ``normalized.json`` da far compilare all'agente."""

    def empty_section(keys: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {k: {"y0": None, "y1": None} for k in keys}

    return {
        "meta": {
            "nome_azienda": None,
            "anno": anno,
            "tipologia": None,
            "ateco": None,
            "partita_iva": None,
            "forma_giuridica": None,
            "sede": None,
        },
        "conto_economico": empty_section(mapping.CE_KEYS),
        "stato_patrimoniale": empty_section(mapping.SP_KEYS),
    }

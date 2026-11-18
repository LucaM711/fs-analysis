"""Modello dati canonico del bilancio riclassificato e (de)serializzazione JSON.

``normalized.json`` e' il contratto fra l'agente (che mappa le voci sporche) e
l'engine. Struttura attesa::

    {
      "meta": {"nome_azienda": str, "anno": int, "ateco": str|null,
               "partita_iva": str|null, "forma_giuridica": str|null, "sede": str|null},
      "conto_economico":   {"<chiave>": {"y0": num, "y1": num, ..., "yN-1": num}, ...},
      "stato_patrimoniale":{"<chiave>": {"y0": num, "y1": num, ..., "yN-1": num}, ...}
    }

``y0`` = ultimo esercizio, ``y1`` = precedente, ``yK`` = K esercizi prima. Servono
almeno 2 esercizi; se una voce ha ``yK``, tutte le voci devono avere ``y0..yK``.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import mapping

MIN_YEARS = 2
_YEAR_KEY = re.compile(r"^y(\d+)$")

# Voci non incluse nella quadratura per cui, se il dato non e' separabile dal
# bilancio (es. abbreviato), e' ammesso il valore letterale "n.d.": il modello
# marchera' DSO/DPO come "Non Calcolabile".
ND = "n.d."
NON_NUMERIC_OK = ("debiti_verso_fornitori", "crediti_verso_clienti")


class ValidationError(ValueError):
    """Errore di validazione del ``normalized.json``: messaggio per l'operatore."""


def _round2(value: Any, where: str) -> float:
    if isinstance(value, bool):  # float(True) == 1.0: un booleano non e' un importo
        raise ValidationError(f"{where}: valore non numerico ({value!r})")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{where}: valore non numerico ({value!r})") from None
    if not math.isfinite(number):  # json.loads accetta NaN/Infinity
        raise ValidationError(f"{where}: valore non finito ({value!r})")
    return round(number + 0.0, 2)


@dataclass
class CanonicalBalance:
    """Bilancio riclassificato pronto per essere scritto nel foglio Input."""

    meta: dict[str, Any] = field(default_factory=dict)
    conto_economico: dict[str, dict[str, float]] = field(default_factory=dict)
    stato_patrimoniale: dict[str, dict[str, float]] = field(default_factory=dict)
    years: tuple[str, ...] = ("y0", "y1")

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
        try:
            int(meta["anno"])
        except (TypeError, ValueError):
            raise ValidationError(f"meta.anno deve essere un anno numerico ({meta['anno']!r}).") from None

        ce_in = data.get("conto_economico") or {}
        sp_in = data.get("stato_patrimoniale") or {}

        # Esercizi: da y0 fino al piu' vecchio valorizzato in una voce qualsiasi.
        n = MIN_YEARS
        for section in (ce_in, sp_in):
            for cell in section.values() if isinstance(section, dict) else ():
                for k, v in cell.items() if isinstance(cell, dict) else ():
                    match = _YEAR_KEY.match(str(k))
                    if match and v is not None:
                        n = max(n, int(match.group(1)) + 1)
        years = tuple(f"y{k}" for k in range(n))

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
                raise ValidationError(f"{name}.{key} deve essere un oggetto con y0, y1, ...")
            allow_nd = key in NON_NUMERIC_OK
            values: dict[str, float] = {}
            for y in years:
                raw = cell.get(y)
                if raw is None:
                    raise ValidationError(
                        f"{name}.{key}.{y} mancante: ogni voce deve avere tutti gli esercizi "
                        f"{years[0]}..{years[-1]}."
                    )
                if allow_nd and isinstance(raw, str) and raw.strip().lower() == ND:
                    values[y] = ND  # type: ignore[assignment]
                else:
                    values[y] = _round2(raw, f"{name}.{key}.{y}")
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


def skeleton(anno: int | None = None, esercizi: int = MIN_YEARS) -> dict[str, Any]:
    """Schema vuoto di ``normalized.json`` (``esercizi`` = y0..y{esercizi-1})."""

    def empty_section(keys: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {k: {f"y{i}": None for i in range(esercizi)} for k in keys}

    return {
        "meta": {k: (anno if k == "anno" else None) for k in mapping.META_KEYS},
        "conto_economico": empty_section(mapping.CE_KEYS),
        "stato_patrimoniale": empty_section(mapping.SP_KEYS),
    }

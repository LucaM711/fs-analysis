"""Verifica della quadratura al centesimo (replica esatta di Input!B52 e B53).

Tutta l'aritmetica e' fatta in centesimi interi per evitare errori di virgola
mobile: una quadratura "al centesimo" deve essere esatta, non approssimata.

Replica delle formule del modello:
    B52 (Attivo):  SUM(immob, rimanenze, crediti, att.fin, disp.liq, ratei att.) == Totale Attivo
    B53 (Passivo): Deb.Fin + (Deb.breve - Deb.Fin.breve) + (Deb.oltre - Deb.Fin.oltre)
                   + TFR + Fondi + Patrimonio Netto + Ratei pass.  == Totale Attivo
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .model import CanonicalBalance

# Residuo massimo (in euro) riconducibile ad arrotondamenti che viene assorbito
# automaticamente nei Ratei e Risconti. Oltre questa soglia e' un errore di
# mappatura e va segnalato all'operatore.
DEFAULT_RECONCILE_EUR = 0.05


def _c(value: float) -> int:
    """Euro -> centesimi interi."""
    return int(round(value * 100.0))


def _e(cents: int) -> float:
    """Centesimi interi -> euro."""
    return round(cents / 100.0, 2)


@dataclass
class YearCheck:
    year: str
    attivo_ok: bool
    passivo_ok: bool
    attivo_residuo: float  # Totale Attivo - somma attivo (euro)
    passivo_residuo: float  # Totale Attivo - composizione passivo (euro)
    adjustments: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.attivo_ok and self.passivo_ok and not self.errors


@dataclass
class VerificationResult:
    years: list[YearCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(y.ok for y in self.years)

    def summary(self) -> str:
        lines = []
        for y in self.years:
            status = "OK" if y.ok else "ERRORE"
            lines.append(f"[{y.year}] quadratura: {status}")
            for a in y.adjustments:
                lines.append(f"    ~ {a}")
            for w in y.warnings:
                lines.append(f"    ! {w}")
            for e in y.errors:
                lines.append(f"    x {e}")
        lines.append("")
        lines.append("Quadratura complessiva al centesimo: " + ("OK" if self.ok else "NON QUADRA"))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "years": [
                {
                    "year": y.year,
                    "ok": y.ok,
                    "attivo_ok": y.attivo_ok,
                    "passivo_ok": y.passivo_ok,
                    "attivo_residuo": y.attivo_residuo,
                    "passivo_residuo": y.passivo_residuo,
                    "adjustments": y.adjustments,
                    "warnings": y.warnings,
                    "errors": y.errors,
                }
                for y in self.years
            ],
        }


_ATTIVO_KEYS = (
    "immobilizzazioni",
    "rimanenze",
    "crediti",
    "attivita_finanziarie",
    "disponibilita_liquide",
    "ratei_risconti_attivi",
)


def verify(balance: "CanonicalBalance", reconcile_eur: float = DEFAULT_RECONCILE_EUR) -> VerificationResult:
    """Verifica e (se nei limiti) riconcilia gli arrotondamenti, in place.

    Modifica ``balance.stato_patrimoniale`` aggiustando i Ratei/Risconti quando il
    residuo e' entro ``reconcile_eur``. Ritorna il report strutturato.
    """

    tol = _c(reconcile_eur)
    result = VerificationResult()

    for year in balance.years:
        sp = lambda k: _c(balance.sp(k, year))  # noqa: E731 - locale, conciso

        totale_attivo = sp("totale_attivo")

        # --- Attivo (B52) ---------------------------------------------------------
        attivo_sum = sum(sp(k) for k in _ATTIVO_KEYS)
        res_att = totale_attivo - attivo_sum

        # --- Passivo (B53, replica esatta) ----------------------------------------
        passivo = (
            sp("totale_debiti_finanziari")
            + (sp("debiti_esigibili_breve") - sp("debiti_finanziari_breve"))
            + (sp("debiti_esigibili_oltre") - sp("debiti_finanziari_oltre"))
            + sp("tfr")
            + sp("fondi_rischi_oneri")
            + sp("totale_patrimonio_netto")
            + sp("ratei_risconti_passivi")
        )
        res_pas = totale_attivo - passivo

        yc = YearCheck(
            year=year,
            attivo_ok=False,
            passivo_ok=False,
            attivo_residuo=_e(res_att),
            passivo_residuo=_e(res_pas),
        )

        # Coerenze interne (non bloccanti ma da segnalare).
        if sp("debiti_esigibili_breve") + sp("debiti_esigibili_oltre") != sp("totale_debiti"):
            yc.warnings.append(
                "Totale Debiti != Debiti a breve + Debiti oltre "
                f"({_e(sp('totale_debiti'))} vs "
                f"{_e(sp('debiti_esigibili_breve') + sp('debiti_esigibili_oltre'))})."
            )
        if sp("debiti_finanziari_breve") + sp("debiti_finanziari_oltre") != sp("totale_debiti_finanziari"):
            yc.warnings.append("Totale Debiti Finanziari != Deb.Fin. breve + Deb.Fin. oltre.")
        if sp("totale_debiti_finanziari") > sp("totale_debiti"):
            yc.warnings.append("Debiti Finanziari > Totale Debiti (debiti commerciali negativi).")

        # --- Riconciliazione attivo ----------------------------------------------
        yc.attivo_ok, adj = _reconcile(
            balance, year, "ratei_risconti_attivi", res_att, tol, "Attivo", "Ratei e Risconti Attivi"
        )
        yc.adjustments += adj["adjustments"]
        yc.errors += adj["errors"]

        # --- Riconciliazione passivo ----------------------------------------------
        yc.passivo_ok, adj = _reconcile(
            balance, year, "ratei_risconti_passivi", res_pas, tol, "Passivo", "Ratei e Risconti Passivi"
        )
        yc.adjustments += adj["adjustments"]
        yc.errors += adj["errors"]

        result.years.append(yc)

    return result


def _reconcile(
    balance: "CanonicalBalance",
    year: str,
    target_key: str,
    residuo_cents: int,
    tol_cents: int,
    side: str,
    target_label: str,
) -> tuple[bool, dict[str, list[str]]]:
    out: dict[str, list[str]] = {"adjustments": [], "errors": []}
    if residuo_cents == 0:
        return True, out
    if abs(residuo_cents) <= tol_cents:
        current = balance.stato_patrimoniale[target_key].get(year, 0.0)
        balance.stato_patrimoniale[target_key][year] = round(current + residuo_cents / 100.0, 2)
        out["adjustments"].append(
            f"{side} [{year}]: residuo {_e(residuo_cents)} EUR assorbito su '{target_label}'."
        )
        return True, out
    out["errors"].append(
        f"{side} [{year}]: sbilancio di {_e(residuo_cents)} EUR oltre la tolleranza "
        f"({_e(tol_cents)} EUR). Verificare la mappatura delle voci."
    )
    return False, out

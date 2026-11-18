"""I 4 grafici standard (PNG), dagli stessi dati di ``metrics.json``.

Servono al PDF e, quando la superficie non supporta grafici interattivi, alla chat.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # nessun display: solo file
import matplotlib.pyplot as plt  # noqa: E402

from .scoring import ALTMAN_DISTRESS, ALTMAN_SAFE  # noqa: E402

INK = "#1f2a3a"
MUTED = "#6b7686"
GRID = "#e3e7ee"
SERIES = ("#2f5d8a", "#5fa8a0", "#e0a43b", "#b85c5c", "#8a7bb5", "#9aa5b4")
ZONES = {"rischio": "#f4d6d6", "grigia": "#eeeeee", "sicurezza": "#d8ecdf"}


def _style(ax, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=10, color=INK, fontweight="bold")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)


def _legend_below(ax) -> None:
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)


def _chronological(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    return list(reversed(metrics["esercizi"]))


def _pct(values: list[Any]) -> list[float]:
    return [float("nan") if x is None else x * 100 for x in values]


def andamento_economico(metrics: dict[str, Any], ax) -> None:
    es = _chronological(metrics)
    years = [str(e["anno"]) for e in es]
    series = (
        ("Valore della produzione", "valore_della_produzione"),
        ("EBITDA", "ebitda"),
        ("Utile (perdita)", "utile_perdita_esercizio"),
    )
    width = 0.8 / len(series)
    for i, (label, key) in enumerate(series):
        xs = [j + (i - 1) * width for j in range(len(years))]
        ax.bar(xs, [e["valori"][key] / 1e6 for e in es], width, label=label, color=SERIES[i])
    ax.set_xticks(range(len(years)), years)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_ylabel("mln €", fontsize=8, color=MUTED)
    _style(ax, "Andamento economico")
    _legend_below(ax)


def struttura_patrimoniale(metrics: dict[str, Any], ax) -> None:
    v = metrics["esercizi"][0]["valori"]
    attivo = (
        ("Immobilizzazioni", v["immobilizzazioni"]),
        ("Rimanenze", v["rimanenze"]),
        ("Crediti", v["crediti"]),
        ("Attivita' fin.", v["attivita_finanziarie"]),
        ("Liquidita'", v["disponibilita_liquide"]),
        ("Ratei e risconti", v["ratei_risconti_attivi"]),
    )
    passivo = (
        ("Patrimonio netto", v["totale_patrimonio_netto"]),
        ("Fondi e TFR", v["fondi_rischi_oneri"] + v["tfr"]),
        ("Debiti non fin.", v["debiti_non_finanziari"]),
        ("Debiti finanziari", v["totale_debiti_finanziari"]),
        ("Ratei e risconti", v["ratei_risconti_passivi"]),
    )
    total = v["totale_attivo"] or 1
    low, high = 0.0, 100.0
    for x, parts in ((0, attivo), (1, passivo)):
        up = down = 0.0  # le quote negative (es. patrimonio netto) scendono sotto lo zero
        for i, (label, amount) in enumerate(parts):
            share = amount / total * 100
            base = up if share >= 0 else down
            ax.bar(x, share, 0.6, bottom=base, color=SERIES[i % len(SERIES)], edgecolor="white")
            if abs(share) >= 6:
                ax.text(x, base + share / 2, f"{label} {share:.0f}%", ha="center", va="center", fontsize=6.5)
            if share >= 0:
                up += share
            else:
                down += share
        low, high = min(low, down), max(high, up)
    ax.set_xticks((0, 1), ("Attivo", "Passivo"))
    ax.set_ylim(low, high)
    if low < 0:
        ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_ylabel("% del totale", fontsize=8, color=MUTED)
    _style(ax, f"Struttura patrimoniale {metrics['esercizi'][0]['anno']}")


def redditivita(metrics: dict[str, Any], ax) -> None:
    es = _chronological(metrics)
    years = [str(e["anno"]) for e in es]
    for i, (label, key) in enumerate((("ROE", "roe"), ("ROI", "roi"), ("ROS", "ros"))):
        ax.plot(years, _pct([e["indici"][key] for e in es]), marker="o", label=label, color=SERIES[i])
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.set_ylabel("%", fontsize=8, color=MUTED)
    _style(ax, "Redditivita'")
    _legend_below(ax)


def solidita(metrics: dict[str, Any], ax) -> None:
    es = _chronological(metrics)
    years = [str(e["anno"]) for e in es]
    z = [e["altman"]["z"] if e["altman"] else float("nan") for e in es]
    finite = [x for x in z if x == x] or [0.0]
    top = max(max(finite), ALTMAN_SAFE) * 1.15
    bottom = min(min(finite), 0) * 1.15
    ax.axhspan(bottom, ALTMAN_DISTRESS, color=ZONES["rischio"], zorder=0)
    ax.axhspan(ALTMAN_DISTRESS, ALTMAN_SAFE, color=ZONES["grigia"], zorder=0)
    ax.axhspan(ALTMAN_SAFE, top, color=ZONES["sicurezza"], zorder=0)
    ax.plot(years, z, marker="o", color=INK, label="Altman Z''")
    ax.set_ylim(bottom, top)
    _style(ax, "Solidita' (Altman Z'')")
    ax.legend(fontsize=7, frameon=False, loc="upper left")


CHARTS = {
    "andamento_economico": andamento_economico,
    "struttura_patrimoniale": struttura_patrimoniale,
    "redditivita": redditivita,
    "solidita": solidita,
}


def render_all(
    metrics: dict[str, Any], out_dir: str | Path, size: tuple[float, float] = (4.2, 2.8)
) -> dict[str, Path]:
    """Scrive i 4 PNG in ``out_dir``; ritorna nome -> path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, draw in CHARTS.items():
        fig, ax = plt.subplots(figsize=size, dpi=200)
        draw(metrics, ax)
        fig.tight_layout()
        path = out_dir / f"{name}.png"
        fig.savefig(path)
        plt.close(fig)
        paths[name] = path
    return paths

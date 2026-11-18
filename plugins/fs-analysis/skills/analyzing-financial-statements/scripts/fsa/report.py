"""Report PDF a layout fisso (A4, 4 pagine) da ``metrics.json`` + i 4 testi.

Il PDF non calcola nulla: formatta i numeri di ``metrics.json``. I testi hanno
riquadri fissi; se un testo non ci sta viene rimpicciolito per non coprire il resto
e ``render`` lo segnala, cosi' l'agente lo accorcia e rigenera.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, Callable
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import registerFont, stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import KeepInFrame, Paragraph, Table, TableStyle

from . import charts
from .metrics import var

PAGE_W, PAGE_H = A4
M = 36  # margine
W = PAGE_W - 2 * M
GAP = 12
COL = (W - GAP) / 2

INK = colors.HexColor("#1f2a3a")
ACCENT = colors.HexColor("#2f5d8a")
MUTED = colors.HexColor("#6b7686")
LIGHT = colors.HexColor("#f3f5f8")
LINE = colors.HexColor("#dde2ea")
GOOD = colors.HexColor("#2e7d4f")
BAD = colors.HexColor("#b84040")
RATING_COLORS = {
    "Eccellente": "#2e7d4f",
    "Positiva": "#5fa86a",
    "Adeguata": "#c9a227",
    "Critica": "#d9822b",
    "Molto Critica": "#b84040",
}
LOWER_IS_BETTER = {"totale_debiti_finanziari"}  # KPI per cui un calo e' un miglioramento
ZONE_LABELS = {"sicurezza": "zona di sicurezza", "grigia": "zona grigia", "rischio": "zona di rischio"}

# DejaVu Sans arriva con matplotlib e copre simboli come ≥ → ≈, che Helvetica (font
# standard del PDF) non ha: li sostituirebbe con altri caratteri senza avvisare.
FONT, BOLD = "DejaVuSans", "DejaVuSans-Bold"
_TTF = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for _name in (FONT, BOLD):
    registerFont(TTFont(_name, str(_TTF / f"{_name}.ttf")))
TEXT_STYLE = ParagraphStyle("testo", fontName=FONT, fontSize=9.5, leading=13, textColor=INK)

# Blocco testuale -> (titolo, pagina, x, y in basso, larghezza, altezza)
TEXT_BLOCKS: dict[str, tuple[str, int, float, float, float, float]] = {
    "economico": ("Ambito economico", 1, M, 52, COL, 368),
    "finanziario_patrimoniale": ("Ambito finanziario e patrimoniale", 1, M + COL + GAP, 52, COL, 368),
    "sintesi": ("Sintesi", 2, M, 420, COL, 316),
    "valutazione": ("Valutazione", 2, M + COL + GAP, 420, COL, 316),
}
Row = tuple[str, Callable[[dict], Any], Callable[[Any], str]]  # etichetta, valore, formato
MAX_TABLE_YEARS = 5  # shortcut: le tabelle mostrano i 5 anni piu' recenti, gli altri solo nei grafici


# --- formattazione italiana -----------------------------------------------------------
def _it(x: float, decimals: int) -> str:
    return f"{x:,.{decimals}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def eur(x: Any) -> str:
    return "n.d." if not isinstance(x, (int, float)) else f"{_it(x, 0)} €"


def eur_short(x: Any) -> str:
    if not isinstance(x, (int, float)):
        return "n.d."
    if abs(x) >= 1e6:
        return f"{_it(x / 1e6, 2)} mln €"
    return f"{_it(x / 1e3, 0)} mila €" if abs(x) >= 1e4 else eur(x)


def pct(x: Any, decimals: int = 1) -> str:
    return "n.d." if x is None else f"{_it(x * 100, decimals)}%"


def ratio(x: Any) -> str:
    return "n.d." if x is None else _it(x, 2)


def days(x: Any) -> str:
    return "n.d." if x is None else f"{_it(x, 0)} gg"


def change(x: Any) -> str:
    return "" if x is None else ("+" if x >= 0 else "−") + pct(abs(x))


# --- testi -----------------------------------------------------------------------------
def _paragraph(text: str) -> Paragraph:
    return Paragraph(escape(text.strip()).replace("\n", "<br/>"), TEXT_STYLE)


def fits(block: str, text: str) -> bool:
    _, _, _, _, w, h = TEXT_BLOCKS[block]
    return _paragraph(text).wrap(w, h)[1] <= h


def budgets() -> dict[str, dict[str, int]]:
    """Capienza indicativa di ogni blocco (il controllo vero e' ``fits``)."""
    sample = "La redditivita' operativa migliora grazie alla crescita dei ricavi e al contenimento dei costi."
    avg = stringWidth(sample, FONT, TEXT_STYLE.fontSize) / len(sample)
    out = {}
    for block, (_, _, _, _, w, h) in TEXT_BLOCKS.items():
        lines = int(h // TEXT_STYLE.leading)
        out[block] = {"max_chars": int(lines * (w / avg)), "lines": lines}
    return out


# --- primitive di disegno ----------------------------------------------------------
def _text(c: Canvas, x: float, y: float, s: str, size: float = 9, font: str = FONT, color=INK, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    draw = {"left": c.drawString, "right": c.drawRightString, "center": c.drawCentredString}[align]
    draw(x, y, s)


def _footer(c: Canvas, meta: dict[str, Any], page: int, pages: int) -> None:
    c.setStrokeColor(LINE)
    c.line(M, 32, PAGE_W - M, 32)
    _text(
        c,
        M,
        20,
        f"Analisi di bilancio · {meta.get('nome_azienda') or ''} · esercizio {meta.get('anno')}",
        7,
        color=MUTED,
    )
    _text(c, PAGE_W - M, 20, f"Pagina {page} di {pages}", 7, color=MUTED, align="right")


def _section(c: Canvas, x: float, y: float, title: str) -> None:
    _text(c, x, y, title.upper(), 8.5, BOLD, ACCENT)


def _table(
    c: Canvas, rows: list[list[str]], x: float, top: float, widths: list[float], bold_rows=()
) -> float:
    """Disegna una tabella con intestazione; ritorna la y del bordo inferiore."""
    t = Table(rows, colWidths=widths, rowHeights=13)
    style = [
        ("FONT", (0, 0), (-1, -1), FONT, 7.5),
        ("FONT", (0, 0), (-1, 0), BOLD, 7.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]
    for r in bold_rows:
        style += [("FONT", (0, r), (-1, r), BOLD, 7.5), ("BACKGROUND", (0, r), (-1, r), LIGHT)]
    t.setStyle(TableStyle(style))
    _, h = t.wrap(sum(widths), 10_000)
    t.drawOn(c, x, top - h)
    return top - h


# --- pagine ------------------------------------------------------------------------
def _page_summary(c: Canvas, m: dict[str, Any]) -> None:
    meta, last = m["meta"], m["esercizi"][0]
    c.setFillColor(INK)
    c.rect(0, PAGE_H - 78, PAGE_W, 78, stroke=0, fill=1)
    _text(c, M, PAGE_H - 38, str(meta.get("nome_azienda") or ""), 18, BOLD, colors.white)
    anni = m["anni"]
    periodo = f"esercizio {anni[0]}" + (f" · andamento {anni[-1]}–{anni[0]}" if len(anni) > 2 else "")
    _text(c, M, PAGE_H - 58, f"Analisi di bilancio · {periodo}", 10, color=colors.HexColor("#c9d3e0"))

    # profilo
    profile = (
        ("Partita IVA", meta.get("partita_iva")),
        ("ATECO", meta.get("ateco")),
        ("Forma giuridica", meta.get("forma_giuridica")),
        ("Sede", meta.get("sede")),
        ("Dimensione (UE)", m["dimensione_impresa"]),
        ("Dipendenti", _it(last["valori"]["dipendenti"], 0)),
    )
    y = PAGE_H - 100
    for i, (label, value) in enumerate(profile):
        x = M + i * (W / len(profile))
        _text(c, x, y, label, 7, color=MUTED)
        _text(c, x, y - 12, str(value or "n.d.")[:28], 8.5, BOLD)

    # valutazione sintetica
    top = PAGE_H - 132
    c.setFillColor(LIGHT)
    c.roundRect(M, top - 92, W, 92, 6, stroke=0, fill=1)
    p = last["punteggio"]
    _section(c, M + 12, top - 16, "Punteggio complessivo")
    score = p["complessivo"]
    _text(c, M + 12, top - 52, "n.d." if score is None else _it(score, 1), 28, BOLD)
    _text(c, M + 12, top - 70, "su 10 · 1 = migliore", 8, color=MUTED)
    _text(c, M + 12, top - 82, f"grade {p['grade'] if p['grade'] is not None else 'n.d.'}", 8, BOLD, MUTED)

    _section(c, M + 150, top - 16, "Rating per area")
    aree = p["aree"] or {}
    for i, area in enumerate(("reddituale", "finanziaria", "patrimoniale")):
        yy = top - 36 - i * 18
        rating = (aree.get(area) or {}).get("rating") or "n.d."
        _text(c, M + 150, yy, area.capitalize(), 9)
        c.setFillColor(colors.HexColor(RATING_COLORS.get(rating, "#9aa5b4")))
        c.roundRect(M + 240, yy - 4, 86, 14, 7, stroke=0, fill=1)
        _text(c, M + 283, yy, rating, 8, BOLD, colors.white, align="center")

    _section(c, M + 360, top - 16, "Altman Z''")
    z = last["altman"]
    _text(c, M + 360, top - 52, "n.d." if not z else _it(z["z"], 2), 28, BOLD)
    if z:
        _text(
            c,
            M + 360,
            top - 70,
            ZONE_LABELS[z["zona"]],
            9,
            BOLD,
            {"sicurezza": GOOD, "rischio": BAD}.get(z["zona"], MUTED),
        )
    _text(c, M + 360, top - 82, "sicurezza oltre 2,60 · rischio sotto 1,10", 8, color=MUTED)

    # KPI
    v, var = last["valori"], last["variazioni"] or {}
    pfn = last["indici"]["pfn"]
    kpis = (
        ("Valore della produzione", v["valore_della_produzione"], "valore_della_produzione"),
        ("EBITDA", v["ebitda"], "ebitda"),
        ("EBIT", v["ebit"], "ebit"),
        ("Utile (perdita)", v["utile_perdita_esercizio"], "utile_perdita_esercizio"),
        ("Patrimonio netto", v["totale_patrimonio_netto"], "totale_patrimonio_netto"),
        ("PFN (+ = cassa netta)", pfn, None),
        ("Disponibilita' liquide", v["disponibilita_liquide"], "disponibilita_liquide"),
        ("Debiti finanziari", v["totale_debiti_finanziari"], "totale_debiti_finanziari"),
    )
    tw, th = (W - 3 * 8) / 4, 46
    for i, (label, value, key) in enumerate(kpis):
        x = M + (i % 4) * (tw + 8)
        y = top - 106 - (i // 4) * (th + 8) - th
        c.setStrokeColor(LINE)
        c.roundRect(x, y, tw, th, 5, stroke=1, fill=0)
        _text(c, x + 8, y + th - 13, label, 7, color=MUTED)
        _text(c, x + 8, y + 18, eur_short(value), 11, BOLD)
        delta = var.get(key) if key else None
        if delta is not None:  # riga sua: accanto al valore non ci sta
            better = delta <= 0 if key in LOWER_IS_BETTER else delta >= 0
            _text(c, x + 8, y + 6, f"{change(delta)} sul {anni[1]}", 7, BOLD, GOOD if better else BAD)


def _draw_text_blocks(c: Canvas, texts: dict[str, str], page: int) -> None:
    for block, (title, pg, x, y, w, h) in TEXT_BLOCKS.items():
        if pg != page:
            continue
        _section(c, x, y + h + 8, title)
        frame = KeepInFrame(w, h, [_paragraph(texts.get(block) or "")], mode="shrink")
        _, used = frame.wrapOn(c, w, h)
        frame.drawOn(c, x, y + h - used)  # allineato in alto


def _page_charts(c: Canvas, chart_paths: dict[str, Path]) -> None:
    cw, ch = COL, COL * 2.8 / 4.2
    for i, name in enumerate(charts.CHARTS):
        x = M + (i % 2) * (COL + GAP)
        y = 400 - (i // 2 + 1) * (ch + 10)
        c.drawImage(str(chart_paths[name]), x, y, cw, ch, preserveAspectRatio=True)


def _money_unit(es: list[dict], rows: list[Row]) -> tuple[float, str]:
    """Importi in euro, o in migliaia oltre i 10 milioni: in colonna non ci stanno."""
    amounts = [
        abs(x) for e in es for _, get, fmt in rows if fmt is eur and isinstance(x := get(e), (int, float))
    ]
    return (1000.0, "migliaia di €") if max(amounts, default=0) >= 1e7 else (1.0, "€")


def _year_table(m: dict[str, Any], rows: list[Row], with_var: bool):
    es = m["esercizi"][:MAX_TABLE_YEARS]
    scale, unit = _money_unit(es, rows)
    voce = f"Voce ({unit})" if any(fmt is eur for _, _, fmt in rows) else "Voce"
    header = [voce] + [str(e["anno"]) for e in es] + (["Var. %"] if with_var else [])
    body, bold = [header], []
    for label, get, fmt in rows:
        if label.startswith("**"):
            label = label.strip("*")
            bold.append(len(body))
        cell = (
            (lambda x: "n.d." if not isinstance(x, (int, float)) else _it(x / scale, 0))
            if fmt is eur
            else fmt
        )
        line = [label] + [cell(get(e)) for e in es]
        if with_var:
            line.append(change(get_var(m, get)))
        body.append(line)
    n = len(header) - 1
    widths = [170.0] + [(W - 170) / n] * n
    return body, widths, bold


def get_var(m: dict[str, Any], get: Callable[[dict], Any]) -> float | None:
    es = m["esercizi"]
    return var(get(es[0]), get(es[1])) if len(es) > 1 else None


def _val(key: str) -> Callable[[dict], Any]:
    return lambda e: e["valori"][key]


def _ind(key: str) -> Callable[[dict], Any]:
    return lambda e: e["indici"][key]


SP_ROWS: list[Row] = [
    ("Immobilizzazioni", _val("immobilizzazioni"), eur),
    ("Rimanenze", _val("rimanenze"), eur),
    ("Crediti", _val("crediti"), eur),
    ("Attivita' finanziarie", _val("attivita_finanziarie"), eur),
    ("Disponibilita' liquide", _val("disponibilita_liquide"), eur),
    ("Ratei e risconti attivi", _val("ratei_risconti_attivi"), eur),
    ("**Totale attivo", _val("totale_attivo"), eur),
    ("Patrimonio netto", _val("totale_patrimonio_netto"), eur),
    ("  di cui capitale sociale", _val("capitale_sociale"), eur),
    ("Fondi per rischi e oneri", _val("fondi_rischi_oneri"), eur),
    ("TFR", _val("tfr"), eur),
    ("Debiti non finanziari", _val("debiti_non_finanziari"), eur),
    ("  a breve", _val("debiti_non_finanziari_breve"), eur),
    ("  oltre l'esercizio", _val("debiti_non_finanziari_oltre"), eur),
    ("Debiti finanziari", _val("totale_debiti_finanziari"), eur),
    ("  a breve", _val("debiti_finanziari_breve"), eur),
    ("  oltre l'esercizio", _val("debiti_finanziari_oltre"), eur),
    ("Ratei e risconti passivi", _val("ratei_risconti_passivi"), eur),
]
CE_ROWS: list[Row] = [
    ("**Valore della produzione", _val("valore_della_produzione"), eur),
    ("  ricavi di vendita", _val("ricavi_di_vendita"), eur),
    ("Costi della produzione", _val("costi_della_produzione"), eur),
    ("  materie", _val("costi_per_materie"), eur),
    ("  servizi", _val("costi_per_servizi"), eur),
    ("  godimento beni di terzi", _val("costi_godimento_beni_terzi"), eur),
    ("  personale", _val("costi_personale"), eur),
    ("  ammortamenti", _val("ammortamenti"), eur),
    ("  accantonamenti per rischi", _val("accantonamenti_per_rischi"), eur),
    ("  oneri diversi di gestione", _val("oneri_diversi_di_gestione"), eur),
    ("**EBITDA", _val("ebitda"), eur),
    ("**EBIT", _val("ebit"), eur),
    ("Proventi finanziari", _val("proventi_finanziari"), eur),
    ("Oneri finanziari", _val("oneri_finanziari"), eur),
    ("**Utile (perdita) d'esercizio", _val("utile_perdita_esercizio"), eur),
    ("Dipendenti", _val("dipendenti"), lambda x: "n.d." if x is None else _it(x, 0)),
]
INDEX_ROWS: list[Row] = [
    ("**Liquidita'", lambda e: None, lambda x: ""),
    ("Test acido", _ind("test_acido"), ratio),
    ("Current ratio", _ind("current_ratio"), ratio),
    ("**Indebitamento", lambda e: None, lambda x: ""),
    ("Rapporto di indebitamento", _ind("rapporto_indebitamento"), ratio),
    ("PFN (+ = cassa netta)", _ind("pfn"), eur_short),
    ("PFN / EBITDA", _ind("pfn_ebitda"), ratio),
    ("Margine di struttura (PN / immob.)", _ind("ims"), ratio),
    ("Copertura interessi (EBITDA / oneri)", _ind("interest_coverage"), ratio),
    ("**Redditivita'", lambda e: None, lambda x: ""),
    ("ROS", _ind("ros"), pct),
    ("ROE", _ind("roe"), pct),
    ("ROI", _ind("roi"), pct),
    ("EBITDA %", _ind("ebitda_pct"), pct),
    ("EBIT %", _ind("ebit_pct"), pct),
    ("Risultato netto %", _ind("risultato_pct"), pct),
    ("**Efficienza", lambda e: None, lambda x: ""),
    ("Asset turnover", _ind("asset_turnover"), ratio),
    ("DSO (giorni incasso)", _ind("dso"), days),
    ("DPO (giorni pagamento)", _ind("dpo"), days),
    ("DIO (giorni magazzino)", _ind("dio"), days),
    ("Ciclo monetario (CCC)", _ind("ccc"), days),
]


def _score_rows() -> list[Row]:
    def area(name: str) -> Callable[[dict], Any]:
        return lambda e: ((e["punteggio"]["aree"] or {}).get(name) or {}).get("rating")

    def alt(key: str) -> Callable[[dict], Any]:
        return lambda e: (e["altman"] or {}).get(key)

    text = lambda x: x or "n.d."  # noqa: E731
    return [
        ("**Punteggio", lambda e: None, lambda x: ""),
        (
            "Punteggio complessivo (1-10)",
            lambda e: e["punteggio"]["complessivo"],
            lambda x: "n.d." if x is None else _it(x, 1),
        ),
        ("Rating reddituale", area("reddituale"), text),
        ("Rating finanziario", area("finanziaria"), text),
        ("Rating patrimoniale", area("patrimoniale"), text),
        ("**Altman Z''", lambda e: None, lambda x: ""),
        ("X1 capitale circolante / attivo", alt("x1"), ratio),
        ("X2 utili non distribuiti / attivo", alt("x2"), ratio),
        ("X3 EBIT / attivo", alt("x3"), ratio),
        ("X4 patrimonio netto / passivita'", alt("x4"), ratio),
        ("Z''", alt("z"), ratio),
        ("Zona", alt("zona"), lambda x: ZONE_LABELS.get(x, "n.d.")),
    ]


def render(metrics: dict[str, Any], texts: dict[str, str], out_path: str | Path) -> list[str]:
    """Scrive il PDF; ritorna gli avvisi sui testi che non entrano nei riquadri."""
    warnings = [
        f"'{block}': il testo non entra nel riquadro ed e' stato rimpicciolito: accorcialo "
        f"(circa {budgets()[block]['max_chars']} caratteri)."
        for block, text in texts.items()
        if text and not fits(block, text)
    ]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta, pages = metrics["meta"], 4
    c = Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"Analisi di bilancio – {meta.get('nome_azienda') or ''} {meta.get('anno')}")
    c.setAuthor("fs-analysis")

    _page_summary(c, metrics)
    _draw_text_blocks(c, texts, 1)
    _footer(c, meta, 1, pages)
    c.showPage()

    _draw_text_blocks(c, texts, 2)
    with tempfile.TemporaryDirectory() as tmp:
        _page_charts(c, charts.render_all(metrics, tmp))
        _footer(c, meta, 2, pages)
        c.showPage()

    _section(c, M, PAGE_H - 48, "Stato patrimoniale riclassificato")
    body, widths, bold = _year_table(metrics, SP_ROWS, with_var=True)
    bottom = _table(c, body, M, PAGE_H - 56, widths, bold)
    _section(c, M, bottom - 24, "Conto economico")
    body, widths, bold = _year_table(metrics, CE_ROWS, with_var=True)
    _table(c, body, M, bottom - 32, widths, bold)
    _footer(c, meta, 3, pages)
    c.showPage()

    _section(c, M, PAGE_H - 48, "Indici")
    body, widths, bold = _year_table(metrics, INDEX_ROWS, with_var=False)
    bottom = _table(c, body, M, PAGE_H - 56, widths, bold)
    _section(c, M, bottom - 24, "Punteggio e Altman Z''")
    body, widths, bold = _year_table(metrics, _score_rows(), with_var=False)
    _table(c, body, M, bottom - 32, widths, bold)
    _footer(c, meta, 4, pages)
    c.save()
    return warnings


def default_filename(meta: dict[str, Any]) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", str(meta.get("nome_azienda") or "azienda")).strip("_").lower()
    return f"{slug or 'azienda'}_{meta.get('anno')}_report.pdf"

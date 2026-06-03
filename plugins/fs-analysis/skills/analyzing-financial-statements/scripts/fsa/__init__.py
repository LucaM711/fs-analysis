"""fsa — engine deterministico per l'analisi di bilancio.

Separazione delle responsabilita':
- la mappatura "voce sporca -> voce canonica" e la stesura del testo sono compiti
  dell'agente (Claude) guidato dalla skill;
- questo package esegue tutto cio' che deve essere deterministico e ripetibile:
  popolamento del foglio ``Input``, verifica della quadratura al centesimo,
  ricalcolo (via LibreOffice) e lettura dei valori derivati, iniezione dei testi
  nel foglio ``Report`` ed esportazione in PDF a layout fisso.

Il foglio di calcolo modello (``assets/template.xlsx``) contiene gia' tutte le
formule di indici, grade e fido: questo engine non le duplica, le valorizza.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Tenuta in sync con plugin.json / pyproject.toml da semantic-release.
__version__ = "0.1.0"

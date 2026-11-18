"""fsa — engine deterministico per l'analisi di bilancio.

Separazione delle responsabilita':
- la mappatura "voce sporca -> voce canonica" e la stesura del testo sono compiti
  dell'agente (Claude) guidato dalla skill;
- questo package esegue tutto cio' che deve essere deterministico e ripetibile:
  validazione, quadratura al centesimo, indici, punteggio, grafici e PDF a layout fisso.

Indici, punteggio e Altman Z'' sono calcolati qui (``metrics``, ``scoring``) e
salvati in ``metrics.json``: la conversazione, i grafici e il PDF leggono solo quello.
"""

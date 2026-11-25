"""Rastreamento de objeto colorido com filtro de Kalman (Opção 01)."""
import sys

# No Windows o terminal (ou um arquivo de log) pode não ser UTF-8: troca
# caracteres que não couberem em vez de parar o programa com erro.
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

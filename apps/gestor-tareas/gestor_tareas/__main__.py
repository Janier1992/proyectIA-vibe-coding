"""Punto de entrada: python -m gestor_tareas."""

import sys

from gestor_tareas.cli import principal

if __name__ == "__main__":
    sys.exit(principal())

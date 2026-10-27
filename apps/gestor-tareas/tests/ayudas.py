"""Ayudantes compartidos por los tests de la CLI."""

import subprocess
import sys
from pathlib import Path
from typing import IO

import pytest

from gestor_tareas import cli

PROYECTO = Path(__file__).resolve().parent.parent
POSIX = pytest.mark.skipif(sys.platform == "win32", reason="permisos POSIX")


class Entorno:
    """Ayudante: ejecuta la CLI contra un archivo temporal y captura la salida."""

    def __init__(self, ruta: Path, capsys: pytest.CaptureFixture[str]) -> None:
        self.ruta = ruta
        self.capsys = capsys

    def main(self, *args: str) -> tuple[int, str, str]:
        codigo = cli.principal(["--archivo", str(self.ruta), *args])
        salida = self.capsys.readouterr()
        return codigo, salida.out, salida.err


def ejecutar(
    env: dict[str, str], *args: str, stdout: IO[str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Ejecuta `python -m gestor_tareas` como proceso real (lista de args, sin shell)."""
    return subprocess.run(  # noqa: S603 - lista de args fija, sin shell
        [sys.executable, "-m", "gestor_tareas", *args],
        cwd=PROYECTO,
        env=env,
        stdout=subprocess.PIPE if stdout is None else stdout,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )

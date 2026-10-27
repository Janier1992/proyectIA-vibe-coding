"""Fixtures compartidas: todo ocurre en tmp_path, nunca en el HOME real."""

from pathlib import Path

import pytest
from ayudas import Entorno


@pytest.fixture
def entorno(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> Entorno:
    monkeypatch.delenv("GESTOR_TAREAS_ARCHIVO", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    return Entorno(tmp_path / "tareas.json", capsys)

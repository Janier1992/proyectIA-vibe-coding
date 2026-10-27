"""Tests de integración de la CLI (criterios de aceptación 1 a 24, 27 y 28)."""

import json
import os
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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


@pytest.fixture
def entorno(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> Entorno:
    monkeypatch.delenv("GESTOR_TAREAS_ARCHIVO", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    return Entorno(tmp_path / "tareas.json", capsys)


def test_list_sin_archivo(entorno: Entorno) -> None:
    assert entorno.main("list") == (0, "No hay tareas.\n", "")
    assert not entorno.ruta.exists()


def test_add_crea_archivo(entorno: Entorno) -> None:
    codigo, salida, _ = entorno.main("add", "Comprar leche")
    assert (codigo, salida) == (0, "Tarea 1 añadida: Comprar leche [media]\n")
    datos = json.loads(entorno.ruta.read_text(encoding="utf-8"))
    assert datos["version"] == 1
    assert datos["siguiente_id"] == 2
    tarea = datos["tareas"][0]
    assert (tarea["id"], tarea["prioridad"], tarea["estado"]) == (1, "media", "pendiente")
    assert datetime.fromisoformat(tarea["creada"]).tzinfo is not None


def test_list_formato_y_orden(entorno: Entorno) -> None:
    entorno.main("add", "Comprar leche")
    entorno.main("add", "Pagar luz", "--prioridad", "alta")
    _, salida, _ = entorno.main("list")
    assert salida.splitlines() == ["   1  [ ]  media  Comprar leche", "   2  [ ]  alta   Pagar luz"]


def test_done_y_filtros(entorno: Entorno) -> None:
    entorno.main("add", "Uno")
    entorno.main("add", "Dos")
    assert entorno.main("done", "1") == (0, "Tarea 1 marcada como hecha.\n", "")
    assert entorno.main("list")[1].splitlines() == ["   2  [ ]  media  Dos"]
    assert entorno.main("list", "--estado", "hecha")[1].splitlines() == ["   1  [x]  media  Uno"]
    todas = entorno.main("list", "--estado", "todas")[1].splitlines()
    assert todas == ["   1  [x]  media  Uno", "   2  [ ]  media  Dos"]
    assert entorno.main("done", "1") == (0, "La tarea 1 ya estaba hecha.\n", "")


def test_remove_no_reutiliza_ids(entorno: Entorno) -> None:
    entorno.main("add", "Uno")
    entorno.main("add", "Dos")
    assert entorno.main("remove", "1") == (0, "Tarea 1 eliminada.\n", "")
    assert entorno.main("add", "Otra")[1] == "Tarea 3 añadida: Otra [media]\n"


def test_texto_de_200_y_201_caracteres(entorno: Entorno) -> None:
    assert entorno.main("add", "a" * 200)[0] == 0
    antes = entorno.ruta.read_bytes()
    codigo, _, err = entorno.main("add", "a" * 201)
    assert codigo == 1
    assert err == "Error: el texto supera el máximo de 200 caracteres (tiene 201).\n"
    assert entorno.ruta.read_bytes() == antes


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vacio(entorno: Entorno, texto: str) -> None:
    codigo, _, err = entorno.main("add", texto)
    assert codigo == 1
    assert err == "Error: el texto de la tarea no puede estar vacío.\n"
    assert not entorno.ruta.exists()


@pytest.mark.parametrize("texto", ["hola\x1b[31m", "a\nb"])
def test_texto_con_control(entorno: Entorno, texto: str) -> None:
    codigo, _, err = entorno.main("add", texto)
    assert codigo == 1
    assert err == "Error: el texto contiene caracteres de control no permitidos.\n"
    assert not entorno.ruta.exists()


@pytest.mark.parametrize(
    "args",
    [
        ["add", "x", "--prioridad", "urgente"],
        ["list", "--estado", "otra"],
        ["done", "abc"],
        ["done", "0"],
        ["remove", "-1"],
        [],
    ],
)
def test_errores_de_uso_codigo_2(entorno: Entorno, args: list[str]) -> None:
    codigo, _, err = entorno.main(*args)
    assert codigo == 2
    assert "usage:" in err
    assert not entorno.ruta.exists()


@pytest.mark.parametrize("comando", ["done", "remove"])
def test_id_inexistente(entorno: Entorno, comando: str) -> None:
    entorno.main("add", "Uno")
    antes = entorno.ruta.read_bytes()
    codigo, _, err = entorno.main(comando, "99")
    assert (codigo, err) == (1, "Error: no existe la tarea con ID 99.\n")
    assert entorno.ruta.read_bytes() == antes


@pytest.mark.parametrize("comando", ["done", "remove"])
def test_id_inexistente_no_crea_archivo(entorno: Entorno, comando: str) -> None:
    assert entorno.main(comando, "1")[0] == 1
    assert not entorno.ruta.exists()


def test_limite_de_mil_tareas(entorno: Entorno) -> None:
    tareas = [
        {"id": i, "texto": "t", "prioridad": "baja", "estado": "pendiente", "creada": "2026-01-01"}
        for i in range(1, 1001)
    ]
    entorno.ruta.write_text(
        json.dumps({"version": 1, "siguiente_id": 1001, "tareas": tareas}), encoding="utf-8"
    )
    codigo, _, err = entorno.main("add", "x")
    assert (codigo, err) == (1, "Error: se alcanzó el máximo de 1000 tareas.\n")


def test_acentos_se_conservan(entorno: Entorno) -> None:
    entorno.main("add", "Reunión ñandú")
    assert "Reunión ñandú" in entorno.main("list")[1]
    assert "Reunión ñandú" in entorno.ruta.read_text(encoding="utf-8")


def test_precedencia_de_archivo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    monkeypatch.setenv("GESTOR_TAREAS_ARCHIVO", str(b))
    assert cli.principal(["add", "En B"]) == 0
    assert b.exists()
    assert cli.principal(["--archivo", str(a), "add", "En A"]) == 0
    assert a.exists()
    capsys.readouterr()
    assert "En B" in json.loads(b.read_text(encoding="utf-8"))["tareas"][0]["texto"]


def test_archivo_por_defecto_en_home(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GESTOR_TAREAS_ARCHIVO", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert cli.principal(["add", "x"]) == 0
    capsys.readouterr()
    assert (tmp_path / ".gestor-tareas.json").exists()


def test_ruta_directorio(entorno: Entorno, tmp_path: Path) -> None:
    codigo = cli.principal(["--archivo", str(tmp_path), "list"])
    err = entorno.capsys.readouterr().err
    assert codigo == 3
    assert err.startswith(f"Error: ruta de archivo no válida '{tmp_path}'")


def test_ruta_padre_inexistente(entorno: Entorno, tmp_path: Path) -> None:
    ruta = tmp_path / "no" / "t.json"
    assert cli.principal(["--archivo", str(ruta), "add", "x"]) == 3
    entorno.capsys.readouterr()
    assert not ruta.parent.exists()


def test_ruta_con_byte_nulo(entorno: Entorno) -> None:
    assert cli.principal(["--archivo", "a\x00b", "list"]) == 3
    assert "ruta de archivo no válida" in entorno.capsys.readouterr().err


@POSIX
def test_symlink_no_modifica_destino(entorno: Entorno, tmp_path: Path) -> None:
    destino = tmp_path / "real.json"
    destino.write_text('{"version": 1, "siguiente_id": 1, "tareas": []}', encoding="utf-8")
    antes = destino.read_bytes()
    enlace = tmp_path / "enlace.json"
    enlace.symlink_to(destino)
    assert cli.principal(["--archivo", str(enlace), "add", "x"]) == 3
    entorno.capsys.readouterr()
    assert destino.read_bytes() == antes


@pytest.mark.parametrize("comando", [["list"], ["add", "x"]])
def test_json_corrupto(entorno: Entorno, comando: list[str]) -> None:
    entorno.ruta.write_bytes(b"{no es json")
    codigo, _, err = entorno.main(*comando)
    assert codigo == 3
    assert err == f"Error: el archivo '{entorno.ruta}' no es JSON válido; corrígelo o elimínalo.\n"
    assert "Traceback" not in err
    assert entorno.ruta.read_bytes() == b"{no es json"


def test_archivo_vacio_no_se_sobrescribe(entorno: Entorno) -> None:
    entorno.ruta.write_bytes(b"")
    assert entorno.main("add", "x")[0] == 3
    assert entorno.ruta.read_bytes() == b""


@pytest.mark.parametrize(
    "contenido",
    [
        "[]",
        '{"version": 1, "siguiente_id": 1}',
        '{"version": 1, "siguiente_id": 1, "tareas": [], "x": 1}',
        '{"version": "1", "siguiente_id": 1, "tareas": []}',
        '{"version": true, "siguiente_id": 1, "tareas": []}',
    ],
)
def test_estructura_invalida(entorno: Entorno, contenido: str) -> None:
    entorno.ruta.write_text(contenido, encoding="utf-8")
    codigo, _, err = entorno.main("list")
    assert codigo == 3
    assert "estructura inválida" in err


def test_version_2(entorno: Entorno) -> None:
    entorno.ruta.write_text('{"version": 2, "siguiente_id": 1, "tareas": []}', encoding="utf-8")
    codigo, _, err = entorno.main("list")
    assert (codigo, err) == (3, "Error: versión de esquema 2 no soportada (se esperaba 1).\n")


def test_archivo_grande_y_no_utf8_y_anidado(entorno: Entorno) -> None:
    entorno.ruta.write_bytes(b" " * (1_048_576 + 1))
    assert "tamaño máximo" in entorno.main("list")[2]
    entorno.ruta.write_bytes(b"\xff\xfe")
    assert "no es JSON válido" in entorno.main("list")[2]
    entorno.ruta.write_bytes(b"[" * 100000)
    codigo, _, err = entorno.main("list")
    assert (codigo, "Traceback" in err) == (3, False)


def test_sin_temporales_y_fallo_de_replace(
    entorno: Entorno, monkeypatch: pytest.MonkeyPatch
) -> None:
    entorno.main("add", "Uno")
    assert list(entorno.ruta.parent.glob(".gestor-tareas-*.tmp")) == []
    antes = entorno.ruta.read_bytes()

    def falla(*_args: object, **_kwargs: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", falla)
    codigo, _, err = entorno.main("add", "Dos")
    assert codigo == 3
    assert err.startswith(f"Error: no se pudo acceder al archivo '{entorno.ruta}'")
    assert entorno.ruta.read_bytes() == antes
    assert list(entorno.ruta.parent.glob(".gestor-tareas-*.tmp")) == []


@POSIX
def test_permisos_0600(entorno: Entorno) -> None:
    entorno.main("add", "Uno")
    assert stat.S_IMODE(entorno.ruta.stat().st_mode) == 0o600
    entorno.ruta.chmod(0o644)
    entorno.main("add", "Dos")
    assert stat.S_IMODE(entorno.ruta.stat().st_mode) == 0o600


def test_list_y_done_idempotente_no_escriben(entorno: Entorno) -> None:
    entorno.main("add", "Uno")
    entorno.main("done", "1")
    antes = entorno.ruta.read_bytes()
    mtime = entorno.ruta.stat().st_mtime_ns
    entorno.main("list")
    entorno.main("done", "1")
    assert entorno.ruta.read_bytes() == antes
    assert entorno.ruta.stat().st_mtime_ns == mtime


def test_help_incluye_archivo_entorno_y_codigos(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.principal(["--help"]) == 0
    salida = capsys.readouterr().out
    for esperado in ("--archivo", "GESTOR_TAREAS_ARCHIVO", "Códigos de salida"):
        assert esperado in salida


def _ejecutar(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - lista de args fija, sin shell
        [sys.executable, "-m", "gestor_tareas", *args],
        cwd=PROYECTO,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_subprocess_extremo_a_extremo(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    ruta = str(tmp_path / "t.json")
    agregado = _ejecutar(env, "--archivo", ruta, "add", "Reunión")
    listar = _ejecutar(env, "--archivo", ruta, "list")
    error = _ejecutar(env, "--archivo", ruta, "done", "9")
    assert (agregado.returncode, agregado.stdout) == (0, "Tarea 1 añadida: Reunión [media]\n")
    assert listar.returncode == 0
    assert "Reunión" in listar.stdout
    assert error.returncode == 1
    assert "Traceback" not in error.stderr

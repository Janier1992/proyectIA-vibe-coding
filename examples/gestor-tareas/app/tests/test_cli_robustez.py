"""Tests de robustez de la CLI: salida rota, --archivo, ayuda, rutas (criterios 30-36)."""

import argparse
import json
import os
import sys
from pathlib import Path

import pytest
from ayudas import POSIX, Entorno, ejecutar

from gestor_tareas import cli


class SalidaRota:
    """Sustituto de sys.stdout cuya escritura falla (disco lleno, tubería cerrada)."""

    def __init__(self, error: OSError) -> None:
        self.error = error

    def write(self, _texto: str) -> int:
        raise self.error

    def flush(self) -> None:
        raise self.error


def test_salida_llena_tras_guardar_avisa_que_se_guardo(
    entorno: Entorno, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", SalidaRota(OSError(28, "No space left on device")))
    codigo = cli.principal(["--archivo", str(entorno.ruta), "add", "Uno"])
    err = capsys.readouterr().err
    assert codigo == 3
    expected = (
        "Error: no se pudo escribir la salida: No space left on device. El cambio sí se guardó.\n"
    )
    assert err == expected
    assert "Uno" in entorno.ruta.read_text(encoding="utf-8")


def test_salida_llena_sin_cambios_no_dice_que_se_guardo(
    entorno: Entorno, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", SalidaRota(OSError(28, "No space left on device")))
    codigo = cli.principal(["--archivo", str(entorno.ruta), "list"])
    err = capsys.readouterr().err
    assert (codigo, err) == (3, "Error: no se pudo escribir la salida: No space left on device.\n")


def test_tuberia_cerrada_es_silenciosa(
    entorno: Entorno, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdout", SalidaRota(BrokenPipeError(32, "Broken pipe")))
    codigo = cli.principal(["--archivo", str(entorno.ruta), "add", "Uno"])
    assert (codigo, capsys.readouterr().err) == (0, "")


@pytest.mark.skipif(not Path("/dev/full").exists(), reason="requiere /dev/full")
def test_dev_full_extremo_a_extremo(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    ruta = str(tmp_path / "t.json")
    with Path("/dev/full").open("w", encoding="utf-8") as lleno:
        proceso = ejecutar(env, "--archivo", ruta, "add", "Uno", stdout=lleno)
    assert proceso.returncode == 3
    assert proceso.stderr == (
        "Error: no se pudo escribir la salida: No space left on device. El cambio sí se guardó.\n"
    )
    assert json.loads(Path(ruta).read_text(encoding="utf-8"))["tareas"][0]["texto"] == "Uno"


def test_stdout_ascii_con_acentos_no_falla(tmp_path: Path) -> None:
    ruta = str(tmp_path / "t.json")
    utf8 = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    assert ejecutar(utf8, "--archivo", ruta, "add", "Reunión ñandú 🎉").returncode == 0
    ascii_env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    proceso = ejecutar(ascii_env, "--archivo", ruta, "list")
    assert proceso.returncode == 0
    assert "Traceback" not in proceso.stderr
    assert "Reuni" in proceso.stdout


def test_archivo_despues_del_subcomando(entorno: Entorno) -> None:
    ruta = str(entorno.ruta)
    assert cli.principal(["add", "Uno", "--archivo", ruta]) == 0
    assert cli.principal(["list", "--archivo", ruta, "--estado", "todas"]) == 0
    assert cli.principal(["done", "1", "--archivo", ruta]) == 0
    assert cli.principal(["remove", "1", "--archivo", ruta]) == 0
    assert json.loads(entorno.ruta.read_text(encoding="utf-8"))["tareas"] == []


def test_archivo_antes_no_se_pisa_y_despues_gana(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b, c = (tmp_path / f"{n}.json" for n in "abc")
    monkeypatch.setenv("GESTOR_TAREAS_ARCHIVO", str(c))
    assert cli.principal(["--archivo", str(a), "add", "En A"]) == 0
    assert cli.principal(["--archivo", str(a), "add", "Otra en B", "--archivo", str(b)]) == 0
    assert (a.exists(), b.exists(), c.exists()) == (True, True, False)
    assert len(json.loads(a.read_text(encoding="utf-8"))["tareas"]) == 1


@pytest.mark.parametrize(
    ("antes", "estado", "esperado"),
    [
        ([], "pendiente", "No hay tareas.\n"),
        ([], "hecha", "No hay tareas.\n"),
        (["done"], "pendiente", "No hay tareas pendientes. Usa --estado todas.\n"),
        (["add"], "hecha", "No hay tareas hechas. Usa --estado todas.\n"),
    ],
)
def test_list_vacio_segun_filtro(
    entorno: Entorno, antes: list[str], estado: str, esperado: str
) -> None:
    if antes:
        entorno.main("add", "Uno")
    if antes == ["done"]:
        entorno.main("done", "1")
    assert entorno.main("list", "--estado", estado) == (0, esperado, "")


def test_list_todas_vacio_con_archivo_sin_tareas(entorno: Entorno) -> None:
    assert entorno.main("list", "--estado", "todas") == (0, "No hay tareas.\n", "")


def test_ayuda_en_espanol(capsys: pytest.CaptureFixture[str]) -> None:
    for comando in (["--help"], ["add", "-h"], ["list", "-h"], ["done", "-h"], ["remove", "-h"]):
        assert cli.principal(comando) == 0
        salida = capsys.readouterr().out
        assert salida.startswith("uso:")
        assert "opciones:" in salida
        assert "muestra esta ayuda y termina" in salida
        assert "usage:" not in salida
        assert "show this help" not in salida
    cli.principal(["add", "-h"])
    assert "(por defecto: media)" in capsys.readouterr().out
    cli.principal(["list", "-h"])
    assert "(por defecto: pendiente)" in capsys.readouterr().out
    cli.principal(["done", "-h"])
    assert "Ejemplo:" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("args", "esperado"),
    [
        (["add", "x", "--prioridad", "urgente"], "opción no válida"),
        (["add"], "faltan argumentos obligatorios: texto"),
        ([], "faltan argumentos obligatorios: COMANDO"),
        (["list", "--zzz"], "argumentos no reconocidos: --zzz"),
        (["done", "0"], "ID no válido"),
        (["remove", "-1"], "ID no válido"),
    ],
)
def test_errores_de_uso_en_espanol(entorno: Entorno, args: list[str], esperado: str) -> None:
    codigo, _, err = entorno.main(*args)
    assert codigo == 2
    assert esperado in err
    assert "invalid choice" not in err
    assert "the following arguments" not in err


@POSIX
def test_fifo_como_archivo_no_cuelga(tmp_path: Path) -> None:
    fifo = tmp_path / "tuberia"
    os.mkfifo(fifo)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proceso = ejecutar(env, "--archivo", str(fifo), "list")
    assert proceso.returncode == 3
    assert (
        proceso.stderr == f"Error: ruta de archivo no válida '{fifo}': no es un archivo regular.\n"
    )


def test_ruta_con_escape_no_emite_esc(entorno: Entorno, tmp_path: Path) -> None:
    ruta = f"{tmp_path}/\x1b[31mROJO/x.json"
    assert cli.principal(["--archivo", ruta, "list"]) == 3
    err = entorno.capsys.readouterr().err
    assert "\x1b" not in err
    assert "\\x1b[31mROJO" in err


def test_ruta_con_acentos_se_muestra_tal_cual(entorno: Entorno, tmp_path: Path) -> None:
    ruta = tmp_path / "ñandú" / "x.json"
    assert cli.principal(["--archivo", str(ruta), "list"]) == 3
    assert f"'{ruta}'" in entorno.capsys.readouterr().err


def test_ruta_con_escape_en_error_de_json(entorno: Entorno, tmp_path: Path) -> None:
    ruta = tmp_path / "a\x1bb.json"
    ruta.write_text("{no", encoding="utf-8")
    assert cli.principal(["--archivo", str(ruta), "list"]) == 3
    err = entorno.capsys.readouterr().err
    assert "\x1b" not in err
    assert "a\\x1bb.json" in err


def test_version_con_otras_claves_es_version_no_soportada(entorno: Entorno) -> None:
    entorno.ruta.write_text('{"version": 2, "otro": []}', encoding="utf-8")
    codigo, _, err = entorno.main("list")
    assert (codigo, err) == (3, "Error: versión de esquema 2 no soportada (se esperaba 1).\n")


def test_version_enorme_se_trunca(entorno: Entorno) -> None:
    entorno.ruta.write_text('{"version": ' + "9" * 500 + ', "siguiente_id": 1}', encoding="utf-8")
    codigo, _, err = entorno.main("list")
    assert codigo == 3
    assert err == f"Error: versión de esquema {'9' * 20}... no soportada (se esperaba 1).\n"


def test_help_por_subprocess_en_espanol() -> None:
    proceso = ejecutar({**os.environ, "PYTHONIOENCODING": "utf-8"}, "--help")
    assert proceso.returncode == 0
    for esperado in ("--archivo", "GESTOR_TAREAS_ARCHIVO", "Códigos de salida", "uso:"):
        assert esperado in proceso.stdout


def test_traduccion_de_opciones_y_argumento(entorno: Entorno) -> None:
    _, _, err = entorno.main("add", "x", "--prioridad", "urgente")
    assert "argumento --prioridad: opción no válida: 'urgente' (opciones: " in err
    assert "choose from" not in err
    assert "argument --prioridad" not in err


def test_traduccion_de_valor_esperado(entorno: Entorno) -> None:
    codigo, _, err = entorno.main("list", "--estado")
    assert codigo == 2
    assert "argumento --estado: se esperaba un valor" in err
    assert "expected one argument" not in err


def test_errores_de_uso_muestran_uso_en_espanol(entorno: Entorno) -> None:
    _, _, err = entorno.main("add")
    assert err.startswith("uso: ")
    assert "usage:" not in err


def test_formato_de_uso_en_espanol_sin_pasar_por_format_help() -> None:
    parser = cli.construir_parser()
    assert parser.format_usage().startswith("uso: ")
    sub = parser.parse_args(["add", "x"])
    assert sub.comando == "add"


def test_parser_ignora_kwargs_que_chocan_con_su_configuracion() -> None:
    parser = cli._Parser(
        prog="p", add_help=True, formatter_class=argparse.HelpFormatter, allow_abbrev=False
    )
    ayuda = parser.format_help()
    assert ayuda.startswith("uso: ")
    assert "muestra esta ayuda y termina" in ayuda


@POSIX
def test_descartar_stdout_apunta_el_descriptor_a_dev_null(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destino = tmp_path / "salida.txt"
    descriptor = os.open(destino, os.O_WRONLY | os.O_CREAT)

    class Falso:
        def fileno(self) -> int:
            return descriptor

    monkeypatch.setattr(sys, "stdout", Falso())
    try:
        cli._descartar_stdout()
        os.write(descriptor, b"perdido")
        assert os.fstat(descriptor).st_rdev == Path(os.devnull).stat().st_rdev
    finally:
        os.close(descriptor)
    assert destino.read_bytes() == b""

"""Tests de la capa de almacenamiento. Todo ocurre en tmp_path, nunca en el HOME real."""

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from gestor_tareas import almacen
from gestor_tareas.logica import agregar_tarea, documento_vacio
from gestor_tareas.modelo import Documento, ErrorDeAlmacen

CREADA = "2026-10-27T09:30:00+00:00"
POSIX = pytest.mark.skipif(sys.platform == "win32", reason="permisos POSIX")


def _doc() -> Documento:
    return agregar_tarea(documento_vacio(), "Reunión ñandú", "alta", CREADA)[0]


def test_resolver_ruta_precedencia(tmp_path: Path) -> None:
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    entorno = {almacen.VARIABLE_ENTORNO: str(b)}
    assert almacen.resolver_ruta(str(a), entorno) == a
    assert almacen.resolver_ruta(None, entorno) == b


def test_resolver_ruta_por_defecto_y_variable_vacia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    esperado = tmp_path / ".gestor-tareas.json"
    assert almacen.resolver_ruta(None, {}) == esperado
    assert almacen.resolver_ruta(None, {almacen.VARIABLE_ENTORNO: ""}) == esperado


@pytest.mark.parametrize("texto", ["", "   ", "a\x00b"])
def test_resolver_ruta_rechaza_invalidas(texto: str) -> None:
    with pytest.raises(ErrorDeAlmacen, match="ruta de archivo no válida"):
        almacen.resolver_ruta(texto, {})


def test_resolver_ruta_expande_usuario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    assert almacen.resolver_ruta("~/x.json", {}) == tmp_path / "x.json"


def test_cargar_inexistente_es_vacio_y_no_crea(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    assert almacen.cargar(ruta) == documento_vacio()
    assert not ruta.exists()


def test_guardar_y_cargar_ida_y_vuelta(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    almacen.guardar(ruta, _doc())
    assert almacen.cargar(ruta) == _doc()
    contenido = ruta.read_text(encoding="utf-8")
    assert "Reunión ñandú" in contenido
    assert contenido.endswith("}\n")
    assert json.loads(contenido)["version"] == 1


def test_directorio_y_padre_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ErrorDeAlmacen, match="es un directorio"):
        almacen.cargar(tmp_path)
    inexistente = tmp_path / "no" / "t.json"
    with pytest.raises(ErrorDeAlmacen, match="directorio padre no existe"):
        almacen.guardar(inexistente, _doc())
    assert not inexistente.parent.exists()


@POSIX
def test_symlink_rechazado_y_destino_intacto(tmp_path: Path) -> None:
    destino = tmp_path / "real.json"
    almacen.guardar(destino, _doc())
    antes = destino.read_bytes()
    enlace = tmp_path / "enlace.json"
    enlace.symlink_to(destino)
    with pytest.raises(ErrorDeAlmacen, match="enlace simbólico"):
        almacen.cargar(enlace)
    with pytest.raises(ErrorDeAlmacen, match="enlace simbólico"):
        almacen.guardar(enlace, documento_vacio())
    assert destino.read_bytes() == antes


@pytest.mark.parametrize("contenido", [b"{no es json", b"", b"   \n", b"\xff\xfe", b"[" * 100000])
def test_json_corrupto(tmp_path: Path, contenido: bytes) -> None:
    ruta = tmp_path / "t.json"
    ruta.write_bytes(contenido)
    with pytest.raises(ErrorDeAlmacen, match="no es JSON válido"):
        almacen.cargar(ruta)
    assert ruta.read_bytes() == contenido


def test_estructura_invalida_incluye_ruta_mostrada(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    ruta.write_text("[]", encoding="utf-8")
    with pytest.raises(ErrorDeAlmacen, match=r"'rel\.json' tiene una estructura inválida"):
        almacen.cargar(ruta, "rel.json")


def test_version_desconocida(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    ruta.write_text('{"version": 2, "siguiente_id": 1, "tareas": []}', encoding="utf-8")
    with pytest.raises(
        ErrorDeAlmacen, match=r"versión de esquema 2 no soportada \(se esperaba 1\)"
    ):
        almacen.cargar(ruta)


def test_archivo_demasiado_grande(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    ruta.write_bytes(b" " * (1_048_576 + 1))
    with pytest.raises(ErrorDeAlmacen, match=r"supera el tamaño máximo permitido \(1 MiB\)"):
        almacen.cargar(ruta)


def test_archivo_que_crece_tras_stat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ruta = tmp_path / "t.json"
    ruta.write_bytes(b" " * (1_048_576 + 10))
    original = Path.stat

    def stat_falso(self: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        resultado = original(self, follow_symlinks=follow_symlinks)
        if self == ruta:
            return os.stat_result((resultado.st_mode, *resultado[1:6], 10, *resultado[7:]))
        return resultado

    monkeypatch.setattr(Path, "stat", stat_falso)
    with pytest.raises(ErrorDeAlmacen, match="supera el tamaño"):
        almacen.cargar(ruta)


@POSIX
def test_permisos_0600_al_crear_y_reescribir(tmp_path: Path) -> None:
    ruta = tmp_path / "t.json"
    almacen.guardar(ruta, _doc())
    assert stat.S_IMODE(ruta.stat().st_mode) == 0o600
    ruta.chmod(0o644)
    almacen.guardar(ruta, documento_vacio())
    assert stat.S_IMODE(ruta.stat().st_mode) == 0o600


def test_sin_temporales_tras_guardar(tmp_path: Path) -> None:
    almacen.guardar(tmp_path / "t.json", _doc())
    assert list(tmp_path.glob(".gestor-tareas-*.tmp")) == []


def test_fallo_de_replace_deja_original_y_sin_temporales(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ruta = tmp_path / "t.json"
    almacen.guardar(ruta, _doc())
    antes = ruta.read_bytes()

    def falla(*_args: object, **_kwargs: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", falla)
    with pytest.raises(ErrorDeAlmacen, match="no se pudo acceder al archivo"):
        almacen.guardar(ruta, documento_vacio())
    assert ruta.read_bytes() == antes
    assert list(tmp_path.glob(".gestor-tareas-*.tmp")) == []


def test_fallo_de_escritura_limpia_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def falla(_fd: int) -> None:
        raise OSError(5, "Input/output error")

    monkeypatch.setattr(os, "fsync", falla)
    with pytest.raises(ErrorDeAlmacen, match="Input/output error"):
        almacen.guardar(tmp_path / "t.json", _doc())
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("normal/ñandú.json", "normal/ñandú.json"),
        ("a\x1b[31mb", "a\\x1b[31mb"),
        ("a\x7fb", "a\\x7fb"),
        ("a\nb", "a\\nb"),
    ],
)
def test_texto_seguro(texto: str, esperado: str) -> None:
    assert almacen.texto_seguro(texto) == esperado


@POSIX
def test_cargar_rechaza_archivo_no_regular(tmp_path: Path) -> None:
    fifo = tmp_path / "tuberia"
    os.mkfifo(fifo)
    with pytest.raises(ErrorDeAlmacen, match="no es un archivo regular"):
        almacen.guardar(fifo, _doc())

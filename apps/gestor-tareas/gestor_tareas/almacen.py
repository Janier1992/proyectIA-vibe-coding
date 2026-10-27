"""Capa de E/S: resolver la ruta, cargar y guardar el archivo JSON de forma atómica."""

import contextlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from gestor_tareas.logica import documento_a_datos, documento_vacio, validar_documento
from gestor_tareas.modelo import (
    TAMANO_MAXIMO_ARCHIVO,
    Documento,
    ErrorDeAlmacen,
    ErrorDeEstructura,
)

VARIABLE_ENTORNO = "GESTOR_TAREAS_ARCHIVO"
NOMBRE_POR_DEFECTO = ".gestor-tareas.json"
PERMISOS_ARCHIVO = 0o600


def ruta_indicada(archivo: str | None, entorno: Mapping[str, str]) -> str | None:
    """Texto de la ruta tal como la dio el usuario (None si se usa la de por defecto)."""
    if archivo is not None:
        return archivo
    return entorno.get(VARIABLE_ENTORNO) or None


def _ruta_invalida(texto: str, motivo: str) -> ErrorDeAlmacen:
    return ErrorDeAlmacen(f"ruta de archivo no válida '{texto}': {motivo}.")


def resolver_ruta(archivo: str | None, entorno: Mapping[str, str]) -> Path:
    """Aplica la precedencia --archivo > variable de entorno > por defecto."""
    texto = ruta_indicada(archivo, entorno)
    if texto is None:
        return Path.home() / NOMBRE_POR_DEFECTO
    if not texto.strip():
        raise _ruta_invalida(texto, "la ruta está vacía")
    if "\x00" in texto:
        raise _ruta_invalida(texto.replace("\x00", ""), "contiene un byte nulo")
    return Path(texto).expanduser().absolute()


def _validar_destino(ruta: Path, mostrar: str) -> None:
    if ruta.is_symlink():
        raise _ruta_invalida(mostrar, "es un enlace simbólico")
    if ruta.is_dir():
        raise _ruta_invalida(mostrar, "es un directorio")
    if not ruta.parent.is_dir():
        raise _ruta_invalida(mostrar, "el directorio padre no existe")


def _error_es(mostrar: str, exc: OSError) -> ErrorDeAlmacen:
    motivo = exc.strerror or "error de entrada/salida"
    return ErrorDeAlmacen(f"no se pudo acceder al archivo '{mostrar}': {motivo}.")


def _leer_bytes(ruta: Path, mostrar: str) -> bytes:
    demasiado_grande = ErrorDeAlmacen(
        f"el archivo '{mostrar}' supera el tamaño máximo permitido (1 MiB)."
    )
    if ruta.stat().st_size > TAMANO_MAXIMO_ARCHIVO:
        raise demasiado_grande
    with ruta.open("rb") as manejador:
        contenido = manejador.read(TAMANO_MAXIMO_ARCHIVO + 1)
    if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
        raise demasiado_grande
    return contenido


def _parsear(contenido: bytes, mostrar: str) -> Documento:
    try:
        datos: object = json.loads(contenido.decode("utf-8"))
    except (ValueError, RecursionError):
        # UnicodeDecodeError y JSONDecodeError son subclases de ValueError.
        msg = f"el archivo '{mostrar}' no es JSON válido; corrígelo o elimínalo."
        raise ErrorDeAlmacen(msg) from None
    try:
        return validar_documento(datos)
    except ErrorDeEstructura as exc:
        msg = f"el archivo '{mostrar}' tiene una estructura inválida: {exc}."
        raise ErrorDeAlmacen(msg) from None


def cargar(ruta: Path, mostrar: str | None = None) -> Documento:
    """Carga y valida el documento; un archivo inexistente es una lista vacía."""
    texto = mostrar if mostrar is not None else str(ruta)
    _validar_destino(ruta, texto)
    try:
        if not ruta.exists():
            return documento_vacio()
        contenido = _leer_bytes(ruta, texto)
    except OSError as exc:
        raise _error_es(texto, exc) from None
    return _parsear(contenido, texto)


def _escribir_temporal(ruta: Path, texto: str) -> Path:
    descriptor, nombre = tempfile.mkstemp(dir=ruta.parent, prefix=".gestor-tareas-", suffix=".tmp")
    temporal = Path(nombre)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as manejador:
            manejador.write(texto)
            manejador.flush()
            os.fsync(manejador.fileno())
        temporal.chmod(PERMISOS_ARCHIVO)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            temporal.unlink()
        raise
    return temporal


def guardar(ruta: Path, doc: Documento, mostrar: str | None = None) -> None:
    """Guarda el documento con escritura atómica y permisos 0o600."""
    texto = mostrar if mostrar is not None else str(ruta)
    _validar_destino(ruta, texto)
    serializado = json.dumps(documento_a_datos(doc), ensure_ascii=False, indent=2, sort_keys=True)
    try:
        temporal = _escribir_temporal(ruta, serializado + "\n")
        try:
            temporal.replace(ruta)
        finally:
            with contextlib.suppress(FileNotFoundError):
                temporal.unlink()
    except OSError as exc:
        raise _error_es(texto, exc) from None

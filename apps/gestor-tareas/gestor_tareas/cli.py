"""Interfaz de línea de comandos: argparse, formateo de salida y códigos de salida."""

import argparse
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from gestor_tareas import almacen, logica
from gestor_tareas.modelo import (
    ESTADOS,
    PRIORIDADES,
    Documento,
    ErrorDeAlmacen,
    ErrorDeDominio,
    Tarea,
)

PROGRAMA = "gestor-tareas"
SALIDA_OK = 0
SALIDA_DOMINIO = 1
SALIDA_ALMACEN = 3

EPILOGO = f"""\
Archivo de datos (precedencia): --archivo > variable de entorno
{almacen.VARIABLE_ENTORNO} > ~/{almacen.NOMBRE_POR_DEFECTO}
(--archivo es una opción global y va antes del subcomando).

Códigos de salida:
  0  éxito
  1  error de validación o de dominio (texto inválido, ID inexistente, límite)
  2  error de uso de la CLI (argumentos inválidos)
  3  error de almacenamiento (JSON corrupto, esquema inválido, ruta o E/S)
"""


def _id_valido(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError:
        msg = f"ID no válido: '{valor}' (se esperaba un entero >= 1)"
        raise argparse.ArgumentTypeError(msg) from None
    if numero < 1:
        msg = f"ID no válido: {numero} (debe ser >= 1)"
        raise argparse.ArgumentTypeError(msg)
    return numero


def construir_parser() -> argparse.ArgumentParser:
    """Construye el parser con sus subcomandos."""
    parser = argparse.ArgumentParser(
        prog=PROGRAMA,
        description="Gestiona una lista personal de tareas en un archivo JSON local.",
        epilog=EPILOGO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--archivo",
        metavar="RUTA",
        help=f"archivo JSON de tareas (por defecto: ${almacen.VARIABLE_ENTORNO} o "
        f"~/{almacen.NOMBRE_POR_DEFECTO}); va antes del subcomando",
    )
    sub = parser.add_subparsers(dest="comando", required=True, metavar="COMANDO")
    agregar = sub.add_parser("add", help="añade una tarea pendiente")
    agregar.add_argument("texto", help="texto de la tarea (máximo 200 caracteres)")
    agregar.add_argument("--prioridad", choices=PRIORIDADES, default="media")
    listar = sub.add_parser("list", help="lista tareas ordenadas por ID")
    listar.add_argument("--estado", choices=(*ESTADOS, "todas"), default="pendiente")
    hecha = sub.add_parser("done", help="marca una tarea como hecha")
    hecha.add_argument("id", type=_id_valido, help="ID de la tarea (entero >= 1)")
    quitar = sub.add_parser("remove", help="elimina una tarea")
    quitar.add_argument("id", type=_id_valido, help="ID de la tarea (entero >= 1)")
    return parser


def formatear_tarea(tarea: Tarea) -> str:
    """Una línea de list: id, marcador, prioridad y texto."""
    marca = "x" if tarea.estado == "hecha" else " "
    return f"{tarea.id:>4}  [{marca}]  {tarea.prioridad:<5}  {tarea.texto}"


def _ahora() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _ejecutar_add(doc: Documento, args: argparse.Namespace) -> tuple[Documento | None, str]:
    nuevo, tarea = logica.agregar_tarea(doc, args.texto, args.prioridad, _ahora())
    return nuevo, f"Tarea {tarea.id} añadida: {tarea.texto} [{tarea.prioridad}]"


def _ejecutar_list(doc: Documento, args: argparse.Namespace) -> tuple[Documento | None, str]:
    tareas = logica.filtrar_tareas(doc, args.estado)
    if not tareas:
        return None, "No hay tareas."
    return None, "\n".join(formatear_tarea(t) for t in tareas)


def _ejecutar_done(doc: Documento, args: argparse.Namespace) -> tuple[Documento | None, str]:
    nuevo, cambio = logica.marcar_hecha(doc, args.id)
    if not cambio:
        return None, f"La tarea {args.id} ya estaba hecha."
    return nuevo, f"Tarea {args.id} marcada como hecha."


def _ejecutar_remove(doc: Documento, args: argparse.Namespace) -> tuple[Documento | None, str]:
    return logica.eliminar_tarea(doc, args.id), f"Tarea {args.id} eliminada."


COMANDOS = {
    "add": _ejecutar_add,
    "list": _ejecutar_list,
    "done": _ejecutar_done,
    "remove": _ejecutar_remove,
}


def _ciclo(args: argparse.Namespace) -> str:
    """Cargar, aplicar la función pura y guardar solo si hubo cambios."""
    entorno = os.environ
    ruta: Path = almacen.resolver_ruta(args.archivo, entorno)
    mostrar = almacen.ruta_indicada(args.archivo, entorno) or str(ruta)
    doc = almacen.cargar(ruta, mostrar)
    nuevo, mensaje = COMANDOS[args.comando](doc, args)
    if nuevo is not None:
        almacen.guardar(ruta, nuevo, mostrar)
    return mensaje


def _codigo_de_salida(exc: SystemExit) -> int:
    return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)


def principal(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la CLI y devuelve el código de salida."""
    try:
        args = construir_parser().parse_args(argv)
    except SystemExit as exc:
        return _codigo_de_salida(exc)
    try:
        mensaje = _ciclo(args)
    except ErrorDeDominio as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return SALIDA_DOMINIO
    except ErrorDeAlmacen as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return SALIDA_ALMACEN
    print(mensaje)
    return SALIDA_OK

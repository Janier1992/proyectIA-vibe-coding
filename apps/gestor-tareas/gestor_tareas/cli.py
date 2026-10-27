"""Interfaz de línea de comandos: argparse, formateo de salida y códigos de salida."""

import argparse
import contextlib
import io
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

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
SALIDA_USO = 2
SALIDA_ALMACEN = 3
MAX_MOTIVO = 100

EPILOGO = f"""\
Archivo de datos (precedencia): --archivo > variable de entorno
{almacen.VARIABLE_ENTORNO} > ~/{almacen.NOMBRE_POR_DEFECTO}
(--archivo puede ir antes o después del subcomando).

Códigos de salida:
  0  éxito
  1  error de validación o de dominio (texto inválido, ID inexistente, límite)
  2  error de uso de la CLI (argumentos inválidos)
  3  error de almacenamiento (JSON corrupto, esquema inválido, ruta o E/S)
     o al escribir la salida (si el comando modificaba datos, el cambio sí se guardó)
"""

# Traducciones de fragmentos de los mensajes de argparse. Lo que no esté aquí se muestra
# tal cual (en inglés); la limitación está documentada en el README.
TRADUCCIONES = (
    ("the following arguments are required: ", "faltan argumentos obligatorios: "),
    ("unrecognized arguments: ", "argumentos no reconocidos: "),
    ("expected one argument", "se esperaba un valor"),
    ("argument ", "argumento "),
    ("invalid choice: ", "opción no válida: "),
    ("(choose from ", "(opciones: "),
)


class _Formateador(argparse.RawDescriptionHelpFormatter):
    """Igual que RawDescriptionHelpFormatter pero con el prefijo de uso en español."""

    def format_help(self) -> str:
        ayuda = super().format_help()
        return "uso: " + ayuda[len("usage: ") :] if ayuda.startswith("usage: ") else ayuda


class _Parser(argparse.ArgumentParser):
    """ArgumentParser con ayuda y errores en español."""

    def __init__(
        self,
        prog: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
    ) -> None:
        super().__init__(
            prog=prog,
            description=description,
            epilog=epilog,
            add_help=False,
            formatter_class=_Formateador,
        )
        self._positionals.title = "argumentos posicionales"
        self._optionals.title = "opciones"
        self.add_argument("-h", "--help", action="help", help="muestra esta ayuda y termina")

    def error(self, message: str) -> NoReturn:
        for original, traduccion in TRADUCCIONES:
            message = message.replace(original, traduccion)
        self.print_usage(sys.stderr)
        self.exit(SALIDA_USO, f"{self.prog}: error: {message}\n")


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


def _archivo_en_subcomando(parser: argparse.ArgumentParser, ayuda: str) -> None:
    """--archivo tras el subcomando; SUPPRESS evita pisar el valor dado antes de él."""
    parser.add_argument("--archivo", metavar="RUTA", default=argparse.SUPPRESS, help=ayuda)


def construir_parser() -> argparse.ArgumentParser:
    """Construye el parser con sus subcomandos."""
    ayuda_archivo = (
        f"archivo JSON de tareas (por defecto: ${almacen.VARIABLE_ENTORNO} o "
        f"~/{almacen.NOMBRE_POR_DEFECTO}); puede ir antes o después del subcomando"
    )
    parser = _Parser(
        prog=PROGRAMA,
        description="Gestiona una lista personal de tareas en un archivo JSON local.",
        epilog=EPILOGO,
    )
    parser.add_argument("--archivo", metavar="RUTA", help=ayuda_archivo)
    sub = parser.add_subparsers(
        dest="comando", required=True, metavar="COMANDO", parser_class=_Parser
    )
    agregar = sub.add_parser(
        "add",
        help="añade una tarea pendiente",
        epilog=f'Ejemplo:\n  {PROGRAMA} add "Pagar luz" --prioridad alta',
    )
    _archivo_en_subcomando(agregar, ayuda_archivo)
    agregar.add_argument("texto", help="texto de la tarea (máximo 200 caracteres)")
    agregar.add_argument(
        "--prioridad", choices=PRIORIDADES, default="media", help="prioridad (por defecto: media)"
    )
    listar = sub.add_parser(
        "list",
        help="lista tareas ordenadas por ID",
        epilog=f"Ejemplo:\n  {PROGRAMA} list --estado todas",
    )
    _archivo_en_subcomando(listar, ayuda_archivo)
    listar.add_argument(
        "--estado",
        choices=(*ESTADOS, "todas"),
        default="pendiente",
        help="estado a mostrar (por defecto: pendiente)",
    )
    hecha = sub.add_parser(
        "done",
        help="marca una tarea como hecha",
        epilog=f"Ejemplo:\n  {PROGRAMA} done 3",
    )
    _archivo_en_subcomando(hecha, ayuda_archivo)
    hecha.add_argument("id", type=_id_valido, help="ID de la tarea (entero >= 1)")
    quitar = sub.add_parser(
        "remove",
        help="elimina una tarea",
        epilog=f"Ejemplo:\n  {PROGRAMA} remove 3",
    )
    _archivo_en_subcomando(quitar, ayuda_archivo)
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


def _mensaje_lista_vacia(doc: Documento, estado: str) -> str:
    if not doc.tareas:
        return "No hay tareas."
    return f"No hay tareas {estado}s. Usa --estado todas."


def _ejecutar_list(doc: Documento, args: argparse.Namespace) -> tuple[Documento | None, str]:
    tareas = logica.filtrar_tareas(doc, args.estado)
    if not tareas:
        return None, _mensaje_lista_vacia(doc, args.estado)
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


def _ciclo(args: argparse.Namespace) -> tuple[str, bool]:
    """Cargar, aplicar la función pura y guardar solo si hubo cambios."""
    entorno = os.environ
    ruta: Path = almacen.resolver_ruta(args.archivo, entorno)
    mostrar = almacen.texto_seguro(almacen.ruta_indicada(args.archivo, entorno) or str(ruta))
    doc = almacen.cargar(ruta, mostrar)
    nuevo, mensaje = COMANDOS[args.comando](doc, args)
    if nuevo is not None:
        almacen.guardar(ruta, nuevo, mostrar)
    return mensaje, nuevo is not None


def _codigo_de_salida(exc: SystemExit) -> int:
    return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)


def _configurar_flujos() -> None:
    """Un carácter no codificable se sustituye en vez de abortar con UnicodeEncodeError."""
    for flujo in (sys.stdout, sys.stderr):
        if isinstance(flujo, io.TextIOWrapper):
            flujo.reconfigure(errors="replace")


def _descartar_stdout() -> None:
    """Redirige stdout a /dev/null para que el vaciado al salir no vuelva a fallar."""
    with contextlib.suppress(OSError, ValueError, AttributeError):
        destino = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(destino, sys.stdout.fileno())
        finally:
            os.close(destino)


def _escribir_error(texto: str) -> None:
    with contextlib.suppress(OSError):
        print(texto, file=sys.stderr)


def _emitir(mensaje: str, *, guardado: bool) -> int:
    """Imprime el resultado; un fallo de salida no es traza ni oculta que se guardó."""
    try:
        print(mensaje)
        sys.stdout.flush()
    except BrokenPipeError:
        _descartar_stdout()
        return SALIDA_OK
    except OSError as exc:
        _descartar_stdout()
        motivo = (exc.strerror or "error de entrada/salida")[:MAX_MOTIVO]
        aviso = " El cambio sí se guardó." if guardado else ""
        _escribir_error(f"Error: no se pudo escribir la salida: {motivo}.{aviso}")
        return SALIDA_ALMACEN
    return SALIDA_OK


def principal(argv: Sequence[str] | None = None) -> int:
    """Ejecuta la CLI y devuelve el código de salida."""
    _configurar_flujos()
    try:
        args = construir_parser().parse_args(argv)
    except SystemExit as exc:
        return _codigo_de_salida(exc)
    except BrokenPipeError:
        _descartar_stdout()
        return SALIDA_OK
    try:
        mensaje, guardado = _ciclo(args)
    except ErrorDeDominio as exc:
        _escribir_error(f"Error: {exc}")
        return SALIDA_DOMINIO
    except ErrorDeAlmacen as exc:
        _escribir_error(f"Error: {exc}")
        return SALIDA_ALMACEN
    return _emitir(mensaje, guardado=guardado)

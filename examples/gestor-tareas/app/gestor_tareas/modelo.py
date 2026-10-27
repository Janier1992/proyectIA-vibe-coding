"""Constantes, tipos y errores de dominio."""

from dataclasses import dataclass

LONGITUD_MAXIMA_TEXTO = 200
MAXIMO_TAREAS = 1000
TAMANO_MAXIMO_ARCHIVO = 1_048_576
VERSION_ESQUEMA = 1
PRIORIDADES = ("alta", "media", "baja")
ESTADOS = ("pendiente", "hecha")


class ErrorDeDominio(Exception):
    """Error de validación o de dominio (código de salida 1)."""


class ErrorDeAlmacen(Exception):
    """Error de almacenamiento (código de salida 3)."""


class ErrorDeEstructura(ErrorDeAlmacen):
    """Estructura inválida; el mensaje es solo el detalle, sin ruta."""


@dataclass(frozen=True, slots=True)
class Tarea:
    """Una tarea almacenada."""

    id: int
    texto: str
    prioridad: str
    estado: str
    creada: str


@dataclass(frozen=True, slots=True)
class Documento:
    """Contenido completo del archivo."""

    siguiente_id: int
    tareas: tuple[Tarea, ...]

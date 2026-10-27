"""Funciones puras de negocio: sin E/S, sin reloj, sin efectos secundarios."""

from dataclasses import replace
from datetime import datetime
from typing import NoReturn

from gestor_tareas.modelo import (
    ESTADOS,
    LONGITUD_MAXIMA_TEXTO,
    MAXIMO_TAREAS,
    PRIORIDADES,
    VERSION_ESQUEMA,
    Documento,
    ErrorDeAlmacen,
    ErrorDeDominio,
    ErrorDeEstructura,
    Tarea,
)

CLAVES_RAIZ = frozenset({"version", "siguiente_id", "tareas"})
CLAVES_TAREA = frozenset({"id", "texto", "prioridad", "estado", "creada"})
MAX_DIGITOS_VERSION = 20
FILTROS_ESTADO = (*ESTADOS, "todas")


def _es_entero(valor: object) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def _texto_imprimible(texto: str) -> bool:
    return all(c == " " or c.isprintable() for c in texto)


def normalizar_texto(texto: str) -> str:
    """Limpia y valida el texto de una tarea."""
    limpio = texto.strip()
    if not limpio:
        msg = "el texto de la tarea no puede estar vacío."
        raise ErrorDeDominio(msg)
    if len(limpio) > LONGITUD_MAXIMA_TEXTO:
        msg = (
            f"el texto supera el máximo de {LONGITUD_MAXIMA_TEXTO} caracteres "
            f"(tiene {len(limpio)})."
        )
        raise ErrorDeDominio(msg)
    if not _texto_imprimible(limpio):
        msg = "el texto contiene caracteres de control no permitidos."
        raise ErrorDeDominio(msg)
    return limpio


def validar_prioridad(valor: str) -> str:
    """Devuelve la prioridad si es válida."""
    if valor not in PRIORIDADES:
        msg = f"prioridad no válida (permitidas: {', '.join(PRIORIDADES)})."
        raise ErrorDeDominio(msg)
    return valor


def documento_vacio() -> Documento:
    """Documento sin tareas."""
    return Documento(siguiente_id=1, tareas=())


def agregar_tarea(
    doc: Documento, texto: str, prioridad: str, creada: str
) -> tuple[Documento, Tarea]:
    """Añade una tarea pendiente y devuelve el documento nuevo y la tarea."""
    limpio = normalizar_texto(texto)
    validar_prioridad(prioridad)
    if len(doc.tareas) >= MAXIMO_TAREAS:
        msg = f"se alcanzó el máximo de {MAXIMO_TAREAS} tareas."
        raise ErrorDeDominio(msg)
    tarea = Tarea(
        id=doc.siguiente_id, texto=limpio, prioridad=prioridad, estado="pendiente", creada=creada
    )
    nuevo = Documento(siguiente_id=doc.siguiente_id + 1, tareas=(*doc.tareas, tarea))
    return nuevo, tarea


def filtrar_tareas(doc: Documento, estado: str) -> tuple[Tarea, ...]:
    """Tareas por estado, ordenadas por id ascendente."""
    if estado not in FILTROS_ESTADO:
        msg = f"estado no válido (permitidos: {', '.join(FILTROS_ESTADO)})."
        raise ErrorDeDominio(msg)
    elegidas = [t for t in doc.tareas if estado in ("todas", t.estado)]
    return tuple(sorted(elegidas, key=lambda t: t.id))


def _buscar(doc: Documento, id_tarea: int) -> Tarea:
    for tarea in doc.tareas:
        if tarea.id == id_tarea:
            return tarea
    msg = f"no existe la tarea con ID {id_tarea}."
    raise ErrorDeDominio(msg)


def marcar_hecha(doc: Documento, id_tarea: int) -> tuple[Documento, bool]:
    """Marca como hecha; devuelve False si ya lo estaba."""
    tarea = _buscar(doc, id_tarea)
    if tarea.estado == "hecha":
        return doc, False
    tareas = tuple(replace(t, estado="hecha") if t.id == id_tarea else t for t in doc.tareas)
    return Documento(siguiente_id=doc.siguiente_id, tareas=tareas), True


def eliminar_tarea(doc: Documento, id_tarea: int) -> Documento:
    """Elimina la tarea; los ID no se reutilizan."""
    _buscar(doc, id_tarea)
    tareas = tuple(t for t in doc.tareas if t.id != id_tarea)
    return Documento(siguiente_id=doc.siguiente_id, tareas=tareas)


def _rechazar(detalle: str) -> NoReturn:
    raise ErrorDeEstructura(detalle)


def _validar_tarea(dato: object) -> Tarea:
    if not isinstance(dato, dict):
        _rechazar("cada tarea debe ser un objeto")
    if set(dato) != CLAVES_TAREA:
        _rechazar("las claves de una tarea no son las esperadas")
    id_tarea, texto = dato["id"], dato["texto"]
    prioridad, estado, creada = dato["prioridad"], dato["estado"], dato["creada"]
    if not _es_entero(id_tarea) or id_tarea < 1:
        _rechazar("'id' debe ser un entero >= 1")
    if not isinstance(texto, str):
        _rechazar("'texto' debe ser una cadena")
    if prioridad not in PRIORIDADES:
        _rechazar("'prioridad' no es válida")
    if estado not in ESTADOS:
        _rechazar("'estado' no es válido")
    _validar_creada(creada)
    try:
        limpio = normalizar_texto(texto)
    except ErrorDeDominio:
        _rechazar("'texto' no es válido")
    if limpio != texto:
        _rechazar("'texto' no es válido")
    return Tarea(id=id_tarea, texto=texto, prioridad=prioridad, estado=estado, creada=creada)


def _validar_creada(creada: object) -> None:
    if not isinstance(creada, str):
        _rechazar("'creada' debe ser una cadena")
    try:
        datetime.fromisoformat(creada)
    except ValueError:
        _rechazar("'creada' no es una fecha ISO 8601")


def _version_corta(version: object) -> str:
    texto = str(version)
    return texto if len(texto) <= MAX_DIGITOS_VERSION else texto[:MAX_DIGITOS_VERSION] + "..."


def _validar_cabecera(datos: dict[object, object]) -> None:
    version = datos.get("version")
    if _es_entero(version) and version != VERSION_ESQUEMA:
        corta = _version_corta(version)
        msg = f"versión de esquema {corta} no soportada (se esperaba {VERSION_ESQUEMA})."
        raise ErrorDeAlmacen(msg)
    if set(datos) != CLAVES_RAIZ:
        _rechazar("las claves de la raíz no son las esperadas")
    if not _es_entero(version):
        _rechazar("'version' debe ser un entero")


def validar_documento(datos: object) -> Documento:
    """Convierte datos de json.loads en Documento aplicando todas las reglas."""
    if not isinstance(datos, dict):
        _rechazar("la raíz debe ser un objeto")
    _validar_cabecera(datos)
    siguiente, lista = datos["siguiente_id"], datos["tareas"]
    if not _es_entero(siguiente) or siguiente < 1:
        _rechazar("'siguiente_id' debe ser un entero >= 1")
    if not isinstance(lista, list):
        _rechazar("'tareas' debe ser una lista")
    if len(lista) > MAXIMO_TAREAS:
        _rechazar(f"hay más de {MAXIMO_TAREAS} tareas")
    tareas = tuple(_validar_tarea(d) for d in lista)
    ids = [t.id for t in tareas]
    if len(set(ids)) != len(ids):
        _rechazar("hay IDs duplicados")
    if ids and siguiente <= max(ids):
        _rechazar("'siguiente_id' debe ser mayor que el máximo ID")
    return Documento(siguiente_id=siguiente, tareas=tareas)


def documento_a_datos(doc: Documento) -> dict[str, object]:
    """Inversa de validar_documento."""
    tareas: list[object] = [
        {
            "id": t.id,
            "texto": t.texto,
            "prioridad": t.prioridad,
            "estado": t.estado,
            "creada": t.creada,
        }
        for t in doc.tareas
    ]
    return {"version": VERSION_ESQUEMA, "siguiente_id": doc.siguiente_id, "tareas": tareas}

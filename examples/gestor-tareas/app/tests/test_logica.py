"""Tests de la lógica pura (criterios 25 y 26 y validación de entradas)."""

import ast
import copy
from pathlib import Path

import pytest

from gestor_tareas import logica
from gestor_tareas.modelo import (
    Documento,
    ErrorDeAlmacen,
    ErrorDeDominio,
    ErrorDeEstructura,
    Tarea,
)

CREADA = "2026-10-27T09:30:00+00:00"


def _tarea(id_tarea: int = 1, estado: str = "pendiente") -> Tarea:
    return Tarea(id=id_tarea, texto="x", prioridad="media", estado=estado, creada=CREADA)


def _tarea_datos(**cambios: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": 2,
        "texto": "a",
        "prioridad": "alta",
        "estado": "hecha",
        "creada": CREADA,
    }
    base.update(cambios)
    return base


def _datos_validos(tareas: list[object] | None = None) -> dict[str, object]:
    lista = [_tarea_datos()] if tareas is None else tareas
    return {"version": 1, "siguiente_id": 5000, "tareas": lista}


def test_normalizar_texto_limpia_espacios() -> None:
    assert logica.normalizar_texto("  hola  ") == "hola"


@pytest.mark.parametrize("texto", ["", "   "])
def test_normalizar_texto_vacio(texto: str) -> None:
    with pytest.raises(ErrorDeDominio, match="no puede estar vacío"):
        logica.normalizar_texto(texto)


def test_normalizar_texto_limites() -> None:
    assert len(logica.normalizar_texto("a" * 200)) == 200
    with pytest.raises(ErrorDeDominio, match=r"\(tiene 201\)"):
        logica.normalizar_texto("a" * 201)


@pytest.mark.parametrize("texto", ["\x1b[31mhola", "a\nb", "a\tb", "\x00", "a\u200bb"])
def test_normalizar_texto_rechaza_control(texto: str) -> None:
    with pytest.raises(ErrorDeDominio, match="caracteres de control"):
        logica.normalizar_texto(texto)


def test_normalizar_texto_acepta_acentos_y_emoji() -> None:
    assert logica.normalizar_texto("Reunión ñandú 😀") == "Reunión ñandú 😀"


def test_validar_prioridad() -> None:
    assert logica.validar_prioridad("alta") == "alta"
    with pytest.raises(ErrorDeDominio):
        logica.validar_prioridad("urgente")


def test_agregar_tarea_asigna_id_y_no_muta() -> None:
    doc = logica.documento_vacio()
    nuevo, tarea = logica.agregar_tarea(doc, " Comprar ", "baja", CREADA)
    assert doc == Documento(siguiente_id=1, tareas=())
    assert nuevo.siguiente_id == 2
    assert tarea == Tarea(1, "Comprar", "baja", "pendiente", CREADA)
    assert nuevo.tareas == (tarea,)


def test_agregar_tarea_es_determinista() -> None:
    doc = logica.documento_vacio()
    assert logica.agregar_tarea(doc, "a", "media", CREADA) == logica.agregar_tarea(
        doc, "a", "media", CREADA
    )


def test_agregar_tarea_limite_de_tareas() -> None:
    tareas = tuple(_tarea(i) for i in range(1, 1001))
    doc = Documento(siguiente_id=1001, tareas=tareas)
    with pytest.raises(ErrorDeDominio, match="máximo de 1000 tareas"):
        logica.agregar_tarea(doc, "x", "media", CREADA)


def test_agregar_tarea_prioridad_invalida() -> None:
    with pytest.raises(ErrorDeDominio):
        logica.agregar_tarea(logica.documento_vacio(), "x", "urgente", CREADA)


def test_filtrar_tareas_ordena_y_filtra() -> None:
    doc = Documento(3, (_tarea(2, "hecha"), _tarea(1), _tarea(3)))
    assert [t.id for t in logica.filtrar_tareas(doc, "todas")] == [1, 2, 3]
    assert [t.id for t in logica.filtrar_tareas(doc, "pendiente")] == [1, 3]
    assert [t.id for t in logica.filtrar_tareas(doc, "hecha")] == [2]
    assert len(doc.tareas) == 3
    with pytest.raises(ErrorDeDominio):
        logica.filtrar_tareas(doc, "otra")


def test_marcar_hecha_y_idempotencia() -> None:
    doc = Documento(2, (_tarea(1),))
    nuevo, cambio = logica.marcar_hecha(doc, 1)
    assert cambio is True
    assert nuevo.tareas[0].estado == "hecha"
    assert doc.tareas[0].estado == "pendiente"
    otra, cambio2 = logica.marcar_hecha(nuevo, 1)
    assert cambio2 is False
    assert otra == nuevo


def test_marcar_hecha_inexistente() -> None:
    with pytest.raises(ErrorDeDominio, match="no existe la tarea con ID 9"):
        logica.marcar_hecha(logica.documento_vacio(), 9)


def test_eliminar_tarea_no_reutiliza_ids() -> None:
    doc = Documento(3, (_tarea(1), _tarea(2)))
    nuevo = logica.eliminar_tarea(doc, 1)
    assert [t.id for t in nuevo.tareas] == [2]
    assert nuevo.siguiente_id == 3
    assert len(doc.tareas) == 2
    with pytest.raises(ErrorDeDominio, match="no existe la tarea con ID 1"):
        logica.eliminar_tarea(nuevo, 1)


def test_ida_y_vuelta() -> None:
    doc = logica.validar_documento(_datos_validos())
    assert logica.validar_documento(logica.documento_a_datos(doc)) == doc
    vacio = logica.documento_vacio()
    assert logica.validar_documento(logica.documento_a_datos(vacio)) == vacio


def _con_tarea(**cambios: object) -> dict[str, object]:
    return _datos_validos([_tarea_datos(**cambios)])


@pytest.mark.parametrize(
    ("datos", "detalle"),
    [
        ([], "la raíz debe ser un objeto"),
        ({"version": 1, "siguiente_id": 1}, "las claves de la raíz"),
        ({**_datos_validos(), "extra": 1}, "las claves de la raíz"),
        ({**_datos_validos(), "version": "1"}, "'version' debe ser un entero"),
        ({**_datos_validos(), "version": True}, "'version' debe ser un entero"),
        ({**_datos_validos(), "siguiente_id": 2}, "'siguiente_id' debe ser mayor"),
        ({**_datos_validos(), "siguiente_id": True}, "'siguiente_id' debe ser un entero"),
        ({**_datos_validos(), "tareas": "no"}, "'tareas' debe ser una lista"),
        ({**_datos_validos(), "tareas": ["x"]}, "cada tarea debe ser un objeto"),
        (_con_tarea(prioridad="urgente"), "'prioridad' no es válida"),
        (_con_tarea(estado="borrada"), "'estado' no es válido"),
        (_con_tarea(id=True), "'id' debe ser un entero"),
        (_con_tarea(id=0), "'id' debe ser un entero"),
        (_con_tarea(texto="\x1b[31m"), "'texto' no es válido"),
        (_con_tarea(texto=5), "'texto' debe ser una cadena"),
        (_con_tarea(texto=" con espacios "), "'texto' no es válido"),
        (_con_tarea(creada="ayer"), "'creada' no es una fecha"),
        (_con_tarea(creada=5), "'creada' debe ser una cadena"),
        (_con_tarea(extra=1), "las claves de una tarea"),
    ],
)
def test_validar_documento_estructura_invalida(datos: object, detalle: str) -> None:
    with pytest.raises(ErrorDeEstructura, match=detalle):
        logica.validar_documento(datos)


def test_validar_documento_no_muta_la_entrada() -> None:
    datos = _datos_validos([_tarea_datos(), _tarea_datos(id=3)])
    copia = copy.deepcopy(datos)
    logica.validar_documento(datos)
    assert datos == copia


def test_documento_a_datos_no_muta_el_documento() -> None:
    doc = Documento(3, (_tarea(1), _tarea(2)))
    copia = copy.deepcopy(doc)
    logica.documento_a_datos(doc)
    assert doc == copia


def test_version_desconocida_gana_a_otras_claves() -> None:
    with pytest.raises(ErrorDeAlmacen, match=r"versión de esquema 2 no soportada") as info:
        logica.validar_documento({"version": 2, "otro": []})
    assert not isinstance(info.value, ErrorDeEstructura)


def test_version_desconocida_enorme_se_trunca() -> None:
    with pytest.raises(ErrorDeAlmacen) as info:
        logica.validar_documento({**_datos_validos(), "version": 10**40})
    assert str(info.value) == (
        f"versión de esquema {'1' + '0' * 19}... no soportada (se esperaba 1)."
    )


def test_validar_documento_ids_duplicados() -> None:
    datos = _datos_validos([_tarea_datos(), _tarea_datos()])
    with pytest.raises(ErrorDeEstructura, match="duplicados"):
        logica.validar_documento(datos)


def test_validar_documento_demasiadas_tareas() -> None:
    datos = _datos_validos([_tarea_datos()] * 1001)
    with pytest.raises(ErrorDeEstructura, match="más de 1000"):
        logica.validar_documento(datos)


def test_validar_documento_version_desconocida() -> None:
    with pytest.raises(ErrorDeAlmacen, match="versión de esquema 2 no soportada") as info:
        logica.validar_documento({**_datos_validos(), "version": 2})
    assert not isinstance(info.value, ErrorDeEstructura)


def test_logica_no_importa_io_ni_lee_el_reloj() -> None:
    fuente = Path(logica.__file__).read_text(encoding="utf-8")
    arbol = ast.parse(fuente)
    prohibidos = {"os", "pathlib", "sys", "json", "time"}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            assert not {a.name.split(".")[0] for a in nodo.names} & prohibidos
        if isinstance(nodo, ast.ImportFrom):
            assert (nodo.module or "").split(".")[0] not in prohibidos
        if isinstance(nodo, ast.Attribute):
            assert nodo.attr not in {"now", "utcnow", "today"}

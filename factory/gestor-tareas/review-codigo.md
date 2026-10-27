# Revisión de Código: gestor-tareas (iteración 3, última)

Rama `factory/gestor-tareas` | PRP `PRPs/gestor-tareas-2026-10-27.md` | Diff revisado: `git diff cd14c96..HEAD -- apps/gestor-tareas` (almacen.py, cli.py, test_cli_robustez.py).

## Resultados reales (ejecutados por el revisor)
| Comprobación | Resultado |
|---|---|
| `quality-gate.sh apps/gestor-tareas` | **GATE: PASS (fallos 0, sin verificar 0)**, 9 filas en PASS, incluida `funciones` |
| `pytest -q` (3.13) | 150 passed |
| `pytest -q` (3.11 y 3.12, venvs en scratchpad) | 150 passed en ambos; `typing.Unpack` OK desde 3.11 (`requires-python >= 3.11`) |
| `ruff check .` / `ruff format --check .` | OK / 13 archivos ya formateados |
| `mypy .` | Success, 12 archivos |
| `noqa` / `type: ignore` nuevos | Ninguno (el único `noqa: S603` en `tests/ayudas.py:33` es previo) |
| Límites | Archivo más grande `cli.py` 299 líneas; ninguna función (producción ni tests) supera 40 líneas (verificado con `ast`) |

## Obligatorios y recomendados de decision.md
| # | Punto | Estado | Mutación sobre copia fuera del repo |
|---|---|---|---|
| 1 | `construir_parser` <= 50 | CUMPLIDO: ~20 líneas, helpers `_subcomando`/`_registrar_*`; gate `funciones` PASS | n/a |
| 2 | `**kwargs` en `_Parser` | CUMPLIDO: `Unpack[_OpcionesParser]` (TypedDict, sin `Any`), fuerza `add_help` y `formatter_class` | quitar `add_help`: falla; quitar `formatter_class`: falla |
| 3 | Tests de `TRADUCCIONES` | CUMPLIDO | borrar cada una de las 6 entradas: falla exactamente 1 test cada vez |
| 4 | `add_usage` en lugar del literal | CUMPLIDO; `format_help` eliminado | pasar `prefix` sin `PREFIJO_USO`: falla |
| 5 | Test de `dup2` | CUMPLIDO: descriptor real, comprueba `st_rdev` de `/dev/null` | `dup2` -> `pass`: falla |
| 6 | Saneo de ruta no duplicado | PARCIAL (ver hallazgo 1) | quitar saneo en `resolver_ruta` (vacía/nulo): 150 passed (sin test) |
| 7 | `build.md` con "Iteración 3" | CUMPLIDO; coincide con lo observado (150 tests, gate 9/9, 3.11-3.13) | n/a |

Sin regresiones: el comportamiento de ayuda, errores y rutas se mantiene (los 144 tests previos siguen en verde y la salida de `_ruta_invalida` es idéntica). Coherencia PRP-código-tests correcta.

## Hallazgos
Ninguno BLOQUEANTE ni CAMBIOS.

Observaciones menores (no bloquean, sin acción obligatoria):
1. `gestor_tareas/almacen.py:47,49`: las dos ramas de `resolver_ruta` (ruta vacía / byte nulo) sanean con `texto_seguro` pero ningún test lo cubre (quitar el saneo deja 150 en verde). Una ruta como `"\n"` o `"\x1b "` seguida de espacios... en la rama vacía solo aplica a espacios en blanco no imprimibles (p. ej. `"\n"`). Sugerencia: añadir un test con `--archivo $'\n'` que compruebe que el error no contiene el salto crudo. Además el saneo sigue en tres sitios (`cli.py:230`, `almacen.py:99`, `almacen.py:128`) aunque `texto_seguro` es idempotente; la afirmación del builder de que `cargar`/`guardar` "ya reciben texto seguro" es cierta, pero entonces su saneo es redundante. Solo estético; el decision.md lo marcaba "solo si es trivial".
2. `cli.py:61-68`: `add_usage` usa `argparse._MutuallyExclusiveGroup` (API privada) en la firma, necesario para mypy estricto; aceptable, sin cambios necesarios.

VEREDICTO: APROBADO

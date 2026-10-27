# Revisión de código: gestor-tareas (iteración 2)

Rama `factory/gestor-tareas`, diff `7a3bc26..HEAD` sobre `apps/gestor-tareas`. PRP: `PRPs/gestor-tareas-2026-10-27.md`.

## Resultados reales
| Verificación | Resultado |
|---|---|
| Gate `quality-gate.sh apps/gestor-tareas` (raíz) | GATE: PASS, 8/8 (fallos 0, sin verificar 0) |
| Gate `quality-gate.sh .` (raíz entera) | FAIL, pero no es del proyecto: pytest no encuentra `gestor_tareas` desde la raíz y bandit escanea todo el monorepo. Es el desajuste monorepo/gate ya conocido; la verificación vigente es la del subdirectorio. |
| `pytest -q` (.venv, 3.13) | 144 passed |
| `pytest -q` en 3.11 y 3.12 (venvs temporales, copia fuera del repo) | 144 passed en ambas |
| `ruff check .` / `ruff format --check .` | All checks passed / 13 files already formatted |
| `mypy .` (estricto) | Success, 12 files |
| Líneas por archivo | máx. 294 (tests) y 281 (`cli.py`); todo bajo 500 |

El `quality-gate.md` del repo quedó sobrescrito por mi última ejecución, la del subdirectorio (PASS).

## Mutaciones: ¿cada arreglo tiene un test que falla sin él?
Hecho en una copia fuera del repo (scratchpad), revirtiendo un arreglo cada vez.

| Arreglo revertido | Tests que fallan |
|---|---|
| `except BrokenPipeError` en `_emitir` | 1 |
| `reconfigure(errors="replace")` | 1 |
| Aviso "El cambio sí se guardó" siempre | 1 |
| `default=SUPPRESS` en `--archivo` | 47 |
| Mensaje de `list` vacío por filtro | 2 |
| Rechazo de FIFO | 2 (uno agota el timeout de 30 s) |
| `texto_seguro` sin filtrar | 5 |
| Truncado de versión | 2 |
| Versión validada antes que las claves | 7 |
| Traducción `unrecognized arguments` | 1 |
| Traducción `the following arguments are required` | 2 |
| Título `opciones`, `-h` en español, epílogo con ejemplo | 1 cada uno |
| **`os.dup2` en `_descartar_stdout`** | **0 (sin cobertura)** |
| **Traducción `("argument ", "argumento ")`** | **0 (sin cobertura)** |
| **Traducción `("(choose from ", "(opciones: ")`** | **0 (sin cobertura)** |
| **Traducción `("expected one argument", ...)`** | **0 (sin cobertura)** |
| **`texto_seguro` en `almacen.cargar`** | 0 (redundante: `_ruta_invalida` ya escapa; ver nota) |

## Hallazgos

### CAMBIOS-1: `construir_parser` supera las 50 líneas
`gestor_tareas/cli.py:108` (def a 159): 52 líneas por `ast`. Rompe el límite de 50 de `CLAUDE.md` por 2. Corrección: extraer la construcción de cada subcomando (p. ej. `_registrar_add(sub, ayuda_archivo)`) o mover los 4 subparsers a una función auxiliar. El gate no lo detecta.

### CAMBIOS-2: parser propio frágil frente a versiones de Python
`gestor_tareas/cli.py:44-74`. Con 3.11, 3.12 y 3.13 todo pasa (probado). Pero `requires-python = ">=3.11"` no tiene tope y el CI usa solo 3.12:
- `_Parser.__init__` acepta solo `prog`, `description` y `epilog`. `add_subparsers(parser_class=_Parser)` le pasa los kwargs de `add_parser`; si una versión futura de argparse inyecta otros (hay cambios de color y sugerencias en 3.14, no verificables aquí, no hay 3.14 instalado), fallaría con `TypeError` en cualquier invocación. Corrección: `def __init__(self, **kwargs: Any)` con `add_help=False` y `formatter_class` forzados.
- `_Formateador.format_help` depende de que la salida empiece por la cadena literal `"usage: "`. Si argparse colorea o cambia el prefijo, el `if` falla en silencio y se vuelve al inglés sin error. El test `test_ayuda_en_espanol` lo detectaría en CI, pero solo en 3.12. Corrección: añadir 3.11 y 3.13 (o la última estable) a la matriz del `quality.yml` plantilla, o usar el gancho `add_usage` del formateador, que es la vía soportada para el prefijo.
- `TRADUCCIONES` hace `str.replace` sobre texto inglés de CPython, que ha cambiado entre versiones (las comillas de `choose from` cambiaron). Está limitado a fragmentos, falla de forma segura (queda en inglés) y el README lo documenta, así que es mantenible. Se acepta, pero ver CAMBIOS-3.

### CAMBIOS-3: cobertura incompleta de la tabla `TRADUCCIONES` y de `_descartar_stdout`
- `cli.py:35-36, 38`: las entradas `"argument "`, `"(choose from "` y `"expected one argument"` pueden borrarse sin que falle ningún test. `test_errores_de_uso_en_espanol` solo comprueba `"opción no válida"` y la ausencia de `invalid choice`. Corrección: afirmar `"(opciones: "` y `"argumento --prioridad"` en el caso de prioridad, y añadir el caso `["list", "--estado"]` con `"se esperaba un valor"`. Es la fragilidad entre versiones que más conviene proteger con tests, porque esas cadenas son las que pueden cambiar.
- `cli.py:216-221` (`_descartar_stdout`): sustituir el `dup2` por `pass` no rompe nada. `test_dev_full_extremo_a_extremo` no comprueba que stderr esté libre de `Exception ignored ... flush` (sí fija `stderr ==` exacto, pero el vaciado final de Python no escribe ahí en este caso). Los tests con `capsys` omiten el `dup2` por diseño (nota 4 del build). Corrección: en el test de `/dev/full`, afirmar `returncode == 3` con `stderr` exacto (ya está) y añadir otro con salida que no se vacíe hasta el final, o un test con un descriptor real redirigido que compruebe que `/dev/null` sustituye a stdout. Menor, no bloquea.

### Nota (sin acción): doble saneo de la ruta
`almacen.py:99, 128` aplican `texto_seguro` a `mostrar` y `_ruta_invalida` lo vuelve a aplicar. Es idempotente y no cambia la salida, solo es redundante. Quitar uno de los dos simplificaría.

## Sin hallazgos en
- Regresiones en lógica pura y CLI: el reordenamiento de `_validar_cabecera` conserva los dos mensajes; un entero `bool` queda excluido por `_es_entero`. 144 tests en 3.11/3.12/3.13.
- `noqa` / `type: ignore`: ninguno nuevo en producción. El único `noqa: S603` en tests (`ayudas.py:33`) es el de siempre, movido de archivo. Los `N818` se retiraron y se cubren con `per-file-ignores` acotado a `modelo.py` y comentado.
- Reparto de tests: `ayudas.py` (43), `conftest.py` (16), `test_cli_robustez.py` (213), `test_cli.py` (294). Sin duplicación relevante.
- PRP coherente con código y tests: criterios 30 a 36, tabla de mensajes, código 3 ampliado y nota de CI coinciden con lo implementado. El CI queda declarado como inerte en el monorepo y el README lo dice.
- Manejo de errores en salida: `BrokenPipeError` -> 0 en silencio; otro `OSError` -> 3 con aviso de guardado; `_escribir_error` suprime fallos de stderr.

## Resumen
Los arreglos de la iteración 2 funcionan y casi todos tienen un test que falla sin ellos, con las excepciones de CAMBIOS-3. No hay defecto que impida producción. Pendientes: recortar `construir_parser` a 50 líneas, endurecer `_Parser.__init__` con `**kwargs` y los tests de traducciones.

VEREDICTO: CAMBIOS

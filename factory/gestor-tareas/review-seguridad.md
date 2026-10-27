# Revisión de Seguridad: gestor-tareas (iteración 2)

Diff revisado: `git diff 7a3bc26..HEAD -- apps/gestor-tareas` (13 archivos). Sin dependencias de runtime nuevas.

## Quality gate (`factory/gestor-tareas/quality-gate.md`)
GATE: PASS (fallos 0, sin verificar 0). Filas: secretos PASS, tamano PASS, patrones-peligrosos PASS, tests-py PASS, lint-py PASS, tipos-py PASS, sast-py (bandit -ll) PASS, dependencias-py (pip-audit -r requirements.txt) PASS. Sin `.env` versionados ni credenciales.

## Observaciones de la iteración 1
| Observación | Estado | Evidencia |
|---|---|---|
| ESC en ruta impresa | Resuelta | `almacen.texto_seguro` en `_ruta_invalida`, `cargar`, `guardar`, `_ciclo`. `--archivo $'\e[31mX/a.json'` (antes y después del subcomando) imprime `'\x1b[31mX/a.json'` escapado. Es idempotente (la doble aplicación no altera el resultado). Acentos intactos. |
| FIFO cuelga | Resuelta | `almacen.py:_validar_destino` rechaza lo existente que no sea archivo regular antes de abrir. Probado con `mkfifo`: código 3 inmediato `no es un archivo regular`. |
| Orden de validación de versión | Resuelta | `logica.py:_validar_cabecera` valida versión antes del conjunto de claves; entero enorme truncado a 20 dígitos (`99999999999999999999...`). Un JSON con 5000 dígitos lo rechaza el parser (límite de int de Python) con código 3, sin traza. |
| Versión enorme (info) | Resuelta | Truncado en `_version_corta`. |

## Búsqueda de regresiones en código nuevo
- `cli._emitir`: `BrokenPipeError` devuelve 0 en silencio; otro `OSError` devuelve 3 con mensaje fijo (`strerror` acotado a 100 caracteres) y avisa "El cambio sí se guardó" cuando corresponde. Probado con `> /dev/full` en `list` (3) y `add` (3 con aviso); con `| true` el resultado es 0. La indicación de guardado es veraz: el guardado ocurre antes de emitir. No filtra datos ni trazas.
- `_descartar_stdout`: abre `os.devnull` y hace `dup2` sobre el descriptor de stdout; cierra el descriptor temporal en `finally`; errores suprimidos de forma acotada (`OSError, ValueError, AttributeError`). Sin fuga de descriptores. Efecto limitado al propio proceso.
- `_configurar_flujos` (`errors="replace"`): con `PYTHONIOENCODING=ascii` el texto `ñandú` se muestra como `?and?` sin `UnicodeEncodeError`. Solo afecta a `TextIOWrapper`. Los caracteres de control no pasan a la salida, porque `validar_texto` los rechaza al validar.
- `_escribir_error` suprime `OSError` al escribir en stderr, así que un stderr roto no genera traza. Quedaría sin tratar un `ValueError` por stderr cerrado, y no es explotable.
- `_Parser`/`_Formateador`/`TRADUCCIONES`: el `error()` propio solo hace `str.replace` sobre el mensaje de argparse y lo escribe en stderr con código 2. Los valores que el usuario ha puesto en el mensaje (por ejemplo `'bogus'`) los cita argparse con `repr`, de modo que los caracteres de control salen escapados. No hay `eval` ni formato con el texto del usuario como plantilla. Probado: `--estado foo`, falta de `id`, comando desconocido y `--archivo` sin valor dan código 2 en español, sin traza.
- `--archivo` en subparsers con `SUPPRESS`: `--archivo a.json list --archivo nonexist/x.json` usa el segundo valor (gana el más cercano al subcomando) y `--archivo nonexist/x.json list --archivo a.json` usa `a.json`. Es coherente con lo documentado y no hay elusión de validación: ambas vías pasan por `resolver_ruta` y `_validar_destino`.
- `_mensaje_lista_vacia`: interpola `args.estado`, que `choices` restringe a valores fijos. Sin inyección.

## Ataques repetidos (cwd temporal en el scratchpad, HOME falso)
| Prueba | Resultado |
|---|---|
| Symlink al archivo y a `/etc/passwd` | Código 3 `es un enlace simbólico`; destino sin modificar. OK |
| Directorio como destino (`/tmp`) | Código 3. OK |
| FIFO | Código 3 inmediato (sin timeout). OK |
| Directorio padre inexistente | Código 3. OK |
| JSON `[` x 100000 (recursión) | Código 3, sin traza. OK |
| JSON con `\u001b[2J` en el texto | Código 3 `'texto' no es válido`; no llega al terminal. OK |
| Versión con entero de 29 y 5000 dígitos | Código 3, mensaje truncado o genérico. OK |
| Permisos del archivo creado | `0600`. OK |
| Atomicidad / temporales | El directorio queda sin `.gestor-tareas-*.tmp`; la ruta de escritura (`mkstemp` + `fsync` + `replace`, `unlink` en `BaseException`) no cambió respecto a la iteración 1, y los tests de fallo siguen en verde en el gate (144 tests). OK |
| Rutas `..`, `/etc/passwd`, byte nulo, ruta vacía, bytes no UTF-8 | Sin cambios en `resolver_ruta`; cubiertas por los tests existentes en verde. OK |

## Hallazgos
Ninguno BLOQUEANTE ni de severidad CAMBIOS. Observaciones residuales, ya aceptadas en la iteración 1:
1. **Info** `almacen.py:_validar_destino` / `guardar`: ventana TOCTOU entre validación y `replace`. `replace` sustituye el enlace sin seguirlo, así que no hay escritura fuera del destino.
2. **Info** Un symlink en un directorio padre se acepta. Solo se protege el último componente, lo cual es aceptable porque la ruta la elige el propio usuario.
3. **Info** `apps/gestor-tareas/.github/workflows/quality.yml`: acciones fijadas por tag y no por SHA, con `permissions: contents: read` correcto. GitHub no lo ejecuta en este monorepo, y el README y la cabecera lo declaran. Revisar al mover el proyecto a su propio repo.
4. **Info** Las herramientas de desarrollo tienen versiones fijadas sin hash (deuda declarada). No hay dependencias de runtime.
5. **Info** La traducción de errores de argparse depende del formato de mensajes de la versión de Python (probado en 3.13). Lo no traducido sale en inglés, sin impacto de seguridad.

No hay datos personales en logs, ni red, ni CORS ni webhooks (no aplican).

VEREDICTO: APROBADO

# Revisión de seguridad: gestor-tareas (iteración 3, final)

Diff revisado: `git diff cd14c96..HEAD -- apps/gestor-tareas` (almacen.py, cli.py, tests/test_cli_robustez.py).

## Quality gate
`factory/gestor-tareas/quality-gate.md`: GATE PASS (0 fallos, 0 sin verificar). Secretos, patrones peligrosos, tamaño y funciones, tests (150 passed), ruff, mypy, bandit (-ll) y pip-audit: todos PASS.

## Regresiones buscadas en lo cambiado
- `_Parser.__init__` con `**kwargs`/TypedDict: `add_help` y `formatter_class` se fuerzan; no abre superficie nueva. Sin hallazgos.
- Gancho `add_usage` (sustituye a `format_help`): el prefijo "uso:" sale también en errores y subcomandos. Sin hallazgos.
- Saneo movido: `_ruta_invalida` ya no sanea, pero todos sus llamadores pasan texto saneado. En `resolver_ruta` (vacía/NUL) se llama a `texto_seguro`; en `_validar_destino` recibe el `texto` saneado de `cargar`/`guardar`. La doble aplicación es idempotente (la barra invertida es imprimible). Sin regresión.

## Ataques reales (ruta con ESC, `\x1b[31m`)
Todos con `--archivo` antes y después del subcomando. La salida se inspeccionó con `cat -v` y no hay ESC crudo en ninguna.
- Directorio: error escapado, rc=3.
- FIFO: no se bloquea (timeout 5 s no alcanzado), "no es un archivo regular", rc=3.
- Symlink con ESC en el nombre (`add`/`list`): rechazado y escapado, rc=3.
- Directorio padre inexistente con ESC: `\x1b[31mnodir/x.json` escapado en ambos órdenes y también vía `GESTOR_TAREAS_ARCHIVO`.
- Ruta vacía o solo espacios, y ruta con NUL + ESC (llamando a `principal` directamente): `'a\x1bb': contiene un byte nulo`, rc=3.
- JSON inválido en un archivo con ESC en el nombre: nombre escapado.
- Opción inválida (`--estado`) y comando inválido con ESC: argparse los escapa (`%r`).

## Repetición de ataques clave
- JSON hostil: truncado, `[1,[[[[` y 100000 `[` anidados (RecursionError): error controlado rc=3, sin traceback.
- Permisos: el archivo creado tiene modo 600.
- Atomicidad: no quedan temporales `.gestor-tareas-*.tmp` en el directorio tras las operaciones. Los tests cubren el fallo a mitad de escritura.
- Symlink a /etc/passwd: rechazado sin leer ni escribir.

## Hallazgos
- BAJO / informativo (no bloquea; ya existía en cd14c96 y no es regresión): `cli.py:104`, `_id_valido` incrusta `'{valor}'` sin escapar. `gestor-tareas done $'\e[31mx'` emite el ESC crudo en el mensaje de error de argparse. Solo refleja el argv del propio usuario en su terminal, sin vector remoto. Corrección sugerida: `almacen.texto_seguro(valor)` o `{valor!r}`.

Sin hallazgos bloqueantes ni de severidad CAMBIOS.

VEREDICTO: APROBADO

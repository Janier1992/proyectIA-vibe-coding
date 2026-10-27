# Revisión UX (iteración 2): gestor-tareas (CLI)

Método: ejecuté la herramienta real (`.venv/bin/python -m gestor_tareas`) desde directorios temporales fuera del repo. `pytest -q`: 144 passed.

## Verificación de los 4 hallazgos obligatorios de la iteración 1

| # | Hallazgo | Resultado | Evidencia |
|---|---|---|---|
| 1 | Salida rota | CORREGIDO | `list > /dev/full`: `Error: no se pudo escribir la salida: No space left on device.`, código 3. `add "zz" > /dev/full`: mismo mensaje más ` El cambio sí se guardó.`, código 3, y la tarea 3 aparece luego en `list`. Con `PYTHONIOENCODING=ascii` y acentos: no hay traceback, sale `caf? ?and?`, código 0. `list \| head -0`: código 0 y sin ruido. |
| 2 | `--archivo` tras el subcomando | CORREGIDO | `add x --archivo otro.json`, `list --archivo otro.json` y `--archivo otro.json list` dan el mismo resultado y crean `otro.json`. Aparece en la ayuda de los 4 subcomandos. |
| 3 | Mensaje de `list` por filtro | CORREGIDO | Sin tareas: `No hay tareas.` Con tareas pero filtro vacío: `No hay tareas hechas. Usa --estado todas.` y `No hay tareas pendientes. Usa --estado todas.` Ambos con código 0. |
| 4 | Ayuda y argparse en español | CORREGIDO | `--help` general y de `add`, `list`, `done` y `remove` están en español (`uso:`, `argumentos posicionales:`, `opciones:`, `muestra esta ayuda y termina`). Los defaults se ven (`por defecto: media`, `por defecto: pendiente`, ruta del archivo). Cada subcomando trae `Ejemplo:`. La ayuda general trae precedencia del archivo y tabla de códigos de salida. |

## Regresiones revisadas
- Errores de uso, todos en español y con código 2: sin comando, comando desconocido, falta de `texto` o `id`, `id` no numérico, `done 0`, prioridad inválida y opción desconocida. Los mensajes dicen qué se esperaba (por ejemplo `ID no válido: 'abc' (se esperaba un entero >= 1)`).
- Códigos de salida coherentes con el README y la ayuda: 0 éxito; 1 ID inexistente o texto vacío o en blanco; 2 uso; 3 JSON corrupto (`b.json`), directorio padre inexistente y fallo de escritura de salida. Los errores van con el prefijo `Error: ` y son accionables (`corrígelo o elimínalo`).
- README: el inicio rápido de 3 comandos coincide con la salida real. La sección "CI" dice con claridad que la plantilla no se ejecuta en el monorepo y da el gate local como verificación vigente. La cabecera del workflow lo repite. La tabla de códigos de salida y la sección Limitaciones son coherentes con lo observado.

## Hallazgos menores (no bloquean; opcionales)
1. `gestor_tareas/cli.py` (tabla `TRADUCCIONES`): el mensaje de `invalid choice` queda como `opción no válida: 'hechas' (opciones: 'pendiente', 'hecha', 'todas')`. Es claro, pero el mensaje de `list` vacío habla de "hechas/pendientes" en plural y `--estado` acepta el singular. Mejora opcional: aceptar también el plural o escribir en el mensaje el valor exacto (`--estado hecha`). Al escribir "hechas" el usuario ve un error de uso que lista las opciones válidas, así que no queda sin salida.
2. La opción corta `-a` no existe y da `argumentos no reconocidos: -a f.json`. Es aceptable (nunca se prometió) y el mensaje es claro.
3. Higiene del repo, fuera de UX: `apps/gestor-tareas/.claude/` aparece sin seguimiento en `git status`. Debe decidirse si se commitea (el workflow la asume copiada) o se ignora.

No hay hallazgos CAMBIOS ni BLOQUEANTES. Los criterios de accesibilidad del tema (teclado y foco, contraste, alt) no aplican a una CLI. Los equivalentes se cumplen: no se depende del color, la salida es texto plano y los errores se envían a stderr.

VEREDICTO: APROBADO

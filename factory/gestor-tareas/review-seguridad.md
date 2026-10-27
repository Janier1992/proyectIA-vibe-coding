# Revisión de seguridad: gestor-tareas

Rama `factory/gestor-tareas`, diff `3a44109..HEAD -- apps/gestor-tareas`. Riesgo: bajo (CLI local, sin red, sin dependencias de runtime, sin auth ni datos personales).

## Quality gate (ejecutado por el revisor)
`bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md` -> exit 0, **GATE: PASS (fallos 0, sin verificar 0)**.
- secretos: PASS (regex integrado; gitleaks no instalado).
- patrones-peligrosos: PASS (sin eval/shell=True/verify=False).
- sast-py: PASS (bandit -ll).
- dependencias-py: PASS (pip-audit -r requirements.txt; sin dependencias de runtime).
- También PASS: tamano, tests-py, lint-py, tipos-py.
- `.env` versionados: ninguno. Sin credenciales en el código.

## Pruebas de ataque a la CLI (cwd temporal en el scratchpad, HOME falso, fuera del repo)
| Prueba | Resultado |
|---|---|
| `--archivo sub/../a.json`, `../w/a.json` | Se resuelven y funcionan. Es el comportamiento esperado de una ruta elegida por el propio usuario; no hay confinamiento (ni se promete). OK |
| `/etc/passwd`, `/etc/shadow` | Rechazados como JSON no válido (3), sin volcar contenido. OK |
| Directorio como destino | Código 3 "es un directorio". OK |
| Symlink al archivo (`l.json -> a.json`) y a `/etc/passwd` | Código 3 "enlace simbólico"; no se sigue ni se sobrescribe. OK |
| Symlink en el directorio padre (`rl/f.json`) | Se acepta y escribe dentro del destino. Aceptable (solo se protege el último componente) |
| Byte nulo (vía llamada directa a `principal`, bash no lo permite en argv) | Código 3 "contiene un byte nulo". OK |
| Ruta vacía | Código 3. OK |
| Ruta con bytes no UTF-8 | Sin traceback; se muestra escapada (`\udcff`). OK |
| JSON: 0 bytes | Código 3 "no es JSON válido" (no se trata como lista vacía). OK |
| JSON: profundidad 100000 (`[` y `{"a":`) | Código 3, sin traceback (RecursionError capturado). OK |
| JSON: 2 MB | Rechazado por tamaño (1 MiB). `/dev/zero` también (lectura acotada). OK |
| JSON: claves extra en raíz y en tarea, `id` bool, `id` float, `version` NaN, `creada` inválida, BOM | Todos código 3 con mensaje fijo. OK |
| JSON: texto con `\x1b[2J`, U+202E (bidi), sustituto suelto `\ud800` | Rechazado (3). No llega al terminal. OK |
| IDs enormes: CLI `done 9999...` (26 y 5000 dígitos), `0`, `-1`, `1e3` | Argparse rechaza (2) o dominio (1); el límite de 4300 dígitos de Python no produce traceback. OK |
| IDs enormes en JSON (`id` de 4000 dígitos) | Aceptado y funcional (add/list). Sin impacto; el archivo sigue acotado a 1 MiB |
| Texto: ANSI, `\n`, U+202E, bytes inválidos, 201 caracteres | Todos rechazados con código 1. OK |
| Permisos: archivo nuevo | `0600`. Con umask 0 y archivo previo `0666` -> queda `0600`. OK |
| Atomicidad: `Path.replace` falla (ENOSPC) | Código 3, archivo original intacto, sin `.tmp`. OK |
| Atomicidad: `fsync` falla (EIO) | Código 3, original intacto, sin `.tmp`. OK |
| Atomicidad: `KeyboardInterrupt` durante escritura | Se propaga, sin `.tmp` residual. OK |

## Hallazgos
Ninguno BLOQUEANTE ni de severidad CAMBIOS. Observaciones de baja severidad (no impiden la aprobación):

1. **Baja** `gestor_tareas/almacen.py:30-31,56-57` y `cli.py:122`: la ruta que da el usuario (`--archivo` o `GESTOR_TAREAS_ARCHIVO`) se imprime sin sanear en los mensajes de error. Probado: `--archivo $'\e[31mROJO\e[0m/x.json'` emite la secuencia ESC cruda a stderr. El usuario controla esa entrada, pero un wrapper o una variable de entorno heredada podrían inyectar secuencias de control. Corrección sugerida: mostrar `mostrar` con `repr()` o con filtrado de no imprimibles.
2. **Baja** `almacen.py:60-70`: un FIFO (named pipe) como archivo hace que `open("rb")` bloquee indefinidamente (probado: timeout de 5 s). `st_size` es 0 y la comprobación no lo detecta. Es un autobloqueo, no una escalada. Corrección sugerida: exigir `stat.S_ISREG` en `_validar_destino` (también cubre dispositivos).
3. **Info** `almacen.py:34-43,46-52`: hay una ventana TOCTOU entre `_validar_destino` y `replace`. Un atacante local con escritura en el directorio podría cambiar el destino, pero `replace` sustituye el enlace y no lo sigue, así que no hay escritura fuera del destino. Riesgo aceptado.
4. **Info** `logica.py:158`: en el mensaje de versión desconocida se interpola un entero arbitrario (hasta ~1 MiB de dígitos, ampliación en stderr). Está acotado por el límite de tamaño; opcionalmente se puede truncar.
5. **Info** `.github/workflows/quality.yml`: las acciones están fijadas por tag (`@v4`, `@v5`), no por SHA, y `permissions: contents: read` es correcto. Está en `apps/gestor-tareas/.github/`, y GitHub solo ejecuta workflows de la raíz del repo, así que no corre allí (desviación declarada). Revisar al mover el proyecto a su propio repo.
6. **Info** Las herramientas de desarrollo tienen versiones fijadas sin hash; es deuda declarada y no hay dependencias de runtime.

Sin datos personales en logs, sin red, sin CORS ni webhooks (no aplican).

VEREDICTO: APROBADO

# Revisión UX: gestor-tareas (CLI)

Método: ejecución real (`python3 -m gestor_tareas`, PYTHONPATH al proyecto, archivos en un directorio temporal fuera del repo). Nota: `apps/gestor-tareas/.venv` no existe; no hace falta, ya que no hay dependencias de runtime. Diff revisado: `apps/gestor-tareas` (cli.py, README.md).

## Lo que funciona bien
- `--help` raíz: descripción, subcomandos, precedencia del archivo, `GESTOR_TAREAS_ARCHIVO` y códigos de salida (0/1/2/3). Cumple el criterio 27.
- Confirmaciones claras y con el ID: `Tarea 1 añadida: ... [media]`, `Tarea 1 marcada como hecha.`, `La tarea 1 ya estaba hecha.`, `Tarea 2 eliminada.`
- Errores de dominio y almacenamiento: prefijo `Error:`, van a stderr, sin traceback, accionables (`corrígelo o elimínalo`, `el directorio padre no existe`, `es un directorio`). Códigos verificados: 0, 1 (ID inexistente, vacío, control), 2 (uso), 3 (JSON corrupto, ruta).
- `list`: orden por ID, columnas alineadas, estado con `[x]`/`[ ]` en texto (no depende del color; no se emite ningún color/ANSI). Con pipe, `cat -A` y redirección a archivo la salida es idéntica y limpia. UTF-8 (CJK, emoji) correcto. Compatible con lector de pantalla (texto plano línea por línea).
- `list` no escribe; `done` idempotente; `add -- "-x"` funciona.
- IDs 0/abc: mensaje claro con código 2.

## Hallazgos

### CAMBIOS-1: `--archivo` después del subcomando da un error sin pista
`cli.py:50-56` (opción solo en el parser raíz). Reproducido: `gestor-tareas list --archivo X` -> `error: unrecognized arguments: --archivo X` (código 2). Es el error más probable de un usuario nuevo; el mensaje no dice que debe ir antes del subcomando (solo lo dice `--help`/README).
Corrección sugerida: aceptar `--archivo` también en los subparsers (parent parser con `default=argparse.SUPPRESS`) o, como mínimo, añadir al `usage`/mensaje de error la pista "`--archivo` va antes del comando".

### CAMBIOS-2: Traceback ante fallo de escritura en stdout (y mensaje engañoso tras persistir)
`cli.py:148` (`print(mensaje)` sin protección). Reproducido: `list > /dev/full` -> `OSError: [Errno 28]` con traceback, exit 1; con `PYTHONIOENCODING=ascii`, `list` con emoji -> `UnicodeEncodeError` con traceback. Peor: en `add`/`done`/`remove` el guardado ya ocurrió antes del `print`, por lo que el usuario ve un traceback y código 1 (que el README define como "error de validación") aunque el cambio sí se guardó. Esto contradice la promesa de "sin traceback" y de códigos coherentes. Un `| head` (BrokenPipe) tiene el mismo riesgo.
Corrección sugerida: envolver la impresión en `try/except (OSError, UnicodeEncodeError)`; con BrokenPipe salir en silencio; en el resto escribir `Error: no se pudo escribir la salida: ...` a stderr con código 3 (documentarlo), y/o imprimir la confirmación de forma tolerante (`errors="replace"`).

### CAMBIOS-3: `list` vacío por filtro es ambiguo
`cli.py:97-98`. Con 1 tarea hecha y ninguna pendiente, `list` imprime `No hay tareas.` aunque existe una; el usuario puede creer que perdió datos. Corrección: mensaje según filtro, p. ej. `No hay tareas pendientes.` y, si el documento tiene tareas de otro estado, sugerir `Usa --estado todas.` (el PRP fija `No hay tareas.` para archivo inexistente, mantener ese caso).

### CAMBIOS-4: Ayuda de subcomandos incompleta y mezcla de idiomas
`cli.py:65,68`. `add --prioridad` y `list --estado` no tienen `help` ni indican el valor por defecto (`media`, `pendiente`); `done --help`/`add --help` no tienen epílogo ni ejemplo. Las cadenas de argparse salen en inglés (`usage:`, `show this help message and exit`, `the following arguments are required`, `invalid choice`) mezcladas con el resto en español, lo que afecta a lectores de pantalla con voz española. Corrección: añadir `help=` con defaults; localizar con `add_help=False` + `-h` en español y subclase de `ArgumentParser.error`, o aceptar y documentar la limitación.

### Observaciones (no bloquean)
- `remove` no pide confirmación ni muestra el texto eliminado; es destructivo e irreversible (el ID no se reutiliza). En CLI no interactiva es aceptable y el PRP solo exige confirmación con ID, pero imprimir el texto (`Tarea 2 eliminada: Pagar luz.`) permitiría detectar errores de ID. Sugerido, no exigido.
- Texto largo (hasta 200 car.) no se trunca ni ajusta; aceptable, sigue legible en pipes.
- README: es correcto y completo, pero el "empezar en un minuto" exige deducir cómo ejecutar; falta un bloque de inicio rápido con ejemplos concretos (`cd apps/gestor-tareas; python -m gestor_tareas add "Comprar leche"`, `list`, `done 1`), y menciona que `python` debe ser >= 3.11. Añadir 4 líneas de ejemplo con salida esperada. No documenta el comando `-h` por subcomando ni un alias `gestor-tareas` (el `prog` en la ayuda dice `gestor-tareas` pero se ejecuta con `python -m gestor_tareas`; pequeña incoherencia).

## Veredicto
Sin defectos que bloqueen producción (no hay pérdida de datos ni fallos de accesibilidad graves), pero hay cuatro puntos de pulido que conviene corregir, siendo el 1 y el 2 los más relevantes.

VEREDICTO: CAMBIOS

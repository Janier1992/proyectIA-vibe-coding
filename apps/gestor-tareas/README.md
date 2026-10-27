# gestor-tareas

CLI en Python 3 para gestionar una lista personal de tareas guardada en un único archivo JSON local.
Solo usa la librería estándar (Python >= 3.11); no tiene dependencias de runtime.

## Uso

Desde `apps/gestor-tareas/`:

```bash
python -m gestor_tareas [--archivo RUTA] <comando> [args]
```

`--archivo` es una opción global y va **antes** del subcomando.

| Comando | Descripción |
|---|---|
| `add TEXTO [--prioridad alta\|media\|baja]` | Añade una tarea pendiente (prioridad por defecto `media`) |
| `list [--estado pendiente\|hecha\|todas]` | Lista por ID ascendente (por defecto `pendiente`) |
| `done ID` | Marca como hecha (idempotente) |
| `remove ID` | Elimina la tarea; su ID no se reutiliza |

`ID` debe ser un entero >= 1; un valor menor o no numérico es un error de uso (código 2).
Formato de `list`: `   3  [ ]  media  Comprar leche` (`[x]` = hecha, `[ ]` = pendiente).

## Archivo de datos

Precedencia: `--archivo` > variable de entorno `GESTOR_TAREAS_ARCHIVO` (vacía = no definida)
> `~/.gestor-tareas.json`. El archivo se crea con el primer `add` y siempre queda con modo `0600`.
Esquema versionado (`version: 1`); la escritura es atómica (temporal + `os.replace`).
Se rechazan enlaces simbólicos, directorios, directorios padre inexistentes, archivos de más de
1 MiB y más de 1000 tareas. Texto de tarea: 1 a 200 caracteres, sin caracteres de control.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito |
| 1 | Error de validación o de dominio (texto inválido, ID inexistente, límite de tareas) |
| 2 | Error de uso de la CLI (argumentos inválidos) |
| 3 | Error de almacenamiento (JSON corrupto, esquema inválido, ruta, permisos o E/S) |

Los errores van a stderr con el prefijo `Error: `; los resultados, a stdout.

## Limitaciones

- Sin bloqueo de archivo entre procesos: si dos procesos escriben a la vez, gana la última escritura.
- No hay migraciones: una versión de esquema desconocida se rechaza.

## Desarrollo y calidad

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check . && ruff format --check .
mypy .
bandit -q -r . -ll -x ./tests
pip-audit -r requirements.txt
```

El CI (`.github/workflows/quality.yml`) ejecuta `bash .claude/scripts/quality-gate.sh .` asumiendo
que `.claude/` del motor se copió al proyecto. Recomendado: proteger `main` exigiendo el check
"Quality gate".

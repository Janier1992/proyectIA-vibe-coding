# gestor-tareas

CLI en Python 3 para gestionar una lista personal de tareas guardada en un único archivo JSON local.
Solo usa la librería estándar; no tiene dependencias de runtime. Requiere **Python >= 3.11**.

## Inicio rápido

```bash
cd apps/gestor-tareas
python -m gestor_tareas add "Pagar luz" --prioridad alta   # Tarea 1 añadida: Pagar luz [alta]
python -m gestor_tareas list                               #    1  [ ]  alta   Pagar luz
python -m gestor_tareas done 1                             # Tarea 1 marcada como hecha.
```

`gestor-tareas` es solo el nombre (`prog`) que se muestra en la ayuda y en los errores; el
comando real es `python -m gestor_tareas`. Ayuda: `python -m gestor_tareas --help` o
`python -m gestor_tareas <comando> -h`.

## Uso

Desde `apps/gestor-tareas/`:

```bash
python -m gestor_tareas [--archivo RUTA] <comando> [args]
```

`--archivo` puede ir antes o después del subcomando (`list --archivo RUTA` equivale a
`--archivo RUTA list`); si se da en ambos sitios, gana el de después.

| Comando | Descripción |
|---|---|
| `add TEXTO [--prioridad alta\|media\|baja]` | Añade una tarea pendiente (prioridad por defecto `media`) |
| `list [--estado pendiente\|hecha\|todas]` | Lista por ID ascendente (por defecto `pendiente`) |
| `done ID` | Marca como hecha (idempotente) |
| `remove ID` | Elimina la tarea; su ID no se reutiliza |

`ID` debe ser un entero >= 1; un valor menor o no numérico es un error de uso (código 2).
Formato de `list`: `   3  [ ]  media  Comprar leche` (`[x]` = hecha, `[ ]` = pendiente).
Sin tareas guardadas: `No hay tareas.` Con tareas pero ninguna en el filtro:
`No hay tareas pendientes. Usa --estado todas.` (o `hechas`).

## Archivo de datos

Precedencia: `--archivo` > variable de entorno `GESTOR_TAREAS_ARCHIVO` (vacía = no definida)
> `~/.gestor-tareas.json`. El archivo se crea con el primer `add` y siempre queda con modo `0600`.
Esquema versionado (`version: 1`); la escritura es atómica (temporal + `os.replace`).
Se rechazan enlaces simbólicos, directorios, archivos no regulares (FIFO, dispositivos),
directorios padre inexistentes, archivos de más de
1 MiB y más de 1000 tareas. Texto de tarea: 1 a 200 caracteres, sin caracteres de control.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito |
| 1 | Error de validación o de dominio (texto inválido, ID inexistente, límite de tareas) |
| 2 | Error de uso de la CLI (argumentos inválidos) |
| 3 | Error de almacenamiento (JSON corrupto, esquema inválido, ruta, permisos o E/S) o al escribir la salida (disco lleno, `/dev/full`); en `add`/`done`/`remove` el mensaje avisa de que el cambio sí se guardó |

Los errores van a stderr con el prefijo `Error: `; los resultados, a stdout. Una tubería cerrada
(`list | head`) termina en silencio. Los caracteres de stdout/stderr que la codificación no admita
se sustituyen por `?` en vez de abortar. Las rutas mostradas en errores escapan los caracteres no
imprimibles (por ejemplo `\x1b`).

## Limitaciones

- Sin bloqueo de archivo entre procesos: si dos procesos escriben a la vez, gana la última escritura.
- No hay migraciones: una versión de esquema desconocida se rechaza.
- La ayuda (`uso:`, `opciones:`, `-h`) y los errores de uso más comunes están en español; los
  mensajes de `argparse` que no figuran en la tabla `TRADUCCIONES` de `cli.py` (casos raros, como
  abreviaturas ambiguas) se muestran en inglés.

## Desarrollo y calidad

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check . && ruff format --check .
mypy .
bandit -q -r . -ll -x ./tests
pip-audit -r requirements.txt
```

## CI

`.github/workflows/quality.yml` es una **plantilla** para cuando este proyecto viva en su propio
repositorio (ahí `.github/` queda en la raíz). **GitHub no la ejecuta dentro de este monorepo**:
solo lee `.github/workflows/` de la raíz, que contiene el CI del motor. Para usarla hay que copiar
el proyecto junto con `.claude/scripts/quality-gate.sh` y, recomendado, proteger `main` exigiendo
el check "Quality gate". Mientras tanto, la verificación vigente es el gate local, desde la raíz
del repositorio:

```bash
bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md
```

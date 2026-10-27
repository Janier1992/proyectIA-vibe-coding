# Producción: gestor-tareas

Estado: **verificado mecánicamente, pendiente de decisión y despliegue humanos.** Riesgo: bajo. Decisión del Approver: `APROBADO_AUTO` (ver `decision.md`). Esto significa "verificado con herramientas", no "revisado por una persona".

## Qué es y cómo se distribuye
- CLI de Python (`python -m gestor_tareas`), solo librería estándar, sin dependencias de runtime. Requiere Python >= 3.11 (probado en 3.11, 3.12 y 3.13).
- El proyecto **no define punto de entrada de consola ni sistema de build** (`pyproject.toml` no tiene `[project.scripts]` ni `[build-system]`). Hoy se usa copiando la carpeta o ejecutando el módulo desde ella. Si se quiere `pip install` o un comando `gestor-tareas`, es trabajo nuevo y pasa por una corrida Factory propia.

## Checklist previo al uso real
- [ ] Una persona confirmó el destino de entrega (PR) y la decisión del Approver.
- [ ] Una persona decidió qué hacer con `apps/gestor-tareas/.github/workflows/quality.yml`: GitHub no lo ejecuta dentro de este monorepo; solo funciona si el proyecto vive en su propio repositorio con `.claude/scripts/quality-gate.sh` copiado.
- [ ] En el entorno destino: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` y `bash .claude/scripts/quality-gate.sh .` en `PASS` (9 verificaciones).
- [ ] Prueba manual rápida (ver criterio de éxito).
- [ ] Probado en el sistema operativo real de uso: **no se probó en Windows** (los tests de permisos y symlinks se omiten allí).

## Configuración
- **Variables de entorno:** `GESTOR_TAREAS_ARCHIVO` (opcional). Ruta por defecto: `~/.gestor-tareas.json`.
- **Migraciones / feature flags:** ninguno. El archivo JSON tiene `version: 1`; una versión desconocida se rechaza con código 3.
- **Permisos:** el archivo se crea con modo `0600`.

## Monitoreo
- No hay servicio que monitorear. La señal operativa es el código de salida: 0 éxito, 1 validación o dominio, 2 uso, 3 almacenamiento o salida.

## Plan de rollback
- Volver a la versión anterior de la carpeta. El formato de datos es `version: 1` y no hay migraciones, así que no hay datos que revertir. Conserva una copia del archivo JSON antes de actualizar.

## Criterio de éxito
- `python -m gestor_tareas add "prueba" --archivo /tmp/t.json` imprime `Tarea 1 añadida: prueba [media]` y sale con 0.
- `list --archivo /tmp/t.json` muestra la tarea; `done 1` la marca; `list` ya no la muestra y avisa `No hay tareas pendientes. Usa --estado todas.`
- Un archivo corrupto da un error de una línea con código 3 y **no se sobrescribe**.

## Riesgos y deuda conocida (no bloquean)
- Sin bloqueo de archivo entre procesos: gana la última escritura (documentado en el README).
- Ventana TOCTOU entre validar y reemplazar el destino, sin escritura fuera del destino; un symlink en un directorio padre se acepta.
- Un ID inválido con caracteres de control se refleja sin escapar en el error de uso (solo el argumento del propio usuario).
- Herramientas de desarrollo con versión fijada pero sin hash.
- Lo que argparse no traduce (fuera de la tabla `TRADUCCIONES`) sale en inglés; Python >= 3.14 no se ha probado.

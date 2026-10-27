# Decision: gestor-tareas

Rama `factory/gestor-tareas` | PRP `PRPs/gestor-tareas-2026-10-27.md` | Riesgo declarado: **bajo** (CLI local, sin red, auth, pagos, datos personales, migraciones ni infraestructura).

## Gate (re-ejecutado por el approver)
`bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md` -> exit 0, **GATE: PASS (fallos 0, sin verificar 0)**, 8/8 en PASS. El gate no cubre los defectos de abajo (no ejecuta salida a stdout rota ni codificaciones).

## Veredictos
| Revisor | Veredicto | Nota |
|---|---|---|
| Seguridad | APROBADO | 2 observaciones bajas, 4 informativas |
| UX | **CAMBIOS** | 4 hallazgos; verificados de forma independiente |
| UI | APROBADO (no aplica) | CLI sin interfaz gráfica, conforme al PRP |
| Código | APROBADO | 3 mejoras menores, 4 opcionales de tests |

## Verificación independiente de los hallazgos de UX (ejecutada por el approver)
| Hallazgo | Caso ejecutado | Resultado | Estado |
|---|---|---|---|
| CAMBIOS-1 | `list --archivo x` | `error: unrecognized arguments: --archivo x`, rc 2, sin pista de que va antes del subcomando | CONFIRMADO |
| CAMBIOS-2 | `list > /dev/full` | Traceback `OSError: [Errno 28]`, rc 1 | CONFIRMADO |
| CAMBIOS-2 | `PYTHONIOENCODING=ascii list` con acento/emoji | Traceback `UnicodeEncodeError`, rc 1 | CONFIRMADO |
| CAMBIOS-2 | `add "otra" > /dev/full` | rc 1 pero la tarea 2 **sí quedó guardada** (mensaje engañoso: rc 1 = "validación") | CONFIRMADO |
| CAMBIOS-3 | tras `done` de todas, `list` | `No hay tareas.` aunque existen 2 hechas | CONFIRMADO |
| CAMBIOS-4 | `add -h` | Cadenas de argparse en inglés (`usage:`, `options:`, `show this help message and exit`); `--prioridad` sin help ni default visible | CONFIRMADO |
| Seguridad 1 | `--archivo $'\e[31mROJO/x.json' list` | ESC crudo en stderr | CONFIRMADO |
| Seguridad 2 | FIFO como `--archivo` | `timeout 3` -> rc 124, cuelgue | CONFIRMADO |

## Decisión
Regla 0: gate en PASS, no aplica. Regla 1: hay CAMBIOS pendientes de UX confirmados (el CAMBIOS-2 contradice el criterio "sin traza" del PRP y puede informar un error tras haber persistido el cambio) -> **RECHAZADO**, vuelve al `builder`. No se llega a las reglas 2-4; cuando la iteración quede limpia, el riesgo es bajo y con los 4 revisores en APROBADO y el gate en PASS correspondería `APROBADO_AUTO` (mecánico; fusión a `main` solo con orden explícita, PR por defecto). Esta es la iteración 1 de 3.

## Lista consolidada para el builder

### (a) Obligatorios (CAMBIOS de UX; por prioridad)
1. **CAMBIOS-2, salida rota** (`cli.py` ~148, `print(mensaje)`). Proteger la impresión: `BrokenPipeError` -> salida silenciosa (cerrar stdout sin traza; evitar el aviso de flush al salir); resto de `OSError` y `UnicodeEncodeError` -> `Error: no se pudo escribir la salida: {strerror/motivo acotado}.` a stderr, código 3, documentado en README y epílogo de `--help`. Para `UnicodeEncodeError`, preferible reconfigurar stdout/stderr con `errors="replace"` y no fallar. Cubrir también `add`/`done`/`remove`, donde el guardado ya ocurrió: el mensaje no debe sugerir que no se guardó (por ejemplo, avisar que el cambio sí se guardó). Tests: `/dev/full` (monkeypatch de stdout que lance `OSError`), `BrokenPipeError`, stdout ascii con acentos/emoji, y un subprocess sin Traceback.
2. **CAMBIOS-1, `--archivo` tras el subcomando**. Preferible aceptarlo también en los subparsers (parent parser con `default=argparse.SUPPRESS`, de modo que el valor global no se pise) manteniendo la precedencia `--archivo` > entorno > defecto. Si se complica, mínimo: la pista `--archivo va antes del comando` en el error de uso. Test para el caso elegido y actualizar README y `--help`.
3. **CAMBIOS-3, `list` vacío por filtro**. Archivo inexistente o sin tareas: mantener `No hay tareas.` (criterio 1). Con tareas pero ninguna en el filtro: `No hay tareas pendientes.` / `No hay tareas hechas.` y, si existen de otro estado, añadir `Usa --estado todas.` en la misma línea o en una segunda línea a stdout. Tests por cada combinación.
4. **CAMBIOS-4, ayuda**. Añadir `help=` a `--prioridad` (default `media`) y `--estado` (default `pendiente`) y un epílogo con ejemplo en `add`/`done`/`remove`. Localizar las cadenas de argparse: `add_help=False` + `-h/--help` con texto en español, `ArgumentParser.error` en español (`uso:`, `error: ...`) y títulos de sección en español (`argumentos posicionales`, `opciones`). Si el costo de traducir `invalid choice`/`required` resulta alto, se acepta traducir solo `usage`/`options`/`-h` y documentar la limitación restante en README; no dejar la mezcla sin documentar.

### (b) Recomendados en la misma iteración (bajo costo)
5. **Seguridad 2, FIFO/dispositivos**: exigir `stat.S_ISREG` sobre el destino existente en `_validar_destino` (y en `cargar`) con `ErrorDeAlmacen` (`ruta de archivo no válida '{ruta}': no es un archivo regular.`), código 3. Test con `os.mkfifo` (omitir en Windows). Comprobar antes de `open` para no bloquear.
6. **Seguridad 1, sanear la ruta impresa**: aplicar un único helper (en `almacen.py`) que sustituya los caracteres no imprimibles de `mostrar` (p. ej. `\x1b` -> `\x1b` escapado, usando `repr`-like o filtro `isprintable`) y usarlo en `almacen.py:30-31,56-57` y `cli.py:122`. Test: ruta con ESC no emite ESC crudo en stderr; las rutas normales con acentos siguen apareciendo tal cual (no usar `repr` completo si añade comillas que rompen los mensajes exactos del PRP).
7. **Código 2, orden de validación de versión**: en `_validar_cabecera`, validar `version` antes del conjunto de claves cuando `version` existe y es entero (así `version: 2` con otro esquema da `versión de esquema 2 no soportada`). Test.
8. **Seguridad 4, versión desconocida**: truncar el entero en el mensaje (p. ej. a 20 caracteres con `...`).
9. **Código 3, `# noqa: N818`**: mover a `per-file-ignores` de `gestor_tareas/modelo.py` con comentario, o renombrar; objetivo del PRP: cero `noqa` en producción.
10. **UX, `remove`**: imprimir el texto eliminado (`Tarea 2 eliminada: Pagar luz.`). Es cambio de salida respecto de la tabla del PRP (`Tarea 3 eliminada.`), por lo que solo incluirlo si el criterio 5 y la tabla del PRP se actualizan a la vez; si hay duda, dejarlo en (c).
11. **UX, README**: bloque de inicio rápido de 4 líneas con salida esperada (`cd apps/gestor-tareas`, `python -m gestor_tareas add ...`, `list`, `done 1`), requisito Python >= 3.11 y aclaración de que `gestor-tareas` es solo el `prog` mostrado en ayuda.
12. **Tests de bajo costo (código 4-7)**: `match=` con el detalle esperado en los casos inválidos de `validar_documento`; no-mutación de `validar_documento` y `documento_a_datos`; eliminar la línea sin efecto de `monkeypatch.setattr(almacen, "TAMANO_MAXIMO_ARCHIVO", ...)` (`test_almacen.py:126`); afirmar `ID no válido` en `done 0` / `remove -1`; criterio 27 con `python -m gestor_tareas --help` por subprocess.

### (c) Opcionales, dejar fuera de esta iteración
- TOCTOU entre validación y `replace` (aceptado: `replace` no sigue enlaces).
- IDs enormes aceptados en el JSON (acotado por el límite de 1 MiB).
- Symlink en directorios padre (solo se protege el último componente, por diseño).
- Truncar o ajustar textos largos en `list`.
- Hash-pinning y lockfile de herramientas de desarrollo (YAGNI declarado en el PRP).
- Pinning de acciones de GitHub por SHA (ver CI).
- Prueba de emoji de extremo a extremo (el comportamiento se cubre con el test de ascii de (a)1).
- Bloqueo de archivo entre procesos y soporte de Windows (fuera de alcance del PRP).

## CI inerte (`apps/gestor-tareas/.github/workflows/quality.yml`)
Decisión: **no crear workflow en la raíz y no mover el archivo**; conservarlo como plantilla autocontenida del ejemplo y dejarlo explícito.
- Justificación: la raíz `.github/workflows/` es el CI del kit (`validate-engine.yml`), que valida el motor, no cada ejemplo. Añadir ahí un workflow del ejemplo cambia la infraestructura de CI del repositorio, lo cual el protocolo (regla 2) envía a un humano, y fue precisamente lo que la orden expresa evitó. El workflow interno es correcto para el caso en que el ejemplo se copie a su propio repositorio (ahí sí es raíz y `.claude/` se copia junto).
- Qué debe hacer el builder dentro del ejemplo: (1) añadir al README del proyecto una sección corta "CI" que diga que el workflow es una plantilla para cuando el proyecto viva en su propio repositorio, que GitHub no lo ejecuta dentro de este monorepo, que requiere copiar `.claude/scripts/quality-gate.sh` y que el gate local es la verificación vigente aquí; (2) añadir un comentario de cabecera en el propio `quality.yml` con lo mismo; (3) no reclamar en ningún reporte que "el CI valida" este proyecto; (4) dejar la desviación del PRP registrada en `build.md` (ya lo está), actualizándolo en la nueva iteración. No tocar `validate-engine.yml` ni crear `.github/workflows/` en la raíz.
- Asunto para el humano en la revisión del PR: confirmar la desviación (CI propio del ejemplo, sin gate automático en el monorepo) o pedir expresamente un workflow raíz; esa decisión es de infraestructura y no se toma automáticamente.

## Nota sobre el entorno
`apps/gestor-tareas/.venv` no existe en el árbol actual (el revisor de UX también lo señaló) pero las herramientas están en el `PATH` y el gate pasa. Para reproducibilidad el builder debe crear el `.venv` con `pip install -r requirements-dev.txt` antes de re-ejecutar el gate (`.venv/` ya está ignorado en git).

DECISION: RECHAZADO

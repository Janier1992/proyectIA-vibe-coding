# Build: gestor-tareas

Rama: `factory/gestor-tareas` | PRP: `PRPs/gestor-tareas-2026-10-27.md` | Proyecto: `apps/gestor-tareas/`

## Tareas completadas
1. Scaffolding y baseline: `pyproject.toml` (ruff amplio, mypy estricto, pytest), `requirements.txt` (solo comentario), `requirements-dev.txt` (versiones fijadas), `.gitignore`, `README.md`, `__init__.py`, `__main__.py`.
2. Modelo y errores: `modelo.py` (constantes, `Tarea`, `Documento`, `ErrorDeDominio`, `ErrorDeAlmacen`, `ErrorDeEstructura`).
3. Lógica pura: `logica.py` + `tests/test_logica.py`.
4. Almacenamiento: `almacen.py` + `tests/test_almacen.py`.
5. CLI: `cli.py` + `tests/test_cli.py` (incluye test con `subprocess`, sin shell).
6. CI: `apps/gestor-tareas/.github/workflows/quality.yml` (ver desviaciones).
7. Gate ejecutado y en PASS.

## Archivos (todos bajo `apps/gestor-tareas/`)
`pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`, `README.md`, `.github/workflows/quality.yml`, `gestor_tareas/{__init__,__main__,modelo,logica,almacen,cli}.py`, `tests/{test_logica,test_almacen,test_cli}.py`. Además `factory/gestor-tareas/{build.md,quality-gate.md}`.

## Resultados reales
Las herramientas se ejecutaron en un venv creado con `pip install -r requirements-dev.txt` (ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, bandit 1.9.4, pip-audit 2.10.1; las versiones fijadas se resolvieron e instalaron sin ajustes).
- `pytest -q`: 109 passed.
- `ruff check .`: All checks passed. `ruff format --check .`: 9 files already formatted.
- `mypy .` (estricto, incluye tests): Success, no issues found in 9 source files.
- `bandit -q -r . -ll -x ./tests`: sin hallazgos (exit 0).
- `pip-audit -r requirements.txt`: No known vulnerabilities found.
- `bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md`: exit 0, `GATE: PASS (fallos: 0, sin verificar: 0)`, las 8 verificaciones en PASS (secretos, tamano, patrones-peligrosos, tests-py, lint-py, tipos-py, sast-py, dependencias-py).

Cobertura de criterios de aceptación: los 29 criterios tienen test (1-12, 15-24 en `test_cli`/`test_almacen`; 13 en `test_almacen`+`test_cli`; 14 en `test_cli`/`test_almacen`; 25-26 en `test_logica`; 27-28 en `test_cli`). El criterio 29 es el propio gate. Sin `gate-ignore`. No se debilitó ninguna regla de ruff/mypy/bandit ni se borraron tests.

## Desviaciones respecto del PRP
1. CI: por orden expresa, el workflow se creó en `apps/gestor-tareas/.github/workflows/quality.yml` (no en la raíz), con el proyecto como raíz, `quality-gate.sh . --out quality-gate.md` (asume `.claude/` copiado al proyecto) e instalación de `requirements.txt` y `requirements-dev.txt`. No se creó `.github/workflows/` en la raíz. No se pudo ejecutar este workflow localmente.
2. Entorno de herramientas: en esta máquina `mypy` y `pytest` están instalados en entornos `uv tool` aislados, por lo que mypy no ve `pytest` y falla con `import-not-found`/`untyped-decorator` en los tests. No se tocó la configuración: se ejecutó el gate con un venv único con `requirements-dev.txt` en el `PATH` (como indica el PRP y como hace el CI). Quien ejecute el gate debe tener las herramientas en un mismo entorno.
3. `os.replace`/`os.chmod`: ruff `PTH` (obligatorio por el PRP) prohíbe llamarlos directamente; se usan `Path.replace` y `Path.chmod`, que invocan `os.replace`/`os.chmod`. El comportamiento es idéntico y el test que parchea `os.replace` funciona.
4. IDs 0/negativos (decisión pedida por el PRP): se rechazan con código 2 desde argparse (`ID no válido`); archivo sin cambios. Documentado en README.
5. Se añadió `ErrorDeEstructura(ErrorDeAlmacen)` en `modelo.py` para que la lógica pura devuelva solo el `{detalle}` y `almacen.cargar` componga el mensaje con la ruta (la lógica no conoce rutas). La versión desconocida se lanza como `ErrorDeAlmacen` con el mensaje final.
6. Mensajes con `{ruta}`: `cargar`/`guardar` aceptan un parámetro opcional `mostrar` para imprimir la ruta tal como la dio el usuario (sin resolver), conforme al PRP.
7. `# noqa` (2 en `modelo.py`, 1 en `tests/test_cli.py`), todos con código y motivo: `N818` en `ErrorDeDominio`/`ErrorDeAlmacen` (nombres fijados por el PRP y por el contrato de mensajes; la regla exige sufijo `Error`); `S603` en el `subprocess.run` del test (lista de argumentos fija, sin shell, `sys.executable`). Objetivo del PRP era cero; estos tres están justificados.
8. Los identificadores del código son ASCII (`agregado` en vez de `añadir`).

## Deuda técnica / limitaciones
- Sin bloqueo de archivo entre procesos (última escritura gana); documentado en README.
- Sin hash-pinning de herramientas de desarrollo (YAGNI, declarado en el PRP); sin lockfile porque no hay dependencias de runtime.
- Sin medición de cobertura (`pytest-cov` fuera de alcance).
- Se mantiene fuera de alcance Windows en la práctica: los tests de permisos y symlinks se omiten ahí; no se probó en Windows.
- Python 3.13 local; CI usa 3.12 y el proyecto declara >= 3.11. `datetime.UTC` existe desde 3.11, pero no se ejecutó en 3.11/3.12 localmente.

## Iteración 2

Origen: `decision.md` (RECHAZADO, iteración 1 de 3). Aplicados todos los obligatorios (a) y los recomendados (b); los opcionales (c) quedan fuera. Entorno: `apps/gestor-tareas/.venv` ya existía (Python 3.13.17, `requirements-dev.txt`); el gate lo prioriza.

### Qué se corrigió
| # | Hallazgo | Corrección | Test que falla sin el arreglo |
|---|---|---|---|
| a1 | CAMBIOS-2 salida rota | `cli._emitir`: `BrokenPipeError` -> código 0 y silencio; otro `OSError` -> `Error: no se pudo escribir la salida: {motivo<=100}.` (+ ` El cambio sí se guardó.` si hubo guardado), código 3; stdout se redirige a `/dev/null` para que el vaciado final no falle; stdout/stderr se reconfiguran con `errors="replace"` (no hay `UnicodeEncodeError`); `BrokenPipeError` también en `--help` | `test_salida_llena_*`, `test_tuberia_cerrada_es_silenciosa`, `test_dev_full_extremo_a_extremo` (subprocess con `/dev/full`), `test_stdout_ascii_con_acentos_no_falla` (`PYTHONIOENCODING=ascii`) |
| a2 | CAMBIOS-1 `--archivo` tras el subcomando | Opción también en los 4 subparsers con `default=argparse.SUPPRESS` (no pisa el valor global); precedencia intacta | `test_archivo_despues_del_subcomando`, `test_archivo_antes_no_se_pisa_y_despues_gana` |
| a3 | CAMBIOS-3 `list` vacío por filtro | `No hay tareas pendientes. Usa --estado todas.` / `No hay tareas hechas. ...`; sin tareas se mantiene `No hay tareas.` | `test_list_vacio_segun_filtro` (4 combinaciones) + `test_list_todas_vacio_...` |
| a4 | CAMBIOS-4 ayuda | Parser propio (`_Parser`/`_Formateador`): `-h` en español, `uso:`, `argumentos posicionales`, `opciones`; `error()` traduce los mensajes de argparse de la tabla `TRADUCCIONES`; `help` con defaults en `--prioridad`/`--estado`; epílogo con ejemplo en los 4 subcomandos | `test_ayuda_en_espanol`, `test_errores_de_uso_en_espanol`, `test_help_por_subprocess_en_espanol`, `test_errores_de_uso_codigo_2` (ahora `uso:`) |
| b5 | Seguridad 2, FIFO | `_validar_destino` rechaza lo que exista y no sea archivo regular (`no es un archivo regular`), antes de abrir | `test_fifo_como_archivo_no_cuelga` (subprocess, `os.mkfifo`), `test_cargar_rechaza_archivo_no_regular` |
| b6 | Seguridad 1, ESC en ruta | `almacen.texto_seguro` (escapa lo no imprimible; acentos intactos) aplicado en `_ruta_invalida`, `cargar`, `guardar` y `cli._ciclo` | `test_ruta_con_escape_*`, `test_texto_seguro`, `test_ruta_con_acentos_se_muestra_tal_cual` |
| b7 | Código 2, orden de versión | `_validar_cabecera` valida la versión antes del conjunto de claves | `test_version_desconocida_gana_a_otras_claves`, `test_version_con_otras_claves_...` |
| b8 | Seguridad 4, versión enorme | Entero truncado a 20 dígitos + `...` | `test_version_desconocida_enorme_se_trunca`, `test_version_enorme_se_trunca` |
| b9 | `# noqa: N818` | Retirados de `modelo.py`; `per-file-ignores` de `gestor_tareas/modelo.py` en `pyproject.toml` con comentario. Cero `noqa` en producción. | gate (lint) |
| b11 | README | Inicio rápido de 3 comandos con salida, Python >= 3.11, aclaración de `prog`, `--archivo` flexible, mensajes de `list`, código 3 ampliado, limitación de traducción de argparse, sección "CI" | n/a |
| b12 | Tests baratos | `match=` con el detalle en cada caso inválido de `validar_documento`; no-mutación de `validar_documento`/`documento_a_datos`; eliminada la línea sin efecto de `test_almacen.py`; `ID no válido` afirmado en `done 0`/`remove -1`; criterio 27 por subprocess | los propios tests |

CI inerte (decisión del Approver): no se creó workflow en la raíz ni se movió el archivo; `apps/gestor-tareas/.github/workflows/quality.yml` lleva cabecera que dice que GitHub no lo ejecuta en este monorepo y que el gate local es la verificación vigente; README con sección "CI". No se afirma que "el CI valida" este proyecto.

### Cambios al PRP (`PRPs/gestor-tareas-2026-10-27.md`) hechos a la vez que el código y los tests
- Especificación: `--archivo` antes o después del subcomando; mensaje de `list` vacío por filtro (criterio 1 ampliado); código 3 incluye archivo no regular y error al escribir la salida; filas nuevas en la tabla de mensajes (escritura de salida; archivo no regular); fila de argparse ahora "localizado al español" (`uso:`); `{ruta}` con caracteres no imprimibles escapados; requisitos de UX de la ayuda; criterio 27 (español); nota en la sección CI.
- Criterios nuevos 30 a 36 (salida rota, `--archivo` flexible, `list` por filtro, ayuda en español, FIFO, ruta saneada, versión). El texto del criterio 9 (código 2 de argparse) no cambia.
- Tests existentes ajustados: `test_errores_de_uso_codigo_2` espera `uso:` en lugar de `usage:`.

### Resultados reales (desde `apps/gestor-tareas`, con `.venv`)
- `pytest -q`: 144 passed (antes 109). Sin los cambios de `gestor_tareas/` fallan 33 de ellos (comprobado con `git stash` de la carpeta de producción; el de FIFO agota el timeout de 30 s en vez de colgarse).
- `ruff check .`: All checks passed. `ruff format --check .`: 13 files already formatted.
- `mypy .` (estricto): Success, no issues found in 12 source files.
- `bandit -q -r . -ll -x ./tests,./.venv`: sin hallazgos (exit 0).
- `bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md` (raíz): **GATE: PASS (fallos: 0, sin verificar: 0)**, 8/8 en PASS.

### Desviaciones y notas
1. Se omite (b10, `remove` imprime el texto eliminado) por orden expresa: el comportamiento de `remove` no cambia (`Tarea N eliminada.`).
2. Los tests se repartieron: `tests/ayudas.py` (helpers `Entorno`, `ejecutar`, `POSIX`), `tests/conftest.py` (fixture `entorno`) y `tests/test_cli_robustez.py` (criterios 30 a 36) para respetar las 500 líneas por archivo. El único `# noqa: S603` (subprocess con lista fija, sin shell) es el existente, movido a `ayudas.py`; no se añadió ningún `noqa` ni `type: ignore` nuevo.
3. La traducción de argparse cubre `usage`/`options`/`-h`/secciones y los mensajes `required`, `unrecognized arguments`, `invalid choice`, `expected one argument` y el prefijo `argument`; el resto se muestra en inglés y está documentado en el README. El texto de `invalid choice` depende del formato de argparse de cada versión de Python (probado en 3.13).
4. El `dup2` de stdout a `/dev/null` tras un fallo de escritura se omite en silencio si stdout no tiene descriptor (pytest/capsys).
5. Código de salida 0 para `BrokenPipeError` (decisión del Builder: patrón `| head`); el Approver no fijó un código.
6. Siguen abiertos los opcionales (c) y el CI sin ejecución automática en el monorepo (confirmación humana en la revisión del PR).

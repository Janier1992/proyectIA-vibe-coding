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

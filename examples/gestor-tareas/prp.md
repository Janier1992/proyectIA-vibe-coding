# PRP: Gestor de tareas CLI (`gestor-tareas`)

Fecha: 2026-10-27 | Tipo: software (CLI Python, sin red, sin HTTP) | Plantilla base: `prp_backend_api.md` adaptada a CLI
Rama de trabajo: `examples/gestor-tareas/run` | Directorio del proyecto: `examples/gestor-tareas/app/`

## Goal
CLI en Python 3 que gestiona una lista personal de tareas persistida en un único archivo JSON local. Solo librería estándar en runtime (`argparse`, `json`, `pathlib`, `os`, `tempfile`, `dataclasses`, `datetime`, `sys`). La lógica de negocio es pura (sin E/S) y está separada del almacenamiento y de la CLI para poder testearla sin tocar disco.

### Alcance
- Comandos: `add`, `list`, `done`, `remove`.
- Persistencia JSON con esquema versionado, escritura atómica, permisos `0o600`.
- Validación de entradas, errores claros sin traza, códigos de salida definidos.
- Baseline de calidad completo (ruff amplio con seguridad, mypy estricto, pytest, bandit, pip-audit) y quality gate en PASS.

### No-alcance (YAGNI)
Edición de texto, fechas de vencimiento, etiquetas, búsqueda, ordenación configurable, deshacer, múltiples listas, sincronización/red, colores ANSI, i18n, paquete instalable en PyPI/entry point (se ejecuta con `python -m gestor_tareas`), bloqueo de archivo entre procesos concurrentes (se documenta como limitación), migraciones entre versiones de esquema (solo se rechaza una versión desconocida), cobertura medida con `pytest-cov`, UI gráfica.

### Nivel de riesgo: **bajo**
Justificación: herramienta local de un solo usuario, sin red, sin autenticación, sin pagos, sin datos personales sensibles (texto libre del propio usuario), sin migraciones destructivas ni infraestructura; el único efecto persistente es un archivo JSON local, escrito de forma atómica. Puntos que se vigilan pese al riesgo bajo: `--archivo` es entrada no confiable (rutas) y el JSON del disco es entrada no confiable. No sube a medio porque no hay datos de terceros ni privilegios elevados. Si el builder añadiera cualquier acceso a red, auth o borrado de archivos distintos del propio JSON, el riesgo deberá reevaluarse.

### Revisores aplicables
- Seguridad: aplica (rutas, JSON no confiable, escritura atómica, permisos).
- UX: aplica, entendido como salida de terminal y mensajes de error (sin UI gráfica).
- **UI: NO aplica.** Es una CLI sin interfaz gráfica; el revisor de UI debe emitir "no aplica" (sin contraste, layout ni WCAG que evaluar).
- Código: aplica.

## Success Criteria
- [ ] Los 4 comandos funcionan según la especificación de CLI y los casos de aceptación de este PRP.
- [ ] El archivo JSON respeta el esquema versionado; versión desconocida, estructura inválida o JSON corrupto producen error claro, código 3, sin traza y sin modificar el archivo.
- [ ] Escritura atómica (temporal en el mismo directorio + `os.replace`); el archivo final tiene modo `0o600` en POSIX.
- [ ] Toda entrada se valida (texto, prioridad, estado, ID, ruta) antes de tocar disco.
- [ ] Lógica pura en `logica.py` sin importar `os`, `pathlib`, `sys` ni `json`; ninguna función pura hace E/S ni lee el reloj.
- [ ] `bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out examples/gestor-tareas/run/quality-gate.md` termina con `GATE: PASS` (exit 0), con `dependencias-py` en PASS.
- [ ] Todos los casos de aceptación (sección final) tienen un test pytest asociado y pasan.

## Estructura de archivos (tarea del Builder)
Nota de nomenclatura: el directorio del proyecto es `kebab-case` (`gestor-tareas`) según CLAUDE.md; el paquete Python usa `snake_case` (`gestor_tareas`) porque un identificador importable no admite guiones. Es una excepción obligada por el lenguaje, no una desviación.

```
examples/gestor-tareas/app/
  pyproject.toml            # ruff, mypy, pytest (sin [project.dependencies] con terceros)
  requirements.txt          # solo comentario (runtime vacío)
  requirements-dev.txt      # herramientas de calidad con versión fijada
  README.md                 # uso, variables de entorno, límites, códigos de salida
  .gitignore                # __pycache__/, .mypy_cache/, .ruff_cache/, .pytest_cache/, .venv/
  gestor_tareas/
    __init__.py             # __version__ (str)
    __main__.py             # llama a cli.principal() y hace sys.exit con su retorno
    modelo.py               # constantes, Tarea (dataclass frozen), errores de dominio, tipos
    logica.py               # funciones PURAS
    almacen.py              # E/S: resolver ruta, cargar, guardar atómico
    cli.py                  # argparse, formateo de salida, mapeo error -> código de salida
  tests/
    test_logica.py
    test_almacen.py
    test_cli.py
.github/workflows/quality.yml   # en la RAÍZ del repo (ver sección CI)
```
Límites del motor: archivos <= 500 líneas, funciones <= 50 líneas, una responsabilidad por módulo.

## Especificación de la CLI

Invocación: `python -m gestor_tareas [--archivo RUTA] <comando> [args]` ejecutado desde `examples/gestor-tareas/app/`. `--archivo` es opción global y puede ir **antes o después** del subcomando (documentarlo en `--help`); si se da en ambos sitios gana el de después; la precedencia `--archivo` > entorno > defecto no cambia.

| Comando | Sintaxis | Comportamiento | Salida en stdout (éxito) |
|---|---|---|---|
| `add` | `add TEXTO [--prioridad alta\|media\|baja]` | Añade tarea `pendiente`; prioridad por defecto `media` | `Tarea 3 añadida: Comprar leche [media]` |
| `list` | `list [--estado pendiente\|hecha\|todas]` | Lista tareas ordenadas por `id` ascendente; estado por defecto `pendiente` | Una línea por tarea (formato abajo); si no hay ninguna: `No hay tareas.` (archivo inexistente o sin tareas); si hay tareas pero ninguna en el filtro: `No hay tareas pendientes. Usa --estado todas.` / `No hay tareas hechas. Usa --estado todas.` |
| `done` | `done ID` | Marca la tarea como `hecha`. Idempotente: si ya estaba hecha, éxito con aviso | `Tarea 3 marcada como hecha.` / `La tarea 3 ya estaba hecha.` |
| `remove` | `remove ID` | Elimina la tarea; el ID no se reutiliza | `Tarea 3 eliminada.` |

Formato de línea de `list`: `{id:>4}  [{x| }]  {prioridad:<5}  {texto}` donde `[x]` = hecha y `[ ]` = pendiente. Ejemplo: `   3  [ ]  media  Comprar leche`. Solo stdout para resultados; todos los errores a stderr.

Resolución de la ruta del archivo (orden de precedencia): `--archivo` > variable de entorno `GESTOR_TAREAS_ARCHIVO` > `~/.gestor-tareas.json` (`Path.home() / ".gestor-tareas.json"`). Una variable de entorno definida pero vacía se trata como no definida.

### Códigos de salida
| Código | Significado |
|---|---|
| 0 | Éxito |
| 1 | Error de validación o de dominio (texto vacío/largo/con caracteres de control, ID inexistente, límite de tareas alcanzado) |
| 2 | Error de uso de la CLI (argumentos inválidos: prioridad/estado fuera de lista, ID no entero, falta de subcomando). Lo produce `argparse` (`SystemExit(2)`); no se redefine |
| 3 | Error de almacenamiento (JSON corrupto, esquema inválido, versión desconocida, ruta inválida/symlink/directorio/archivo no regular, permisos o E/S del sistema, archivo demasiado grande) o error al escribir la salida (stdout lleno o inválido; un `BrokenPipeError` termina en silencio con 0) |

`cli.principal(argv: Sequence[str] | None = None) -> int` devuelve el código; solo `__main__.py` llama a `sys.exit`. Ninguna excepción prevista llega al usuario como traza: se captura en `principal` y se traduce a mensaje + código. No usar `except Exception` desnudo ni silenciar errores (B110/BLE001).

### Mensajes de error (stderr, prefijo fijo `Error: `, una línea, en español, sin rutas internas de Python ni trazas)
| Condición | Mensaje exacto | Código |
|---|---|---|
| Texto vacío o solo espacios | `Error: el texto de la tarea no puede estar vacío.` | 1 |
| Texto > 200 caracteres | `Error: el texto supera el máximo de 200 caracteres (tiene {n}).` | 1 |
| Texto con caracteres de control | `Error: el texto contiene caracteres de control no permitidos.` | 1 |
| ID inexistente | `Error: no existe la tarea con ID {id}.` | 1 |
| Límite de tareas | `Error: se alcanzó el máximo de 1000 tareas.` | 1 |
| ID no entero / prioridad o estado inválidos / falta subcomando | Mensaje de `argparse` localizado al español (`uso: ...` + `<prog>: error: ...`) | 2 |
| Archivo no es JSON válido | `Error: el archivo '{ruta}' no es JSON válido; corrígelo o elimínalo.` | 3 |
| JSON válido con estructura inválida | `Error: el archivo '{ruta}' tiene una estructura inválida: {detalle}.` | 3 |
| Versión de esquema desconocida | `Error: versión de esquema {v} no soportada (se esperaba 1).` | 3 |
| Archivo > 1 MiB | `Error: el archivo '{ruta}' supera el tamaño máximo permitido (1 MiB).` | 3 |
| Ruta es un directorio, symlink, archivo no regular (FIFO, dispositivo) o el directorio padre no existe | `Error: ruta de archivo no válida '{ruta}': {motivo}.` | 3 |
| `OSError` al leer/escribir (permisos, disco lleno) | `Error: no se pudo acceder al archivo '{ruta}': {strerror}.` | 3 |
| `OSError` al escribir la salida (stdout) | `Error: no se pudo escribir la salida: {strerror}.` y, si el comando ya había guardado cambios, se añade ` El cambio sí se guardó.` | 3 |

`{ruta}` es la ruta tal como la dio el usuario (sin resolver) y con los caracteres no imprimibles escapados (`\x1b`), `{detalle}` y `{motivo}` son textos propios y acotados (nunca el repr de una excepción de Python ni contenido del archivo sin acotar). Mensajes de sugerencia opcional permitidos solo si caben en la misma línea.

## Modelo de datos (esquema JSON versionado)

Archivo en UTF-8, `json.dump(..., ensure_ascii=False, indent=2, sort_keys=True)` más salto de línea final:
```json
{
  "version": 1,
  "siguiente_id": 4,
  "tareas": [
    {
      "id": 3,
      "texto": "Comprar leche",
      "prioridad": "media",
      "estado": "pendiente",
      "creada": "2026-10-27T09:30:00+00:00"
    }
  ]
}
```
Reglas de validación al cargar (todas en `almacen.cargar` / función pura `logica.validar_documento`; cualquier violación = error de almacenamiento código 3):
- Raíz es objeto con exactamente las claves `version`, `siguiente_id`, `tareas` (claves extra rechazadas).
- `version == 1` (entero, no `bool`). Otro valor -> mensaje de versión no soportada.
- `siguiente_id`: entero >= 1 (no `bool`) y estrictamente mayor que el máximo `id` existente.
- `tareas`: lista de <= 1000 elementos; cada tarea es objeto con exactamente `id` (entero >= 1, no `bool`, único), `texto` (str, 1..200 tras validación, sin caracteres de control), `prioridad` in {`alta`,`media`,`baja`}, `estado` in {`pendiente`,`hecha`}, `creada` (str ISO 8601 parseable con `datetime.fromisoformat`).
- Tipos desconocidos nunca se `eval`úan ni se deserializan con `pickle`; solo `json.loads`.
- Archivo inexistente = lista vacía válida (`version 1`, `siguiente_id 1`), **no** es error; el archivo se crea en la primera escritura (`add`). Los comandos `list`, `done` y `remove` sobre archivo inexistente no lo crean (`done`/`remove` fallan con ID inexistente, código 1).
- Archivo existente de 0 bytes o solo espacios = JSON corrupto (código 3), para no sobrescribir datos por accidente.

### Límites (constantes `UPPER_SNAKE_CASE` en `modelo.py`)
| Constante | Valor | Uso |
|---|---|---|
| `LONGITUD_MAXIMA_TEXTO` | 200 | Longitud del texto tras `strip()` (en caracteres, no bytes) |
| `MAXIMO_TAREAS` | 1000 | Tareas almacenadas simultáneamente |
| `TAMANO_MAXIMO_ARCHIVO` | 1_048_576 (1 MiB) | Bytes máximos al leer, comprobado antes de parsear |
| `VERSION_ESQUEMA` | 1 | Versión del documento |
| `PRIORIDADES` | `("alta","media","baja")` | Lista permitida |
| `ESTADOS` | `("pendiente","hecha")` | Lista permitida; `todas` solo es filtro de `list`, nunca un estado almacenado |

Tipos (`modelo.py`): `Tarea` como `@dataclass(frozen=True, slots=True)` con campos `id: int`, `texto: str`, `prioridad: str`, `estado: str`, `creada: str`; `Documento` como dataclass frozen con `siguiente_id: int` y `tareas: tuple[Tarea, ...]`. Errores: `class ErrorDeDominio(Exception)` (código 1) y `class ErrorDeAlmacen(Exception)` (código 3), cada uno con un mensaje ya listo para el usuario. Se permite `Literal["alta","media","baja"]` para prioridad si mypy estricto lo soporta sin `cast`.

## Contrato de las funciones puras (`logica.py`)
Sin E/S, sin reloj, sin globales mutables, sin efectos secundarios; nunca mutan sus argumentos (devuelven nuevos objetos inmutables). Todas con anotaciones completas de parámetros y retorno.

| Función | Firma | Contrato |
|---|---|---|
| `normalizar_texto` | `(texto: str) -> str` | `strip()`; lanza `ErrorDeDominio` si queda vacío, si `len > LONGITUD_MAXIMA_TEXTO`, o si contiene algún carácter con `unicodedata.category` en `{Cc, Cf, Cs, Co, Cn}` o saltos de línea/tabulaciones (regla simple: rechazar todo carácter no `str.isprintable()` salvo espacio normal). Devuelve el texto limpio |
| `validar_prioridad` | `(valor: str) -> str` | Devuelve `valor` si está en `PRIORIDADES`; si no lanza `ErrorDeDominio` (defensa en profundidad: argparse ya restringe con `choices`) |
| `agregar_tarea` | `(doc: Documento, texto: str, prioridad: str, creada: str) -> tuple[Documento, Tarea]` | Normaliza y valida; lanza `ErrorDeDominio` si ya hay `MAXIMO_TAREAS`; asigna `id = doc.siguiente_id`; devuelve documento nuevo con `siguiente_id + 1` y la tarea creada. `creada` lo inyecta el llamador (la CLI usa `datetime.now(timezone.utc).isoformat(timespec="seconds")`) para mantener la pureza |
| `filtrar_tareas` | `(doc: Documento, estado: str) -> tuple[Tarea, ...]` | `estado` in `pendiente`/`hecha`/`todas`; orden por `id` ascendente; `ErrorDeDominio` si el estado es otro |
| `marcar_hecha` | `(doc: Documento, id_tarea: int) -> tuple[Documento, bool]` | Devuelve documento nuevo y `True` si cambió, `False` si ya estaba hecha (idempotente); `ErrorDeDominio` (`no existe la tarea con ID {id}.`) si no existe |
| `eliminar_tarea` | `(doc: Documento, id_tarea: int) -> Documento` | Elimina la tarea; `siguiente_id` no cambia (los ID no se reutilizan); `ErrorDeDominio` si no existe |
| `documento_vacio` | `() -> Documento` | `Documento(siguiente_id=1, tareas=())` |
| `validar_documento` | `(datos: object) -> Documento` | Convierte el valor devuelto por `json.loads` en `Documento` aplicando todas las reglas de la sección Modelo de datos; lanza `ErrorDeAlmacen` con `{detalle}` acotado; nunca lanza `KeyError`/`TypeError`/`AttributeError` |
| `documento_a_datos` | `(doc: Documento) -> dict[str, object]` | Inversa de la anterior; resultado serializable por `json` |

## Capa de almacenamiento (`almacen.py`)

| Función | Contrato |
|---|---|
| `resolver_ruta(archivo: str \| None, entorno: Mapping[str, str]) -> Path` | Aplica la precedencia `--archivo` > `GESTOR_TAREAS_ARCHIVO` > por defecto. Rechaza cadena vacía/solo espacios y rutas con byte nulo. Aplica `Path(...).expanduser()` y la hace absoluta con `Path.absolute()` (sin seguir symlinks, **no** `resolve()` para no seguir enlaces). Lanza `ErrorDeAlmacen` |
| `cargar(ruta: Path) -> Documento` | Si la ruta es symlink (`is_symlink()`) o directorio -> `ErrorDeAlmacen`. Si no existe -> `documento_vacio()`. Comprueba `stat().st_size <= TAMANO_MAXIMO_ARCHIVO` antes de leer; lee con `open(..., "rb")` limitado a `TAMANO_MAXIMO_ARCHIVO + 1` bytes (por si el archivo crece entre `stat` y lectura), decodifica UTF-8 estricto, `json.loads`, y delega en `validar_documento`. `UnicodeDecodeError`, `json.JSONDecodeError`, `RecursionError`, `ValueError` y `OSError` se traducen a `ErrorDeAlmacen` con los mensajes de la tabla |
| `guardar(ruta: Path, doc: Documento) -> None` | Exige que el directorio padre exista (no lo crea) y que la ruta destino no sea symlink ni directorio. Serializa **antes** de abrir nada. Crea el temporal con `tempfile.mkstemp(dir=ruta.parent, prefix=".gestor-tareas-", suffix=".tmp")` (modo `0o600`, mismo sistema de archivos), escribe, `flush` + `os.fsync`, `os.chmod(tmp, 0o600)` explícito, `os.replace(tmp, ruta)`. En `finally`, si el temporal sigue existiendo se elimina (`contextlib.suppress(FileNotFoundError)`); un fallo de escritura deja el archivo original intacto. Tras `os.replace`, el archivo final tiene modo `0o600` aunque antes tuviera otro |

Guardado solo ocurre en `add`, `done` (solo si cambió) y `remove`; `list` y errores de validación nunca escriben. Escritura y lectura de cada comando son un ciclo cargar -> función pura -> guardar; sin caché ni estado global.

## Implementation Blueprint

### Lista de tareas
```yaml
Task 1: Scaffolding y baseline de calidad
  CREATE: examples/gestor-tareas/app/{pyproject.toml, requirements.txt, requirements-dev.txt, .gitignore, README.md}
  CREATE: examples/gestor-tareas/app/gestor_tareas/{__init__.py, __main__.py}
  VALIDATE: ruff check . ; mypy . (desde examples/gestor-tareas/app/)

Task 2: Modelo y errores
  CREATE: examples/gestor-tareas/app/gestor_tareas/modelo.py
  VALIDATE: mypy estricto sin errores

Task 3: Lógica pura + tests
  CREATE: examples/gestor-tareas/app/gestor_tareas/logica.py
  CREATE: examples/gestor-tareas/app/tests/test_logica.py
  VALIDATE: pytest -q tests/test_logica.py

Task 4: Almacenamiento + tests (usar tmp_path de pytest, nunca el HOME real)
  CREATE: examples/gestor-tareas/app/gestor_tareas/almacen.py
  CREATE: examples/gestor-tareas/app/tests/test_almacen.py
  VALIDATE: pytest -q tests/test_almacen.py

Task 5: CLI + tests de integración (invocar cli.principal(argv) con capsys, y un test con subprocess usando sys.executable y lista de args, sin shell=True)
  CREATE: examples/gestor-tareas/app/gestor_tareas/cli.py
  CREATE: examples/gestor-tareas/app/tests/test_cli.py
  VALIDATE: pytest -q

Task 6: CI
  CREATE: .github/workflows/quality.yml (raíz del repo; ver sección CI)

Task 7: Gate
  RUN: bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out examples/gestor-tareas/run/quality-gate.md
  EXPECT: GATE: PASS
```

### Validation Loop
```bash
cd examples/gestor-tareas/app
python3 -m venv /tmp/venv-gestor && . /tmp/venv-gestor/bin/activate   # o usar las herramientas ya instaladas
pip install -r requirements-dev.txt
pytest -q
ruff check .
ruff format --check .
mypy .
bandit -q -r . -ll -x ./tests
pip-audit -r requirements.txt
cd ../..
bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out examples/gestor-tareas/run/quality-gate.md
```
Prueba manual mínima (usar archivo temporal, nunca el HOME real):
```bash
export GESTOR_TAREAS_ARCHIVO="$(mktemp -u)"      # el archivo aún no existe
python -m gestor_tareas add "Comprar leche" --prioridad alta
python -m gestor_tareas list
python -m gestor_tareas done 1
python -m gestor_tareas list --estado todas
python -m gestor_tareas remove 1
```

## Baseline de calidad y seguridad (obligatorio)
Ver `.claude/prompts/estandar-calidad.md`. Esta sección refleja cómo `.claude/scripts/quality-gate.sh` detecta y ejecuta Python; el gate se ejecuta **desde la raíz del repo** con el directorio del proyecto como argumento, y el script hace `cd examples/gestor-tareas/app`, de modo que todos los comandos corren con ese directorio como cwd.

### Cómo el gate evalúa este proyecto
| Verificación del gate | Comando real ejecutado (cwd = `examples/gestor-tareas/app`) | Requisito para PASS |
|---|---|---|
| `secretos` | `gitleaks` si existe; si no, regex integrado sobre archivos no-test | Ningún literal tipo `password/token/secret/api_key = "..."` (8+ caracteres) en código no-test, ningún `.env` versionado. Los tests (`test_*.py`) están exentos del regex, pero igualmente no deben contener secretos reales |
| `tamano` | recuento de líneas de `*.py` | Cada archivo <= 500 líneas |
| `patrones-peligrosos` | grep en `*.py` no-test (los de `tests/` se omiten) de `eval(`, `exec(`, `os.system(`, `shell=True`, `pickle.load(s)(`, `verify=False` | Ninguna aparición **ni siquiera en comentarios o docstrings** de código de producción (evitar escribir esas cadenas literales, p. ej. en la documentación del módulo). Usar `ast.literal_eval` tampoco es necesario; no se usa |
| `tests-py` | `pytest -q` | Debe existir al menos un archivo `tests/test_*.py` (existe) y pasar. `pyproject.toml` fija `pythonpath = ["."]` y `testpaths = ["tests"]` para que `import gestor_tareas` funcione sin instalar el paquete |
| `lint-py` | `ruff check . --extend-exclude 'node_modules,.git,.claude,.agents,factory,PRPs,examples,dist,build,.next,.venv,venv,__pycache__,coverage'` | Cero errores con la configuración de `pyproject.toml` |
| `tipos-py` | `mypy . --ignore-missing-imports --exclude '(node_modules\|...\|coverage)/'` | Cero errores en modo estricto, **incluidos los tests** (también deben estar totalmente tipados: `def test_x(tmp_path: Path) -> None`). Ojo: `--exclude` de la línea de comandos reemplaza al `exclude` del pyproject; no depender de él |
| `sast-py` | `bandit -q -r . -ll -x ./tests,./node_modules,...` | Cero hallazgos de severidad media o superior. Los tests quedan excluidos de bandit, pero igualmente no deben usar `shell=True` |
| `dependencias-py` | Si existe `requirements.txt`: `pip-audit -r requirements.txt`. **Si no existe y hay `pyproject.toml`, el gate devuelve UNVERIFIED** | Por eso `requirements.txt` es **obligatorio**: contiene solo comentarios (sin paquetes). Verificado empíricamente en este entorno con pip-audit 2.10.1: un `requirements.txt` solo de comentarios devuelve "No known vulnerabilities found" (exit 0) = PASS. Sin `requirements.txt` el resultado sería UNVERIFIED y el gate no sería PASS |

El gate imprime una fila por verificación; el resultado esperado es 8 filas en PASS (`secretos`, `tamano`, `patrones-peligrosos`, `tests-py`, `lint-py`, `tipos-py`, `sast-py`, `dependencias-py`), `GATE: PASS (fallos: 0, sin verificar: 0)`. Como las rutas excluidas incluyen `factory`, `PRPs` y `.claude`, el reporte generado en `examples/gestor-tareas/run/quality-gate.md` no contamina el análisis.

El gate necesita que `ruff`, `mypy`, `pytest`, `bandit` y `pip-audit` estén en el `PATH` (si falta alguna el resultado es UNVERIFIED). Entorno de referencia verificado: Python 3.13.17, ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, bandit 1.9.4, pip-audit 2.10.1.

### Herramientas
- Tests: `pytest`. Linter: `ruff` (`ruff check` y `ruff format --check`; el formato no lo ejecuta el gate pero se exige en Validation Loop). Tipos: `mypy` estricto. SAST: `bandit`. Auditoría: `pip-audit`.
- `requirements.txt` (runtime, vacío):
  ```
  # Sin dependencias de runtime: gestor-tareas usa solo la librería estándar de Python.
  ```
- `requirements-dev.txt` (reproducibilidad; versiones fijadas con `==` a las verificadas en el entorno; el builder confirma con `pip index versions <paquete>` o instalación real que existen y son los paquetes oficiales, y ajusta solo si alguna no se resuelve):
  ```
  ruff==0.16.9
  mypy==2.3.1
  pytest==9.1.1
  bandit==1.9.4
  pip-audit==2.10.1
  ```
- Lockfile: no aplica en runtime (cero dependencias de terceros). Las herramientas de desarrollo quedan fijadas por versión exacta; no se exige hash-pinning (YAGNI), se declara en el reporte del Builder.

### `pyproject.toml` (requisitos de contenido, el Builder lo escribe)
- `[project]`: `name = "gestor-tareas"`, `version = "0.1.0"`, `requires-python = ">=3.11"`, **sin** `dependencies` de terceros (lista vacía o ausente). Sin `[build-system]` obligatorio (no se empaqueta).
- `[tool.pytest.ini_options]`: `pythonpath = ["."]`, `testpaths = ["tests"]`, `addopts = "-ra --strict-markers"`.
- `[tool.mypy]`: `python_version = "3.11"`, `strict = true`, `warn_unreachable = true`, `warn_unused_ignores = true`, `disallow_any_explicit = true`, `show_error_codes = true`. Sin `# type: ignore` salvo caso justificado con código de error y comentario.
- `[tool.ruff]`: `target-version = "py311"`, `line-length = 100`, `extend-exclude` con las carpetas del motor.
- `[tool.ruff.lint]`: reglas amplias, como mínimo `select = ["E", "W", "F", "I", "N", "UP", "B", "A", "C4", "C90", "S", "BLE", "SIM", "PTH", "RET", "ARG", "ANN", "PL", "TRY", "PT", "RUF", "ERA", "PERF", "FBT", "DTZ", "EM", "ISC", "G", "T10"]`. `C90` con `max-complexity = 10`. `S` (flake8-bandit) cubre seguridad. `DTZ` fuerza datetimes con zona horaria.
- `[tool.ruff.lint.per-file-ignores]`: solo para `tests/**`: `S101` (assert) y `PLR2004` (números mágicos en asserts). Cualquier otra supresión (`# noqa`) debe llevar código de regla y motivo; objetivo: cero.
- Si una regla de la lista no existe o cambia de nombre en la versión instalada de ruff, el Builder la sustituye por su equivalente y lo documenta; **no** se permite reducir la cobertura general ni usar `select = ["ALL"]` con listas amplias de `ignore` para esquivar problemas.
- Regla de pytest/ruff: los tests no usan `print` ni `shell=True`.

### Dependencias nuevas
Ninguna en runtime (solo librería estándar). Dev: ruff, mypy, pytest, bandit, pip-audit, todos oficiales (Astral, python/mypy, pytest-dev, PyCQA, PyPA), justificados por el estándar de calidad del motor.

### CI
El template `.claude/templates/ci-quality.yml` ejecuta el gate sobre `.`, pero este proyecto vive en `examples/gestor-tareas/app/` y mypy/ruff deben correr con ese directorio como cwd. Por tanto el Builder crea `.github/workflows/quality.yml` **adaptado** (iteración 2: por decisión del Approver queda como plantilla en `examples/gestor-tareas/app/.github/workflows/quality.yml`, que GitHub no ejecuta en este monorepo; el gate local es la verificación vigente, ver README) (no copia literal): mismos `permissions: contents: read`, `on: push/pull_request`, `actions/checkout@v4`, `actions/setup-python@v5` con `python-version: "3.12"`; instala `pip install -r examples/gestor-tareas/app/requirements-dev.txt` (y `requirements.txt`); y ejecuta `bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out quality-gate.md` más el paso de publicar reporte en `$GITHUB_STEP_SUMMARY`. Se omite `setup-node` (no hay Node). El workflow existente `validate-engine.yml` no se modifica. Recomendación documentada (no ejecutable por el agente): proteger `main` exigiendo el check "Quality gate". El CI usa Python 3.12 y el proyecto soporta >= 3.11, por lo que los tests no deben depender de comportamiento exclusivo de 3.13.

## Amenazas relevantes (OWASP) y mitigaciones
| Amenaza | Riesgo concreto | Mitigación obligatoria | Test |
|---|---|---|---|
| A01 Control de acceso / manejo de rutas (path traversal, symlinks) | `--archivo` o la variable de entorno apuntan a un archivo no deseado, a un directorio o a un symlink hacia otro destino | La ruta se usa exactamente como se indicó (`expanduser` + `absolute`, sin `resolve()`); se rechazan symlinks, directorios y byte nulo; no se crean directorios padre; el temporal se crea en el mismo directorio que el destino con `mkstemp` (nombre impredecible, `O_EXCL`), nunca en `/tmp` fijo; la CLI nunca borra ni toca archivos distintos al indicado y a su propio temporal | `test_almacen`: symlink, directorio, byte nulo, padre inexistente |
| A04 Diseño inseguro / integridad de datos (escritura no atómica) | Corte o error a mitad de escritura corrompe la lista | Temporal + `fsync` + `os.replace`; serializar antes de abrir; limpieza del temporal en `finally`; el original queda intacto si algo falla | `test_almacen`: fallo simulado de `os.replace` deja original igual y sin temporales residuales |
| A05 Configuración insegura / permisos | Archivo legible por otros usuarios | Archivo final siempre `0o600` (`mkstemp` + `chmod` explícito); documentado en README | `test_almacen`: `stat.S_IMODE == 0o600` tras crear y tras reescribir un archivo preexistente con `0o644` (omitir en Windows con `pytest.mark.skipif(sys.platform == "win32")`) |
| A08 Integridad de software y datos (deserialización de JSON no confiable) | Archivo manipulado con tipos inesperados, claves extra, IDs duplicados, valores enormes, anidamiento profundo | Solo `json.loads` (sin `pickle`, sin `eval`); validación estricta de esquema con lista permitida; tope de tamaño 1 MiB y de 1000 tareas; se capturan `RecursionError`/`ValueError`; rechazo de `bool` donde se espera `int`; claves desconocidas rechazadas | `test_logica`/`test_almacen`: tipos erróneos, IDs duplicados, `siguiente_id` inconsistente, JSON profundo, archivo grande |
| A03 Inyección | Inyección de secuencias de escape ANSI/terminal mediante el texto de una tarea que luego se imprime con `list`; inyección de comandos | Rechazo de caracteres de control/no imprimibles en `add` y también al cargar el archivo (un archivo manipulado no puede inyectar escapes); sin `subprocess`, `os.system`, `shell=True`, `eval`/`exec` en producción | `test_logica`: `"\x1b[31mhola"`, `"a\nb"`, `"\t"` rechazados |
| A09 Registro y errores | Trazas o internals filtrados al usuario | Todo error previsto se traduce a mensaje de una línea con código; no se imprime `repr` de excepciones ni contenido del archivo; no hay logs de datos del usuario; los mensajes no incluyen la ruta absoluta resuelta | `test_cli`: ninguna salida de error contiene `Traceback` |
| A06 Componentes vulnerables | Dependencias de terceros | Runtime sin dependencias; dev tools fijadas; `pip-audit` en el gate y en CI | gate |
| A07 Autenticación / secretos | No aplica auth; secretos | No hay credenciales; el gate de secretos debe estar en PASS | gate |
| Condiciones de carrera (TOCTOU) y concurrencia | Dos procesos escriben a la vez; archivo cambia entre `stat` y lectura | Lectura acotada a `TAMANO_MAXIMO_ARCHIVO + 1` bytes; `os.replace` atómico impide archivos parciales; **limitación documentada**: sin bloqueo de archivo entre procesos, la última escritura gana (aceptado por YAGNI y riesgo bajo) | revisión |

SSRF y subida de archivos: no aplican (sin red). Cabeceras/CSP: no aplican (sin web).

## Requisitos de UX (terminal)
- `--help` en el comando raíz y en cada subcomando, con descripción en español, cadenas de la ayuda (`uso:`, `opciones:`, `-h`) y errores de uso comunes en español, `--prioridad`/`--estado` con su valor por defecto en el `help`, ejemplo en `add`/`list`/`done`/`remove`, valores permitidos de `--prioridad`/`--estado` (usar `choices`) y mención de `--archivo` y `GESTOR_TAREAS_ARCHIVO` (con la precedencia). `prog` fijo: `gestor-tareas`.
- Mensajes siempre en español, una línea, accionables, con prefijo `Error: ` a stderr; resultados a stdout. Sin colores ni animaciones (compatible con redirección y lectores de pantalla); salida estable y parseable en `list`.
- Confirmaciones concretas que repiten el ID afectado (ver tabla de comandos). `done` sobre una tarea ya hecha no es error.
- Códigos de salida 0/1/2/3 documentados en README y `--help` (epílogo).
- Accesibilidad: no depender de color ni de símbolos Unicode; los marcadores son `[x]`/`[ ]`. Salida en UTF-8; el texto con acentos se imprime tal cual. **El revisor de UI no aplica** (CLI sin interfaz gráfica; contraste/WCAG 1.4.11 no son evaluables).
- Los comandos de test deben funcionar con el Python instalado (3.13) y en CI (3.12): usar `pytest -q` desde `examples/gestor-tareas/app/`.

## Criterios de aceptación verificables (cada uno con test pytest)
Notación: `A` = archivo temporal en `tmp_path`, `main(args)` = `cli.principal(["--archivo", str(A), *args])`.

Comandos y persistencia
1. Archivo inexistente: `main(["list"])` -> código 0, stdout `No hay tareas.`; `A` no existe después. Archivo sin tareas: igual (con cualquier `--estado`).
2. `main(["add","Comprar leche"])` en archivo inexistente -> código 0, stdout `Tarea 1 añadida: Comprar leche [media]`; `A` existe y contiene `version==1`, `siguiente_id==2`, una tarea con `id==1`, `prioridad=="media"`, `estado=="pendiente"`, `creada` parseable.
3. `add "Pagar luz" --prioridad alta` luego `list` -> dos líneas ordenadas por ID; `   2  [ ]  alta   Pagar luz` aparece (formato exacto con el ancho de columnas especificado).
4. `done 1` -> código 0, `Tarea 1 marcada como hecha.`; `list` (por defecto pendiente) no muestra la 1; `list --estado hecha` solo la 1; `list --estado todas` ambas (la 1 con `[x]`). `done 1` otra vez -> código 0, `La tarea 1 ya estaba hecha.`.
5. `remove 1` -> código 0, `Tarea 1 eliminada.`; `add "Otra"` después recibe ID 3, **no** reutiliza 1 ni 2 si `siguiente_id` era 3 (los IDs no se reutilizan).
6. `add` con texto de exactamente 200 caracteres -> código 0; con 201 -> código 1 y `Error: el texto supera el máximo de 200 caracteres (tiene 201).`; el archivo no cambia (comparar bytes antes/después).
7. `add "   "` y `add ""` -> código 1, `Error: el texto de la tarea no puede estar vacío.`; el archivo no se crea ni cambia.
8. `add "hola\x1b[31m"`, `add "a\nb"` -> código 1, `Error: el texto contiene caracteres de control no permitidos.`.
9. `add "x" --prioridad urgente` -> código 2 (argparse), nada escrito. `list --estado otra` -> código 2. `done abc` -> código 2. Sin subcomando -> código 2.
10. `done 99` y `remove 99` con ID inexistente -> código 1, `Error: no existe la tarea con ID 99.`; archivo sin cambios. `done 0` / `remove -1` -> código 1 o 2 con mensaje claro y archivo sin cambios (ID debe ser entero >= 1; documentar el elegido y testearlo).
11. Con 1000 tareas guardadas, `add "x"` -> código 1, `Error: se alcanzó el máximo de 1000 tareas.`.
12. Texto con acentos y emoji común (`"Reunión ñandú"`) se guarda y se lista idéntico (`ensure_ascii=False`, UTF-8).

Ruta del archivo
13. Precedencia: con `GESTOR_TAREAS_ARCHIVO=B` y sin `--archivo`, se usa `B`; con ambos, gana `--archivo`; sin ninguno, se usa `Path.home()/".gestor-tareas.json"` (test de `resolver_ruta` con `entorno` inyectado y `monkeypatch` de `HOME`; ningún test escribe en el HOME real). Variable vacía = no definida.
14. `--archivo` apunta a un directorio -> código 3 con `Error: ruta de archivo no válida ...`; a un symlink (a un archivo válido) -> código 3 y el destino del symlink no se modifica; con directorio padre inexistente -> código 3 y no se crea el directorio; ruta con byte nulo -> código 3.

Archivo corrupto / no confiable
15. `A` con contenido `{no es json` -> `list` y `add` devuelven código 3, mensaje `Error: el archivo '...' no es JSON válido; corrígelo o elimínalo.`, **sin** `Traceback` en stderr, y el contenido de `A` queda byte a byte igual.
16. `A` vacío (0 bytes) -> código 3 (no se sobrescribe).
17. JSON válido pero inválido en estructura -> código 3 con `estructura inválida` para cada caso: raíz lista; falta `tareas`; clave extra; `version` = `"1"` (str) o `true`; `siguiente_id` <= max id; IDs duplicados; `prioridad` = `"urgente"`; `estado` = `"borrada"`; `id` = `true`; `texto` con `\x1b`; `creada` = `"ayer"`; más de 1000 tareas.
18. `version: 2` -> código 3 con `Error: versión de esquema 2 no soportada (se esperaba 1).`.
19. Archivo > 1 MiB -> código 3 con mensaje de tamaño, sin cargar todo en memoria; bytes no UTF-8 (`b"\xff\xfe"`) -> código 3 como JSON no válido.
20. JSON con anidamiento extremo (p. ej. `"[" * 100000`) -> código 3 sin traza.

Escritura atómica y permisos
21. Tras `add`, no queda ningún archivo `.gestor-tareas-*.tmp` en el directorio.
22. Con `os.replace` parcheado (`monkeypatch`) para lanzar `OSError`: `add` devuelve código 3 (`Error: no se pudo acceder al archivo ...`), el archivo original queda byte a byte igual y no quedan temporales.
23. El archivo creado tiene modo `0o600`; un archivo preexistente con `0o644` pasa a `0o600` tras una escritura (POSIX).
24. Escritura nunca en `list`: el `mtime`/contenido de `A` no cambia tras `list` ni tras un `done` idempotente.

Lógica pura
25. Cada función de `logica.py` tiene tests que comprueban que no mutan su entrada (el `Documento` original es igual tras la llamada) y que `agregar_tarea` es determinista dado `creada`. Un test estático comprueba que `logica.py` no importa `os`, `pathlib`, `sys`, `json` ni `time`, y que `datetime` solo se usa para parsear (nunca `now`/`utcnow`) (lectura de `ast` del archivo).
26. `validar_documento(documento_a_datos(doc)) == doc` para documentos válidos (ida y vuelta).

Calidad
27. `python -m gestor_tareas --help` (subprocess) devuelve 0 e incluye `--archivo`, `GESTOR_TAREAS_ARCHIVO` y los códigos de salida; el texto está en español (`uso:`, `opciones:`).
28. Ejecución real con `subprocess.run([sys.executable, "-m", "gestor_tareas", ...], cwd=<proyecto>, capture_output=True, text=True, check=False)` (lista de argumentos, sin shell): `add` y `list` funcionan de extremo a extremo y el código de salida del proceso coincide con `principal`.
29. `bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out examples/gestor-tareas/run/quality-gate.md` -> exit 0 y `GATE: PASS (fallos: 0, sin verificar: 0)`; `ruff format --check .` sin diferencias; ningún `# noqa` / `# type: ignore` sin motivo.

Iteración 2 (hallazgos de revisión)
30. Salida rota: stdout que lanza `OSError` (o `/dev/full` por subprocess) -> código 3, `Error: no se pudo escribir la salida: ...` sin `Traceback`; tras `add` el mensaje añade `El cambio sí se guardó.` y la tarea está guardada; `BrokenPipeError` -> código 0 y stderr vacío; stdout `ascii` con acentos/emoji no falla.
31. `--archivo` tras el subcomando funciona en `add`/`list`/`done`/`remove`; un `--archivo` previo no se pisa si el subcomando no lo repite.
32. `list` con tareas pero ninguna en el filtro: `No hay tareas pendientes. Usa --estado todas.` / `No hay tareas hechas. Usa --estado todas.`; sin tareas: `No hay tareas.`
33. Ayuda y errores de uso en español (`uso:`, `opciones:`, `-h`, `faltan argumentos obligatorios`, `opción no válida`); `--prioridad`/`--estado` muestran su valor por defecto; `add`/`list`/`done`/`remove` incluyen ejemplo.
34. `--archivo` apuntando a un FIFO -> código 3 `ruta de archivo no válida '{ruta}': no es un archivo regular.` sin bloquearse.
35. Una ruta con `\x1b` no emite ESC crudo en stderr (se muestra `\x1b`); rutas con acentos se muestran tal cual.
36. `version` entero distinto de 1 se informa como versión no soportada aunque haya otras claves; el entero se trunca a 20 dígitos con `...`.

## Definición de terminado
Gate en PASS; los 29 criterios cubiertos por tests en verde; sin BLOQUEANTE ni CAMBIOS de los revisores de seguridad, UX y código (UI: "no aplica"); README del proyecto con uso, límites, códigos de salida, variable de entorno y la limitación de concurrencia; el Builder reporta en `build.md` cualquier ajuste respecto de este PRP (por ejemplo, reglas de ruff renombradas o la decisión sobre ID 0/negativos). Sin push a `main`; entrega por PR (riesgo bajo, pero la fusión a `main` solo con orden explícita).

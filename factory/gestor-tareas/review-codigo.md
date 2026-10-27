# Revisión de Código: gestor-tareas

Rama `factory/gestor-tareas` | PRP `PRPs/gestor-tareas-2026-10-27.md` | Nivel de riesgo: bajo | Diff: `git diff 3a44109..HEAD -- apps/gestor-tareas` (15 archivos, 1387 líneas)

## Resultados reales (ejecutados por el revisor, venv `apps/gestor-tareas/.venv`)
| Comprobación | Resultado |
|---|---|
| `bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md` | `GATE: PASS (fallos: 0, sin verificar: 0)`, 8/8 en PASS (incluye `dependencias-py`) |
| `pytest -q` (Python 3.13.17) | 109 passed |
| `pytest -q` en Python 3.11 y 3.12 (venvs temporales con pytest 9.1.1) | 109 passed en ambos |
| `ruff check .` / `ruff format --check .` | All checks passed / 10 files already formatted |
| `mypy .` (estricto, incluye tests) | Success, 9 source files |
| `bandit -q -r . -ll -x ./tests` | Sin hallazgos (exit 0) |
| `pip-audit -r requirements.txt` | No known vulnerabilities found |

## Límites y nomenclatura
- Archivos: el mayor es `tests/test_cli.py` (332 líneas); ninguno supera 500. Funciones todas por debajo de 50 líneas. C90 (complejidad 10) en PASS.
- Nomenclatura conforme a CLAUDE.md (directorio kebab-case, paquete snake_case por obligación del lenguaje, constantes UPPER_SNAKE_CASE).
- Sin código muerto ni duplicación relevante. Estructura proporcionada (KISS): `COMANDOS` como dispatch simple, sin capas extra.

## Separación lógica pura / E/S / CLI
Correcta. `logica.py` solo importa `dataclasses`, `datetime` (únicamente `fromisoformat`), `typing` y `modelo`; no lee reloj (la CLI inyecta `creada` vía `_ahora()`), todas las funciones devuelven objetos nuevos inmutables (`frozen`, tuplas). `almacen.py` concentra la E/S y compone los mensajes con la ruta; `cli.py` solo orquesta (cargar, función pura, guardar solo si `nuevo is not None`) y traduce excepciones a códigos. `ErrorDeEstructura` es un ajuste razonable y documentado para que la lógica no conozca rutas. Solo `__main__.py` llama a `sys.exit`.

## Manejo de errores y llamadas externas
- Sin red. E/S de disco: `OSError` traducido en `cargar` y `guardar`; `RecursionError`/`ValueError` capturados al parsear; lectura acotada a `TAMANO_MAXIMO_ARCHIVO + 1`; temporal con `mkstemp` en el mismo directorio, `fsync`, `chmod 0o600`, `replace`, limpieza en `finally`. El `except BaseException` en `_escribir_temporal` relanza siempre (no silencia), válido.
- No hay `except Exception` desnudo; ruff `BLE`/`TRY` en PASS.

## Cobertura de los 29 criterios de aceptación
Cada criterio tiene al menos un test con aserciones reales; verifiqué que los tests comparan valores exactos (código, stdout/stderr completos, bytes del archivo antes/después, modo con `stat.S_IMODE`, `mtime_ns`) y no pasan en vacío.

| Criterios | Test(s) | Valoración |
|---|---|---|
| 1-2, 3, 4, 5 | `test_list_sin_archivo`, `test_add_crea_archivo`, `test_list_formato_y_orden`, `test_done_y_filtros`, `test_remove_no_reutiliza_ids` | Sólidos (formato exacto, orden, idempotencia, no reutilización de ID) |
| 6, 7, 8 | `test_texto_de_200_y_201_caracteres`, `test_texto_vacio`, `test_texto_con_control` | Sólidos (mensaje exacto, archivo no creado/sin cambios) |
| 9, 10 | `test_errores_de_uso_codigo_2`, `test_id_inexistente*` | Cubiertos. La decisión sobre `done 0`/`remove -1` (código 2) está documentada en README y build.md |
| 11, 12 | `test_limite_de_mil_tareas`, `test_acentos_se_conservan` | Cubiertos (el emoji solo se prueba en `test_logica`, no de extremo a extremo) |
| 13, 14 | `test_precedencia_de_archivo`, `test_resolver_ruta_*`, `test_archivo_por_defecto_en_home`, `test_ruta_*`, `test_symlink_*` | Cubiertos; HOME se redirige a `tmp_path`, ningún test toca el HOME real |
| 15-20 | `test_json_corrupto`, `test_archivo_vacio_*`, `test_estructura_invalida`, `test_validar_documento_*`, `test_version_2`, `test_archivo_grande_y_no_utf8_y_anidado`, `test_archivo_que_crece_tras_stat` | Cubiertos. Los 12+ casos del criterio 17 se distribuyen entre `test_logica` (parametrizado) y 5 casos en `test_cli` |
| 21-24 | `test_sin_temporales_y_fallo_de_replace`, `test_permisos_0600`, `test_list_y_done_idempotente_no_escriben`, `test_fallo_de_escritura_limpia_temporal` | Sólidos (parcheo real de `os.replace`/`os.fsync`) |
| 25-26 | `test_agregar_tarea_*`, `test_marcar_hecha_*`, `test_eliminar_*`, `test_logica_no_importa_io_ni_lee_el_reloj`, `test_ida_y_vuelta` | Cubiertos; el test estático por `ast` es real |
| 27-28 | `test_help_incluye_archivo_entorno_y_codigos`, `test_subprocess_extremo_a_extremo` | Cubiertos (subprocess con lista de argumentos, sin shell) |
| 29 | Gate + `ruff format --check` | PASS |

## Hallazgos

Ningún BLOQUEANTE. Ningún defecto de correctitud encontrado. Observaciones (no bloquean; el approver decide):

### CAMBIOS menores (recomendados, no críticos)
1. `apps/gestor-tareas/.github/workflows/quality.yml:1`: GitHub solo ejecuta workflows ubicados en `.github/workflows/` de la raíz del repositorio, por lo que este archivo es inerte en este monorepo. Además asume que `.claude/` está copiado dentro del proyecto. Es una desviación declarada en build.md (por orden expresa), contraria al PRP (sección CI: workflow en la raíz con `quality-gate.sh apps/gestor-tareas`). Corrección: confirmar que el humano acepta la desviación o crear el workflow en la raíz como indicaba el PRP. Hoy no existe gate automático en CI.
2. `gestor_tareas/logica.py:151-159`: `_validar_cabecera` comprueba las claves de la raíz antes que la versión. Un documento con `version: 2` y un esquema distinto (claves diferentes) se reporta como "estructura inválida" en vez de "versión de esquema 2 no soportada". Con el esquema actual de v1 el criterio 18 se cumple, pero la comprobación de versión debería ir primero cuando `version` existe. Corrección: leer `datos.get("version")` y validar versión antes del conjunto de claves.
3. `gestor_tareas/modelo.py:13,17`: los `# noqa: N818` llevan código pero el motivo ("nombre fijado por el PRP") describe el origen y no la razón técnica. Alternativa más limpia y alineada con el PRP ("objetivo: cero"): `per-file-ignores` de `N818` solo para `gestor_tareas/modelo.py` en `pyproject.toml` con comentario, o renombrar a `DominioError`/`AlmacenError`. Justificación aceptable tal como está.

### Calidad de tests (mejoras opcionales)
4. `tests/test_logica.py:148-174`: los casos inválidos de `validar_documento` solo afirman el tipo `ErrorDeEstructura`; un caso podría fallar por una razón distinta de la prevista y el test seguiría en verde. Sugerencia: parametrizar con el fragmento de detalle esperado (`match=`).
5. `tests/test_logica.py:195` / criterio 25: no hay test de no-mutación para `validar_documento` (dict de entrada) ni `documento_a_datos`; los demás sí lo verifican.
6. `tests/test_almacen.py:126`: `monkeypatch.setattr(almacen, "TAMANO_MAXIMO_ARCHIVO", 1_048_576)` es una asignación del mismo valor, sin efecto; el resto del test (stat falseado) sí ejercita la lectura acotada y es válido. Se puede eliminar la línea.
7. `tests/test_cli.py:119-123`: para `done 0`/`remove -1` solo se afirma `"usage:"`; conviene afirmar también `ID no válido` para fijar la decisión documentada. El criterio 27 se prueba con `principal(["--help"])` y no con `python -m gestor_tareas --help` como dice el PRP (equivalente funcionalmente).

## Los 3 `# noqa`
- `modelo.py:13` y `modelo.py:17` (`N818`): justificados (nombres exigidos por el contrato del PRP); ver punto 3.
- `tests/test_cli.py:311` (`S603`): justificado; `subprocess.run` con lista de argumentos fija, `sys.executable`, sin shell, `check=False` explícito, y es un test requerido por el criterio 28.
- No hay `# type: ignore`. Número de supresiones coherente con el reporte del Builder.

## Entorno de herramientas (`requirements-dev.txt`)
Coherente. Las 5 herramientas (ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, bandit 1.9.4, pip-audit 2.10.1) están fijadas con `==` y coinciden exactamente con las versiones instaladas en `.venv`; todas están en el mismo entorno, necesario para que mypy vea `pytest` al tipar los tests (limitación documentada por el Builder: con `uv tool` aislados, mypy falla en los tests; no es defecto del proyecto). `.venv/` está en `.gitignore`. Sin runtime dependencies. Dependencias transitivas sin fijar y sin hash-pinning: aceptado por el PRP (YAGNI).

## Veredicto
El código cumple los criterios del PRP, el gate está en PASS y las herramientas pasan en limpio en 3.11, 3.12 y 3.13. Las observaciones son menores; el punto 1 (CI inerte) queda a decisión del approver/humano por ser una desviación consciente.

VEREDICTO: APROBADO

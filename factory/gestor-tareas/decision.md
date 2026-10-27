# Decision: gestor-tareas (iteración 2)

Rama `factory/gestor-tareas` | PRP `PRPs/gestor-tareas-2026-10-27.md` | Riesgo declarado: **bajo** (CLI local, sin red, auth, pagos, datos personales, migraciones ni infraestructura).

## Historial
- **Iteración 1: RECHAZADO.** UX con 4 CAMBIOS confirmados (`--archivo` tras el subcomando, traza ante salida rota o ascii, `list` vacío por filtro, ayuda en inglés), más 2 observaciones de seguridad (ESC crudo en rutas, FIFO colgado). Gate en PASS. El builder los corrigió en la iteración 2 (144 tests en 3.11/3.12/3.13).
- **Iteración 2: ver abajo.**

## Gate (re-ejecutado por el approver)
`bash .claude/scripts/quality-gate.sh apps/gestor-tareas --out factory/gestor-tareas/quality-gate.md` -> exit 1, **GATE: FAIL (fallos 1, sin verificar 0)**.
Único fallo: verificación nueva `funciones`, `gestor_tareas/cli.py:107 construir_parser(52)`. Las otras 8 (secretos, tamaño, patrones, pytest, ruff, mypy, bandit, pip-audit) en PASS. Nota: el revisor de código vio PASS porque su gate aún no incluía la verificación `funciones`.

## Veredictos
| Revisor | Veredicto |
|---|---|
| Seguridad | APROBADO |
| UX | APROBADO |
| UI | APROBADO (no aplica) |
| Código | **CAMBIOS** |

## Verificación independiente de los hallazgos de código
| Hallazgo | Comprobación del approver | Estado |
|---|---|---|
| CAMBIOS-1 función de 52 líneas | `ast` y gate: `construir_parser` = 52 (>50, límite de CLAUDE.md) | CONFIRMADO |
| CAMBIOS-2 `_Parser.__init__` | Solo acepta `prog`, `description`, `epilog`; `add_parser` pasa kwargs de más a `parser_class` | CONFIRMADO (riesgo latente; hoy pasa en 3.11-3.13) |
| CAMBIOS-2 literal `"usage: "` | `_Formateador.format_help` usa `startswith("usage: ")` y degrada en silencio a inglés | CONFIRMADO (falla segura, no rompe) |
| CAMBIOS-3 tests de TRADUCCIONES | Búsqueda en `tests/`: ningún test afirma `(opciones: `, `argumento --` ni `se esperaba un valor` | CONFIRMADO |
| CAMBIOS-3 `dup2` en `_descartar_stdout` | Sin test que lo detecte (mutación del revisor: 0 fallos) | CONFIRMADO (menor) |

## Decisión
Regla 0: gate en `FAIL` -> `RECHAZADO`, con independencia del juicio de los revisores. Regla 1 también aplica: CAMBIOS de código confirmados. No se evalúan las reglas 2-4; con el riesgo bajo, cuando el gate pase y los 4 revisores estén en APROBADO correspondería `APROBADO_AUTO` (mecánico; PR por defecto, `main` solo con orden explícita).

**ÚLTIMA ITERACIÓN PERMITIDA:** esta fue la construcción 2 de 3; la siguiente (3.ª) es la última. Si tras ella queda un BLOQUEANTE, CAMBIOS o el gate no está en PASS, el trabajo se escala a una persona en lugar de volver al builder.

## Lista priorizada para el builder

### (a) Obligatorios
1. **Gate en PASS: recortar `construir_parser` a <=50 líneas** (`cli.py:107`). Extraer helpers por subcomando (p. ej. `_registrar_add(sub, ...)`) o un helper para los subparsers; sin cambiar el comportamiento. Ejecutar `quality-gate.sh apps/gestor-tareas` y confirmar 9/9 PASS (incluida `funciones`); revisar que ninguna otra función quede cerca del límite.
2. **Endurecer `_Parser.__init__`**: `def __init__(self, **kwargs: Any)` fijando `add_help=False` y `formatter_class=_Formateador` (con `kwargs.setdefault`/sobrescritura), de modo que kwargs nuevos de argparse no provoquen `TypeError`. Mantener los 144 tests en verde.
3. **Tests de `TRADUCCIONES`** (cada entrada debe fallar si se borra): afirmar `(opciones: ` y `argumento --prioridad` en el caso de prioridad inválida, y añadir `["list", "--estado"]` con `se esperaba un valor`.

### (b) Recomendados de bajo costo
4. Sustituir la dependencia del literal `"usage: "` por el gancho `add_usage` del formateador, o, si no es trivial, añadir 3.11 y 3.13 a la matriz de `quality.yml` (plantilla) y dejar el test `test_ayuda_en_espanol` como red de seguridad.
5. Test de `_descartar_stdout`: un subprocess o descriptor real que compruebe que, tras un fallo de salida, stdout queda apuntando a `/dev/null` (que `dup2` no pueda sustituirse por `pass`). Menor.
6. Quitar el doble saneo de ruta (`almacen.py:99, 128` vs `_ruta_invalida`), solo si es trivial y sin cambiar la salida.
7. Actualizar `build.md` con la sección "Iteración 3" y el resultado del gate nuevo.

### (c) Fuera de alcance
- Soporte o pruebas con Python 3.14+ (no hay intérprete disponible; el riesgo se cubre con el punto (a)2).
- Desajuste monorepo/gate en la raíz (`quality-gate.sh .` falla por pytest/bandit del monorepo, ajeno al proyecto).
- CI del ejemplo como plantilla inerte en el monorepo (decisión de infraestructura para el humano en el PR).
- Los puntos (c) de la iteración 1 (TOCTOU, IDs enormes, symlinks en padres, truncado de textos, hash-pinning, pinning de acciones por SHA, bloqueo entre procesos, Windows).

DECISION: RECHAZADO

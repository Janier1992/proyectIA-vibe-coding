# Decision: gestor-tareas (iteración 3, última)

Rama `examples/gestor-tareas/run` | PRP `examples/gestor-tareas/prp.md` | Riesgo declarado: **bajo** (CLI local, sin red, auth, pagos, datos personales, migraciones ni infraestructura). Reconfirmado: el diff no añade nada de esas categorías.

## Historial
- **Iteración 1: RECHAZADO.** UX con 4 CAMBIOS (`--archivo` tras el subcomando, traza ante salida rota o ascii, `list` vacío por filtro, ayuda en inglés) y 2 observaciones de seguridad (ESC crudo en rutas, FIFO colgado). Corregido en la iteración 2.
- **Iteración 2: RECHAZADO.** Gate en FAIL por la verificación nueva `funciones` (`construir_parser` = 52 líneas) y CAMBIOS de código (`_Parser.__init__` frágil, `TRADUCCIONES` sin tests, `dup2` sin test). Corregido en la iteración 3.
- **Iteración 3: ver abajo.**

## Gate (re-ejecutado por el approver)
`bash .claude/scripts/quality-gate.sh examples/gestor-tareas/app --out examples/gestor-tareas/run/quality-gate.md` -> exit 0, **GATE: PASS (fallos 0, sin verificar 0)**, 9 filas en PASS: secretos, tamano, funciones, patrones-peligrosos, tests-py, lint-py, tipos-py, sast-py, dependencias-py.

Ejecución propia con `.venv` de `examples/gestor-tareas/app`: `pytest` 150 passed; `ruff check` OK; `mypy` sin errores (12 archivos). Con `ast`, la función más larga de producción es `principal` (19 líneas) y en `almacen.py` `guardar` (14).

## Veredictos
| Revisor | Veredicto |
|---|---|
| Seguridad (iter. 3) | APROBADO |
| UX (iter. 3) | APROBADO |
| UI (iter. 2, vigente) | APROBADO (no aplica) |
| Código (iter. 3) | APROBADO |

UI vigente: `git diff cd14c96..HEAD --stat` toca solo scripts de `.claude`, `.gitignore`, `almacen.py`, `cli.py`, `tests/test_cli_robustez.py` y artefactos de `factory/`. No hay HTML, CSS, JS ni GUI.

## Verificación independiente de los obligatorios de la iteración 2
| Obligatorio | Comprobación del approver | Estado |
|---|---|---|
| 1. `construir_parser` <= 50 y gate 9/9 | Gate re-ejecutado: `funciones` PASS; máximo 19 líneas con `ast` | CUMPLIDO |
| 2. `_Parser.__init__` robusto | `cli.py:85-88`: `**kwargs: Unpack[_OpcionesParser]`, fuerza `add_help=False` y `formatter_class=_Formateador`; mypy OK | CUMPLIDO |
| 3. Tests de `TRADUCCIONES` | `test_cli_robustez.py:219` (`argumento --prioridad ... (opciones: `) y `:227` (`se esperaba un valor`); el revisor de código borró cada una de las 6 entradas y falló exactamente 1 test cada vez | CUMPLIDO |
| Rec. 4 `add_usage` en vez de `"usage: "` | `cli.py:59-66`; el literal ya no existe | CUMPLIDO |
| Rec. 5 test de `dup2` | Test con descriptor real; la mutación `dup2` -> `pass` falla (según el revisor) | CUMPLIDO |
| Rec. 7 `build.md` iteración 3 | Presente y coherente con lo observado | CUMPLIDO |

## Observaciones menores nuevas: ¿CAMBIOS?
Ninguna se trata como CAMBIOS. La decisión se justifica por severidad, alcance y regla:
1. **`_id_valido` con ESC crudo (`cli.py:104`)**: existía ya en cd14c96, no es regresión de esta iteración. Solo refleja el argv del propio usuario en su propia terminal, sin vector remoto ni persistencia. Los dos revisores que lo vieron o no lo clasificaron como bloqueante o lo marcaron BAJO/informativo. No cumple el umbral de CAMBIOS. **Recomendado para una iteración futura:** `{valor!r}` o `texto_seguro(valor)`.
2. **Ramas de saneo sin test (`almacen.py:47,49`)**: son defensa en profundidad redundante. `cargar`/`guardar`/`cli` ya sanean y `texto_seguro` es idempotente, y los ataques reales con ESC en rutas (directorio, FIFO, symlink, padre inexistente, NUL) fueron verificados por Seguridad con `cat -v` sin ESC crudo. El hueco es de cobertura de mutación, no de comportamiento. No bloquea. **Recomendado:** un test con `--archivo $'\n'`.
3. **API privada `argparse._MutuallyExclusiveGroup` en la firma de `add_usage` (`cli.py:61-68`)**: solo en anotación de tipo, requerida por mypy estricto; no se ejecuta en tiempo de ejecución como dependencia frágil. Aceptable, sin cambio.

Ninguna toca seguridad real, corrección funcional ni límites de CLAUDE.md, por lo que no justifican impedir el avance.

## Decisión
- Regla 0: gate en `PASS` con 9/9 verificaciones, ninguna sin verificar. Pasa.
- Regla 1: sin BLOQUEANTE ni CAMBIOS pendientes (los de la iteración 2 están cerrados y verificados). Pasa.
- Reglas 2 y 3: riesgo `bajo`; no toca auth, pagos, datos personales, migraciones ni infraestructura. No se activan.
- Regla 4: riesgo bajo, 4 revisores en APROBADO, gate en PASS -> **APROBADO_AUTO**.

`APROBADO_AUTO` significa "verificado mecánicamente", no "nadie lo miró". Siguiente paso según el flujo: entrega por **PR** (nunca push directo a `main`; la fusión a `main` solo con orden explícita) y despliegue solo con confirmación humana. Queda como decisión de infraestructura para la persona en el PR: `quality.yml` dentro del ejemplo es una plantilla inerte en el monorepo.

## Pendiente no bloqueante (para el PR o una iteración futura)
- `{valor!r}`/`texto_seguro` en `_id_valido`.
- Test de las ramas de saneo de `resolver_ruta` (`--archivo $'\n'`).
- Saneo de ruta en tres sitios (estético).
- Fuera de alcance: puntos (c) de las iteraciones 1 y 2 (TOCTOU, IDs enormes, hash-pinning, Windows, Python 3.14+, desajuste del gate en la raíz del monorepo).

DECISION: APROBADO_AUTO

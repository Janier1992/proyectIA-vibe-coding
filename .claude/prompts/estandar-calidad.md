# Estándar de Calidad y Seguridad

Aplica a todo proyecto creado con este motor. Está pensado para que la calidad y la seguridad **no dependan de una inspección humana del código**: lo que importa se verifica con herramientas y se bloquea si falla.

## Principio rector
**Sin verificación mecánica no hay aprobación automática.** Una opinión de un agente (incluido un revisor) nunca reemplaza el resultado de una herramienta. Lo no verificable se declara `UNVERIFIED` y requiere a una persona.

## Quality gate (`.claude/scripts/quality-gate.sh`)
| Verificación | Qué garantiza | Resultado si falla |
|---|---|---|
| `secretos` | Sin credenciales ni `.env` versionado | FAIL |
| `tamano` | Archivos ≤ 500 líneas (mantenibilidad) | FAIL |
| `patrones-peligrosos` | Sin `eval`, `innerHTML`, `shell=True`, `verify=False`, etc. | FAIL |
| `tests-*` | Hay tests y pasan | FAIL (sin tests = FAIL) |
| `lint-*` | Linter del stack sin errores (ESLint/Biome, Ruff) | FAIL; sin linter = UNVERIFIED |
| `tipos-*` | Tipado estático sin errores (tsc, mypy) | FAIL |
| `sast-*` | Análisis estático de seguridad (bandit, semgrep) | FAIL; sin herramienta = UNVERIFIED |
| `dependencias-*` | Sin vulnerabilidades high/critical y con lockfile | FAIL; sin red = UNVERIFIED |

Salida: `0` PASS, `1` FAIL, `2` UNVERIFIED. El gate corre en el Builder, en los revisores, en el Approver y en el CI del proyecto.

## Baseline que todo proyecto debe configurar (lo hace el Builder)
1. **Tests** automatizados de la lógica de negocio y de los casos de error.
2. **Linter** y, si el stack lo admite, **tipado estático** con los scripts `lint` y `typecheck` (Node) o `ruff`/`mypy` (Python).
3. **Entorno reproducible**: en Python crea `.venv/` con `pip install -r requirements-dev.txt` (el gate prioriza `.venv/bin`; mypy y pytest deben compartir entorno). En Node usa `npm ci`.
4. **Auditoría de dependencias** con lockfile versionado. Verifica que cada paquete exista y sea el oficial (no inventes ni aceptes nombres parecidos), con versión fijada y justificación en el PRP.
5. **CI** copiado desde `.claude/templates/ci-quality.yml` a `.github/workflows/quality.yml`, y recomendar proteger `main` exigiendo ese check.
6. **`.env.example`** con variables sin valores reales; `.env` en `.gitignore`.

## Checklist de seguridad (OWASP Top 10) para los revisores
- **Control de acceso**: autorización en el servidor para cada recurso; nunca confiar en el cliente.
- **Inyección**: consultas parametrizadas, sin concatenar SQL/comandos; salida codificada (`textContent`, no `innerHTML`).
- **Criptografía y secretos**: sin secretos en código; TLS verificado; contraseñas con hash adaptativo (argon2/bcrypt).
- **Validación de entradas** en el borde, con listas permitidas, límites y tipos.
- **Componentes vulnerables**: dependencias auditadas y actualizadas.
- **Autenticación y sesiones**: sin credenciales por defecto, expiración de sesión, límite de intentos.
- **Registro y errores**: logs sin datos personales ni secretos; mensajes de error que no filtran internals.
- **SSRF y subida de archivos**: validar destinos y tipos; no abrir URLs arbitrarias.
- **Cabeceras y CSP** en aplicaciones web (`frame-ancestors`, `nosniff`, `Referrer-Policy`).

## Definición de "terminado"
- Gate en `PASS` (o `UNVERIFIED` con aprobación humana explícita de cada punto sin verificar).
- Criterios de aceptación del PRP cubiertos con tests.
- Reportes de revisión sin BLOQUEANTE ni CAMBIOS.
- Documentación actualizada y checklist de producción con plan de rollback.

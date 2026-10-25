# Review de seguridad: calculadora-propinas

Alcance: apps/calculadora-propinas/ (index.html, ui.js, calculator.js, styles.css, tests) y cambios de configuracion (.claude/settings.json, hooks, .gitignore).

## Lista de verificacion
- Secretos/credenciales y .env versionados: ninguno. `git ls-files | grep env` sin resultados; sin URLs ni tokens en el codigo.
- Inyeccion/XSS: ui.js solo escribe con `textContent`/`value`/`hidden`/`setAttribute` fijos. Sin innerHTML, eval, document.write ni handlers inline. Los mensajes de error son constantes, no eco de la entrada del usuario. Entradas validadas con regex estricta (calculator.js:156) y limites maximos (MAX_BILL, MAX_TIP_PERCENT, MAX_PEOPLE).
- Auth/RLS/backend: no aplica (app estatica sin backend ni datos persistidos).
- Dependencias: ninguna nueva (sin package.json, node_modules ni lockfile). Tests usan solo `node:test` nativo.
- Datos personales/logs/CORS: no se registran ni transmiten datos; sin red. `autocomplete="off"` en los campos.
- Automatizaciones: sin webhooks. El hook log-tool-usage.sh solo registra el nombre de la herramienta en `.claude/logs/` (ignorado por git, .gitignore:1); no guarda contenido de entradas. `$CLAUDE_PROJECT_DIR` va entre comillas.
- CSP (index.html:6): `default-src 'none'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'`. Restrictiva y coherente con que no haya inline.

## Hallazgos
Ninguno BLOQUEANTE ni de severidad CAMBIOS.

Observaciones informativas (no requieren accion):
- `frame-ancestors` no puede fijarse por `<meta>`; si se despliega en un host real, anadir `X-Frame-Options`/`frame-ancestors` por cabecera HTTP (solo relevante en despliegue).
- Los scripts no usan SRI, pero son del mismo origen (`'self'`), por lo que no es necesario.

VEREDICTO: APROBADO

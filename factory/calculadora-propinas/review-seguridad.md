# Review de seguridad: calculadora-propinas (iteración 2)

Alcance: `git diff 1a6e9af..HEAD` (ui.js, calculator.js, calculator.test.js, index.html, styles.css, PRP) más el estado final de apps/calculadora-propinas/.

## Cambios de la iteración revisados
- ui.js: nuevas constantes de mensaje fijas (EMPTY_BILL, EMPTY_FIX) escritas con `textContent`; `syncShortcuts` usa `setAttribute('aria-pressed', String(...))` comparando `dataset.tip` con el valor recortado. Sin innerHTML, eval ni eco de la entrada del usuario.
- index.html: se quitó `hidden` de los `<p class="error">` y se añadió `aria-live`/`aria-pressed`. Sin scripts ni handlers inline; la CSP (`default-src 'none'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'none'`) no cambia.
- calculator.js: solo se añadió una tilde al texto de un mensaje constante.
- Tests y PRP: comandos de validación y casos nuevos, sin impacto de seguridad.
- styles.css: solo presentación.

## Lista de verificación
- Secretos y `.env`: ninguno añadido.
- Inyección/XSS: sin vectores nuevos. Los textos dinámicos son constantes.
- Auth/RLS/backend: no aplica (app estática).
- Dependencias: ninguna nueva.
- Datos personales, logs, CORS: sin red ni persistencia.
- Automatizaciones/webhooks: sin cambios.

## Hallazgos
Ninguno BLOQUEANTE ni de severidad CAMBIOS.

Informativo: `frame-ancestors` no se puede fijar por `<meta>`. Si se despliega en un host real, enviar `X-Frame-Options` o `frame-ancestors` por cabecera HTTP.

VEREDICTO: APROBADO

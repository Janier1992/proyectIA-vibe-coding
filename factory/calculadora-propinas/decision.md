# Decision: calculadora-propinas (iteracion 2)

PRP: PRPs/calculadora-propinas-2026-10-25.md | Riesgo: bajo | Rama: factory/calculadora-propinas

## Historial
- Iteracion 1: RECHAZADO. Sin BLOQUEANTES, pero UX y UI con CAMBIOS (contraste de bordes, texto guia contradictorio, errores sin anuncio, tildes). Devuelto al builder con 4 puntos obligatorios.

## Veredictos (iteracion 2)
| Revisor | Veredicto |
|---|---|
| Seguridad | APROBADO |
| Codigo | APROBADO |
| UX | APROBADO |
| UI | APROBADO |

Los 4 reportes existen y fueron sobrescritos en la iteracion 2. Sin BLOQUEANTES ni CAMBIOS pendientes.

## Validaciones ejecutadas por el Approver
- `node --test apps/calculadora-propinas/*.test.js`: 33 tests, 33 pass, 0 fail.
- grep de sinks peligrosos en calculator.js y ui.js: sin coincidencias.
- grep `https?://` en la app: sin coincidencias.
- Archivos en la app: los 5 del PRP, sin extras.

## Verificacion independiente de los 4 obligatorios de la iteracion 1
1. Contraste de bordes: CORREGIDO. `--control-border` en styles.css:11 (claro `hsl(220 15% 45%)`) y :27 (oscuro `hsl(225 15% 58%)`), usado en input (:75), chip (:116) y boton secundario (:126). Calcule el ratio contra `--surface`: 5.20:1 claro; en oscuro ~4.8:1 (aproximado, con superficie de saturacion 25%). Ambos >= 3:1. `--border` se mantiene en divisores.
2. Texto guia: CORREGIDO. ui.js:17-18 y :37 devuelven EMPTY_BILL si falla el monto y EMPTY_FIX en los demas casos; solo textContent.
3. Errores anunciados: CORREGIDO. index.html:20, :26 y :38 son `<p class="error" aria-live="polite">` presentes en el DOM, sin `hidden`; ui.js solo cambia su texto.
4. Tildes: CORREGIDO. index.html:27 "rápidos", :36 "Número de personas", calculator.js:24 "número".

## Regla aplicada
1. Sin BLOQUEANTE ni CAMBIOS: no aplica.
2. No toca auth, pagos, datos personales, migraciones ni infraestructura; riesgo no es alto.
3. Riesgo no es medio.
4. Riesgo bajo, 4 revisores en APROBADO, validaciones verdes: APROBADO_AUTO.

## Nota para el humano (no bloquea)
Pendiente de verificacion manual: lector de pantalla real, teclado de extremo a extremo, 768px, contraste con herramienta. Si se despliega en un host real, fijar `frame-ancestors`/`X-Frame-Options` por cabecera HTTP. Menores abiertos: h1 sin peso 800 de la skill, mensajes con limites duplicados de MAX_*, blur marca "tocado" en campo vacio.

DECISION: APROBADO_AUTO

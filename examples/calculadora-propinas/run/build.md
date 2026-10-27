# Build: calculadora-propinas

PRP: `examples/calculadora-propinas/prp.md` | Rama: `examples/calculadora-propinas/run` | Node v22.22.0

## Tareas completadas
1. Logica pura: `examples/calculadora-propinas/app/calculator.js` (parseNumber, validateInputs, calculateTip, MAX_BILL/MAX_TIP_PERCENT/MAX_PEOPLE; centavos enteros; export UMD minimo).
2. Tests: `calculator.test.js`, 30 casos con `node:test` + `node:assert/strict`.
3. Marcado: `index.html` (lang="es", CSP del PRP, form novalidate, labels, errores con aria-describedby, region aria-live, atajos 10/15/18/20, Limpiar, scripts defer sin inline).
4. Estilos: `styles.css` (tokens HSL claro/oscuro, color-scheme, responsive, focus-visible, touch targets 44px, reduced-motion).
5. Capa DOM: `ui.js` (solo textContent/value, estados vacio/error/resultado, errores solo tras input/blur, Limpiar devuelve foco a monto).
6. Verificacion final: ver abajo.

## Archivos
Nuevos: los 5 de `examples/calculadora-propinas/app/` (calculator.js 95 lineas, calculator.test.js 117, index.html 55, styles.css 180, ui.js 82) y este `build.md`.

## Resultados de validacion (reales)
- `node --test` dentro de `examples/calculadora-propinas/app/` y `node --test examples/calculadora-propinas/app/*.test.js`: 30 tests, 30 pass, 0 fail, exit 0.
- `node --check` calculator.js, ui.js, calculator.test.js: OK.
- grep de sinks (innerHTML, outerHTML, insertAdjacentHTML, document.write, eval(, new Function) en calculator.js y ui.js: sin coincidencias (exit 1). Tambien sin `on*=` inline, `javascript:`, `<style` ni `<script>` inline en index.html.
- grep `https?://` en html/css/js: sin coincidencias. Sin node_modules ni package-lock.
- `wc -l`: todos < 500 lineas; funciones < 50 lineas.
- Smoke test headless con DOM falso (script temporal fuera del repo): estado vacio inicial sin errores; 200/15%/4 personas -> $30.00 / $230.00 / $57.50; people=2.5 -> mensaje + aria-invalid y resultados ocultos; Limpiar restablece valores y enfoca monto.
- Valores de coma flotante: 0.1 @20% -> tip 0.02, total 0.12; 19.99 @18% -> tip 3.6, total 23.59; 33.33 @15% /3 -> 5 / 38.33 / 12.78.

## Desviaciones del PRP
1. El comando literal `node --test examples/calculadora-propinas/app/` FALLA en Node 22.22 (exit 1, MODULE_NOT_FOUND: trata el directorio como archivo). Es un defecto del comando del PRP, no del codigo. Equivalentes que pasan: `cd examples/calculadora-propinas/app && node --test` o `node --test examples/calculadora-propinas/app/*.test.js`. Recomendado corregir el PRP/plantilla.
2. `validateInputs` acepta strings ademas de numeros (usa parseNumber), para que la UI pase el texto crudo sin duplicar logica. Para bill se exige que redondee a >= 1 centavo (0.004 se rechaza), coherente con "0.01 valido".
3. `calculateTip` lanza `RangeError` con entradas invalidas (decision permitida por el PRP; testeada). Devuelve ademas `tipPerPerson`.
4. Moneda fija `USD` en constante `CURRENCY` de ui.js (PRP la deja configurable); locale segun navegador.
5. Mensajes en español sin tildes/enie ("numero") para mantener ASCII en el codigo; deuda menor de redaccion.

## No verificado (pendiente humano)
Verificacion visual en navegador real: 375/768/1440px, ambos temas, solo teclado, contraste 4.5:1 medido, consola/Network. No hay navegador en el entorno; contraste y layout estan disenados por tokens pero sin medicion automatizada.

## Deuda tecnica
- Sin tests de DOM/E2E (fuera de alcance por PRP).
- Mensajes de error con limites (1.000.000, 100) duplicados como texto respecto a las constantes MAX_*.
- Blur sobre campo vacio sin tocar marca el campo como "tocado" y muestra error al tabular; aceptado por "aparecen tras input/blur".

## Iteracion 2

Hallazgos obligatorios (decision.md):
1. Contraste: nuevo token `--control-border` (claro `hsl(220 15% 45%)`, oscuro `hsl(225 15% 58%)`) usado en input, chip y boton secundario; `--border` se mantiene en la tarjeta y el divisor. Ratios calculados con script (formula WCAG, sin Playwright): claro 5.20:1 sobre `--surface` y 4.48:1 sobre `--surface-alt`; oscuro 4.88:1 y 4.19:1. Todos >= 3:1. Error (`--danger`) y foco (outline 3px) siguen distinguibles.
2. Texto guia: `ui.js` muestra "Ingresa el monto de la cuenta para ver el resultado" si el monto es invalido/vacio y "Corrige los campos marcados para ver el resultado" si el monto es valido y falla otro campo (solo textContent).
3. Errores anunciados: los tres `<p class="error">` llevan `aria-live="polite"` y ya no usan `hidden`; permanecen en el DOM y solo cambia su texto (vacio = sin anuncio). CSS `.error:empty` colapsa el hueco y oculta el icono.
4. Tildes: "Porcentajes rápidos", "Número de personas", mensaje "número entero" en calculator.js. Ningun test comparaba el texto; se agrego uno que lo verifica.

Opcionales aplicados: grid de 4 columnas en atajos; "Limpiar" con clase `.btn-secondary` (contorno, sin gradiente); `aria-pressed` en atajos (se sincroniza en cada render con el valor del campo, y el chip activo se rellena con `--primary`); tests de bill 0.004/0.005 y de `tipPerPerson`.

PRP: comando de test corregido a `node --test examples/calculadora-propinas/app/*.test.js` en `examples/calculadora-propinas/prp.md` (3 lugares). `.claude/PRPs/templates/prp_frontend.md` no contiene comando de test; sin cambios.

Validacion: `node --test examples/calculadora-propinas/app/*.test.js` 33/33; `node --check` ui.js y calculator.js OK; greps de sinks y `https?://` sin coincidencias; `wc -l` todos < 500 (max 182). Playwright/navegador no disponibles: contraste por calculo, verificacion visual sigue pendiente de humano.

No hechos (fuera de alcance): opcionales 7 (DRY de mensajes) y 9 (touched solo si cambia el valor).

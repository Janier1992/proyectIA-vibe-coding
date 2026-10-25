# Build: calculadora-propinas

PRP: `PRPs/calculadora-propinas-2026-10-25.md` | Rama: `factory/calculadora-propinas` | Node v22.22.0

## Tareas completadas
1. Logica pura: `apps/calculadora-propinas/calculator.js` (parseNumber, validateInputs, calculateTip, MAX_BILL/MAX_TIP_PERCENT/MAX_PEOPLE; centavos enteros; export UMD minimo).
2. Tests: `calculator.test.js`, 30 casos con `node:test` + `node:assert/strict`.
3. Marcado: `index.html` (lang="es", CSP del PRP, form novalidate, labels, errores con aria-describedby, region aria-live, atajos 10/15/18/20, Limpiar, scripts defer sin inline).
4. Estilos: `styles.css` (tokens HSL claro/oscuro, color-scheme, responsive, focus-visible, touch targets 44px, reduced-motion).
5. Capa DOM: `ui.js` (solo textContent/value, estados vacio/error/resultado, errores solo tras input/blur, Limpiar devuelve foco a monto).
6. Verificacion final: ver abajo.

## Archivos
Nuevos: los 5 de `apps/calculadora-propinas/` (calculator.js 95 lineas, calculator.test.js 117, index.html 55, styles.css 180, ui.js 82) y este `build.md`.

## Resultados de validacion (reales)
- `node --test` dentro de `apps/calculadora-propinas/` y `node --test apps/calculadora-propinas/*.test.js`: 30 tests, 30 pass, 0 fail, exit 0.
- `node --check` calculator.js, ui.js, calculator.test.js: OK.
- grep de sinks (innerHTML, outerHTML, insertAdjacentHTML, document.write, eval(, new Function) en calculator.js y ui.js: sin coincidencias (exit 1). Tambien sin `on*=` inline, `javascript:`, `<style` ni `<script>` inline en index.html.
- grep `https?://` en html/css/js: sin coincidencias. Sin node_modules ni package-lock.
- `wc -l`: todos < 500 lineas; funciones < 50 lineas.
- Smoke test headless con DOM falso (script temporal fuera del repo): estado vacio inicial sin errores; 200/15%/4 personas -> $30.00 / $230.00 / $57.50; people=2.5 -> mensaje + aria-invalid y resultados ocultos; Limpiar restablece valores y enfoca monto.
- Valores de coma flotante: 0.1 @20% -> tip 0.02, total 0.12; 19.99 @18% -> tip 3.6, total 23.59; 33.33 @15% /3 -> 5 / 38.33 / 12.78.

## Desviaciones del PRP
1. El comando literal `node --test apps/calculadora-propinas/` FALLA en Node 22.22 (exit 1, MODULE_NOT_FOUND: trata el directorio como archivo). Es un defecto del comando del PRP, no del codigo. Equivalentes que pasan: `cd apps/calculadora-propinas && node --test` o `node --test apps/calculadora-propinas/*.test.js`. Recomendado corregir el PRP/plantilla.
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

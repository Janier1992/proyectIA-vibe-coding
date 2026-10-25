# Review de Codigo: calculadora-propinas

Rama: factory/calculadora-propinas | PRP: PRPs/calculadora-propinas-2026-10-25.md | Riesgo: bajo

## Validacion ejecutada (real)
- `node --test apps/calculadora-propinas/*.test.js`: 30 tests, 30 pass, 0 fail.
- `node --check` calculator.js, ui.js, calculator.test.js: OK.
- grep de sinks peligrosos en calculator.js y ui.js: sin coincidencias.
- grep `https?://` en los archivos de la app: sin coincidencias.
- `wc -l`: 95 / 117 / 55 / 180 / 82 lineas (limite 500). Ninguna funcion supera 50 lineas.
- Solo existen los 5 archivos previstos. No hay linter ni tipos en el repo (segun PRP).
- El comando literal `node --test apps/calculadora-propinas/` del PRP falla en Node 22. Es un defecto del PRP, no del codigo, y el builder lo reporto.

## Correctitud frente a criterios
- Casos base, dividido, 0%, redondeo (33.33/15/3 -> 5 / 38.33 / 12.78) y coma flotante (0.1, 19.99): cubiertos y correctos.
- parseNumber, rechazos y limites exactos de validacion, y multiples errores a la vez: cubiertos. Hay mas de 15 casos.
- UI: renderizado solo con textContent/value, estados vacio/error/resultado, aria-invalid y aria-describedby, Limpiar con foco, submit prevenido. `[hidden]` esta protegido con `display:none !important`. Hay `overflow-wrap`, `focus-visible` y `prefers-reduced-motion`.
- Los criterios visuales (375/768/1440px, contraste, teclado) no se pudieron verificar: no hay navegador. Quedan pendientes para un humano, como declara build.md.

## Hallazgos

### CAMBIOS
Ninguno obligatorio.

### Menores (no bloquean)
1. `calculator.js:21-25` y `calculator.js:15-17`: los limites estan duplicados como texto en MESSAGES y como constantes MAX_*. Sugerencia: construir los mensajes a partir de las constantes. El builder ya lo registro como deuda.
2. `calculator.js:76`: `billCents * tipPercent / 100` con porcentajes decimales (ej. 12.5) puede caer en un medio centavo inexacto en coma flotante, y Math.round puede desviar un centavo. No hay impacto con porcentajes enteros. Es un caso borde aceptable.
3. `calculator.test.js`: falta un test explicito del rechazo de bill 0.004 (decision del builder, `calculator.js:44`) y de `tipPerPerson`. Cobertura de lo agregado fuera del PRP.
4. `calculator.js:24` e `index.html:36`: textos en español sin tilde ("numero"). Es una deuda de redaccion ya declarada. Afecta a la calidad del copy, no al codigo.
5. `ui.js:68`: el evento blur marca como "tocado" y muestra error al tabular sobre un campo vacio. Es consistente con "aparecen tras input/blur" del PRP. Se acepta.
6. `ui.js:5`: moneda fija USD en una constante, permitido por el PRP.

## Resumen
Codigo simple, sin duplicacion de logica de negocio (la UI delega en TipCalculator), sin sobre-ingenieria ni codigo muerto. El manejo de errores es correcto: calculateTip lanza RangeError y la UI valida antes de llamarlo. No hay llamadas externas. Se cumplen los limites de tamano y la nomenclatura.

VEREDICTO: APROBADO

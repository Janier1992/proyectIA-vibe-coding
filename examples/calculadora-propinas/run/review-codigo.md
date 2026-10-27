# Review de Codigo (iteracion 2): calculadora-propinas

Rama: examples/calculadora-propinas/run | PRP: examples/calculadora-propinas/prp.md | Riesgo: bajo

## Validacion ejecutada (real)
- `node --test examples/calculadora-propinas/app/*.test.js`: 33 tests, 33 pass, 0 fail.
- `node --check` calculator.js, ui.js, calculator.test.js: OK.
- grep de sinks (innerHTML, outerHTML, insertAdjacentHTML, document.write, eval(, new Function) en calculator.js y ui.js: sin coincidencias.
- grep `https?://` en la app: sin coincidencias.
- `wc -l`: 95 / 133 / 55 / 182 / 96 (limite 500). Ninguna funcion supera 50 lineas.

## Revision del diff 1a6e9af..HEAD
- calculator.js: solo cambia el texto del mensaje (tilde). Sin regresion; test nuevo lo cubre.
- calculator.test.js: +3 tests (bill 0.004/0.005, tipPerPerson, tilde). Correctos y cubren el menor 3 previo.
- ui.js: `showResults(result, errors)` y `emptyMessage` usan solo textContent. `syncShortcuts` recibe string (readValues devuelve `.value`), `.trim()` seguro. Quitar `el.hidden` es coherente con index.html (ya no hay `hidden` en los errores). El texto inicial de `#empty-state` en HTML coincide con EMPTY_BILL. Sin codigo muerto.
- index.html/styles.css: `.btn-reset` renombrado por completo a `.btn-secondary` (sin referencias huerfanas); `.error:empty` colapsa el hueco; `--control-border` aplicado a input, chip y boton secundario. Contrastes declarados >= 3:1 (no los medi; calculo del builder).
- PRP: comando de test corregido en los 3 lugares; ahora el comando del PRP funciona.

## Hallazgos

### BLOQUEANTE / CAMBIOS
Ninguno.

### Menores (no bloquean)
1. `calculator.js:21-25`: limites duplicados como texto y constantes MAX_* (deuda declarada, opcional 7 no aplicado).
2. `ui.js` blur marca "tocado" en campo vacio (opcional 9 no aplicado, aceptado por el PRP).
3. `calculator.js:76`: porcentajes decimales pueden desviar un centavo por coma flotante; caso borde aceptable.
4. Verificacion visual en navegador (375/768/1440, temas, teclado) sigue pendiente de un humano; no hay navegador en el entorno.

## Resumen
Los 4 hallazgos obligatorios de la iteracion 1 estan resueltos sin regresiones. Codigo simple, sin duplicacion de logica de negocio, limites de tamano y nomenclatura respetados.

VEREDICTO: APROBADO

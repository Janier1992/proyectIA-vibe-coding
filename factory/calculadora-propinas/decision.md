# Decision: calculadora-propinas

PRP: PRPs/calculadora-propinas-2026-10-25.md | Riesgo: bajo | Rama: factory/calculadora-propinas

## Veredictos
| Revisor | Veredicto |
|---|---|
| Seguridad | APROBADO |
| Codigo | APROBADO |
| UX | CAMBIOS (4) |
| UI | CAMBIOS (1, coincide con UX CAMBIOS-1) |

Los 4 reportes existen. Validaciones del builder: 30/30 tests, node --check, greps de seguridad y limites de tamano en verde.
Ningun BLOQUEANTE. Hay CAMBIOS pendientes, asi que aplica la regla 1: RECHAZADO (el riesgo bajo no permite saltarla).

## Verificacion independiente (leido en el codigo)
- Contraste de borde: confirmado. styles.css:10 `--border: hsl(220 18% 76%)` sobre superficie clara, styles.css:25 `hsl(225 15% 34%)` en oscuro. Se usa como unico borde de input (styles.css:73), chips (styles.css:111) y divisor (styles.css:129). La cifra exacta (1.86:1 / 2.05:1) la calculo la review UI; no la recalcule.
- Tildes: confirmado en index.html:27, index.html:36 y calculator.js:24.
- Texto guia enganoso: confirmado. ui.js:36 oculta resultados y muestra empty-state siempre que `result` es null, incluso con monto valido y otro campo invalido.
- Errores sin anuncio: confirmado. index.html:20, :26 y :38 son `<p class="error" hidden>` sin role ni aria-live. Se ocultan con `hidden` (ui.js:29), asi que los cambios de contenido no se anuncian de forma fiable.

## Hallazgos para el builder (priorizados)

### Obligatorios (CAMBIOS)
1. Contraste de bordes de controles < 3:1 (WCAG 1.4.11). Origen: UX CAMBIOS-1 y UI 1.
   - styles.css:10 y styles.css:25 (definicion de `--border`); usos en styles.css:73 (input) y styles.css:111 (chip).
   - Crear un token `--control-border` con >= 3:1 contra `--surface` en ambos temas (sugerencia: claro `hsl(220 15% 45%)`, oscuro `hsl(225 15% 58%)`). Usarlo en input y chip; mantener `--border` para el divisor de styles.css:52 y :129. Verificar el ratio con calculo o herramienta y comprobar que el estado de error y el foco siguen distinguibles.
2. Texto guia contradictorio con monto valido y otro campo invalido (UX CAMBIOS-3).
   - ui.js:34-38 y index.html:46.
   - Si el monto es vacio o invalido, mostrar "Ingresa el monto de la cuenta para ver el resultado". Si el monto es valido y falla otro campo, mostrar "Corrige los campos marcados para ver el resultado". Mantener sin NaN/ceros y usar solo textContent.
3. Errores no anunciados a lectores de pantalla (UX CAMBIOS-4).
   - index.html:20, :26, :38 (`<p class="error">`); ui.js:25-32.
   - Agregar `role="alert"` o `aria-live="polite"` a los tres elementos, dejandolos en el DOM. Comprobar que el patron de `hidden` no impida el anuncio (por ejemplo, vaciar el texto en lugar de depender solo de `hidden`).
4. Tildes y enie omitidas (UX CAMBIOS-2; tambien UI 5 y codigo 4).
   - index.html:27 "Porcentajes rapidos" -> "Porcentajes rápidos".
   - index.html:36 "Numero de personas" -> "Número de personas" (texto fijado por el PRP).
   - calculator.js:24 "numero" -> "número". Actualizar el test si compara el texto del mensaje.
   - El archivo ya declara UTF-8; revisar tambien `<meta charset>` y que los tests sigan en verde.

### Opcionales (no bloquean; hacer si es barato)
5. styles.css:150 y index.html:28-31: el chip "20%" cae solo en una segunda linea a 375px. Usar `display: grid; grid-template-columns: repeat(4, 1fr)` en `.shortcuts`.
6. styles.css:112 y :172: h1 con peso 800 y tracking negativo segun la skill. "Limpiar" (accion secundaria) tiene el estilo de CTA primario; darle estilo secundario.
7. calculator.js:15-25: construir los mensajes a partir de MAX_BILL/MAX_TIP_PERCENT/MAX_PEOPLE (DRY).
8. calculator.test.js: agregar tests para el rechazo de bill 0.004 (calculator.js:44) y para `tipPerPerson`.
9. ui.js:68: marcar `touched` en blur solo si el valor cambio (para no mostrar error al tabular sobre un campo vacio). Opcional.
10. Atajos sin `aria-pressed` ni indicador activo. Mejora opcional.

## Defecto del PRP (no del codigo)
El comando `node --test apps/calculadora-propinas/` falla en Node 22. Usar `node --test apps/calculadora-propinas/*.test.js`. Corregir el PRP o la plantilla.

## Pendiente de verificacion humana (aunque se resuelvan los cambios)
Revision visual real en 768 y 1440px, teclado de extremo a extremo, lector de pantalla, contraste medido con herramienta y consola/Network. Seguridad (informativo): fijar `frame-ancestors` por cabecera HTTP si se despliega en un host real.

## Siguiente paso
Devolver al builder con los puntos 1-4. Tras los cambios, volver a pasar las revisiones UX y UI (y re-ejecutar tests). Con riesgo bajo y los 4 revisores en APROBADO, la siguiente pasada seria APROBADO_AUTO.

DECISION: RECHAZADO

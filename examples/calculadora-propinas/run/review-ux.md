# Review UX (iteración 2): calculadora-propinas

Diff revisado: `git diff 1a6e9af..HEAD`. Tests: 33/33 en verde (`node --test *.test.js`).

## Hallazgos obligatorios previos
1. Contraste de bordes (WCAG 1.4.11): CORREGIDO. Nuevo token `--control-border` (styles.css:11 claro `hsl(220 15% 45%)`, styles.css:27 oscuro `hsl(225 15% 58%)`), usado en input (styles.css:75), chip y botón secundario. Estimación de ratio de unos 5:1 en ambos temas, por encima de 3:1. `--border` se conserva en los divisores. El estado de error (`--danger`) y el foco siguen distinguibles.
2. Texto guía contradictorio: CORREGIDO. ui.js:17-18 y :37-39 muestran "Ingresa el monto..." si falla el monto y "Corrige los campos marcados..." en los demás casos. Se usa solo `textContent`.
3. Errores sin anuncio: CORREGIDO. index.html:20, :26 y :38 pasan a `<p class="error" aria-live="polite">` sin `hidden`, y ui.js:31 solo vacía o rellena el texto. Un `aria-live` presente en el DOM desde la carga y vacío anuncia bien los cambios de contenido posteriores. El patrón anterior (`hidden`) era el problema, no el `<p>` vacío. El `::before` con ⚠ es decorativo y `.error:empty` evita el hueco visual.
4. Tildes: CORREGIDO. "Porcentajes rápidos", "Número de personas" y calculator.js:24 "número", con test añadido. `<meta charset="utf-8">` está presente.

## Regresiones
Ninguna bloqueante. El alcance cubre además los opcionales 5, 6, 8 y 10: chips en grid de 4 columnas, "Limpiar" con estilo secundario, tests nuevos y `aria-pressed` sincronizado en cada `render()`, incluido el reset.

Observaciones menores, no bloquean:
- El cambio de texto de `#empty-state` dentro de la región `aria-live` de resultados puede generar un anuncio extra. Es aceptable.
- Con foco en un campo vacío, el blur marca `touched` y muestra error (opcional 9, sin cambios).

Pendiente de verificación humana: prueba con lector de pantalla real, teclado de extremo a extremo y medición del contraste con herramienta.

VEREDICTO: APROBADO

# Review UI: calculadora-propinas

Verificado con Playwright (chromium) en 375 y 1440 px, claro y oscuro (prefers-color-scheme), estados vacio, resultado y error; ademas 320 px con monto maximo. Sin errores de consola ni de pagina; sin scroll horizontal (scrollWidth == viewport en 320/375/1440). Contraste calculado a partir de los tokens HSL.

## Cumple
- Tokens HSL en :root con redefinicion oscura y color-scheme; sin colores hardcodeados repetidos (solo el degradado del boton y la sombra de la tarjeta).
- Texto/fondo 16.5:1 (claro) y 14.1:1 (oscuro); muted >= 5.85:1; danger 7.5/7.1:1; texto del boton >= 5.6:1. Cumple 4.5:1.
- Responsive correcto; jerarquia visual de "Total a pagar" y "Por persona"; cifras tabulares; error con icono + texto (no solo color).
- Foco visible 3px en ambos temas; touch targets 44px; inputs 16px; transiciones 160-200 ms; prefers-reduced-motion respetado.

## Hallazgos
1. CAMBIOS - `apps/calculadora-propinas/styles.css:65` y `:81` (`--border`, usado en `input` linea 128 y `.chip` linea 166): el borde de los campos y chips tiene contraste 1.86:1 (claro) y 2.05:1 (oscuro) contra la superficie. WCAG 1.4.11 exige >= 3:1 para limites de controles de formulario. Correccion: oscurecer `--border` en claro (p. ej. `hsl(220 15% 52%)`) y aclararlo en oscuro (p. ej. `hsl(225 15% 52%)`), o usar un token `--control-border` separado del divisor de tarjeta/resultados.
2. Menor (no bloquea) - `styles.css:150` y `index.html:28-31`: a 375 px el chip "20%" cae solo en una segunda linea. Sugerencia: `display:grid; grid-template-columns: repeat(4, 1fr)` en `.shortcuts`.
3. Menor (no bloquea) - `styles.css:112` y `:172`: la skill pide h1 con peso 800 y letter-spacing -0.05em; el h1 usa el peso por defecto sin tracking. "Limpiar" (accion secundaria) tiene el estilo de CTA primario con degradado y compite con los resultados; considerar estilo secundario.
4. Informativo - La skill sugiere Inter/Outfit y glassmorphism; el PRP fija pila de sistema y sin fuentes remotas, por lo que no se reporta como defecto.
5. Informativo - Mensajes sin tildes/enie ("Numero", "rapidos", "entero ... personas") visibles en la UI (`index.html:27,36`, ui.js). Es deuda ya declarada por el builder; afecta la calidad percibida en espanol.

## No verificado
Navegacion solo con teclado de extremo a extremo, 768 px, y contraste del estado hover/disabled (solo calculado para estados base). Capturas efimeras en el scratchpad, no versionadas.

VEREDICTO: CAMBIOS

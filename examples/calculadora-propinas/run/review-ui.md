# Review UI: calculadora-propinas (iteracion 2)

Verificado con Playwright (chromium) en 375 y 1440 px, claro y oscuro (prefers-color-scheme), estados vacio, resultado y error. Valores medidos con getComputedStyle (no solo calculados de tokens). Sin errores de consola ni de pagina; sin scroll horizontal (scrollWidth == viewport en 375 y 1440). Capturas efimeras en el scratchpad, no versionadas.

## Hallazgos previos
1. CAMBIOS (contraste de borde de controles) - RESUELTO. `--control-border` en `styles.css:10` y `:26`, usado en input (`:75`), `.chip` y `.btn-secondary`. Medido en el render: borde input/boton vs superficie 5.20:1 (claro) y 4.90:1 (oscuro); borde de chip vs su fondo `--surface-alt` 4.47:1 (claro) y 4.20:1 (oscuro). Todos >= 3:1. El estado de error (borde `--danger`) sigue diferenciandose del normal en la captura.
2. Grid de atajos - RESUELTO. `.shortcuts` con 4 columnas: a 375 px los cuatro chips quedan en una sola fila (y=299, 67x44 px cada uno); a 1440 px tambien (102x44). Sin desborde, alto tactil 44 px.
3. "Limpiar" como accion secundaria - RESUELTO (`.btn-secondary`, contorno sin degradado). Peso/tracking del h1 de la skill: sigue sin aplicarse (menor, no bloquea).
4. Tildes - RESUELTO en la UI visible ("Número de personas", "Porcentajes rápidos", mensaje de "número entero").

## Cumple
- Tokens HSL con redefinicion oscura y color-scheme; sin colores repetidos hardcodeados.
- Chip activo (`aria-pressed=true`) una vez asentada la transicion: texto/fondo 5.97:1 (claro) y 10.7:1 (oscuro). Un valor transitorio menor medido a los 160 ms de la transicion no es el estado final.
- Errores con icono + texto, colapsan sin hueco cuando estan vacios; texto guia del estado vacio correcto; foco visible 3px en ambos temas; touch targets 44 px; transiciones 160-200 ms; prefers-reduced-motion respetado.
- Responsive y ambos temas coherentes en las capturas.

## Menores (no bloquean)
- `styles.css:36` (h1): la skill pide peso 800 y letter-spacing -0.05em; no aplicado.
- La skill sugiere Inter/Outfit y glassmorphism; el PRP fija pila de sistema y sin recursos remotos, por lo que no es defecto.

## No verificado
Navegacion solo con teclado de extremo a extremo, 768 px, y contraste de hover/disabled.

VEREDICTO: APROBADO

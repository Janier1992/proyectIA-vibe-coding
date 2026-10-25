# Review UX: calculadora-propinas

Revisión por lectura de código de `index.html`, `styles.css`, `ui.js` y los mensajes de `calculator.js`. Sin navegador. Riesgo del PRP: bajo.

## Cubierto correctamente
- Flujo completo sin pasos muertos: tres campos, atajos, Limpiar y recálculo en `input`. Limpiar devuelve el foco a monto (`ui.js:62`).
- Estado vacío con texto guía, sin ceros ni NaN (`index.html:46`, `ui.js:36-38`). Los resultados solo se pintan si la validación pasa.
- Errores por campo con `aria-describedby`, `aria-invalid`, ícono "⚠" además del color (`styles.css:93`) y texto accionable (`calculator.js:22-24`). Los errores no aparecen al cargar (`touched`).
- `<label for>` visible en todos los campos, `lang="es"`, `inputmode` correcto y `novalidate` con `submit` prevenido.
- Foco visible con `:focus-visible` y anillo de 3px. Touch targets de 44px (`min-height: 2.75rem`). Inputs de 16px. `prefers-reduced-motion` respetado.
- Acción "Limpiar" no destructiva (solo restablece valores). No requiere confirmación.

## Hallazgos

### CAMBIOS-1: el borde de los inputs no llega a 3:1 (WCAG 1.4.11)
- `styles.css:10` y `styles.css:73`, tema oscuro en `styles.css:25`.
- `--border` (`hsl(220 18% 76%)`) sobre `--surface` blanca da un contraste estimado de ~1.8:1. En oscuro (`hsl(225 15% 34%)` sobre `hsl(225 25% 14%)`) da ~1.9:1. El borde es el único indicador visual del límite del campo. Es una estimación a mano y requiere medición.
- Corrección: usar un token `--input-border` con contraste >= 3:1 contra `--surface` en ambos temas (por ejemplo, claro `hsl(220 15% 45%)` y oscuro `hsl(220 15% 58%)`).

### CAMBIOS-2: tildes y eñes omitidas en texto visible
- `index.html:36` ("Numero de personas"), `index.html:27` ("Porcentajes rapidos"), `calculator.js:24` ("numero").
- El PRP fija el texto "Número de personas". La ortografía incorrecta degrada la calidad y la pronunciación con lector de pantalla. `<meta charset="utf-8">` ya está presente, así que no hay razón técnica para omitirlas.
- Corrección: escribir "Número", "rápidos", "número" (UTF-8 es seguro).

### CAMBIOS-3: el estado vacío engaña cuando el monto es válido pero otro campo no
- `ui.js:36` y `index.html:46`.
- Con monto válido y personas = 0, los resultados se ocultan y aparece "Ingresa el monto de la cuenta para ver el resultado", aunque el monto ya está ingresado. El error del campo de personas sí se ve, pero el texto guía contradice al usuario.
- Corrección: mostrar el texto guía solo si el monto está vacío o inválido. Si el monto es válido y falla otro campo, mostrar "Corrige los campos marcados para ver el resultado".

### CAMBIOS-4: los errores no se anuncian a lectores de pantalla al aparecer
- `index.html:20`, `index.html:26` y `index.html:38` (`<p class="error" hidden>`), `ui.js:28-30`.
- `aria-describedby` solo se lee cuando el campo recibe el foco. Mientras el usuario escribe y aparece el error, no hay anuncio. Se pierde el requisito de accesibilidad "mensajes claros y accionables".
- Corrección: añadir `role="alert"`, o `aria-live="polite"` en los `<p class="error">`, manteniendo los elementos en el DOM.

### Menores (no bloquean)
- `ui.js:68` con `touched`: tabular por el monto vacío muestra "Ingresa un monto…" sin haber escrito nada (ya anotado en la deuda del builder). El PRP dice que los errores no deben aparecer "antes de que el usuario toque el campo". Es defendible porque aparece tras blur. Alternativa: marcar `touched` en `blur` solo si el valor cambió.
- Los atajos 10/15/18/20 no indican cuál está activo (sin `aria-pressed` ni estilo). Mejora opcional.
- Moneda fija USD con locale del navegador (`ui.js:5`): en `es-*` se muestra como "US$". Está documentado y es aceptable.

## Requiere verificación visual humana (no verificable por código)
- Layout sin scroll horizontal en 320, 375, 768 y 1440px. Revisar que `dd.big` de 1.6rem con importes largos (1.000.000 + propina) no desborde.
- Contraste >= 4.5:1 de texto en ambos temas, medido con herramienta. Mi estimación: `--text-muted`, `--danger` y el botón primario parecen pasar.
- Contraste 3:1 de bordes y del anillo de foco (CAMBIOS-1).
- Navegación solo con teclado: orden monto, porcentaje, atajos, personas, Limpiar, y foco visible en cada elemento.
- Comportamiento real con un lector de pantalla (región `aria-live` en `index.html:44` y CAMBIOS-4).
- Animación `reveal` y reduced-motion.
- Que la consola y Network estén limpias con la CSP.

VEREDICTO: CAMBIOS

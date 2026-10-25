# PRP: Calculadora de Propinas

Fecha: 2026-10-25 | Rama: `factory/calculadora-propinas` | Plantilla: `prp_frontend.md` | Tipo: software

## Goal
Página web estática (HTML/CSS/JS vanilla, cero dependencias, sin build) en `apps/calculadora-propinas/`. El usuario ingresa monto de la cuenta, porcentaje de propina y número de personas, y ve en tiempo real: propina total, total a pagar y monto por persona. Las entradas inválidas se validan y se comunican con mensajes claros. La lógica de cálculo es pura, exportable a Node (tests con `node:test`) y usable en el navegador.

## Nivel de riesgo: bajo
Justificación: app estática del lado cliente, sin auth, pagos, datos personales, red, almacenamiento, migraciones ni infraestructura. El único riesgo relevante es de corrección numérica (redondeo de dinero) y de XSS si se usara `innerHTML`, ambos cubiertos abajo.

## Alcance
- Tres entradas: monto de la cuenta, porcentaje de propina, número de personas.
- Tres salidas: propina total, total a pagar, monto por persona.
- Validación con mensajes por campo, estado vacío y estado de error.
- Atajos de porcentaje (botones 10 / 15 / 18 / 20) que rellenan el campo de porcentaje (opcional dentro del alcance, ver tareas; sin lógica extra).
- Modo claro/oscuro automático por `prefers-color-scheme`, responsive.
- Tests unitarios de la lógica con `node:test`.

## No-alcance (YAGNI)
- Sin frameworks, bundlers, npm install, `package.json` con dependencias, TypeScript, ni CDN/fuentes externas.
- Sin persistencia (localStorage/cookies), sin backend, sin analítica, sin i18n multi-idioma, sin selector de moneda (se formatea con `Intl.NumberFormat` según locale del navegador, moneda fija configurable en una constante).
- Sin división desigual de cuenta, sin redondeo de propina "hacia arriba" como feature, sin historial.
- Sin toggle manual de tema (solo `prefers-color-scheme`).
- Sin tests de DOM/E2E automatizados (la capa DOM se verifica manualmente; ver validación).

## Estructura de archivos
```
apps/calculadora-propinas/
  index.html            # marcado semántico, carga styles.css y scripts
  styles.css            # tokens HSL, claro/oscuro, responsive
  calculator.js         # lógica pura (sin DOM), UMD mínimo: module.exports en Node, window.TipCalculator en navegador
  ui.js                 # único archivo que toca el DOM; usa window.TipCalculator
  calculator.test.js    # node:test + node:assert/strict
```
Límites CLAUDE.md: archivos < 500 líneas, funciones < 50 líneas, `camelCase` funciones, `UPPER_SNAKE_CASE` constantes, archivos `kebab-case`.

## Contrato de la lógica (`calculator.js`)
Exporta (nombres fijados para que builder y tests coincidan):
- `parseNumber(raw)`: convierte string de entrada a número; acepta coma o punto decimal; devuelve `NaN` para vacío, espacios o texto no numérico. No usa `eval` ni `Function`.
- `validateInputs({ bill, tipPercent, people })`: devuelve `{ valid: boolean, errors: { bill?: string, tipPercent?: string, people?: string } }`. Mensajes en español.
- `calculateTip({ bill, tipPercent, people })`: devuelve `{ tipTotal, total, perPerson, tipPerPerson }` en valores numéricos redondeados a 2 decimales. Lanza `RangeError` o devuelve error controlado si las entradas son inválidas (decisión del builder, documentada y testeada; la UI siempre valida antes).
- Constantes exportadas: `MAX_BILL`, `MAX_TIP_PERCENT`, `MAX_PEOPLE`.

Reglas de validación (fuente de verdad):
| Campo | Regla |
|---|---|
| bill | número finito, > 0, <= `MAX_BILL` (1_000_000) |
| tipPercent | número finito, >= 0, <= `MAX_TIP_PERCENT` (100); 0 es válido |
| people | entero, >= 1, <= `MAX_PEOPLE` (100); rechaza decimales (2.5), 0, negativos |
| general | rechaza `NaN`, `Infinity`, vacío, texto, notación científica fuera de rango |

Reglas de cálculo y redondeo:
- Calcular en centavos enteros (`Math.round(bill * 100)`) para evitar errores de coma flotante (ej. 0.1 + 0.2).
- `tipTotal = round(billCents * tipPercent / 100)` en centavos; `total = billCents + tipTotal`.
- `perPerson = total / people` redondeado a centavos con `Math.round`; documentar en un comentario que la suma de partes puede diferir del total en 1-2 centavos y que el total mostrado es el exacto (comportamiento aceptado, no se reparte el resto).
- Resultados convertidos a unidades (dividir por 100) solo al devolver.

## Success Criteria / Criterios de aceptación (verificables)
Lógica (automatizable con `node --test`):
- [ ] `node --test apps/calculadora-propinas/*.test.js` termina con código 0 y 0 fallos.
- [ ] Caso base: bill 100, tip 15, people 1 -> tipTotal 15.00, total 115.00, perPerson 115.00.
- [ ] Caso dividido: bill 200, tip 10, people 4 -> tipTotal 20.00, total 220.00, perPerson 55.00.
- [ ] Propina 0%: bill 50, tip 0, people 2 -> tipTotal 0, total 50, perPerson 25.
- [ ] Redondeo: bill 33.33, tip 15, people 3 -> resultados con exactamente 2 decimales sin artefactos de coma flotante (valores esperados calculados a mano en el test).
- [ ] Caso de coma flotante: bill 0.1 con tip 20 y bill 19.99 con tip 18 no producen resultados como `0.020000000000000004`.
- [ ] `parseNumber` acepta `"12.5"` y `"12,5"`; devuelve `NaN` para `""`, `"   "`, `"abc"`, `"12abc"`, `"1e999"`.
- [ ] Validación rechaza: bill vacío, 0, negativo, `NaN`, `Infinity`, > `MAX_BILL`; tip negativo o > 100; people 0, negativo, 2.5, vacío, > `MAX_PEOPLE`. Cada rechazo tiene un mensaje no vacío en la clave correcta.
- [ ] Validación acepta límites exactos: tip 0, tip 100, people 1, people `MAX_PEOPLE`, bill 0.01, bill `MAX_BILL`.
- [ ] Múltiples errores simultáneos se reportan todos a la vez.
- [ ] Al menos 15 casos de prueba en total, agrupados con `describe`/`test` de `node:test`.

UI (verificación manual / inspección de código):
- [ ] Al abrir `index.html` (doble clic o servidor estático) sin consola de errores, se ve el estado vacío (sin resultados ni errores).
- [ ] Cambiar cualquier campo recalcula al instante (evento `input`) sin recargar.
- [ ] Entrada inválida muestra mensaje junto al campo, oculta resultados y no muestra `NaN`, `Infinity` ni `undefined` en ningún caso.
- [ ] `grep -nE "innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function" apps/calculadora-propinas/*.js` no devuelve coincidencias en código de producto.
- [ ] Layout correcto sin scroll horizontal en 375px, 768px y 1440px.
- [ ] Contraste >= 4.5:1 en texto normal en ambos temas.
- [ ] Todo operable solo con teclado, con foco visible.
- [ ] Cero peticiones de red (DevTools Network vacío salvo los propios archivos locales).

## Requisitos de seguridad
- Prohibido `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `new Function`, atributos `on*` inline y `javascript:` URLs. Mostrar datos del usuario y resultados solo con `textContent` / `value`.
- Los mensajes de error provienen de constantes del código, nunca se interpola texto crudo del usuario en el DOM.
- `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'">` en `index.html` (sin scripts ni estilos inline, así que `'unsafe-inline'` no es necesario).
- Sin recursos externos (CDN, fuentes, analítica); sin `localStorage`, cookies ni envío de datos.
- Límites máximos en validación para evitar valores absurdos/overflow visual.
- Sin credenciales ni secretos en el repo.

## Requisitos de UX
- Etiquetas: cada `<input>` con `<label for>` visible (no solo placeholder). Textos sugeridos: "Monto de la cuenta", "Propina (%)", "Número de personas".
- Tipos de campo: `type="text"` con `inputmode="decimal"` para monto y porcentaje (permite coma decimal y validación propia) e `inputmode="numeric"` para personas; `autocomplete="off"`. Valores iniciales: monto vacío, propina 15, personas 1.
- Estado vacío: antes de ingresar un monto válido, la zona de resultados muestra texto guía ("Ingresa el monto de la cuenta para ver el resultado") y no valores en cero.
- Estado de error: mensaje en texto bajo el campo con `id` vinculado por `aria-describedby`, `aria-invalid="true"` en el campo, ícono/texto además del color (no depender solo del color rojo). Un error por campo, redactado en español claro y accionable (ej. "Ingresa un monto mayor que 0").
- Los errores no aparecen al cargar la página ni antes de que el usuario toque el campo; aparecen tras interacción (input/blur).
- Resultados en una región `aria-live="polite"` (o `<output>`) para lectores de pantalla.
- Teclado: orden de tabulación lógico (monto, porcentaje, atajos, personas), botones de atajo alcanzables y activables con Enter/Espacio, botón "Limpiar" que restablece valores y devuelve el foco al primer campo. Enter en un campo no recarga la página (usar `<form novalidate>` con `submit` prevenido o sin form).
- Formato de moneda con `Intl.NumberFormat` (2 decimales, separador de miles según locale).
- `lang="es"` en `<html>`.

## Requisitos de UI (skill `ui-ux-aesthetics`)
- **Tipografía**: pila de sistema (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`), sin fuentes remotas; cifras con `font-variant-numeric: tabular-nums`; total a pagar con jerarquía visual mayor.
- **Colores (HSL en custom properties en `:root`)**: `--background`, `--surface`, `--text`, `--text-muted`, `--primary`, `--primary-contrast`, `--border`, `--danger`, `--focus-ring`. Valores oscuros redefinidos dentro de `@media (prefers-color-scheme: dark)`. Paleta cohesionada, no colores genéricos puros; acento primario con degradado sutil permitido. `color-scheme: light dark` declarado.
- **Layout**: tarjeta central (`max-width` ~ 480px), mobile-first, gap con unidades relativas, resultados en tres filas/tarjetas con "Total a pagar" y "Por persona" destacados. Sin scroll horizontal desde 320px.
- **Micro-animaciones**: transición 150-200ms en hover/focus/active de botones y bordes de input; leve fade/translate al actualizar resultados; respetar `@media (prefers-reduced-motion: reduce)` desactivando animaciones.
- **Foco visible**: `:focus-visible` con anillo de alto contraste en ambos temas.
- **Touch targets**: mínimo 44x44px en botones de atajo y Limpiar; tamaño de fuente de inputs >= 16px (evita zoom en iOS).
- Sin imágenes placeholder; si se usan íconos, SVG inline limpio o ninguno.

## Tareas de implementación (orden secuencial)
```yaml
Task 1: Lógica pura
  CREATE: apps/calculadora-propinas/calculator.js
  CONTENT: parseNumber, validateInputs, calculateTip, constantes de límites; aritmética en centavos; export dual (module.exports si existe `module`, si no window.TipCalculator).
  VALIDATE: node -e "const c=require('./apps/calculadora-propinas/calculator.js'); console.log(c.calculateTip({bill:100,tipPercent:15,people:1}))"

Task 2: Tests unitarios
  CREATE: apps/calculadora-propinas/calculator.test.js
  CONTENT: casos de la sección Criterios de aceptación (lógica) con node:test + node:assert/strict.
  VALIDATE: node --test apps/calculadora-propinas/*.test.js (0 fallos)

Task 3: Marcado
  CREATE: apps/calculadora-propinas/index.html
  CONTENT: estructura semántica (main, h1, form novalidate, labels, mensajes de error por campo con ids, región de resultados, botón Limpiar, atajos), meta viewport, CSP, lang="es", carga de styles.css, calculator.js y luego ui.js (script con defer, sin inline).

Task 4: Estilos
  CREATE: apps/calculadora-propinas/styles.css
  CONTENT: tokens HSL claro/oscuro, layout responsive mobile-first, estados focus/error/hover/disabled, reduced-motion.

Task 5: Capa DOM
  CREATE: apps/calculadora-propinas/ui.js
  CONTENT: leer inputs, llamar a TipCalculator.validateInputs/calculateTip, renderizar solo con textContent, gestionar estados vacío/error/resultado, aria-invalid/aria-describedby, atajos, Limpiar y foco. Sin lógica de negocio duplicada (DRY).

Task 6: Verificación final
  RUN: todos los comandos de validación; revisar manualmente los criterios de UI en 375/768/1440px, ambos temas y solo con teclado.
```

## Comandos de validación
```bash
# 1. Tests unitarios (requisito principal; Node 22)
node --test apps/calculadora-propinas/*.test.js

# 2. Sintaxis de cada archivo JS
node --check apps/calculadora-propinas/calculator.js
node --check apps/calculadora-propinas/ui.js
node --check apps/calculadora-propinas/calculator.test.js

# 3. Seguridad: sin sinks peligrosos en código de producto (debe no devolver nada)
grep -nE "innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function" \
  apps/calculadora-propinas/calculator.js apps/calculadora-propinas/ui.js

# 4. Sin dependencias ni recursos externos (debe no devolver nada)
grep -nE "https?://" apps/calculadora-propinas/index.html apps/calculadora-propinas/styles.css apps/calculadora-propinas/ui.js apps/calculadora-propinas/calculator.js
ls apps/calculadora-propinas/ | grep -E "node_modules|package-lock" ; true

# 5. Límites de tamaño (cada archivo < 500 líneas)
wc -l apps/calculadora-propinas/*

# 6. Verificación visual y funcional (servidor estático sin dependencias)
python3 -m http.server 8080 --directory apps/calculadora-propinas
# Abrir http://localhost:8080 y comprobar: 375px, 768px, 1440px; tema claro y oscuro
# (emulación prefers-color-scheme en DevTools); navegación solo con Tab/Enter/Espacio;
# consola sin errores; Network sin peticiones externas.
```
Nota: el repo no tiene linter ni tipos configurados; el builder no debe añadir dependencias para ello (YAGNI). `node --check` y los tests son el gate automatizado.

## Riesgos y casos de borde a cubrir
- Coma flotante en dinero (resuelto con centavos enteros).
- Entradas pegadas con espacios o separador de miles; decisión: `parseNumber` recorta espacios y acepta solo coma o punto decimal, rechaza el resto.
- Campo con valor válido que pasa a vacío: volver al estado vacío, no mostrar ceros ni `NaN`.
- Diferencia de 1-2 centavos entre `perPerson * people` y `total`: documentada y aceptada.
- Valores muy grandes que desbordan el layout: acotados por `MAX_*`; el CSS debe permitir `overflow-wrap: anywhere` en resultados.

## Definición de terminado
Todos los criterios de aceptación marcados, comandos 1-5 sin fallos ni coincidencias indebidas, verificación visual del punto 6 realizada, y los cinco archivos presentes en `apps/calculadora-propinas/` sin archivos extra.

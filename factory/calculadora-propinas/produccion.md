# Producción: calculadora-propinas

Estado: **listo para despliegue, pendiente de confirmación humana.** Riesgo: bajo. Decisión: `APROBADO_AUTO` (ver `decision.md`).

## Artefacto a desplegar
- Carpeta estática `apps/calculadora-propinas/` (`index.html`, `styles.css`, `calculator.js`, `ui.js`). `calculator.test.js` no es necesario en el servidor.
- Sin build, sin dependencias, sin backend.

## Checklist previo
- [ ] Una persona revisó las capturas/verificación visual pendiente: 768 px, hover/disabled.
- [ ] Prueba manual solo con teclado, de extremo a extremo.
- [ ] Prueba con un lector de pantalla real (los errores usan `aria-live="polite"`).
- [ ] Contraste confirmado con herramienta en ambos temas (calculado: borde de controles >= 4.19:1).
- [ ] `node --test apps/calculadora-propinas/*.test.js` en verde (33/33 en la última corrida).
- [ ] Consola y Network limpias en el entorno real (no debe haber peticiones externas).

## Configuración de despliegue
- **Variables de entorno:** ninguna.
- **Migraciones:** ninguna.
- **Feature flags:** ninguno.
- **Cabeceras HTTP (el `<meta>` no las cubre):** `Content-Security-Policy` con `frame-ancestors 'none'` (o `X-Frame-Options: DENY`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.
- **Moneda:** fija en USD (constante `CURRENCY` en `ui.js`); cámbiala antes de publicar si el público es de otro país.
- **Hosting sugerido:** cualquier hosting estático (GitHub Pages, Netlify, Vercel, Cloudflare Pages).

## Monitoreo
- No hay backend que monitorear. Opcional: monitor de disponibilidad HTTP sobre la URL pública.

## Plan de rollback
- Redesplegar el commit anterior o retirar la carpeta publicada. No hay estado ni datos que revertir.

## Criterio de éxito post-despliegue
- La página carga sin errores de consola.
- Caso de control: cuenta 200, propina 15%, 4 personas da propina 30.00, total 230.00, 57.50 por persona.
- Una entrada inválida (por ejemplo 2.5 personas) muestra el error y no muestra resultado.

## Deuda conocida (no bloquea)
- Mensajes de error con los límites duplicados respecto a las constantes `MAX_*`.
- Un campo vacío se marca como "tocado" al perder el foco.
- Porcentajes decimales pueden desviar un centavo por coma flotante.
- No hay tests de DOM.

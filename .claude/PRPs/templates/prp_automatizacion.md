# PRP Automatización: [nombre]

## Objetivo
[Qué proceso se automatiza y qué resultado de negocio produce]

## Plataforma
- **Herramienta**: [n8n | Make | Zapier | script programado]
- **Disparador**: [webhook | cron | evento de app] — frecuencia y volumen esperado
- **Sistemas involucrados**: [APIs, bases de datos, correo, etc.]

## Flujo (nodos / pasos)
1. [Disparador]
2. [Transformación / validación de datos]
3. [Acción en sistema externo]
4. [Notificación o registro]

## Manejo de errores
- Reintentos con backoff, timeout por nodo y rama de error con alerta.
- Idempotencia: qué pasa si el mismo evento llega dos veces.
- Datos de respaldo o cola de reintento manual.

## Seguridad
- Credenciales solo en el gestor de la plataforma o variables de entorno (nunca en el JSON del flujo).
- Webhooks autenticados (token o firma). Datos personales mínimos y sin loguear.

## Criterios de aceptación
- [ ] Caso feliz probado con datos de ejemplo
- [ ] Caso de error probado (API caída, dato inválido)
- [ ] Flujo exportado en `automatizaciones/[nombre].json`
- [ ] Nivel de riesgo: [bajo | medio | alto] — justificación

## Validación
```bash
# Ejecución de prueba y verificación del resultado esperado
```

## Baseline de calidad y seguridad (obligatorio)
Ver `.claude/prompts/estandar-calidad.md`.
- **Herramientas**: [linter, tipado, framework de tests, auditoría de dependencias del stack]
- **Dependencias nuevas**: [paquete@versión fija: justificación; confirmar que existe y es el oficial]
- **Amenazas relevantes** (OWASP): [control de acceso, inyección, validación de entradas, secretos...] y cómo se mitigan
- **CI**: `.github/workflows/quality.yml` desde `.claude/templates/ci-quality.yml`
- **Gate esperado**: `bash .claude/scripts/quality-gate.sh . --out factory/[feature]/quality-gate.md` en PASS

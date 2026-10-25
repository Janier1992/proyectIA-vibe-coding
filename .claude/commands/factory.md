---
description: "Ejecuta el pipeline Factory completo: Entrada, Spec writer, Builder, revisión paralela (Seguridad/UX/UI/Código), Approver, compuerta humana, Main o PR, y Producción."
argument-hint: "[descripción | issue | archivo-requerimientos]"
---

# Factory: de la idea a producción

Entrada: $ARGUMENTS

Ejecuta las fases en orden. No saltes fases ni avances si la anterior falló. Los artefactos de cada corrida van en `factory/[feature]/`.

```
Entrada → Spec writer → Builder → [Seguridad | UX | UI | Código] → Approver → ¿Humano? → [Main | PR] → Producción
```

## 1. Entrada
- Clasifica el tipo: `software`, `automatización` o `mixto`. Si es ambiguo o falta información crítica, pregunta antes de continuar.
- Define `[feature]` en kebab-case. Crea `factory/[feature]/` y la rama `factory/[feature]` (nunca trabajes en `main`).
- Si hay código previo, ejecuta `/primer` mentalmente: lee `CLAUDE.md` y el layout.

## 2. Spec writer
- Lanza el agente `spec-writer` con la entrada y el tipo. Resultado: `PRPs/[feature]-[fecha].md` con criterios de aceptación y nivel de riesgo.
- Para automatizaciones se usa la plantilla `prp_automatizacion.md`.

## 3. Builder
- Lanza el agente `builder` con la ruta del PRP. Resultado: código en la rama y `factory/[feature]/build.md`.
- Haz commit en la rama de trabajo al terminar.

## 4. Revisión paralela
- Lanza **en un solo mensaje, en paralelo**, los cuatro agentes: `revisor-seguridad`, `revisor-ux`, `revisor-ui`, `revisor-codigo`. Cada uno recibe `[feature]` y la ruta del PRP.
- Cada uno escribe `factory/[feature]/review-*.md` con su `VEREDICTO`.

## 5. Approver
- Lanza el agente `approver`. Resultado: `factory/[feature]/decision.md`.
- Si `DECISION: RECHAZADO`: vuelve a la fase 3 pasando al `builder` la lista de hallazgos. Máximo 3 iteraciones; después, detente y reporta al usuario.

## 6. ¿Humano?
- `APROBADO_AUTO`: continúa a la fase 7 con destino por defecto **PR**.
- `REQUIERE_HUMANO`: presenta al usuario el resumen de `decision.md` (riesgo, hallazgos, diff) y espera su respuesta explícita. Sin respuesta, no avances.

## 7. Main o PR
- **PR (por defecto)**: sube la rama `factory/[feature]` y abre un PR con el resumen de `decision.md`. Solo si el usuario lo autoriza o la fase 6 lo indica.
- **Main**: únicamente si el usuario lo pide explícitamente para este cambio y el riesgo es `bajo`. Nunca hagas push directo a `main` por iniciativa propia.

## 8. Producción
- Genera `factory/[feature]/produccion.md`: checklist de despliegue (variables de entorno, migraciones, feature flags, monitoreo, plan de rollback y criterio de éxito post-despliegue).
- El despliegue lo confirma una persona; no despliegues a producción sin su "sí" explícito.
- Al cerrar, invoca `gestor-documentacion` con los archivos modificados.

## Reporte final
Tabla con el estado de cada fase (completada, fallida, omitida y por qué), veredictos de los 4 revisores, decisión, destino (PR/Main), enlaces a los artefactos y siguientes pasos.

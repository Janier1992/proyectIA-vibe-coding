# Revisión UX - gestor-tareas (iteración 3)

Verificado ejecutando la herramienta real desde un directorio temporal fuera del repo.

- Ayuda general y de add/list/done/remove: prefijo `uso:`, títulos "argumentos posicionales"/"opciones", descripciones, ejemplos, epílogo y códigos de salida en español. Salida 0.
- Errores de uso (salida 2, con `uso:` en español): sin comando, comando desconocido, prioridad inválida, estado inválido, falta de valor (`se esperaba un valor`), ID inválido (abc, 0, -5), opción desconocida (`argumentos no reconocidos`), falta de argumento (`faltan argumentos obligatorios`). Sin restos de "usage:", "choose from" ni "expected one argument".
- list por filtro: pendiente, hecha, todas y vacíos con mensajes accionables ("No hay tareas pendientes. Usa --estado todas.", "No hay tareas."). Salida 0.
- Dominio: ID inexistente -> `Error: ...` salida 1. Almacén: JSON corrupto -> salida 3 con mensaje accionable.
- Cambio a `add_usage` y `_Parser(**kwargs)`: sin regresiones. Accesibilidad CLI: texto plano, sin dependencia de color.

Sin hallazgos.

VEREDICTO: APROBADO

# Calculadora de propinas

App web estática (HTML, CSS y JavaScript sin dependencias) que calcula la propina y el total a pagar, y los divide entre varias personas. Es el ejemplo de la primera corrida de `/factory`; los artefactos están en [`examples/calculadora-propinas/run/`](../run/).

## Cómo abrirla

Abre `examples/calculadora-propinas/app/index.html` directamente en el navegador (no requiere servidor ni instalación).

## Tests

Requiere Node.js con `node:test` (Node 18 o superior; probado en Node 22). Desde la raíz del repositorio:

```bash
node --test examples/calculadora-propinas/app/*.test.js
```

Nota: usa el patrón `*.test.js`; pasar un directorio (`node --test <directorio>`) falla en Node 22.

## Estructura

```
examples/calculadora-propinas/app/
├── index.html           # Marcado de la página
├── styles.css           # Estilos
├── calculator.js        # Lógica de cálculo (sin DOM)
├── ui.js                # Enlace entre el DOM y la lógica
└── calculator.test.js   # Tests unitarios de calculator.js
```

#!/bin/bash
# Autotest del quality gate: proyectos sintéticos buenos y malos con el resultado esperado.
# Uso: bash .claude/scripts/test-quality-gate.sh
GATE="$(cd "$(dirname "$0")" && pwd)/quality-gate.sh"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
failures=0

# expect <nombre> <salida-esperada> <directorio> [texto-en-reporte]
expect() {
  local out code
  out=$(bash "$GATE" "$3" 2>&1); code=$?
  if [ "$code" = "$2" ] && { [ -z "$4" ] || echo "$out" | grep -q "$4"; }; then echo "✅ $1"
  else echo "❌ $1 (salida=$code, esperada=$2)"; failures=$((failures + 1)); fi
}
newproj() { mkdir -p "$TMP/$1"; echo "$TMP/$1"; }

p=$(newproj vacio);                                                    expect "proyecto vacío pasa" 0 "$p"
p=$(newproj js-ok); echo 'export const sum = (a, b) => a + b;' > "$p/sum.js"
echo 'import test from "node:test"; test("ok", () => {});' > "$p/sum.test.js"; expect "JS limpio sin linter queda UNVERIFIED" 2 "$p" "lint-js"
p=$(newproj js-sin-tests); echo 'export const a = 1;' > "$p/a.js";       expect "JS sin tests falla" 1 "$p" "Sin tests"
p=$(newproj js-test-roto); echo 'x' > "$p/a.js"
echo 'import test from "node:test"; test("rojo", () => { throw new Error("x"); });' > "$p/a.test.js"; expect "tests en rojo fallan" 1 "$p" "tests-js"
p=$(newproj secreto); key="sk-$(printf 'a%.0s' {1..30})"; echo "const k = \"$key\";" > "$p/a.js"; expect "secreto hardcodeado falla" 1 "$p" "secretos"
p=$(newproj env-versionado); echo 'A=1' > "$p/.env";                    expect "archivo .env falla" 1 "$p" "secretos"
p=$(newproj eval); echo 'eval(userInput);' > "$p/a.js";                  expect "eval falla" 1 "$p" "patrones-peligrosos"
p=$(newproj innerhtml); echo 'el.innerHTML = name;' > "$p/a.js";         expect "innerHTML falla" 1 "$p" "patrones-peligrosos"
p=$(newproj ignorado); echo 'el.innerHTML = "<b>fijo</b>"; // gate-ignore: literal constante' > "$p/a.js"
echo 'import test from "node:test"; test("ok", () => {});' > "$p/a.test.js"; expect "gate-ignore suprime el falso positivo" 2 "$p" "patrones-peligrosos"
p=$(newproj grande); seq 1 600 | sed 's/^/const v/;s/$/ = 1;/' > "$p/big.js"; expect "archivo >500 líneas falla" 1 "$p" "tamano"
p=$(newproj py); echo 'import os' > "$p/a.py"; echo 'x = 1' > "$p/test_a.py"
if command -v ruff >/dev/null 2>&1 && command -v pytest >/dev/null 2>&1; then expect "Python con import sin uso falla (ruff)" 1 "$p" "lint-py"; fi
p=$(newproj py-venv); echo 'x = 1' > "$p/a.py"; echo 'def test_a() -> None: pass' > "$p/test_a.py"
mkdir -p "$p/.venv/bin"; printf '#!/bin/bash\necho venv-ruff-usado; exit 1\n' > "$p/.venv/bin/ruff"; chmod +x "$p/.venv/bin/ruff"
expect "el gate prioriza las herramientas de .venv" 1 "$p" "venv-ruff-usado"
p=$(newproj py-funcion-larga); { echo 'def larga() -> int:'; for i in $(seq 1 55); do echo "    x$i = $i"; done; echo '    return x1'; } > "$p/a.py"
expect "función >50 líneas falla" 1 "$p" "funciones"
p=$(newproj py-shell); echo 'import subprocess; subprocess.run(cmd, shell=True)' > "$p/a.py"; expect "shell=True falla" 1 "$p" "patrones-peligrosos"

[ "$failures" -eq 0 ] && echo "✅ Autotest del quality gate correcto" || { echo "$failures prueba(s) fallida(s)"; exit 1; }

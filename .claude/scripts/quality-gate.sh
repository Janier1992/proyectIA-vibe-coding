#!/bin/bash
# Quality gate agnóstico al stack: verifica calidad y seguridad de forma mecánica (sin juicio de LLM).
# Uso: bash .claude/scripts/quality-gate.sh [directorio-del-proyecto] [--out reporte.md]
# Salida: 0 = PASS | 1 = FAIL | 2 = UNVERIFIED (falta una herramienta; requiere revisión humana)
# Suprimir un falso positivo puntual: añade "gate-ignore: motivo" en la misma línea.

ROOT="."; OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    *) ROOT="$1"; shift ;;
  esac
done
OUT_ABS=""
[ -n "$OUT" ] && OUT_ABS="$(cd "$(dirname "$OUT")" 2>/dev/null && pwd)/$(basename "$OUT")"
cd "$ROOT" || { echo "Directorio inválido: $ROOT"; exit 1; }
# Reproducibilidad: si el proyecto tiene un entorno virtual, sus herramientas tienen prioridad
# (mypy y pytest deben vivir en el mismo entorno que las dependencias del proyecto).
for venv in .venv venv; do
  [ -d "$venv/bin" ] && { PATH="$PWD/$venv/bin:$PATH"; export PATH; break; }
done

MAX_FILE_LINES=500
MAX_FUNC_LINES=50
EXCLUDE_DIRS=(node_modules .git .claude .agents factory PRPs examples dist build .next .venv venv __pycache__ coverage)
EXCL_RE='(node_modules|\.git|\.claude|\.agents|factory|PRPs|examples|dist|build|\.next|\.venv|venv|__pycache__|coverage)'
EXCL_CSV=$(IFS=,; echo "${EXCLUDE_DIRS[*]}")
ROWS=()
add() { ROWS+=("$1|$2|$3"); }

# Lista archivos por extensión, sin directorios excluidos
find_files() {
  local names=() prune=() ext d
  for ext in "$@"; do names+=(-o -name "*.$ext"); done
  for d in "${EXCLUDE_DIRS[@]}"; do prune+=(-o -name "$d"); done
  find . -type d \( "${prune[@]:1}" \) -prune -o -type f \( "${names[@]:1}" \) -print | sed 's#^\./##'
}
has_files() { [ -n "$(find_files "$@" | head -n 1)" ]; }
is_test_file() { echo "$1" | grep -qE '\.(test|spec)\.|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)(tests?|__tests__)/'; }

# Ejecuta un comando y registra PASS/FAIL con las últimas líneas de salida
run_tool() {
  local id="$1" cmd="$2" log; log=$(mktemp)
  if bash -c "$cmd" >"$log" 2>&1; then add "$id" PASS "$cmd"
  else add "$id" FAIL "$cmd → $(tail -n 3 "$log" | tr '\n|' ' /' | cut -c1-220)"; fi
  rm -f "$log"
}
# Si la herramienta no está instalada el resultado es UNVERIFIED (nunca PASS por omisión)
need_tool() {
  if command -v "$2" >/dev/null 2>&1; then run_tool "$1" "$3"
  else add "$1" UNVERIFIED "Falta la herramienta '$2'"; fi
}

check_secrets() {
  if command -v gitleaks >/dev/null 2>&1; then run_tool secretos "gitleaks detect --no-git --source . --redact -q"; return; fi
  local pat="AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36}|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|(api[_-]?key|secret|passw(or)?d|token)[A-Za-z_]*[[:space:]]*[:=][[:space:]]*[\"'][^\"'\$ {}]{8,}[\"']"
  local excl=() d hits envs="" f
  for d in "${EXCLUDE_DIRS[@]}"; do excl+=(--exclude-dir="$d"); done
  hits=$(grep -rInE "$pat" . "${excl[@]}" --exclude='*.md' --exclude='*.lock' --exclude='package-lock.json' \
    --exclude='*.example' --exclude='*.test.*' --exclude='*.spec.*' --exclude='test_*.py' 2>/dev/null | grep -v 'gate-ignore' | head -n 3)
  while read -r f; do
    git rev-parse --git-dir >/dev/null 2>&1 && ! git ls-files --error-unmatch "$f" >/dev/null 2>&1 && continue
    envs="$envs $f"
  done < <(find . -type d \( -name node_modules -o -name .git \) -prune -o -type f \( -name '.env' -o -name '.env.*' \) ! -name '*.example' -print)
  if [ -n "$hits" ] || [ -n "$envs" ]; then
    add secretos FAIL "Posibles secretos: $(echo "$hits" | cut -d: -f1,2 | tr '\n' ' ')${envs:+ .env versionado:$envs}"
  else add secretos PASS "Sin secretos (regex integrado; instala gitleaks para mayor cobertura)"; fi
}

check_size() {
  local f big=""
  while read -r f; do
    [ "$(wc -l < "$f")" -gt "$MAX_FILE_LINES" ] && big="$big $f"
  done < <(find_files js jsx ts tsx mjs cjs py sh html css)
  if [ -z "$big" ]; then add tamano PASS "Todos los archivos ≤ $MAX_FILE_LINES líneas"
  else add tamano FAIL "Superan $MAX_FILE_LINES líneas:$big"; fi
}

# Límite de CLAUDE.md: funciones de Python con más de MAX_FUNC_LINES líneas (medido con ast)
check_func_size() {
  has_files py || return
  local py='
import ast, sys
limit = int(sys.argv[1])
for path in sys.argv[2:]:
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = node.end_lineno - node.lineno + 1
            if size > limit:
                print(f"{path}:{node.lineno} {node.name}({size})")
'
  local hits
  hits=$(find_files py | tr '\n' '\0' | xargs -0 python3 -c "$py" "$MAX_FUNC_LINES" | tr '\n' ' ')
  if [ -z "$hits" ]; then add funciones PASS "Funciones Python ≤ $MAX_FUNC_LINES líneas"
  else add funciones FAIL "Superan $MAX_FUNC_LINES líneas: $hits"; fi
}

check_patterns() {
  local js='\beval\(|new Function\(|\.innerHTML[[:space:]]*\+?=|\.outerHTML[[:space:]]*=|insertAdjacentHTML\(|document\.write\(|dangerouslySetInnerHTML|rejectUnauthorized:[[:space:]]*false'
  local py='\beval\(|\bexec\(|os\.system\(|shell=True|pickle\.loads?\(|verify=False'
  local f pat hit hits=""
  while read -r f; do
    is_test_file "$f" && continue
    case "$f" in *.py) pat="$py" ;; *) pat="$js" ;; esac
    hit=$(grep -nE "$pat" "$f" | grep -v 'gate-ignore' | head -n 1 | cut -d: -f1)
    [ -n "$hit" ] && hits="$hits $f:$hit"
  done < <(find_files js jsx ts tsx mjs cjs html py)
  if [ -z "$hits" ]; then add patrones-peligrosos PASS "Sin eval/innerHTML/shell=True/verify=False y similares"
  else add patrones-peligrosos FAIL "Patrones inseguros en:$hits"; fi
}

# --- Node / JavaScript / TypeScript ---
pkg_info() {
  node -e 'const p=require("./package.json"),s=p.scripts||{};
    const n=Object.keys(p.dependencies||{}).length+Object.keys(p.devDependencies||{}).length;
    console.log([s.test&&!/no test specified/.test(s.test)?1:0,s.lint?1:0,s.typecheck?1:0,n].join(" "))' 2>/dev/null
}
node_tests() {
  local tf; tf=$(find_files js mjs cjs | grep -E '\.(test|spec)\.|(^|/)(tests?|__tests__)/' | tr '\n' ' ')
  if [ "$1" = 1 ]; then run_tool tests-js "npm test --silent"
  elif [ -n "$tf" ]; then run_tool tests-js "node --test $tf"
  else add tests-js FAIL "Sin tests automatizados"; fi
}
node_types() {
  if [ -f tsconfig.json ]; then
    if [ "$1" = 1 ]; then run_tool tipos-ts "npm run typecheck --silent"; else run_tool tipos-ts "npx --no-install tsc --noEmit"; fi
  elif has_files ts tsx; then add tipos-ts UNVERIFIED "Hay TypeScript sin tsconfig.json"
  else add tipos-ts SKIP "JavaScript sin TypeScript"; fi
}
node_audit() {
  local log rc
  if [ "$1" = 0 ]; then add dependencias-js SKIP "Sin dependencias"; return; fi
  if [ ! -f package-lock.json ]; then
    if ls pnpm-lock.yaml yarn.lock >/dev/null 2>&1; then add dependencias-js UNVERIFIED "Audita con pnpm/yarn audit"
    else add dependencias-js FAIL "Dependencias sin lockfile (builds no reproducibles)"; fi
    return
  fi
  log=$(npm audit --audit-level=high 2>&1); rc=$?
  if [ $rc -eq 0 ]; then add dependencias-js PASS "npm audit sin vulnerabilidades high/critical"
  elif echo "$log" | grep -qiE 'ENOTFOUND|ECONNREFUSED|EAI_AGAIN|ETIMEDOUT|403|network|audit endpoint'; then
    add dependencias-js UNVERIFIED "npm audit sin acceso al registro"
  else add dependencias-js FAIL "npm audit: $(echo "$log" | grep -iE 'high|critical' | head -n 1 | tr '|' '/')"; fi
}
check_node() {
  has_files js jsx ts tsx mjs cjs || [ -f package.json ] || return
  local t=0 l=0 ty=0 n=0
  [ -f package.json ] && read -r t l ty n < <(pkg_info)
  node_tests "$t"
  if [ "$l" = 1 ]; then run_tool lint-js "npm run lint --silent"; else add lint-js UNVERIFIED "Sin script lint (configura ESLint o Biome)"; fi
  node_types "$ty"
  node_audit "$n"
}

# --- Python ---
check_python() {
  has_files py || return
  if has_files py && [ -n "$(find_files py | grep -E '(^|/)test_[^/]*\.py$|_test\.py$|(^|/)tests?/')" ]; then
    need_tool tests-py pytest "pytest -q"
  else add tests-py FAIL "Sin tests automatizados"; fi
  need_tool lint-py ruff "ruff check . --extend-exclude '$EXCL_CSV'"
  need_tool tipos-py mypy "mypy . --ignore-missing-imports --exclude '$EXCL_RE/'"
  need_tool sast-py bandit "bandit -q -r . -ll -x ./tests,$(echo "$EXCL_CSV" | sed 's#\([^,]*\)#./\1#g')"
  if [ -f requirements.txt ]; then need_tool dependencias-py pip-audit "pip-audit -r requirements.txt"
  elif [ -f pyproject.toml ]; then add dependencias-py UNVERIFIED "Audita las dependencias de pyproject.toml con pip-audit"
  else add dependencias-py SKIP "Sin manifiesto de dependencias"; fi
}

report() {
  local fails=0 unv=0 r id st det icon status code lines=""
  for r in "${ROWS[@]}"; do
    IFS='|' read -r id st det <<<"$r"
    case "$st" in PASS) icon="✅" ;; FAIL) icon="❌"; fails=$((fails + 1)) ;; UNVERIFIED) icon="⚠️"; unv=$((unv + 1)) ;; *) icon="➖" ;; esac
    lines="$lines| $id | $icon $st | $det |"$'\n'
  done
  if [ $fails -gt 0 ]; then status=FAIL; code=1; elif [ $unv -gt 0 ]; then status=UNVERIFIED; code=2; else status=PASS; code=0; fi
  local body="# Quality Gate"$'\n\n'"| Verificación | Estado | Detalle |"$'\n'"|---|---|---|"$'\n'"$lines"$'\n'
  body="$body**GATE: $status** (fallos: $fails, sin verificar: $unv)"$'\n\n'
  body="$body- PASS: verificado mecánicamente. FAIL: bloquea el avance. UNVERIFIED: falta herramienta; no permite aprobación automática."$'\n'
  echo "$body"
  [ -n "$OUT_ABS" ] && echo "$body" > "$OUT_ABS"
  exit $code
}

check_secrets; check_size; check_func_size; check_patterns; check_node; check_python
report

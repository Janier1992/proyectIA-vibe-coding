# Quality Gate

| Verificación | Estado | Detalle |
|---|---|---|
| secretos | ✅ PASS | Sin secretos (regex integrado; instala gitleaks para mayor cobertura) |
| tamano | ✅ PASS | Todos los archivos ≤ 500 líneas |
| patrones-peligrosos | ✅ PASS | Sin eval/innerHTML/shell=True/verify=False y similares |
| tests-py | ✅ PASS | pytest -q |
| lint-py | ✅ PASS | ruff check . --extend-exclude 'node_modules,.git,.claude,.agents,factory,PRPs,examples,dist,build,.next,.venv,venv,__pycache__,coverage' |
| tipos-py | ✅ PASS | mypy . --ignore-missing-imports --exclude '(node_modules|\.git|\.claude|\.agents|factory|PRPs|examples|dist|build|\.next|\.venv|venv|__pycache__|coverage)/' |
| sast-py | ✅ PASS | bandit -q -r . -ll -x ./tests,./node_modules,./.git,./.claude,./.agents,./factory,./PRPs,./examples,./dist,./build,./.next,./.venv,./venv,./__pycache__,./coverage |
| dependencias-py | ✅ PASS | pip-audit -r requirements.txt |

**GATE: PASS** (fallos: 0, sin verificar: 0)

- PASS: verificado mecánicamente. FAIL: bloquea el avance. UNVERIFIED: falta herramienta; no permite aprobación automática.


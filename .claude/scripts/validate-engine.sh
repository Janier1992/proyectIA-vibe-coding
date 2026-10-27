#!/bin/bash
# Valida la consistencia del motor agéntico (reglas, agentes, comandos, skills, Factory).
# Uso: bash .claude/scripts/validate-engine.sh   (desde la raíz del repositorio)

cd "$(dirname "$0")/../.." || exit 1
errors=0
fail() { echo "❌ $1"; errors=$((errors + 1)); }
ok() { echo "✅ $1"; }

# 1. Frontmatter con description en agentes, comandos y skills
for f in .claude/agents/*.md .claude/commands/*.md .claude/skills/*/SKILL.md; do
  [ "$(sed -n '1p' "$f")" = "---" ] || fail "$f: no empieza con frontmatter '---'"
  sed -n '2,8p' "$f" | grep -q "^description:" || fail "$f: falta 'description' en el frontmatter"
done
ok "Frontmatter de agentes, comandos y skills revisado"

# 2. Piezas del pipeline Factory: existen y /factory las referencia
for agent in spec-writer builder approver revisor-seguridad revisor-ux revisor-ui revisor-codigo gestor-documentacion; do
  [ -f ".claude/agents/$agent.md" ] || fail "Falta el agente $agent"
  grep -q "$agent" .claude/commands/factory.md || fail "factory.md no referencia al agente $agent"
done
for tpl in prp_base prp_frontend prp_backend_api prp_automatizacion; do
  [ -f ".claude/PRPs/templates/$tpl.md" ] || fail "Falta la plantilla $tpl.md"
done
ok "Agentes y plantillas del pipeline Factory presentes"

# 3. Rutas .claude/... mencionadas en la documentación y comandos existen
refs=$(grep -rhoE '\.claude/[A-Za-z0-9_./-]+\.(md|sh|json)' CLAUDE.md README.md .cursorrules .windsurfrules .agents/AGENTS.md .claude/commands .claude/agents 2>/dev/null | sort -u)
for ref in $refs; do [ -e "$ref" ] || fail "Ruta referenciada pero inexistente: $ref"; done
ok "Rutas .claude/ referenciadas existen"

# 4. Skills: fuente única (.agents/skills es symlink a .claude/skills)
[ "$(readlink .agents/skills)" = "../.claude/skills" ] || fail ".agents/skills debe ser symlink a ../.claude/skills"

# 5. Hook registrado y válido
python3 -c "import json; json.load(open('.claude/settings.json'))" 2>/dev/null || fail ".claude/settings.json no es JSON válido"
hook=$(grep -oE '\.claude/hooks/[A-Za-z0-9_.-]+\.sh' .claude/settings.json | head -n 1)
{ [ -n "$hook" ] && [ -x "$hook" ]; } || fail "El hook registrado no existe o no es ejecutable"
ok "Skills y hook consistentes"

# 6. Todos los archivos de reglas apuntan a CLAUDE.md y mencionan Factory
for f in .cursorrules .windsurfrules .agents/AGENTS.md; do
  grep -q "CLAUDE.md" "$f" || fail "$f no referencia CLAUDE.md"
  grep -qi "factory" "$f" || fail "$f no menciona la metodología Factory"
done
grep -q "/factory" CLAUDE.md || fail "CLAUDE.md no documenta /factory"

# 7. Límite de 500 líneas por archivo (excluye ejemplos)
while read -r f; do
  [ -f "$f" ] && [ "$(wc -l < "$f")" -gt 500 ] && fail "$f supera 500 líneas"
done < <(git ls-files | grep -v '^examples/')

# 8. El kit permanece genérico: carpetas de salida vacías y sin dependencias del ejemplo
for dir in PRPs factory; do
  extra=$(git ls-files "$dir" | grep -v '/\.gitkeep$')
  [ -z "$extra" ] || fail "$dir/ debe estar vacía en el kit (mueve los ejemplos a examples/): $extra"
done
grep -rnE "examples/[A-Za-z0-9]|calculadora-propinas" --exclude-dir=scripts .claude CLAUDE.md .cursorrules .windsurfrules .agents/AGENTS.md >/dev/null 2>&1 \
  && fail "El motor no debe depender del ejemplo (referencias a examples/ o calculadora-propinas)"
ok "Kit genérico: sin artefactos ni dependencias de ejemplos"

# 9. Los tests de los ejemplos siguen pasando (si hay Node)
if command -v node >/dev/null 2>&1; then
  for t in examples/*/app/; do
    ls "$t"*.test.js >/dev/null 2>&1 || continue
    node --test "$t"*.test.js >/dev/null 2>&1 || fail "Fallan los tests de $t"
  done
  ok "Tests de ejemplos revisados"
fi

[ "$errors" -eq 0 ] && echo "✅ Motor consistente" || { echo "$errors problema(s) encontrados"; exit 1; }

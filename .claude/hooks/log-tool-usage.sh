#!/bin/bash
# PostToolUse hook: registra el nombre de cada herramienta usada (log de auditoría)

input=$(cat)
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
toolName=$(echo "$input" | sed -n 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

mkdir -p .claude/logs
echo "[$timestamp] Tool used: ${toolName:-unknown}" >> .claude/logs/tool-usage.log

# Siempre retorna éxito para no bloquear herramientas
echo "{}"

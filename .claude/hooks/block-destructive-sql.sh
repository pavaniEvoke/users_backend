#!/usr/bin/env bash
# Evoke guardrail: block destructive SQL (PreToolUse / Bash).
payload="$(cat)"
# Pull the command out of the JSON payload; fall back to the raw payload.
cmd="$(printf '%s' "$payload" | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception:
    pass' 2>/dev/null)"
[ -z "$cmd" ] && cmd="$payload"

if printf '%s' "$cmd" | grep -Eiq 'drop[[:space:]]+(table|database|schema)|truncate[[:space:]]+(table[[:space:]]+)?[a-z0-9_."`\[]'; then
  echo "BLOCKED by Evoke guardrail (block-destructive-sql): DROP TABLE/DATABASE/SCHEMA and TRUNCATE are not permitted from the agent. Use a reviewed, reversible migration instead, or run it yourself against the right environment." >&2
  exit 2
fi
exit 0

#!/usr/bin/env bash
# Evoke guardrail: block force-push (PreToolUse / Bash).
payload="$(cat)"
# Pull the command out of the JSON payload; fall back to the raw payload.
cmd="$(printf '%s' "$payload" | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception:
    pass' 2>/dev/null)"
[ -z "$cmd" ] && cmd="$payload"

if printf '%s' "$cmd" | grep -Eiq 'git[[:space:]]+push' \
  && printf '%s' "$cmd" | grep -Eiq -- '--force([^-]|$)|(^|[[:space:]])-f([[:space:]]|$)' \
  && ! printf '%s' "$cmd" | grep -Eiq -- '--force-with-lease'; then
  echo "BLOCKED by Evoke guardrail (block-force-push): 'git push --force' is not permitted from the agent. Use '--force-with-lease' if you must rewrite, and confirm the branch is not shared." >&2
  exit 2
fi
exit 0

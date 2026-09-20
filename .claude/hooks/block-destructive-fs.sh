#!/usr/bin/env bash
# Evoke guardrail: block destructive filesystem deletions (PreToolUse / Bash).
# Exit 2 blocks the tool call and returns the message to the agent.
payload="$(cat)"
# Pull the command out of the JSON payload; fall back to the raw payload.
cmd="$(printf '%s' "$payload" | python3 -c 'import sys,json
try:
    print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception:
    pass' 2>/dev/null)"
[ -z "$cmd" ] && cmd="$payload"

if printf '%s' "$cmd" | grep -Eiq 'rm[[:space:]]+-[a-z]*r[a-z]*f|rm[[:space:]]+-[a-z]*f[a-z]*r|rm[[:space:]]+-r[[:space:]]+-f|rm[[:space:]]+-f[[:space:]]+-r|git[[:space:]]+clean[[:space:]]+-[a-z]*f[a-z]*d|find[[:space:]].*-delete'; then
  echo "BLOCKED by Evoke guardrail (block-destructive-fs): a recursive/force delete (e.g. 'rm -rf') is not permitted from the agent. If this is truly intended, run it yourself in a terminal." >&2
  exit 2
fi
exit 0

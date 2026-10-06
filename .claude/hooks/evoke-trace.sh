#!/usr/bin/env bash
# Evoke observability launcher. Never blocks. Never writes to stdout/stderr.
set -u
EVENT="${1:-tool:after}"
payload="$(cat)"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || pwd)}"
PY_CACHE="$ROOT/.agent/logs/.python"
PY=""; [ -r "$PY_CACHE" ] && PY="$(cat "$PY_CACHE" 2>/dev/null)"
if [ -z "$PY" ] || ! "$PY" -c "" >/dev/null 2>&1; then
  PY=""
  for c in "${EVOKE_TRACE_PYTHON:-}" python3 python py; do
    [ -z "$c" ] && continue
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "" >/dev/null 2>&1; then PY="$c"; break; fi
  done
  [ -n "$PY" ] && { mkdir -p "$ROOT/.agent/logs" 2>/dev/null; printf '%s' "$PY" >"$PY_CACHE" 2>/dev/null; }
fi
[ -z "$PY" ] && exit 0
printf '%s' "$payload" | "$PY" "$HERE/evoke_trace.py" "$EVENT" "$ROOT" >/dev/null 2>&1
exit 0

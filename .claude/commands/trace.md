---
description: Summarize local agent audit JSONL logs
---

Summarize the local Evoke audit trail for this repository.

1. Read `.agent/logs/kit-inventory.json` if present.
2. Read today's `.agent/logs/agent-audit-YYYY-MM-DD.jsonl` (and yesterday if thin).
3. Report:
   - Sessions started (timestamp + session_id)
   - Main-agent tool activity
   - Skills invoked
   - Hooks invoked
   - Sub-agents invoked
   - What each was doing (`doing` / redacted `input`)
4. Optionally run:
   `python .claude/hooks/kit_inventory.py .` (or the matching path under
   `.cursor/hooks/` / `.github/hooks/`) to refresh the inventory.

Do not delete or truncate log files.

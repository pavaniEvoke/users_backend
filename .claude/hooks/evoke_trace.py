#!/usr/bin/env python3
"""
Evoke kit observability core.

Non-blocking hook handler. Reads vendor hook JSON from stdin, appends a
redacted JSONL record to .agent/logs/agent-audit-YYYY-MM-DD.jsonl.

Usage (from hook launcher / PowerShell):
  python evoke_trace.py <event> [repo_root]

Semantic events (argv[1]):
  session:start | session:end | tool:after
  subagent:start | subagent:stop | hook:after

Never writes to stdout/stderr. Always exits 0.
Never logs tool output (secrets). Scrubbing is best-effort.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- limits (scrub before truncate so regex tokens are not split) ---
MAX_STR = 400
MAX_LINE = 8192
MAX_LIST = 20
MAX_DEPTH = 4
RETENTION_DAYS = 30

SIZE_KEYS = {
    "content",
    "new_string",
    "old_string",
    "new_str",
    "old_str",
    "edits",
    "patch",
    "prompt",
    "transcript",
}

SESSION_KEYS = ("session_id", "conversation_id", "thread_id", "sessionId", "threadId")
TOOL_KEYS = ("tool_name", "toolName", "tool")
INPUT_KEYS = ("tool_input", "toolInput", "input", "arguments")
OUTPUT_KEYS = ("tool_output", "toolOutput", "tool_response", "toolResponse", "output", "response")
STATUS_KEYS = ("status", "error", "is_error", "isError")
DURATION_KEYS = ("duration_ms", "duration", "durationMs", "elapsed_ms")
TOOL_USE_ID_KEYS = ("tool_use_id", "toolUseId", "id", "call_id", "callId")
ACTOR_KEYS = ("user_email", "userEmail", "actor", "user")
CWD_KEYS = ("cwd", "working_directory", "workingDirectory", "workspace_roots")
FILE_PATH_KEYS = (
    "file_path",
    "filePath",
    "target_file",
    "targetFile",
    "path",
    "file",
    "filename",
    "file_name",
    "fileName",
    "notebook_path",
    "notebookPath",
    "uri",
)
PERM_KEYS = ("permission_mode", "permissionMode", "permission")
SOURCE_KEYS = ("source", "trigger", "reason")
AGENT_ID_KEYS = ("agent_id", "agentId", "subagent_id", "subagentId")
SUBAGENT_TYPE_KEYS = ("subagent_type", "subagentType", "agent", "agent_type", "agentType")

# Tool-name heuristics → activity class
AGENT_TOOLS = {"agent", "task", "tasktool", "dispatch_agent", "run_agent"}
SKILL_TOOLS = {"skill", "skills", "slashcommand", "slash_command", "run_skill", "invoke_skill"}
HOOK_TOOLS = {"hook", "hooks", "run_hook"}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|"
               r"xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    re.compile(r"://[^/\s:@]+:[^/\s@]+@"),
    re.compile(r"(?i)\b(key|token|secret|password|passwd|api[_-]?key)\s*[:=]\s*\S+"),
]
OPAQUE_TOKEN = re.compile(r"[A-Za-z0-9+/=_-]{32,}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "+00:00")


def first(payload: dict, keys: tuple[str, ...], default: Any = None) -> Any:
    for k in keys:
        v = payload.get(k)
        if v not in (None, ""):
            return v
    return default


def looks_secret(token: str) -> bool:
    has_upper = any(c.isupper() for c in token)
    has_lower = any(c.islower() for c in token)
    has_digit = any(c.isdigit() for c in token)
    if has_upper and has_lower and has_digit:
        return True
    return any(c in token for c in "+/=")


def collect_env_secrets() -> list[str]:
    out: list[str] = []
    for name, val in os.environ.items():
        if not val or len(val) < 8:
            continue
        n = name.upper()
        if any(x in n for x in ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "AUTH")):
            out.append(val)
    return out


def scrub_text(text: str, env_secrets: list[str] | None = None) -> str:
    if not isinstance(text, str) or not text:
        return text
    s = text
    for pat in SECRET_PATTERNS:
        s = pat.sub("[REDACTED]", s)
    for val in env_secrets or []:
        if val in s:
            s = s.replace(val, "[REDACTED]")
    def _opaque(m: re.Match[str]) -> str:
        tok = m.group(0)
        return "[REDACTED]" if looks_secret(tok) else tok
    s = OPAQUE_TOKEN.sub(_opaque, s)
    return s


def redact(value: Any, depth: int = 0, env_secrets: list[str] | None = None, key: str | None = None) -> Any:
    if depth > MAX_DEPTH:
        return {"_omitted": "max_depth"}
    if isinstance(value, str):
        s = scrub_text(value, env_secrets)
        if key and key.lower() in SIZE_KEYS and len(s) > MAX_STR:
            return s[:MAX_STR] + f"…[+{len(s) - MAX_STR} chars]"
        if len(s) > MAX_STR * 4:
            return s[: MAX_STR * 4] + f"…[+{len(s) - MAX_STR * 4} chars]"
        return s
    if isinstance(value, list):
        items = [redact(v, depth + 1, env_secrets) for v in value[:MAX_LIST]]
        if len(value) > MAX_LIST:
            items.append({"_omitted": f"{len(value) - MAX_LIST} more items"})
        return items
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            # Never persist tool output blobs
            if k in OUTPUT_KEYS or k in {"transcript_path", "transcriptPath", "transcript"}:
                continue
            out[str(k)] = redact(v, depth + 1, env_secrets, key=str(k))
        return out
    return value


def detect_provider(payload: dict) -> str:
    # Heuristics — vendors disagree on field names
    if "tool_response" in payload or "hook_event_name" in payload:
        return "claude-code"
    if "tool_output" in payload or "user_email" in payload or "conversation_id" in payload:
        return "cursor"
    if "timeoutSec" in payload:
        return "copilot"
    cwd = str(first(payload, CWD_KEYS, "") or "")
    if "\\" in cwd and "claude" in cwd.lower():
        return "claude-code"
    return "unknown"


def extract_file_refs(tool_input: Any, cwd: str | None = None) -> dict[str, Any]:
    """Pull file path + basename from common tool input shapes (Read/Edit/Write/…)."""
    paths: list[str] = []

    def add(raw: Any) -> None:
        if raw is None:
            return
        if isinstance(raw, list):
            for item in raw:
                add(item)
            return
        if isinstance(raw, dict):
            nested = first(raw, FILE_PATH_KEYS, None)
            if nested:
                add(nested)
            return
        s = str(raw).strip()
        if not s or s.startswith("{") or len(s) > 1024:
            return
        # Skip obvious non-paths (shell commands without path separators / extension)
        if "\n" in s:
            return
        paths.append(s)

    if isinstance(tool_input, dict):
        add(first(tool_input, FILE_PATH_KEYS, None))
        # Multi-file edits: edits[].path / files[]
        for key in ("edits", "files", "paths", "file_paths", "filePaths"):
            block = tool_input.get(key)
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        add(first(item, FILE_PATH_KEYS, None))
                    else:
                        add(item)
            elif isinstance(block, dict):
                add(first(block, FILE_PATH_KEYS, None))
        # Notebook / afterFileEdit style
        for key in ("old_path", "oldPath", "new_path", "newPath"):
            if tool_input.get(key):
                add(tool_input.get(key))

    # Dedupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if not uniq:
        return {}

    primary = uniq[0]
    try:
        name = Path(primary).name
    except Exception:
        name = primary.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    out: dict[str, Any] = {
        "file_path": primary,
        "file_name": name,
    }
    if len(uniq) > 1:
        out["file_paths"] = uniq[:20]
        out["file_names"] = [Path(p).name for p in uniq[:20]]
    return out


def classify_activity(tool: str | None, tool_input: Any) -> dict[str, Any]:
    """Map a tool call to main / skill / subagent / hook activity."""
    name = (tool or "").strip()
    low = name.lower().replace("-", "_").replace(" ", "_")
    inp = tool_input if isinstance(tool_input, dict) else {}

    activity = "tool"
    agent_type = "main"
    agent_id = None
    skill_id = None
    hook_id = None
    doing = None

    if low in AGENT_TOOLS or low.endswith("_agent") or name == "Agent":
        activity = "subagent_invoked"
        agent_type = "subagent"
        agent_id = first(inp, SUBAGENT_TYPE_KEYS) or first(inp, AGENT_ID_KEYS)
        doing = first(inp, ("description", "prompt", "task", "goal"), None)
        if isinstance(doing, str) and len(doing) > MAX_STR:
            doing = doing[:MAX_STR] + "…"
    elif low in SKILL_TOOLS or "skill" in low:
        activity = "skill_invoked"
        skill_id = (
            first(inp, ("skill", "skill_name", "skillName", "name", "command", "id"))
            or name
        )
        doing = first(inp, ("description", "prompt", "args", "arguments", "query"), None)
        if isinstance(doing, str) and len(doing) > MAX_STR:
            doing = doing[:MAX_STR] + "…"
    elif low in HOOK_TOOLS or "hook" in low:
        activity = "hook_invoked"
        hook_id = first(inp, ("hook", "hook_name", "hookName", "name", "id")) or name
        doing = first(inp, ("description", "event", "matcher"), None)
    else:
        activity = "main_agent_tool"
        agent_type = "main"
        doing = first(inp, ("description", "command", "file_path", "path", "pattern"), None)
        if doing is None and isinstance(inp, dict) and inp:
            # compact one-line summary of keys
            doing = "keys:" + ",".join(list(inp.keys())[:8])

    files = extract_file_refs(inp)
    return {
        "activity": activity,
        "agent_type": agent_type,
        "agent_id": agent_id,
        "skill_id": skill_id,
        "hook_id": hook_id,
        "doing": doing,
        **files,
    }


def git_info(root: Path) -> dict[str, str] | None:
    try:
        def run(args: list[str]) -> str:
            p = subprocess.run(
                args,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            return (p.stdout or "").strip()

        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        head = run(["git", "rev-parse", "--short", "HEAD"])
        if not branch and not head:
            return None
        out: dict[str, str] = {}
        if branch:
            out["branch"] = branch
        if head:
            out["head"] = head
        return out or None
    except Exception:
        return None


def resolve_root(argv_root: str | None) -> Path:
    if argv_root:
        return Path(argv_root).resolve()
    env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("EVOKE_KIT_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    try:
        p = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if p.returncode == 0 and p.stdout.strip():
            return Path(p.stdout.strip()).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


def log_path(root: Path) -> Path:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    d = root / ".agent" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"agent-audit-{day}.jsonl"


def refresh_kit_inventory(root: Path) -> dict[str, Any] | None:
    """Re-scan .claude/.cursor/.github skills, hooks, rules, instructions."""
    try:
        inv_path = Path(__file__).resolve().parent / "kit_inventory.py"
        if inv_path.is_file():
            subprocess.run(
                [sys.executable, str(inv_path), str(root)],
                capture_output=True,
                timeout=8,
                check=False,
            )
    except Exception:
        pass
    return load_kit_inventory(root)


def load_kit_inventory(root: Path) -> dict[str, Any] | None:
    inv = root / ".agent" / "logs" / "kit-inventory.json"
    if not inv.is_file():
        return None
    try:
        return json.loads(inv.read_text(encoding="utf-8"))
    except Exception:
        return None


def tool_status(payload: dict) -> tuple[str, str | None]:
    err = first(payload, ("error", "error_message", "errorMessage"), None)
    if err:
        msg = scrub_text(str(err), collect_env_secrets())
        if len(msg) > 200:
            msg = msg[:200] + "…"
        return "error", msg
    st = first(payload, STATUS_KEYS, None)
    if isinstance(st, bool):
        return ("error" if st else "ok"), None
    if isinstance(st, str) and st.lower() in {"error", "failed", "fail"}:
        return "error", None
    # Presence of tool output without explicit error → ok; we still do not store it
    return "ok", None


def duration_ms(payload: dict) -> int | None:
    raw = first(payload, DURATION_KEYS, None)
    if raw is None:
        return None
    try:
        v = float(raw)
        # Cursor may send seconds; treat small floats as ms if large, else ms if already int-like
        if v < 1000 and isinstance(raw, float) and not float(raw).is_integer():
            return int(v * 1000)
        return int(v)
    except Exception:
        return None


def build_record(event: str, payload: dict, root: Path) -> dict[str, Any]:
    env_secrets = collect_env_secrets()
    provider = detect_provider(payload)
    session_id = first(payload, SESSION_KEYS)
    cwd = first(payload, CWD_KEYS)
    if isinstance(cwd, list):
        cwd = cwd[0] if cwd else None

    # Normalize semantic event → record event name
    semantic = event.strip().lower()
    event_map = {
        "session:start": "session_start",
        "sessionstart": "session_start",
        "session:end": "session_end",
        "sessionend": "session_end",
        "tool:after": "PostToolUse",
        "posttooluse": "PostToolUse",
        "subagent:start": "subagent_start",
        "subagentstart": "subagent_start",
        "subagent:stop": "subagent_stop",
        "subagentstop": "subagent_stop",
        "hook:after": "hook_invoked",
        "pretooluse": "PreToolUse",
    }
    rec_event = event_map.get(semantic, semantic)

    record: dict[str, Any] = {
        "v": 1,
        "timestamp": _now_iso(),
        "session_id": session_id,
        "agent_type": "main",
        "agent_id": first(payload, AGENT_ID_KEYS),
        "event": rec_event,
        "tool_provider": provider,
    }

    actor = first(payload, ACTOR_KEYS)
    if actor:
        record["actor"] = scrub_text(str(actor), env_secrets)

    perm = first(payload, PERM_KEYS)
    if perm:
        record["permission_mode"] = perm

    if rec_event in {"session_start", "session_end"}:
        record["cwd"] = str(cwd or root)
        record["source"] = first(payload, SOURCE_KEYS)
        gi = git_info(root)
        if gi:
            record["git"] = gi
        if rec_event == "session_start":
            record["retention_days"] = RETENTION_DAYS
            record["activity"] = "session_started"
            record["doing"] = "Session started"
            inv = refresh_kit_inventory(root) or load_kit_inventory(root)
            if inv:
                summary = inv.get("summary") or {}
                record["kit"] = {
                    "skills_count": summary.get("skills_count", len(inv.get("skills") or [])),
                    "hooks_count": summary.get("hooks_count", len(inv.get("hooks") or [])),
                    "rules_count": summary.get("rules_count", len(inv.get("rules") or [])),
                    "instructions_count": summary.get(
                        "instructions_count", len(inv.get("instructions") or [])
                    ),
                    "skills": summary.get("skill_ids")
                    or [s.get("id") or s.get("name") for s in (inv.get("skills") or [])][:50],
                    "hooks": summary.get("hook_ids")
                    or [h.get("id") or h.get("name") for h in (inv.get("hooks") or [])][:50],
                    "rules": summary.get("rule_ids")
                    or [r.get("id") or r.get("name") for r in (inv.get("rules") or [])][:50],
                    "instructions": summary.get("instruction_ids")
                    or [
                        i.get("id") or i.get("name") for i in (inv.get("instructions") or [])
                    ][:50],
                }
        else:
            record["activity"] = "session_ended"
            record["doing"] = first(payload, SOURCE_KEYS, "Session ended")
            dms = duration_ms(payload)
            if dms is not None:
                record["duration_ms"] = dms
        return {k: v for k, v in record.items() if v is not None}

    if rec_event in {"subagent_start", "subagent_stop"}:
        sub_type = first(payload, SUBAGENT_TYPE_KEYS) or first(payload, AGENT_ID_KEYS)
        record["agent_type"] = "subagent"
        record["agent_id"] = sub_type
        record["activity"] = "subagent_invoked" if rec_event == "subagent_start" else "subagent_stopped"
        record["doing"] = first(payload, ("description", "prompt", "reason", "task"), None)
        record["cwd"] = str(cwd) if cwd else None
        inp = first(payload, INPUT_KEYS, {})
        if isinstance(inp, dict) and inp:
            record["input"] = redact(inp, env_secrets=env_secrets)
        return {k: v for k, v in record.items() if v is not None}

    if rec_event == "hook_invoked" or semantic == "hook:after":
        record["activity"] = "hook_invoked"
        record["agent_type"] = "hook"
        record["hook_id"] = first(payload, ("hook", "hook_name", "hookName", "name", "matcher"), "unknown")
        record["doing"] = first(payload, ("description", "event", "verdict"), "Hook ran")
        record["cwd"] = str(cwd) if cwd else None
        return {k: v for k, v in record.items() if v is not None}

    # tool:after / PostToolUse / PreToolUse
    tool = first(payload, TOOL_KEYS)
    tool_input = first(payload, INPUT_KEYS, {})
    tool_use_id = first(payload, TOOL_USE_ID_KEYS)
    status, err_msg = tool_status(payload)

    cls = classify_activity(str(tool) if tool else None, tool_input)
    record.update(
        {
            "tool": tool,
            "tool_use_id": tool_use_id,
            "status": status,
            "activity": cls["activity"],
            "agent_type": cls["agent_type"],
            "agent_id": cls["agent_id"] or record.get("agent_id"),
            "skill_id": cls["skill_id"],
            "hook_id": cls["hook_id"],
            "doing": cls["doing"],
        }
    )
    if cwd:
        record["cwd"] = str(cwd)
    # File touched by this tool (alongside cwd)
    if cls.get("file_path"):
        record["file_path"] = cls["file_path"]
    if cls.get("file_name"):
        record["file_name"] = cls["file_name"]
    if cls.get("file_paths"):
        record["file_paths"] = cls["file_paths"]
    if cls.get("file_names"):
        record["file_names"] = cls["file_names"]
    # Also probe top-level payload (some vendors put path outside tool_input)
    if "file_name" not in record:
        top_files = extract_file_refs(payload, str(cwd) if cwd else None)
        record.update(top_files)
    if err_msg:
        record["error"] = err_msg
    dms = duration_ms(payload)
    if dms is not None:
        record["duration_ms"] = dms
    if isinstance(tool_input, (dict, list, str)):
        record["input"] = redact(tool_input, env_secrets=env_secrets)

    # Help fix adapters when vendor payload is unknown
    if tool is None and not isinstance(tool_input, dict):
        record["_unmapped"] = sorted(payload.keys())

    # Drop null decorative keys
    return {k: v for k, v in record.items() if v is not None}


def append_record(root: Path, record: dict[str, Any]) -> None:
    path = log_path(root)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    if len(line.encode("utf-8")) > MAX_LINE:
        slim = dict(record)
        if "input" in slim:
            slim["input"] = {"_omitted": f"record exceeded {MAX_LINE} bytes"}
        line = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
        if len(line.encode("utf-8")) > MAX_LINE:
            slim = {
                "v": 1,
                "timestamp": record.get("timestamp"),
                "session_id": record.get("session_id"),
                "event": record.get("event"),
                "activity": record.get("activity"),
                "input": {"_omitted": f"record exceeded {MAX_LINE} bytes"},
            }
            line = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def read_stdin_payload() -> dict:
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"_payload": data}
    except Exception:
        return {"_raw": scrub_text(raw[:2000], collect_env_secrets())}


def main(argv: list[str]) -> int:
    try:
        event = argv[1] if len(argv) > 1 else "tool:after"
        root = resolve_root(argv[2] if len(argv) > 2 else None)
        payload = read_stdin_payload()
        record = build_record(event, payload, root)
        append_record(root, record)
    except Exception:
        # Never break the session
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

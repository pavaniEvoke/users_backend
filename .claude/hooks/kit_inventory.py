#!/usr/bin/env python3
"""
Scan a generated kit under .claude/ / .cursor/ / .github/ and write
.agent/logs/kit-inventory.json listing skills, hooks, rules, instructions,
agents, and commands. Used by evoke_trace on session:start and by /trace.

Usage:
  python kit_inventory.py [repo_root]
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_text(path: Path, limit: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _frontmatter(text: str, fallback: str) -> dict[str, Any]:
    meta: dict[str, Any] = {"id": fallback, "name": fallback}
    if not text.startswith("---"):
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            meta["name"] = m.group(1).strip()
        return meta
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text[3:500]
    for key in ("name", "id", "description", "title"):
        m = re.search(rf"(?m)^{key}\s*:\s*(.+)$", block)
        if m:
            val = m.group(1).strip().strip("\"'")
            meta[key if key != "title" else "name"] = val
            if key in {"name", "id"}:
                meta["id"] = val
    return meta


def discover_skills(root: Path) -> list[dict[str, Any]]:
    """Pick skills from .claude/skills, .cursor/skills, .github/skills."""
    found: dict[str, dict[str, Any]] = {}
    # Primary kit layout the user expects
    globs = [
        ".claude/skills/*/SKILL.md",
        ".claude/skills/**/*.md",
        ".cursor/skills/*/SKILL.md",
        ".cursor/skills/**/*.md",
        ".github/skills/*/SKILL.md",
        ".github/skills/**/*.md",
        # Cursor legacy rule-form skills
        ".cursor/rules/skill-*.mdc",
    ]
    for pattern in globs:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            parts = Path(rel).parts
            skill_key = path.stem
            if "skills" in parts:
                idx = parts.index("skills")
                if idx + 1 < len(parts):
                    skill_key = Path(parts[idx + 1]).stem
            elif skill_key.startswith("skill-"):
                skill_key = skill_key[len("skill-") :]
            text = _read_text(path)
            meta = _frontmatter(text, skill_key)
            sid = Path(str(meta.get("id") or skill_key)).stem
            entry = {
                "id": sid,
                "name": meta.get("name") or sid,
                "path": rel,
                "kind": "skill",
                "root": parts[0] if parts else "",
            }
            if meta.get("description"):
                entry["description"] = meta["description"]
            prev = found.get(sid)
            # Prefer */skills/*/SKILL.md over rule mirrors
            prefer = path.name.upper() == "SKILL.MD" and "skills" in parts
            if prev is None or prefer:
                found[sid] = entry
    return sorted(found.values(), key=lambda x: x["id"])


def _hooks_from_settings(path: Path, root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        data = json.loads(_read_text(path, 200000) or "{}")
    except Exception:
        return out
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return out
    rel_cfg = path.relative_to(root).as_posix()
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            nested = entry.get("hooks")
            if isinstance(nested, list):
                for j, h in enumerate(nested):
                    if not isinstance(h, dict):
                        continue
                    cmd = h.get("command") or h.get("bash") or h.get("powershell")
                    out.append(
                        {
                            "id": f"{event}:{entry.get('matcher', '*')}:{j}",
                            "name": Path(str(cmd or "hook")).name,
                            "event": event,
                            "matcher": entry.get("matcher"),
                            "command": cmd,
                            "kind": "observability" if "evoke" in str(h).lower() else "hook",
                            "config": rel_cfg,
                        }
                    )
            else:
                cmd = entry.get("command") or entry.get("bash") or entry.get("powershell")
                out.append(
                    {
                        "id": f"{event}:{i}",
                        "name": Path(str(cmd or "hook")).name,
                        "event": event,
                        "command": cmd,
                        "kind": "observability" if "evoke" in str(entry).lower() else "hook",
                        "config": rel_cfg,
                    }
                )
    return out


def discover_hooks(root: Path) -> list[dict[str, Any]]:
    """Pick hooks from .claude/hooks, .cursor/hooks, .github/hooks (+ configs)."""
    found: list[dict[str, Any]] = []
    for cfg in (root / ".claude" / "settings.json", root / ".cursor" / "hooks.json"):
        if cfg.is_file():
            found.extend(_hooks_from_settings(cfg, root))
    gh = root / ".github" / "hooks"
    if gh.is_dir():
        for path in sorted(gh.glob("*.json")):
            found.extend(_hooks_from_settings(path, root))
    # Script files under the three provider hook dirs
    for pattern in (
        ".claude/hooks/*",
        ".cursor/hooks/*",
        ".github/hooks/*",
        "guardrails/*",
    ):
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".sh", ".ps1", ".js"}:
                continue
            rel = path.relative_to(root).as_posix()
            hid = path.stem
            if any(h.get("name") == path.name or hid in str(h.get("id")) for h in found):
                continue
            root_name = Path(rel).parts[0] if Path(rel).parts else ""
            found.append(
                {
                    "id": hid,
                    "name": path.name,
                    "path": rel,
                    "kind": "observability" if "evoke" in path.name.lower() or "kit_inventory" in path.name else "script",
                    "event": None,
                    "root": root_name,
                }
            )
    return found


def discover_rules(root: Path) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for pattern in (
        ".cursor/rules/*.mdc",
        ".cursor/rules/*.md",
        ".github/instructions/*.md",
        ".claude/guidelines/*.md",
        ".github/guidelines/*.md",
    ):
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            # skip skill-/agent- prefixed cursor rules (tracked elsewhere)
            stem = path.stem
            if stem.startswith("skill-") or stem.startswith("agent-") or stem.startswith("org-"):
                continue
            rel = path.relative_to(root).as_posix()
            text = _read_text(path)
            meta = _frontmatter(text, stem)
            rid = Path(str(meta.get("id") or stem)).stem
            found[rid] = {
                "id": rid,
                "name": meta.get("name") or rid,
                "path": rel,
                "kind": "rule",
            }
    return sorted(found.values(), key=lambda x: x["id"])


def discover_instructions(root: Path) -> list[dict[str, Any]]:
    """Top-level instruction / working-agreement files."""
    candidates = [
        "CLAUDE.md",
        "AGENTS.md",
        ".github/copilot-instructions.md",
        ".claude/README.md",
        ".cursor/README.md",
        ".github/README.md",
    ]
    out: list[dict[str, Any]] = []
    for rel in candidates:
        path = root / rel
        if not path.is_file():
            continue
        text = _read_text(path, 2000)
        name = path.name
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            name = m.group(1).strip()
        out.append({"id": Path(rel).stem, "name": name, "path": rel, "kind": "instruction"})
    return out


def discover_agents(root: Path) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for pattern in (
        ".claude/agents/*.md",
        ".github/agents/*.md",
        ".github/agents/*.agent.md",
        ".cursor/rules/agent-*.mdc",
    ):
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            stem = path.stem.replace(".agent", "")
            if stem.startswith("agent-"):
                stem = stem[len("agent-") :]
            rel = path.relative_to(root).as_posix()
            text = _read_text(path)
            meta = _frontmatter(text, stem)
            aid = Path(str(meta.get("id") or stem)).stem
            found[aid] = {
                "id": aid,
                "name": meta.get("name") or aid,
                "path": rel,
                "kind": "agent",
            }
    return sorted(found.values(), key=lambda x: x["id"])


def discover_commands(root: Path) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for pattern in (
        ".claude/commands/*.md",
        ".cursor/commands/*.md",
        ".github/prompts/*.md",
        ".github/prompts/*.prompt.md",
    ):
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            stem = path.stem.replace(".prompt", "")
            rel = path.relative_to(root).as_posix()
            text = _read_text(path)
            meta = _frontmatter(text, stem)
            cid = Path(str(meta.get("id") or stem)).stem
            found[cid] = {
                "id": cid,
                "name": meta.get("name") or cid,
                "path": rel,
                "kind": "command",
            }
    return sorted(found.values(), key=lambda x: x["id"])


def build_inventory(root: Path) -> dict[str, Any]:
    skills = discover_skills(root)
    hooks = discover_hooks(root)
    rules = discover_rules(root)
    instructions = discover_instructions(root)
    agents = discover_agents(root)
    commands = discover_commands(root)
    return {
        "v": 1,
        "generated_at": _now(),
        "root": str(root),
        "skills": skills,
        "hooks": hooks,
        "rules": rules,
        "instructions": instructions,
        "agents": agents,
        "commands": commands,
        "summary": {
            "skills_count": len(skills),
            "hooks_count": len(hooks),
            "rules_count": len(rules),
            "instructions_count": len(instructions),
            "agents_count": len(agents),
            "commands_count": len(commands),
            "skill_ids": [s["id"] for s in skills],
            "hook_ids": [h["id"] for h in hooks],
            "rule_ids": [r["id"] for r in rules],
            "instruction_ids": [i["id"] for i in instructions],
            "agent_ids": [a["id"] for a in agents],
            "command_ids": [c["id"] for c in commands],
        },
    }


def write_inventory(root: Path, also_audit: bool = True) -> Path:
    inv = build_inventory(root)
    out_dir = root / ".agent" / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "kit-inventory.json"
    out.write_text(json.dumps(inv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if also_audit:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit = out_dir / f"agent-audit-{day}.jsonl"
        lines: list[str] = []
        lines.append(
            json.dumps(
                {
                    "v": 1,
                    "timestamp": _now(),
                    "agent_type": "system",
                    "agent_id": "kit_inventory",
                    "event": "kit_inventory",
                    "activity": "kit_scanned",
                    "doing": (
                        f"Indexed {inv['summary']['skills_count']} skills, "
                        f"{inv['summary']['hooks_count']} hooks from "
                        ".claude/ .cursor/ .github/"
                    ),
                    "kit": inv["summary"],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        # One log line per skill and hook present on disk
        for s in inv.get("skills") or []:
            lines.append(
                json.dumps(
                    {
                        "v": 1,
                        "timestamp": _now(),
                        "agent_type": "skill",
                        "agent_id": s.get("id"),
                        "skill_id": s.get("id"),
                        "event": "kit_asset",
                        "activity": "skill_registered",
                        "doing": f"Skill present: {s.get('name')}",
                        "status": "ok",
                        "input": {"path": s.get("path"), "kind": "skill"},
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        for h in inv.get("hooks") or []:
            lines.append(
                json.dumps(
                    {
                        "v": 1,
                        "timestamp": _now(),
                        "agent_type": "hook",
                        "agent_id": h.get("id"),
                        "hook_id": h.get("id"),
                        "event": "kit_asset",
                        "activity": "hook_registered",
                        "doing": f"Hook present: {h.get('name')}",
                        "status": "ok",
                        "input": {
                            "path": h.get("path") or h.get("config"),
                            "kind": h.get("kind"),
                            "event": h.get("event"),
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        with audit.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
    return out


def resolve_root(arg: str | None) -> Path:
    if arg:
        return Path(arg).resolve()
    env = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("EVOKE_KIT_ROOT")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def main(argv: list[str]) -> int:
    root = resolve_root(argv[1] if len(argv) > 1 else None)
    path = write_inventory(root)
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

---
description: Resume the iterative execution loop: read the durable plan, pick up from its first open task, and keep going until the plan is empty and archived.
allowed-tools: Bash(cat:*), Bash(ls:*)
---
# /continue

Resume in-progress work from the durable plan instead of starting over. Use this
after a break, a restart, or a fresh session.

First, load the state:
- Read `.agent/plan.md`. If it doesn't exist, there's nothing to resume — say so
  and offer to start a new plan (delegate to the `orchestrator` agent if it's
  installed, otherwise run the iterative execution loop yourself).
- List `.agent/progress/` and read the most recent notes to recover the context
  of what's already done. Trust these notes — do NOT redo a task that has one.
  (`.agent/plan.md` lists only what is still open: finished tasks are removed
  from it as they complete, and finished plans are archived under
  `.agent/completed/`.)

Then resume the loop:
1. Restate the goal and report progress: what `.agent/progress/` shows as done,
   what is still open in the plan, and which task is next.
2. Pick the **first task** in `.agent/plan.md`.
3. Execute it (route a build-a-feature task through the `spec-driven-builder`
   skill; delegate to the right specialist where appropriate).
4. Validate, then write `.agent/progress/NN-<task>.md`, **remove that task's line
   from** `.agent/plan.md`, and update the "current state" section.
5. Continue until `.agent/plan.md` has no tasks left, then move it to
   `.agent/completed/YYYY-MM-DD-<goal-slug>.md` with a one-line outcome summary
   and leave a fresh, empty plan file behind.

Rules: one task at a time, record intermediate outputs before moving on, and never
skip a governance hook or failing check to make progress — surface the blocker in
`.agent/plan.md` and stop.

---
name: AI usage & accountability
description: A named human owns and is accountable for every AI-assisted change; disclose AI use and never bypass a hard guardrail.
---
## Evoke Technologies — AI usage & accountability

- Every AI-generated change is owned by a named human author who is
  accountable for it reaching a protected branch. AI assistance never removes
  human accountability.
- Disclose AI-assisted changes in the PR description (what the agent did, what
  the human verified).
- Treat hard guardrails (secrets, protected-branch merges, production/PII data)
  as non-negotiable. Never weaken or bypass a governance check to make progress —
  surface the blocker instead.
- Waivers to a hard guardrail require a named human approver, are time-bound,
  and are logged. An agent may never grant its own waiver.

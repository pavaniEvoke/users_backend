---
name: Separation of duties
description: The actor that writes a change never approves it; a human verifies before commit and independent review sits before merge.
---
## Evoke Technologies — Separation of duties

- The agent that writes a change never approves it. Generation and validation
  are distinct steps performed by distinct actors.
- A human verifies the change (runs it, exercises new endpoints/tests) before
  it is committed. Do not self-certify and commit.
- Independent review (a validator agent and/or a human reviewer) sits between
  "implemented" and "merged" for every non-trivial change.

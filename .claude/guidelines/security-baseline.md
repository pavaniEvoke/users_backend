---
name: Security policy baseline
description: No committed secrets, parameterized queries, least privilege, and mandatory secret/dependency scanning before merge (OWASP ASVS).
---
## Evoke Technologies — Security policy baseline

- Never commit secrets, tokens, or credentials. Read them from environment
  variables or the organization's secret manager.
- Validate and sanitize all input at system boundaries; use parameterized
  queries. Never build SQL by string concatenation.
- Apply least privilege for every credential, connector, and service account.
  A capability not explicitly granted is denied.
- New and changed code must pass secret scanning and dependency vulnerability
  checks before merge. Do not introduce dependencies with known criticals.
- Follow OWASP ASVS for authentication, session management, and access control.

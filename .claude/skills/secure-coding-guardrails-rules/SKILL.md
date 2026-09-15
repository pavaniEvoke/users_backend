---
name: secure-coding-guardrails-rules
description: Secure-by-default rules applied while generating code: parameterized queries, authz checks, no secrets, safe file/URL handling. Read before writing or editing **/*.
---
## Secure-coding guardrails (apply by default)

- Never build SQL/NoSQL/shell/LDAP strings by concatenation. Use parameterized
  queries / prepared statements / safe APIs.
- Validate and type all external input at the boundary; allowlist, don't blocklist.
- Encode on output. Never inject user data into HTML via innerHTML /
  dangerouslySetInnerHTML.
- Every state-changing or data-returning endpoint gets an explicit authorization
  check, and an ownership check on object access (prevent IDOR). If the rule is
  unknown, scaffold a clearly-marked TODO(authz) and say so — never ship an open
  endpoint silently.
- Never hardcode secrets, keys, tokens, or connection strings; read from env / a
  secret manager. Never log secrets or PII.
- File uploads: validate type & size, store outside web root, generate
  server-side names (no path traversal). Allowlist hosts for server-side fetches
  (SSRF). Never deserialize untrusted data into objects with side effects.
- Hash passwords with bcrypt/argon2/scrypt — never MD5/SHA1 or plaintext.

If a request inherently requires an unsafe choice, STOP, explain the risk in one
or two sentences, offer the secure alternative, and ask before proceeding.

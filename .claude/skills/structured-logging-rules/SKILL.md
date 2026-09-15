---
name: structured-logging-rules
description: Org standard for logs: structured JSON, correct level semantics, correlation/trace IDs, and mandatory secret/PII redaction. Read before writing or editing **/*.
---
## Structured logging (org standard)

- Log structured (JSON or key-value), never bare string interpolation. One event
  per log line with stable field names (`event`, `level`, `requestId`, `userId`).
- Use level semantics correctly: `error` = needs human action; `warn` =
  recoverable/degraded; `info` = business milestone; `debug` = diagnostics off in
  prod. Don't log at `error` for expected validation failures.
- Propagate a **correlation / trace id** through the request and include it on
  every log line and the client error envelope so a report can be traced end to end.
- **Never log secrets or PII**: no passwords, tokens, full PANs, full emails,
  auth headers, connection strings. Redact at the logger (allowlist fields), not
  by remembering at each call site.
- No `console.log`/`printStackTrace`/`print` in committed code — use the project
  logger. Don't log inside hot loops; sample high-volume events.

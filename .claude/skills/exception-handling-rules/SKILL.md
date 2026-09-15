---
name: exception-handling-rules
description: Org standard for errors: no swallowed exceptions, wrap-with-context, typed error taxonomy, a single client-facing error envelope, never leak stack traces. Read before writing or editing **/*.
---
## Exception handling (org standard)

- Never swallow errors. No empty `catch`, no bare `except:`, no
  `catch (e) {}`. If you catch, you handle, rethrow with context, or log and
  fail — and you say which.
- Classify errors: **expected** (validation, not-found, conflict — map to a
  client response), **programmer** (bugs — let them surface in dev, alert in
  prod), **fatal** (fail fast on startup/config errors). Don't treat them the same.
- Wrap-and-rethrow with context, don't blanket-catch and lose the cause
  (`throw new X(msg, { cause })` / Java `new X(msg, e)` / Python `raise X from e`).
- Return a **single error envelope** to clients: `{ error: { code, message,
  requestId } }`. Stable `code` strings; human `message`; never internal detail.
- Never leak stack traces, SQL, or framework internals to a client or an API
  response. Log the detail server-side, return the generic envelope.
- Validate at boundaries; inside trusted code, let invariants throw rather than
  defensively returning nulls that hide bugs.

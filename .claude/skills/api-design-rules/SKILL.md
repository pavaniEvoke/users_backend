---
name: api-design-rules
description: REST conventions: resource naming, versioning, pagination, idempotency, status-code map, and the standard error envelope. Read before writing or editing **/*controller*, **/controllers/**, **/routes/**, **/api/**, **/*.controller.ts.
---
## API design guidelines

- Resources are plural nouns (`/orders`, `/orders/{id}/items`); verbs live in
  the HTTP method, not the path. Use kebab-case paths, camelCase JSON bodies.
- Version explicitly (`/v1/...` or a header). Never break a shipped contract —
  add fields, don't repurpose them; deprecate with a sunset header before removal.
- Use status codes faithfully: 200/201/204 success, 400 validation, 401 unauth,
  403 forbidden, 404 missing, 409 conflict, 422 semantic, 429 rate-limited,
  5xx server. Don't return 200 with an error body.
- List endpoints paginate (cursor or `page`/`pageSize`) and document defaults
  and max page size. Support filtering/sorting via query params, not new routes.
- Mutating endpoints that can be retried are idempotent (use an idempotency key
  for POST where needed). PUT/DELETE are naturally idempotent — keep them so.
- Errors use the **standard envelope** `{ error: { code, message, requestId } }`
  with the same `code` vocabulary across services. Validate input at the edge;
  return all field errors together, not one at a time.

---
name: node-rules
description: Async error handling, input validation, no blocking the event loop. Read before writing or editing **/*.js, **/*.ts.
---
## Node.js / Express

- Don't block the event loop; keep CPU-heavy work off the request path.
- Wrap async route handlers so rejected promises become handled errors (async
  error middleware), not unhandled rejections.
- Validate and sanitize request input (params, query, body, headers) at the boundary.
- Set security headers (helmet), sensible CORS, and rate limits on sensitive routes.
- Read config/secrets from env; fail fast on missing required config at startup.

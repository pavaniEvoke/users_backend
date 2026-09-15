---
description: Write a Conventional Commits message from the staged changes — a focused subject plus an explanatory body.
allowed-tools: Bash(git diff:*), Bash(git status:*)
---
# /commit-message

Write a high-quality commit message for the currently staged changes.

First gather the diff:
- Run `git status` to confirm what is staged.
- Run `git diff --staged` to read the staged changes. If nothing is staged, say so and stop.

Then output a single commit message in **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: feat | fix | refactor | perf | test | docs | build | ci | chore.
- **subject**: imperative mood, lower-case, no trailing period, ≤ 72 chars.
- **body**: wrap at ~72 cols; explain *why* the change was made, not just what.
  Omit if the subject is fully self-explanatory.
- **footer**: `BREAKING CHANGE:` notes and issue/work-item references.

Rules: describe only what the staged diff contains. One logical change per commit —
if the diff spans unrelated changes, point that out and suggest splitting it.

---
description: Generate a pull request title and description from the current branch's changes, with a summary, change list, test notes, and risk callouts.
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git branch:*)
---
# /pr-generation

Generate a clear, reviewer-friendly pull request title and description from the
changes on the current branch.

First gather context:
- Run `git branch --show-current` for the branch name.
- Run `git log --oneline origin/HEAD..HEAD` (or against `main`/`master`) for the commit history.
- Run `git diff origin/HEAD...HEAD` (or against `main`/`master`) to read the actual changes.

Then produce, in Markdown:

**Title** — a concise, conventional-commit-style summary (e.g. `feat(auth): add refresh-token rotation`). Max ~70 chars.

**Description** with these sections:
- **Summary** — 2–4 sentences: what changed and why.
- **Changes** — bulleted list of the meaningful changes (group by area; skip noise).
- **How to test** — concrete steps or commands a reviewer runs to verify.
- **Risk & rollback** — blast radius, data/migration impact, how to revert.
- **Checklist** — tests added/updated, docs updated, no secrets, breaking changes called out.

Rules: describe what the diff actually does — don't invent features that aren't in
the changes. Link the work item if the branch name or commits reference one. Keep
it skimmable: a reviewer should understand the PR in under a minute.

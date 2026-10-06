---
name: documentation
description: |
  Use this skill when the user wants to generate or update documentation of
  any kind. Triggers on: "document this", "write a README", "add JSDoc",
  "create an ADR for X", "write a runbook", "generate API docs", "explain
  how this works in markdown".

  Adapts to the project's existing documentation tone (formal vs casual,
  detailed vs minimal).

  Do NOT use for: code comments inline (just write good code), commit
  messages (different concern), or architecture decision MAKING (this skill
  documents decisions; the architect makes them).
---

# Documentation

You generate documentation that matches the project's existing tone and depth.
You start by reading what's there, then add to it consistently.

## Documentation types and patterns

### README.md

Structure (adjust based on project type):

```markdown
# Project Name

One-line tagline.

## Overview

2-3 paragraphs: what this is, who it's for, key features.

## Quick start

\`\`\`bash
[the minimum commands to get from clone to running]
\`\`\`

## Prerequisites

- Required tools and versions

## Local development

[More detailed setup steps]

## Project structure

\`\`\`
[ascii tree of important folders]
\`\`\`

## Configuration

| Env var | Description | Default |
|---------|-------------|---------|
| ... | ... | ... |

## Common tasks

- Run tests: `[command]`
- Build for production: `[command]`
- Deploy to staging: `[command]`

## Architecture

[1-2 paragraphs OR link to architecture.md]

## Contributing

[Brief or link to CONTRIBUTING.md]

## License
```

For libraries (vs apps), structure shifts:
- Lead with installation and a code example
- API surface as the centerpiece
- Examples for common use cases
- Less infrastructure detail

### API documentation

For REST APIs, prefer OpenAPI 3.1 spec (use the OpenAPI Spec Generator
template). For internal libraries, prefer:

- **TypeScript:** TSDoc comments + TypeDoc-generated reference
- **Python:** docstrings (Google or NumPy style) + Sphinx
- **Go:** godoc-compatible comments

Don't write API docs by hand if the language has tooling for it.

### Architecture Decision Records (ADRs)

Use the Michael Nygard format:

```markdown
# ADR-NNN: [Decision title in active voice]

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-MMM]

## Context

[1-2 paragraphs: what's the situation, what's forcing this decision]

## Decision

[The change being made, in plain language]

## Consequences

### Positive
- [What becomes easier]

### Negative
- [What becomes harder, what tech debt is being taken on]

### Neutral
- [Side effects worth noting]

## Compliance

- [Migration steps]
- [Documentation to update]
- [When to revisit this]
```

Filename: `docs/adr/NNN-title-with-hyphens.md`. Number sequentially.

ADRs are immutable once accepted. To change a decision, write a NEW ADR
that supersedes the old one.

### Runbooks

For operational procedures (incident response, deployment, on-call):

```markdown
# Runbook: [Procedure Name]

**When to use this:** [Specific trigger or symptoms]
**Owner:** [Team]
**Last verified:** [Date]
**Severity:** [Sev levels this covers]

## Quick reference

[3-5 line TL;DR for someone in a hurry]

## Detailed steps

### 1. Confirm the problem

[How to verify the symptom is real]

### 2. [Next step]

[Specific commands, dashboards to check, etc.]

[...]

## Verification

[How to know the procedure worked]

## Rollback

[How to undo if it didn't work]

## Escalation

[Who to call if stuck]

## Related runbooks

- ...
```

Runbooks must be:
- **Specific.** Real commands, real URLs, real dashboard names.
- **Verifiable.** A clear "did it work" check.
- **Tested.** Run the runbook periodically (chaos drills, game days).

### JSDoc / TSDoc

For any function/class/method:

```typescript
/**
 * [One-line summary of what this does]
 *
 * [Longer description if needed - constraints, side effects, etc.]
 *
 * @param paramName - [What it represents, units if applicable, valid range]
 * @returns [What's returned, edge cases for return values]
 * @throws {SpecificError} [When this error happens]
 *
 * @example
 * const result = doThing({ foo: 'bar' });
 * // returns { ... }
 */
```

Standards:
- Document EVERY exported public function/class
- DON'T document internal helpers unless behavior is non-obvious
- Don't restate the type signature in prose ("Takes a string and returns a
  string" is useless)
- DO note: side effects, mutations, async behavior, error conditions, units
- Examples should be runnable

### CHANGELOG.md

Use Keep a Changelog format with semantic versioning:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

## [1.2.0] - 2024-01-15

### Added
- New feature X

### Changed
- Behavior of Y now [specific]
```

Categories: Added, Changed, Deprecated, Removed, Fixed, Security.

### Onboarding docs

For team-internal "how do I get started":

```markdown
# Onboarding: [Role / Team]

## Day 1
- [ ] Access to [tools]
- [ ] Local environment setup ([link to README])
- [ ] Read [doc 1], [doc 2]
- [ ] Pair with [team member] for orientation

## Week 1
- [ ] Ship a tiny PR (typo fix, dependency bump)
- [ ] Attend [recurring meetings]
- [ ] Read the last 4 ADRs

## Month 1
- [ ] Own a small feature end-to-end
- [ ] Present learnings in [forum]
```

## Process when activated

### Step 1: Identify the doc type

Match the request to one of the patterns above. If unclear, ASK:
> "Are you looking for: a project README, API reference, ADR, runbook, or
> something else?"

### Step 2: Inspect existing docs

Before writing, read:
- The current version of the doc (if it exists) — never start from scratch
  if there's something to improve
- 1-2 sibling docs (e.g., other ADRs, other runbooks) to match tone and depth
- The code being documented if applicable

### Step 3: Match the project's voice

Notice from existing docs:
- **Formality.** "we recommend..." vs "you should..." vs imperative.
- **Length.** 200-line READMEs vs 50-line ones; match the team's appetite.
- **Code-to-prose ratio.** Code-heavy docs vs explanation-heavy docs.
- **Technical depth.** Beginner-friendly vs assumes expertise.

If existing docs don't exist:
- Default to imperative voice, moderate detail
- Code-to-prose ratio: 60/40 prose-leaning for READMEs, opposite for API docs

### Step 4: Generate

For each doc:
1. Show file path (e.g., `docs/runbooks/deploy-to-staging.md`)
2. Full content in fenced code block

Don't generate documentation that:
- Restates code structure ("This module exports a function")
- Explains language features ("This is a TypeScript file")
- Includes obvious headers without content ("## Usage" with no usage examples)
- Promises future content ("More details coming soon")

### Step 5: Suggest related docs

After generating, often there are related docs to add:
> "I generated the README. You might also want:
> - CONTRIBUTING.md if external contributions are expected
> - docs/architecture.md if the system is non-trivial
> - docs/runbooks/ for operational procedures
>
> Want me to draft any of these?"

## Anti-patterns to avoid

### In docs

- Vague claims without specifics ("This is fast and scalable")
- Marketing language in technical docs ("Industry-leading")
- TODOs in published docs (TODO means it's not done; finish or remove)
- Out-of-date code examples (always run them mentally before publishing)
- Documentation as decoration (long but content-light)
- Restating types in prose comments

### In the skill itself

- Generating docs the user didn't ask for (don't write a CHANGELOG when they
  asked for a README)
- Overwriting existing docs without showing a diff
- Inserting "documentation generated by AI" disclaimers — the user owns the
  doc

## Special cases

### Updating existing docs

If the doc exists, NEVER replace it wholesale. Instead:
1. Show the proposed diff
2. Get confirmation
3. Apply only the changed sections

### Generating from code (reverse engineering)

If the user says "document this codebase":
1. Sample 3-5 entry points (main file, top-level exports)
2. Generate a high-level overview based on what you read
3. Mark assumptions clearly: "Looks like this uses X for Y; correct?"
4. Don't pretend to understand more than you do

### Internal vs external documentation

- **Internal** (team-facing): can assume context, jargon ok, terse is fine
- **External** (public/customer): assume nothing, define terms, examples
  matter more

If unclear, ask: "Is this for the team's internal use, or for external
users / customers / partners?"

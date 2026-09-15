---
name: greenfield-starter
description: Turns raw requirements into confirmed user stories and a story-by-story build plan for a brand-new project.
---
# Greenfield starter playbook

Use this skill at the very start of a new project, before any code exists.
It converts requirements into a confirmed backlog and a build order. You
facilitate and draft — the human confirms every artifact.

## Step 1 — Capture the inputs

Ask the human for whatever already exists, and record the answers in
`.agent/plan.md`:

- The requirements (a document, a paragraph, or a conversation — capture it).
- Existing user stories, if any (Jira/Azure DevOps export, spreadsheet, prose).
- Repo layout: single repo, or separate frontend / backend repos? Which repo
  is this kit installed in?
- Any existing design inputs: UI mockups, database schema, API contracts,
  architecture diagrams.

## Step 2 — Draft user stories

From the requirements, draft user stories in the form:

> As a <role>, I want <capability>, so that <benefit>.

For each story add acceptance criteria (Given/When/Then). Group stories into
milestones. **Stop and have the human review the story list before going
further** — do not invent scope.

## Step 3 — Establish the foundations

Before the first story, set up the rails every story will run on:

- Project scaffold matching the chosen stack and repo layout.
- Lint, format, and test tooling wired into a single command each.
- CI running lint + tests on every push.
- The conventions the team confirmed (structure, naming, error handling).

## Step 4 — Build story by story

Implement exactly **one story at a time** using the operating procedure in
your instructions: plan the story → build it → stop at the human
verification checkpoint → commit on confirmation → next story. Keep
`.agent/plan.md` trimmed to the stories still open — a finished one moves out
to its `.agent/progress/` note — so anyone can see what is left at a glance.

# Process

This document describes how work moves from idea to merged code on this project. It's deliberately lightweight, but every step is enforced via GitHub's tooling, not just intention.

## Tracking Work

All work starts as a GitHub Issue, this project's task tracker (a lighter-weight Jira). Each Issue gets labels (`feature`, `bug`, `task`) and sits on the Project board (Backlog → In Progress → In Review → Done).

## Branching

Every Issue gets its own feature branch off `main`, named with the issue number for traceability:

    git checkout -b 12-slack-bolt-app

No work happens directly on `main`. Branch protection enforces this even for the repo owner.

## Pull Requests

When a branch is ready, open a PR into `main`. The description must reference the issue it closes (`Closes #12`), which auto-links the two and closes the issue on merge. Use the PR template's checklist before requesting review.

## Review and Approval

**Nothing merges without explicit approval.** Branch protection on `main` requires at least one approving review before merge, even on a one-person project. This is the structural version of "all design and code changes go through the architect."

## Architecture Decisions

Any nontrivial design choice (new dependency, structural change, build-vs-buy call) gets an ADR in `/adr/` *before* the implementing PR is opened. The PR description should link to the ADR it implements.

## Definition of Done

- Code is merged to `main` via an approved PR
- The related Issue is closed automatically via `Closes #N`
- Any new architectural decision has a corresponding ADR
- Docs (this file, the scope doc, README) are updated if the change affects them

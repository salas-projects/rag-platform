# Process

This document describes how work moves from idea to merged code on this project. It's deliberately lightweight, and every step that *can* be mechanically enforced via GitHub's tooling is — the rest relies on intention, and this doc says which is which.

## Tracking Work

All work starts as a GitHub Issue, this project's task tracker (a lighter-weight Jira). Each Issue gets labels (`feature`, `bug`, `task`) and sits on the Project board (Backlog → In Progress → In Review → Done).

## Branching

Every Issue gets its own feature branch off `main`, named with the issue number for traceability:

    git checkout -b 12-slack-bolt-app

No work happens directly on `main`. A repository ruleset on `main` mechanically enforces this (blocks direct pushes, force-pushes, and branch deletion) — it is not just a stated convention.

## Commit Messages

Every commit message leads with the issue number it's associated with, e.g. `#12: add Bolt app skeleton`, including direct-to-trunk doc/process commits. Keeps history traceable to the issue log without reconstruction later.

## Pull Requests

When a branch is ready, open a PR into `main`. The description must reference the issue it closes (`Closes #12`), which auto-links the two and closes the issue on merge. Use the PR template's checklist before requesting review. Merges are squash-only, with the branch auto-deleted on merge, so trunk history stays one commit per issue.

## Review and Approval

**Nothing merges without a green build.** The `main` ruleset requires a PR (direct pushes are rejected) and, once CI exists, a passing required status check. Required *approving reviews* is intentionally set to `0` — GitHub does not allow a PR author to approve their own pull request, so on a one-person project a nonzero approval requirement would deadlock every PR rather than gate it. CI is therefore the actual enforcement mechanism, not a human approval count; see ADR-0006 for the full reasoning. The human step that remains is real, just manual by design: Claude opens every PR but never merges one — the merge action is always a deliberate, separate action taken by the repo owner.

## Architecture Decisions

Any nontrivial design choice (new dependency, structural change, build-vs-buy call) gets an ADR in `/adr/` *before* the implementing PR is opened. The PR description should link to the ADR it implements.

## Testing & Evidence

Automated checks (ruff, pytest, CI runs) and human-verification checks are both logged as they happen in `/testing/test-log.md`, the running record for the project — continuously numbered (`A#` automated, `H#` human), each tied back to the issue/ADR/acceptance criterion it verifies, with a Result, Date, and Evidence.

## Definition of Done

- Code is merged to `main` via an approved PR with a passing required CI check
- The related Issue is closed automatically via `Closes #N`
- Any new architectural decision has a corresponding ADR
- Docs (this file, the scope doc, README) are updated if the change affects them
- Relevant test-log entries are recorded with Result/Date/Evidence

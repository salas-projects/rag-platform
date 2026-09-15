# ADR-0006: Trunk Enforcement Model for a Solo Repo

**Status:** Accepted

## Context

`PROCESS.md` and the project's public README both state that `main` is protected and that
"nothing merges without approval" — language that reads as if a human reviewer gates every
merge, the way it would on a team. On a solo repository this claim needs to be precise about
what GitHub actually mechanically enforces, versus what's aspirational, because the two rules
that would normally do this job don't work the way they would on a team:

- **GitHub does not allow a PR's author to approve their own pull request.** Setting
  `required_approving_review_count` to anything above `0` on this repo — where the only
  collaborator is also the only possible author — doesn't add a review gate, it deadlocks
  every PR permanently, since no one who can review is not also the author.
- With `required_approving_review_count: 0` (ruleset `main-pr`, created outside the ADR process before this workflow
  was audited), the *pull_request* rule still blocks direct pushes and force-pushes to `main`, but
  nothing yet blocks a broken or untested change from being merged.

## Decision

Treat **CI as the enforcement mechanism**, not human approval count, and keep
`required_approving_review_count: 0` as a deliberate, documented consequence of the
self-approval constraint rather than an oversight. Concretely:

- `.github/workflows/ci.yml` runs `ruff check`, `ruff format --check`, and `pytest` on every
  PR into `main` and on every push to `main`.
- Once the `ci` job has reported at least once (GitHub can't require a check name it has never
  seen report), ruleset `main-pr` gets a `required_status_checks` rule naming it, with
  `strict_required_status_checks_policy: true`.
- The human control that remains is procedural, not a GitHub-enforced count: **Claude opens
  every PR but never merges one.** The merge action is always a separate, deliberate action
  taken by the repo owner — so a change can't land silently even though no second reviewer
  exists to formally approve it.

## Consequences

`main` is protected against two independent failure modes by two independent mechanisms: the
ruleset blocks direct/force pushes regardless of content, and CI blocks merging a PR whose
content is broken. Neither depends on a review count that can't function correctly in a
one-person repo. This is also a legitimate, defensible answer to "how do you enforce code
review with no team" in an interview — the honest answer is that self-approval is structurally
impossible on GitHub, so the gate was redesigned around what *can* be mechanically enforced
(build/lint/test correctness) plus a manual-merge discipline, rather than performing a review
process that would be theater on a solo repo.

# Test Log

Running record of every automated and human-verification check performed on this project, per
the testing/evidence convention in the global working agreement. Case numbers are continuously
assigned and never reset across the project's lifetime — `A#` for automated, `H#` for human.

Each entry ties back to an Issue/ADR/acceptance criterion, and carries a Result, Date, and Evidence.

## #1 — Correct process docs and add missing repo hygiene files

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| H1 | Human | `main-pr` ruleset configuration mechanically blocks direct pushes to `main` (verified via config inspection, not a live push — a live test was rejected as too risky since `non_fast_forward` would make an accidental landing unrevertable) | Issue #1, PROCESS.md | Pass | 2026-09-15 | `gh api repos/salas-projects/rag-platform/rules/branches/main` shows active `pull_request` + `non_fast_forward` rules, `bypass_actors: []`, `current_user_can_bypass: "never"` |
| H2 | Human | PR #1 merges cleanly under the `main-pr` ruleset with 0 required approvals (no self-approval deadlock, no unattributed-changes deadlock) | Issue #1 | Pending | | |

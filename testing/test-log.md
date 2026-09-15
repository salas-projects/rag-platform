# Test Log

Running record of every automated and human-verification check performed on this project, per
the testing/evidence convention in the global working agreement. Case numbers are continuously
assigned and never reset across the project's lifetime — `A#` for automated, `H#` for human.

Each entry ties back to an Issue/ADR/acceptance criterion, and carries a Result, Date, and Evidence.

## #1 — Correct process docs and add missing repo hygiene files

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| H1 | Human | `main-pr` ruleset configuration mechanically blocks direct pushes to `main` (verified via config inspection, not a live push — a live test was rejected as too risky since `non_fast_forward` would make an accidental landing unrevertable) | Issue #1, PROCESS.md | Pass | 2026-09-15 | `gh api repos/salas-projects/rag-platform/rules/branches/main` shows active `pull_request` + `non_fast_forward` rules, `bypass_actors: []`, `current_user_can_bypass: "never"` |
| H2 | Human | PR #1 merges cleanly under the `main-pr` ruleset with 0 required approvals (no self-approval deadlock, no unattributed-changes deadlock) | Issue #1 | Pass | 2026-09-15 | PR #2 merged clean at b985e26 — `mergeStateStatus: CLEAN`, `mergeable: MERGEABLE`, no review-required or unattributed-changes block; https://github.com/salas-projects/rag-platform/pull/2 |
| H2 | Human | PR #1 merges cleanly under the `main-pr` ruleset with 0 required approvals (no self-approval deadlock, no unattributed-changes deadlock) | Issue #1 | Pending | | |

## #4 — Pin Python toolchain (uv, 3.12, ruff, pytest)

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| A1 | Automated | `uv sync` resolves and installs the full dependency graph on Python 3.12.14 | Issue #4, ADR-0005 | Pass | 2026-09-15 | `uv sync` — "Resolved 97 packages", installed cleanly, `uv.lock` generated |
| A2 | Automated | `uv run ruff check .` clean | Issue #4, ADR-0005 | Pass | 2026-09-15 | `All checks passed!` |
| A3 | Automated | `uv run pytest` passes with a non-empty suite (guards against pytest exit code 5) | Issue #4, ADR-0005 | Pass | 2026-09-15 | `tests/test_smoke.py::test_packages_import PASSED` — 1 passed in 0.00s |

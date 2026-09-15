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

## #4 — Pin Python toolchain (uv, 3.12, ruff, pytest)

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| A1 | Automated | `uv sync` resolves and installs the full dependency graph on Python 3.12.14 | Issue #4, ADR-0005 | Pass | 2026-09-15 | `uv sync` — "Resolved 97 packages", installed cleanly, `uv.lock` generated |
| A2 | Automated | `uv run ruff check .` clean | Issue #4, ADR-0005 | Pass | 2026-09-15 | `All checks passed!` |
| A3 | Automated | `uv run pytest` passes with a non-empty suite (guards against pytest exit code 5) | Issue #4, ADR-0005 | Pass | 2026-09-15 | `tests/test_smoke.py::test_packages_import PASSED` — 1 passed in 0.00s |

## #6 — Add CI (ruff + pytest) as the required merge gate

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| A4 | Automated | CI workflow (`ci` job: uv sync, ruff check, ruff format --check, pytest) runs green on a PR | Issue #6, ADR-0006 | Pass | 2026-09-15 | PR #7 run 35018260386 — `ci` check passed in 11s: https://github.com/salas-projects/rag-platform/actions/runs/35018260386 |
| H3 | Human | A **failing** CI run blocks merge once `ci` is added as a required status check on ruleset `main-pr` | Issue #6, ADR-0006 | Pass | 2026-09-15 | Ruleset `main-pr` updated with `required_status_checks: [ci]`. Throwaway PR #8 (deliberately broken ruff formatting) got `ci` conclusion FAILURE and `mergeStateStatus: BLOCKED`; closed without merging. |

## #9 — Phase 0: install Docker and stand up Qdrant

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| A5 | Automated | `docker compose up -d --wait` brings Qdrant healthy | Issue #9 | Pass | 2026-09-15 | `docker compose up -d --wait` → `Container rag-platform-qdrant Healthy`; `curl localhost:6333/readyz` → "all shards are ready"; `docker compose ps` showed `Up ... (healthy)`; torn down after with `docker compose down` |
| H4 | Human | Board shows four correct columns with Phase 1 issues in Backlog | Stage 6, Issues #11-#16 | Pass | 2026-09-15 | Board https://github.com/orgs/salas-projects/projects/1 has columns Backlog/In Progress/In Review/Done; `gh project item-list` confirms Issues #11-#16 (connector interface, chunking, embedding interface, Qdrant wrapper, retrieval logic, end-to-end CLI proof) all landed in Backlog |

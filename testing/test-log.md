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

## #11 — Connector interface + docs_site connector

Automated tests are hermetic: all HTTP is mocked via `httpx.MockTransport` against saved fixtures in
`tests/fixtures/docs_site/`, so CI never touches the three documentation sites.

| # | Type | Description | Ties to | Result | Date | Evidence |
|---|------|-------------|---------|--------|------|----------|
| A6 | Automated | Sitemap XML parses; namespaced `<loc>`/`<lastmod>` extracted | Issue #11, ADR-0007 | Pass | 2026-09-15 | `test_parse_sitemap_extracts_namespaced_loc_and_lastmod`, `test_parse_sitemap_handles_missing_lastmod` |
| A7 | Automated | include/exclude + robots filtering rejects Snowflake `commands-*`/release-notes, Matillion `private-docs`/asset fragments, dbt `/learn` and `/blog` | Issue #11, ADR-0007 | Pass | 2026-09-15 | `test_discover_applies_scope_and_robots_end_to_end`, `test_discover_snowflake_excludes_sql_reference_and_release_notes`, 6 × `test_robots_checker_*` |
| A8 | Automated | Extraction returns real prose per site fixture; nav/script/`¶`/markup stripped | Issue #11, ADR-0007 | Pass | 2026-09-15 | `test_extract_article_returns_clean_prose` (3 params: dbt/Snowflake/Matillion) |
| A9 | Automated | `last_updated` chain: in-page date → HTTP header → sitemap lastmod → None, incl. Snowflake-yields-None case | Issue #11, ADR-0007 | Pass | 2026-09-15 | 5 × `test_resolve_last_updated_*`, 2 × `test_extract_page_date_*` |
| A10 | Automated | `RawDocument` shape, frozen-ness, and stable `content_hash` | Issue #11 | Pass | 2026-09-15 | `tests/test_ingestion_base.py` (8 tests), `test_fetch_produces_well_formed_document_with_stable_hash` |
| A11 | Automated | Retry/429/404 handling and disk-cache reuse via MockTransport | Issue #11 | Pass | 2026-09-15 | `test_fetch_retries_on_429_then_succeeds`, `test_fetch_gives_up_after_max_retries`, `test_fetch_returns_none_for_404`, `test_fetch_uses_cache_on_second_call` |
| A12 | Automated | Regression guard: dbt UI chrome stripped, real body content retained | Issue #11, ADR-0007 | Pass | 2026-09-15 | `test_strip_selectors_remove_dbt_ui_chrome` — added after H5 found the defect |
| A13 | Automated | `uv run ruff check .` + `uv run ruff format --check .` clean | Issue #11 | Pass | 2026-09-15 | "All checks passed!" / "34 files already formatted" |
| A14 | Automated | Full suite green | Issue #11 | Pass | 2026-09-15 | `uv run pytest` — 39 passed |
| H5 | Human | Live crawl spot-check against all three real sites; sampled text is article prose with no boilerplate leakage | Issue #11, ADR-0007 | Pass | 2026-09-15 | `uv run python -m connectors.docs_site --source {dbt,snowflake,matillion} --limit 2 --no-cache`. **Found 2 real defects on first run** — (1) every dbt page prefixed with ~12k chars of page-action toolbar + TOC boilerplate, (2) dbt `last_updated` reflecting site deploy time (3 pages minutes apart) rather than the authored date. Both fixed via `strip_selectors`/`date_selector` in `sites.yaml`; re-run shows clean prose previews on all three, dbt dated 2026-09-10 (authored), Snowflake correctly `None`, Matillion from sitemap lastmod. |

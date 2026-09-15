# ADR-0005: Python Toolchain — uv, Python 3.12, ruff, pytest

**Status:** Accepted

## Context

Local system Python is 3.14.6, installed via Homebrew. Airflow (Phase 4) does not support 3.14,
and several other packages in this stack (streamlit, slack-bolt) have less mature 3.14 support at
the time of writing. The project needs a pinned, reproducible interpreter version independent of
whatever the system happens to have, plus a lockfile so "it works on my machine" doesn't become a
Phase-4 surprise once Airflow enters the picture.

## Decision

Use `uv` to both provision the interpreter and manage dependencies: `.python-version` pins 3.12,
`uv python install 3.12` fetches that exact build regardless of system Python, and `pyproject.toml`
+ `uv.lock` define and pin the dependency graph. The project is marked `package = false` (uv's
application mode) rather than a distributable library — `core/`, `connectors/`, and `app/` are
plain importable packages run in place via `uv run`, not built into a wheel.

Phase 1 runtime dependencies only: `qdrant-client`, `voyageai`, `anthropic`, `pyyaml`,
`python-dotenv`. `streamlit` and `slack-bolt` are deferred into `[project.optional-dependencies]`
groups (`streamlit`, `slack`) so they install only when Phase 2/3 actually need them, rather than
sitting unused from day one. `ruff` and `pytest` are dev-only via `[dependency-groups]`.

Not chosen now: the HTML fetch/parse library for the docs-site connector. That's a genuine Phase 1
design decision (readability-style extraction vs. raw BeautifulSoup vs. a docs-specific scraper)
and gets its own ADR when that work starts, rather than being picked as a side effect of this one.

## Consequences

Any machine (or CI runner) gets the identical interpreter and dependency set via `uv sync`,
independent of what's installed system-wide — this is what makes the CI pipeline in ADR-0006
meaningful rather than a coin flip. Introduces one new tool (`uv`) beyond what's already in use;
justified by solving both interpreter pinning and dependency locking in one step rather than two
(e.g. pyenv + pip-tools). `uv.lock` is committed to the repo for reproducibility; `.venv/` stays
gitignored.

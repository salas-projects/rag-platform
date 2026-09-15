# ADR-0007: HTML Fetch and Parse Strategy for the docs_site Connector

**Status:** Accepted

## Context

ADR-0005 pinned the Python toolchain but explicitly deferred one choice: "the HTML fetch/parse
library for the docs-site connector… gets its own ADR when that work starts, rather than being
smuggled in as a dep today." Issue #11 is that work.

The v1 connector ingests public documentation from three known sites — dbt, Snowflake, and
Matillion. Before choosing an approach, each was inspected live rather than assumed:

- **All three are server-rendered.** This was the decisive check: client-side rendering would have
  ruled out a simple HTTP-plus-parser approach entirely and forced a headless browser, with a much
  larger dependency and maintenance burden. Fetching Snowflake's
  `/en/user-guide/tables-storage-considerations` with `curl` yields 12,641 characters of real article
  prose in the raw HTML.
- **All three expose a clean, stable semantic container:** dbt `<article>` (Docusaurus), Snowflake
  `<article data-testid="article-content">`, Matillion `<article class="md-content__inner md-typeset">`.
- **All three publish sitemaps**, though Snowflake's `/en/sitemap.xml` is 9.5 MB across 8,662 URLs.
- **`robots.txt` imposes real restrictions:** Snowflake disallows `/sql-reference/commands-*`,
  `/INCLUDE/`, `/DRAFT/`, `/PREVIEW/`; Matillion disallows `/legal/` and both `private-docs` trees;
  dbt disallows `/learn`.
- **`last_updated` is not uniformly available.** dbt and Matillion return `Last-Modified` headers;
  Snowflake returns only an `etag`. Of the three sitemaps, only Matillion's carries `lastmod`.

## Decision

**Fetch with `httpx`, parse with `BeautifulSoup` backed by `lxml`, and extract using a per-site CSS
selector held in configuration.**

`trafilatura` was the main alternative. It is the better tool when the target pages are unknown or
heterogeneous, because it strips boilerplate heuristically. That advantage does not apply here: there
are exactly three sites, each with a clean semantic container, so a targeted selector is both more
precise and more predictable than a heuristic — and when a site redesigns, a selector fails loudly
and is fixed by editing one config line, rather than silently degrading extraction quality.
`selectolax` was rejected as a micro-optimisation: it is faster, but speed is irrelevant at this
corpus size and it is a more obscure dependency.

Supporting decisions:

- **Discovery via sitemap**, parsed with the standard library's `xml.etree.ElementTree` — no crawler
  and no additional dependency.
- **`robots.txt` is enforced programmatically** with the standard library's `urllib.robotparser`,
  fetched at runtime rather than transcribed into a hand-maintained exclusion list, so the rules
  cannot silently drift out of date.
- **Scoped corpus via config include-patterns**: dbt `/docs/`, `/reference/`, `/best-practices/`;
  Snowflake `/en/user-guide/`; Matillion `/data-productivity-cloud/`, `/metl/`. That is roughly 3,740
  pages of the ~11,100 the sitemaps list. Snowflake's `/en/release-notes/` (1,863 near-duplicate
  pages) and `/en/sql-reference/` (2,562 syntax tables) are excluded deliberately: together they are
  51% of Snowflake's corpus and are the largest source of retrieval noise, competing for top-k slots
  against pages that actually answer questions.
- **Documentation only for v1** — the dbt blog (249 pages) is excluded. `docs/PROJECT_SCOPE.md`'s
  guardrail permits blogs, but blog posts age badly, and outdated guidance retrieved and presented
  with a citation is precisely the failure mode that makes a RAG assistant untrustworthy.
- **`last_updated` is nullable**, resolved by a documented fallback chain: HTTP `Last-Modified`, then
  sitemap `lastmod`, then `None`. Snowflake pages will legitimately carry `None`.
- **`httpx` is promoted to an explicit dependency.** It already resolves transitively via
  `qdrant-client`, and relying on another package's transitive dependency is fragile.

## Consequences

Extraction is precise and debuggable, and adding or rescoping a source is a config edit rather than a
code change — consistent with the connector/persona seams `docs/PROJECT_SCOPE.md` calls for. Two new
dependencies (`beautifulsoup4`, `lxml`) enter the project.

The cost is coupling to three sites' DOM structures: a redesign breaks a selector. This is an
accepted, bounded maintenance burden, made visible by tests that assert real prose is extracted from
saved fixtures, and cheap to fix when it happens.

The scoped corpus means some questions — particularly about specific SQL commands — will have no
grounding and should be answered with "not in the indexed documentation" rather than a guess. The
include-patterns can be widened once Phase 5's evaluation set can actually measure whether doing so
helps or hurts retrieval quality, instead of guessing now.

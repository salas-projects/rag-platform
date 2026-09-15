"""Tests for the docs_site connector (issue #11). All network calls are mocked via
httpx.MockTransport against saved fixtures — see adr/0007-html-fetch-and-parse.md.
Only H5 in testing/test-log.md is a live check, and it isn't run here."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from connectors.docs_site.connector import (
    DocsSiteConnector,
    RobotsChecker,
    compute_section,
    extract_article,
    extract_page_date,
    load_site_profiles,
    matches_scope,
    parse_sitemap,
    resolve_last_updated,
)

FIXTURES = Path(__file__).parent / "fixtures" / "docs_site"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# --- A6: sitemap parsing -----------------------------------------------------------


def test_parse_sitemap_extracts_namespaced_loc_and_lastmod():
    entries = parse_sitemap(fixture_bytes("matillion_sitemap.xml"))
    urls = [url for url, _ in entries]
    assert "https://docs.matillion.com/metl/docs/2914518/" in urls
    lastmods = dict(entries)
    assert lastmods["https://docs.matillion.com/metl/docs/2914518/"] == "2026-08-01"


def test_parse_sitemap_handles_missing_lastmod():
    entries = parse_sitemap(fixture_bytes("dbt_sitemap.xml"))
    assert all(lastmod is None for _, lastmod in entries)
    assert len(entries) == 6


# --- A7: include/exclude + robots filtering -----------------------------------------


def test_matches_scope_include_and_exclude():
    profile = load_site_profiles()["dbt"]
    assert matches_scope("/docs/build/sql-models", profile.include, profile.exclude)
    assert not matches_scope("/blog/some-post", profile.include, profile.exclude)


def test_matches_scope_matillion_excludes_asset_fragments():
    profile = load_site_profiles()["matillion"]
    assert matches_scope(
        "/data-productivity-cloud/designer/docs/example-flights-slim/",
        profile.include,
        profile.exclude,
    )
    assert not matches_scope(
        "/assets/snippets/modular-connector-properties/", profile.include, profile.exclude
    )


def test_robots_checker_blocks_snowflake_sql_reference_commands():
    robots = RobotsChecker(fixture_text("snowflake_robots.txt"))
    assert not robots.can_fetch("https://docs.snowflake.com/en/sql-reference/commands-table")
    assert robots.can_fetch(
        "https://docs.snowflake.com/en/user-guide/tables-storage-considerations"
    )


def test_robots_checker_blocks_matillion_private_docs():
    robots = RobotsChecker(fixture_text("matillion_robots.txt"))
    assert not robots.can_fetch(
        "https://docs.matillion.com/data-productivity-cloud/private-docs/some-internal-page/"
    )
    assert robots.can_fetch(
        "https://docs.matillion.com/data-productivity-cloud/designer/docs/example-flights-slim/"
    )


def test_robots_checker_honours_wildcard_patterns():
    """Regression guard: Python's stdlib urllib.robotparser silently ignores `*` in rule
    paths and would report these Snowflake commands-* URLs as allowed."""
    robots = RobotsChecker("User-agent: *\nDisallow: /en/sql-reference/commands-*\n")
    assert not robots.can_fetch("https://docs.snowflake.com/en/sql-reference/commands-table")
    assert not robots.can_fetch("https://docs.snowflake.com/en/sql-reference/commands-create")
    assert robots.can_fetch("https://docs.snowflake.com/en/sql-reference/constructs")


def test_robots_checker_honours_end_anchor():
    robots = RobotsChecker("User-agent: *\nDisallow: /private$\n")
    assert not robots.can_fetch("https://example.com/private")
    assert robots.can_fetch("https://example.com/private/sub-page")


def test_robots_checker_allow_overrides_longer_disallow():
    robots = RobotsChecker("User-agent: *\nDisallow: /docs/\nAllow: /docs/public/\n")
    assert not robots.can_fetch("https://example.com/docs/secret")
    assert robots.can_fetch("https://example.com/docs/public/page")


def test_robots_checker_ignores_other_user_agent_groups():
    robots = RobotsChecker("User-agent: BadBot\nDisallow: /\n\nUser-agent: *\nDisallow: /nope/\n")
    assert robots.can_fetch("https://example.com/anything")
    assert not robots.can_fetch("https://example.com/nope/x")


def test_robots_checker_blocks_dbt_learn():
    robots = RobotsChecker(fixture_text("dbt_robots.txt"))
    assert not robots.can_fetch("https://docs.getdbt.com/learn/some-course-page")
    assert robots.can_fetch("https://docs.getdbt.com/docs/build/sql-models")


def test_discover_applies_scope_and_robots_end_to_end():
    """Every excluded-by-config-or-robots URL in the fixture sitemaps must be absent
    from discover()'s output; every in-scope one must be present."""
    transport = httpx.MockTransport(_fixture_router)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("dbt", client=client, request_delay=0)

    discovered = list(connector.discover())

    assert "https://docs.getdbt.com/docs/build/sql-models" in discovered
    assert "https://docs.getdbt.com/reference/resource-configs/materialized" in discovered
    assert "https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview" in discovered
    assert not any("/blog" in u for u in discovered)  # out of include scope
    assert not any("/learn" in u for u in discovered)  # blocked by robots.txt


def test_discover_snowflake_excludes_sql_reference_and_release_notes():
    transport = httpx.MockTransport(_fixture_router)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("snowflake", client=client, request_delay=0)

    discovered = list(connector.discover())

    assert "https://docs.snowflake.com/en/user-guide/tables-storage-considerations" in discovered
    assert not any("sql-reference" in u for u in discovered)
    assert not any("release-notes" in u for u in discovered)
    assert not any("/INCLUDE/" in u for u in discovered)


# --- A8: content extraction ----------------------------------------------------------


@pytest.mark.parametrize(
    "html_fixture,selector,expected_title,expected_snippet",
    [
        ("dbt_page.html", "article", "SQL models", "materialized"),
        (
            "snowflake_page.html",
            'article[data-testid="article-content"]',
            "Data storage considerations",
            "Time Travel",
        ),
        (
            "matillion_page.html",
            "article.md-content__inner",
            "S3 Load and transformation",
            "S3",
        ),
    ],
)
def test_extract_article_returns_clean_prose(
    html_fixture, selector, expected_title, expected_snippet
):
    html = fixture_text(html_fixture)
    result = extract_article(html, selector)
    assert result is not None
    title, text = result
    assert title == expected_title
    assert expected_snippet in text
    assert "¶" not in text  # headerlink permalink markers must be stripped
    # No leftover markup. Checked via closing tags rather than a bare "<", because
    # Snowflake's SQL docs legitimately contain literal placeholders like <db_name>.
    assert "</" not in text
    assert "<script" not in text.lower()


def test_extract_article_returns_none_for_missing_selector():
    html = fixture_text("dbt_page.html")
    assert extract_article(html, "div.does-not-exist") is None


def test_strip_selectors_remove_dbt_ui_chrome():
    """Regression guard for a defect found by live H5 verification: without these
    selectors every dbt page began with the page-action toolbar and the on-this-page
    TOC, putting an identical ~12k-char boilerplate prefix on every dbt chunk."""
    profile = load_site_profiles()["dbt"]
    html = fixture_text("dbt_page.html")

    _, polluted = extract_article(html, profile.content_selector)
    _, cleaned = extract_article(html, profile.content_selector, profile.strip_selectors)

    for chrome in ("Copy page as Markdown for LLMs", "Was this page helpful", "Edit this page"):
        assert chrome in polluted
        assert chrome not in cleaned

    assert cleaned.startswith("SQL models")
    assert "​" not in cleaned  # zero-width anchor markers normalised away
    assert len(cleaned) < len(polluted) / 2
    assert "materialized" in cleaned  # real body content survived


# --- A9: last_updated fallback chain, including the Snowflake None case --------------


def test_resolve_last_updated_prefers_in_page_date_over_deploy_timestamp():
    """The in-page date must win: on statically-built sites the HTTP header is the
    deploy time, so trusting it would stamp every page with the same date."""
    page_date = datetime(2026, 9, 10, 22, 32, 49, tzinfo=UTC)
    result = resolve_last_updated(page_date, "Tue, 15 Sep 2026 19:10:54 GMT", "2026-01-01")
    assert result == page_date


def test_resolve_last_updated_falls_back_to_http_header():
    result = resolve_last_updated(None, "Tue, 15 Sep 2026 19:10:54 GMT", "2026-01-01")
    assert result == datetime(2026, 9, 15, 19, 10, 54, tzinfo=UTC)


def test_resolve_last_updated_falls_back_to_sitemap_lastmod():
    result = resolve_last_updated(None, None, "2026-08-01")
    assert result == datetime(2026, 8, 1, tzinfo=UTC)


def test_resolve_last_updated_snowflake_case_is_none():
    """Snowflake has no in-page date, sends no Last-Modified header, and its sitemap has
    no lastmod — this must resolve to None, not raise or fabricate a date."""
    assert resolve_last_updated(None, None, None) is None


def test_resolve_last_updated_ignores_malformed_values():
    assert resolve_last_updated(None, "not-a-date", "also-not-a-date") is None


def test_extract_page_date_reads_dbt_time_element():
    html = fixture_text("dbt_page.html")
    assert extract_page_date(html, "time[datetime]") == datetime(
        2026, 9, 10, 22, 32, 49, tzinfo=UTC
    )


def test_extract_page_date_returns_none_without_selector_or_match():
    html = fixture_text("dbt_page.html")
    assert extract_page_date(html, None) is None
    assert extract_page_date(html, "time.nonexistent") is None


# --- A10: RawDocument shape + stable content_hash ------------------------------------


def test_fetch_produces_well_formed_document_with_stable_hash():
    transport = httpx.MockTransport(_fixture_router)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("dbt", client=client, request_delay=0)

    doc = connector.fetch("https://docs.getdbt.com/docs/build/sql-models")

    assert doc is not None
    assert doc.source == "dbt"
    assert doc.title == "SQL models"
    assert doc.section == "docs/build"
    assert doc.content_hash == doc.content_hash  # deterministic per-instance

    doc2 = connector.fetch("https://docs.getdbt.com/docs/build/sql-models")
    assert doc.content_hash == doc2.content_hash


def test_compute_section_from_url_path():
    assert compute_section("https://docs.getdbt.com/docs/build/sql-models") == "docs/build"
    assert compute_section("https://docs.getdbt.com/blog") == "blog"


# --- A11: retry / 429 handling --------------------------------------------------------


def test_fetch_retries_on_429_then_succeeds():
    attempts = {"count": 0}

    def flaky_router(request: httpx.Request) -> httpx.Response:
        if "sql-models" in request.url.path:
            attempts["count"] += 1
            if attempts["count"] < 2:
                return httpx.Response(429, headers={"retry-after": "0"})
            return httpx.Response(
                200,
                text=fixture_text("dbt_page.html"),
                headers={"last-modified": "Tue, 15 Sep 2026 19:10:54 GMT"},
            )
        return _fixture_router(request)

    transport = httpx.MockTransport(flaky_router)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("dbt", client=client, request_delay=0, sleep_fn=lambda _: None)

    doc = connector.fetch("https://docs.getdbt.com/docs/build/sql-models")

    assert doc is not None
    assert attempts["count"] == 2


def test_fetch_gives_up_after_max_retries():
    def always_429(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"retry-after": "0"})

    transport = httpx.MockTransport(always_429)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector(
        "dbt", client=client, request_delay=0, sleep_fn=lambda _: None, max_retries=2
    )

    doc = connector.fetch("https://docs.getdbt.com/docs/build/sql-models")

    assert doc is None


def test_fetch_returns_none_for_404():
    def not_found(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    transport = httpx.MockTransport(not_found)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("dbt", client=client, request_delay=0)

    assert connector.fetch("https://docs.getdbt.com/docs/build/gone") is None


# --- disk cache -----------------------------------------------------------------------


def test_fetch_uses_cache_on_second_call(tmp_path):
    call_count = {"n": 0}

    def counting_router(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return _fixture_router(request)

    transport = httpx.MockTransport(counting_router)
    client = httpx.Client(transport=transport)
    connector = DocsSiteConnector("dbt", client=client, request_delay=0, cache_dir=tmp_path)

    url = "https://docs.getdbt.com/docs/build/sql-models"
    doc1 = connector.fetch(url)
    calls_after_first = call_count["n"]
    doc2 = connector.fetch(url)

    assert doc1 is not None and doc2 is not None
    assert doc1.content == doc2.content
    assert call_count["n"] == calls_after_first  # second fetch hit the cache, not the network


# --- fixture router --------------------------------------------------------------------


def _fixture_router(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    routes = {
        "https://docs.getdbt.com/sitemap.xml": ("dbt_sitemap.xml", "application/xml"),
        "https://docs.getdbt.com/robots.txt": ("dbt_robots.txt", "text/plain"),
        "https://docs.getdbt.com/docs/build/sql-models": ("dbt_page.html", "text/html"),
        "https://docs.snowflake.com/en/sitemap.xml": ("snowflake_sitemap.xml", "application/xml"),
        "https://docs.snowflake.com/robots.txt": ("snowflake_robots.txt", "text/plain"),
        "https://docs.snowflake.com/en/user-guide/tables-storage-considerations": (
            "snowflake_page.html",
            "text/html",
        ),
        "https://docs.matillion.com/sitemap.xml": ("matillion_sitemap.xml", "application/xml"),
        "https://docs.matillion.com/robots.txt": ("matillion_robots.txt", "text/plain"),
        "https://docs.matillion.com/data-productivity-cloud/designer/docs/example-flights-slim/": (
            "matillion_page.html",
            "text/html",
        ),
    }
    if url in routes:
        filename, content_type = routes[url]
        return httpx.Response(
            200, content=fixture_bytes(filename), headers={"content-type": content_type}
        )
    return httpx.Response(404)

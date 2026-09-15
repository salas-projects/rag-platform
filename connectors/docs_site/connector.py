"""Docs-site connector: fetches public dbt, Snowflake, and Matillion documentation.

See adr/0007-html-fetch-and-parse.md for why httpx + BeautifulSoup/lxml with per-site
selectors was chosen over a generic extractor, and why the corpus is scoped the way it is.
"""

from __future__ import annotations

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from bs4 import BeautifulSoup

from core.ingestion.base import Connector, RawDocument

DEFAULT_CONFIG_PATH = Path(__file__).parent / "sites.yaml"
USER_AGENT = "rag-platform-docs-bot/0.1 (+https://github.com/salas-projects/rag-platform)"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass(frozen=True)
class SiteProfile:
    name: str
    base_url: str
    sitemap_url: str
    content_selector: str
    include: list[str]
    exclude: list[str]
    strip_selectors: list[str]
    date_selector: str | None


def load_site_profiles(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, SiteProfile]:
    raw = yaml.safe_load(config_path.read_text())
    return {
        name: SiteProfile(
            name=name,
            base_url=cfg["base_url"],
            sitemap_url=cfg["sitemap_url"],
            content_selector=cfg["content_selector"],
            include=cfg.get("include", []),
            exclude=cfg.get("exclude", []),
            strip_selectors=cfg.get("strip_selectors", []),
            date_selector=cfg.get("date_selector"),
        )
        for name, cfg in raw.items()
    }


def parse_sitemap(xml_bytes: bytes) -> list[tuple[str, str | None]]:
    """Returns (url, lastmod) pairs. lastmod is None when the sitemap doesn't carry one."""
    root = ET.fromstring(xml_bytes)
    entries = []
    for url_el in root.findall("sm:url", SITEMAP_NS):
        loc = url_el.findtext("sm:loc", namespaces=SITEMAP_NS)
        if not loc:
            continue
        lastmod = url_el.findtext("sm:lastmod", namespaces=SITEMAP_NS)
        entries.append((loc.strip(), lastmod.strip() if lastmod else None))
    return entries


def matches_scope(path: str, include: list[str], exclude: list[str]) -> bool:
    if any(pattern in path for pattern in exclude):
        return False
    return any(pattern in path for pattern in include)


def compute_section(url: str) -> str:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    return "/".join(parts[:-1]) if len(parts) > 1 else path


def resolve_last_updated(
    page_date: datetime | None,
    last_modified_header: str | None,
    sitemap_lastmod: str | None,
) -> datetime | None:
    """In-page date, then HTTP Last-Modified, then sitemap lastmod, then None.

    The in-page date wins because on statically-built docs sites the HTTP header reflects
    *deploy* time, not content change: dbt pages fetched minutes apart all report the same
    build timestamp while their own footers show the true (much older) edit date. Snowflake
    supplies none of the three and legitimately resolves to None — see ADR-0007.
    """
    if page_date:
        return page_date
    if last_modified_header:
        try:
            return parsedate_to_datetime(last_modified_header)
        except (TypeError, ValueError):
            pass
    if sitemap_lastmod:
        try:
            return datetime.fromisoformat(sitemap_lastmod).replace(tzinfo=UTC)
        except ValueError:
            pass
    return None


def extract_page_date(html: str, date_selector: str | None) -> datetime | None:
    """Pull an authored last-updated date out of the page itself (e.g. Docusaurus'
    `<time datetime=...>` footer), which is more truthful than a CDN's Last-Modified."""
    if not date_selector:
        return None
    soup = BeautifulSoup(html, "lxml")
    el = soup.select_one(date_selector)
    if el is None:
        return None
    raw = el.get("datetime") or el.get_text(strip=True)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_article(
    html: str, content_selector: str, strip_selectors: list[str] | None = None
) -> tuple[str, str] | None:
    """Returns (title, cleaned_text), or None if the selector matches nothing.

    `strip_selectors` removes site UI chrome (page-action toolbars, on-this-page TOCs,
    "Was this page helpful?" widgets) that otherwise prefixes every chunk from a site
    with identical boilerplate and degrades retrieval.
    """
    soup = BeautifulSoup(html, "lxml")
    container = soup.select_one(content_selector)
    if container is None:
        return None

    for selector in ["script", "style", "nav", ".headerlink", *(strip_selectors or [])]:
        for junk in container.select(selector):
            junk.decompose()

    heading = container.find(["h1", "h2"])
    title = heading.get_text(strip=True) if heading else None
    if not title and soup.title:
        title = soup.title.get_text(strip=True)
    title = title or "Untitled"

    # Docusaurus salts headings with zero-width spaces as anchor markers; they carry no
    # meaning and would otherwise ride along into the embeddings.
    text = container.get_text(separator="\n", strip=True).replace("​", "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


class RobotsChecker:
    """RFC 9309 robots.txt matcher.

    Deliberately not urllib.robotparser: the stdlib parser silently ignores `*`
    wildcards in rule paths, so Snowflake's `Disallow: /en/sql-reference/commands-*`
    reads as *allowed* there. A scraper that quietly ignores a disallow rule is worse
    than one that has none, so wildcard (`*`) and end-anchor (`$`) matching are
    implemented here instead. Fed already-fetched text so it is testable offline.
    """

    def __init__(self, robots_txt: str) -> None:
        self._rules: list[tuple[str, bool]] = []  # (path_pattern, allowed)
        in_group = False
        for raw_line in robots_txt.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            field, _, value = line.partition(":")
            field = field.strip().lower()
            value = value.strip()
            if field == "user-agent":
                in_group = value == "*"
            elif field in ("allow", "disallow") and in_group and value:
                self._rules.append((value, field == "allow"))

    @staticmethod
    def _matches(pattern: str, path: str) -> bool:
        anchored = pattern.endswith("$")
        if anchored:
            pattern = pattern[:-1]
        regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern)
        return bool(re.match(regex + ("$" if anchored else ""), path))

    def can_fetch(self, url: str) -> bool:
        path = urlparse(url).path or "/"
        best_len, best_allowed = -1, True
        for pattern, allowed in self._rules:
            if not self._matches(pattern, path):
                continue
            # RFC 9309: longest match wins; Allow wins ties.
            length = len(pattern.rstrip("$"))
            if length > best_len or (length == best_len and allowed):
                best_len, best_allowed = length, allowed
        return best_allowed


class DocsSiteConnector(Connector):
    def __init__(
        self,
        source: str,
        config_path: Path = DEFAULT_CONFIG_PATH,
        client: httpx.Client | None = None,
        limit: int | None = None,
        request_delay: float = 0.5,
        sleep_fn: Callable[[float], None] = time.sleep,
        max_retries: int = 3,
        cache_dir: Path | None = None,
    ) -> None:
        profiles = load_site_profiles(config_path)
        if source not in profiles:
            raise ValueError(f"Unknown docs_site source '{source}'; known: {sorted(profiles)}")
        self.name = source
        self.profile = profiles[source]
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True
        )
        self._limit = limit
        self._request_delay = request_delay
        self._sleep_fn = sleep_fn
        self._max_retries = max_retries
        self._cache_dir = cache_dir
        self._sitemap_lastmods: dict[str, str | None] = {}
        self._robots: RobotsChecker | None = None

    def _get_robots(self) -> RobotsChecker:
        if self._robots is None:
            robots_url = urljoin(self.profile.base_url, "/robots.txt")
            response = self._client.get(robots_url)
            self._robots = RobotsChecker(response.text if response.status_code == 200 else "")
        return self._robots

    def discover(self) -> Iterator[str]:
        response = self._client.get(self.profile.sitemap_url)
        response.raise_for_status()
        entries = parse_sitemap(response.content)
        robots = self._get_robots()

        yielded = 0
        for url, lastmod in entries:
            if self._limit is not None and yielded >= self._limit:
                return
            path = urlparse(url).path
            if not matches_scope(path, self.profile.include, self.profile.exclude):
                continue
            if not robots.can_fetch(url):
                continue
            self._sitemap_lastmods[url] = lastmod
            yielded += 1
            yield url

    def fetch(self, url: str) -> RawDocument | None:
        cached_html = self._read_cache(url)
        last_modified_header = None

        if cached_html is not None:
            html = cached_html
        else:
            response = self._fetch_with_retry(url)
            if response is None or response.status_code == 404:
                return None
            response.raise_for_status()
            html = response.text
            last_modified_header = response.headers.get("last-modified")
            self._write_cache(url, html)
            if self._request_delay:
                self._sleep_fn(self._request_delay)

        extracted = extract_article(
            html, self.profile.content_selector, self.profile.strip_selectors
        )
        if extracted is None:
            return None
        title, content = extracted
        if not content.strip():
            return None

        last_updated = resolve_last_updated(
            extract_page_date(html, self.profile.date_selector),
            last_modified_header,
            self._sitemap_lastmods.get(url),
        )

        return RawDocument(
            url=url,
            source=self.name,
            title=title,
            content=content,
            section=compute_section(url),
            last_updated=last_updated,
        )

    def _cache_path(self, url: str) -> Path | None:
        if self._cache_dir is None:
            return None
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.html"

    def _read_cache(self, url: str) -> str | None:
        path = self._cache_path(url)
        return path.read_text(encoding="utf-8") if path and path.exists() else None

    def _write_cache(self, url: str, html: str) -> None:
        path = self._cache_path(url)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")

    def _fetch_with_retry(self, url: str) -> httpx.Response | None:
        for attempt in range(self._max_retries):
            response = self._client.get(url)
            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 2**attempt))
                self._sleep_fn(retry_after)
                continue
            if response.status_code >= 500:
                self._sleep_fn(2**attempt)
                continue
            return response
        return None

    def close(self) -> None:
        self._client.close()

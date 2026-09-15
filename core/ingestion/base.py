"""Connector interface: the seam between a source (a docs site, a PDF folder, a GitHub
repo) and the rest of the pipeline. See docs/PROJECT_SCOPE.md, layer 1 (Ingestion)."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class RawDocument:
    """One fetched page/file, before chunking. `content_hash` lets downstream stages
    (chunking, embedding) skip unchanged documents on a re-crawl."""

    url: str
    source: str
    title: str
    content: str
    section: str
    last_updated: datetime | None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        digest = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        object.__setattr__(self, "content_hash", digest)


class Connector(ABC):
    """A source of raw documents. `docs/PROJECT_SCOPE.md`'s modularity section calls for
    building this interface correctly now even though only one connector exists."""

    name: str

    @abstractmethod
    def discover(self) -> Iterator[str]:
        """Yield the URLs/paths this connector will fetch."""

    @abstractmethod
    def fetch(self, url: str) -> RawDocument | None:
        """Fetch and parse a single URL/path. Returns None if it should be skipped
        (e.g. no extractable content) rather than raising."""

    def run(self) -> Iterator[RawDocument]:
        """Discover then fetch each item, skipping any that come back empty."""
        for url in self.discover():
            document = self.fetch(url)
            if document is not None:
                yield document

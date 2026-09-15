"""Tests for the connector interface itself (issue #11)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from core.ingestion import Connector, RawDocument


def make_doc(content: str = "hello", url: str = "https://example.com/a") -> RawDocument:
    return RawDocument(
        url=url,
        source="test",
        title="Title",
        content=content,
        section="section",
        last_updated=None,
    )


def test_content_hash_is_derived_and_stable():
    assert make_doc().content_hash == make_doc().content_hash


def test_content_hash_changes_with_content():
    assert make_doc("one").content_hash != make_doc("two").content_hash


def test_raw_document_is_frozen():
    doc = make_doc()
    with pytest.raises(AttributeError):
        doc.title = "changed"


def test_last_updated_may_be_none_or_datetime():
    assert make_doc().last_updated is None
    stamped = RawDocument(
        url="https://example.com/b",
        source="test",
        title="T",
        content="c",
        section="s",
        last_updated=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert stamped.last_updated.year == 2026


class _StubConnector(Connector):
    name = "stub"

    def __init__(self, urls: list[str], skip: set[str] | None = None) -> None:
        self._urls = urls
        self._skip = skip or set()

    def discover(self) -> Iterator[str]:
        yield from self._urls

    def fetch(self, url: str) -> RawDocument | None:
        if url in self._skip:
            return None
        return make_doc(content=url, url=url)


def test_run_composes_discover_and_fetch():
    connector = _StubConnector(["https://a", "https://b"])
    assert [d.url for d in connector.run()] == ["https://a", "https://b"]


def test_run_skips_documents_that_fetch_returns_none_for():
    connector = _StubConnector(["https://a", "https://b"], skip={"https://a"})
    assert [d.url for d in connector.run()] == ["https://b"]


def test_connector_cannot_be_instantiated_without_implementing_interface():
    with pytest.raises(TypeError):
        Connector()

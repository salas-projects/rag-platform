"""Manual/H5 verification entry point — not the Phase 1 end-to-end pipeline (that's #16).

uv run python -m connectors.docs_site --source dbt --limit 5
"""

from __future__ import annotations

import argparse
from pathlib import Path

from connectors.docs_site.connector import DocsSiteConnector, load_site_profiles

DEFAULT_CACHE_DIR = Path(".cache/docs_site")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(load_site_profiles()))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--dry-run", action="store_true", help="List discovered URLs only; fetch nothing"
    )
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    connector = DocsSiteConnector(
        source=args.source,
        limit=args.limit,
        cache_dir=None if args.no_cache else args.cache_dir,
    )
    try:
        if args.dry_run:
            for url in connector.discover():
                print(url)
            return

        count = 0
        for doc in connector.run():
            count += 1
            print(f"[{count}] {doc.url}")
            print(f"    title:        {doc.title}")
            print(f"    section:      {doc.section}")
            print(f"    last_updated: {doc.last_updated}")
            print(f"    content:      {len(doc.content)} chars")
            print(f"    preview:      {doc.content[:150]!r}")
    finally:
        connector.close()


if __name__ == "__main__":
    main()

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, TypedDict
import httpx
from typing_extensions import TypeAlias

from crawl4ai import (
    AsyncWebCrawler,
    BFSDeepCrawlStrategy,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    DomainFilter,
    FilterChain,
    URLFilter,
)

# ---------------------------------------------------------------------------
# Simplified type for each CrawlResultContainer-like object
# ---------------------------------------------------------------------------
class _CrawledPageData(TypedDict, total=False):
    url: str | None
    markdown_content: str | None
    html_content: str | None
    metadata: dict[str, Any] | None


CrawledPage: TypeAlias = _CrawledPageData


async def crawl_and_collect_urls(
    root_url: str,
    *,
    max_crawl_depth: int = 4,
    page_timeout_ms: int = 60_000,
    word_count_min: int = 10,
    include_external_links: bool = False,
) -> set[str]:
    """Crawl a single root URL and return a *set* of unique URLs discovered."""

    print(f"\n🚀 Starting URL discovery from {root_url} (max depth {max_crawl_depth})…")
    class ValidURLFilter(URLFilter):
        def apply(self, url: str) -> bool:
            try:
                resp = httpx.head(url, follow_redirects=True, timeout=0.5)
                if r.status_code == 405:
                    r = httpx.get(url, follow_redirects=True, timeout=0.5)
                return 200 <= resp.status_code < 400
            except Exception:
                return False

    url_filter_chain = FilterChain([
        DomainFilter(allowed_domains=["bulletin.brown.edu"]),
        ValidURLFilter()
    ])

    crawl_strat = BFSDeepCrawlStrategy(
        max_depth=max_crawl_depth,
        include_external=include_external_links,
        filter_chain=url_filter_chain
    )

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True,
        page_timeout=page_timeout_ms,
        word_count_threshold=word_count_min,
        deep_crawl_strategy=crawl_strat,
        js_code=[
            """(async () => {
                const selectors = [
                    '.toggle-button', "[data-toggle='collapse']", '.accordion-button',
                    "[role='button'][aria-expanded='false']",
                ];
                for (const selector of selectors) {
                    const toggles = document.querySelectorAll(selector);
                    for (const btn of toggles) {
                        if (btn.offsetParent !== null && !btn.disabled) {
                            try { btn.click(); await new Promise(r => setTimeout(r, 150)); }
                            catch (e) { console.warn('JS click error:', e); }
                        }
                    }
                }
            })();"""
        ],
    )

    seen = set()

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        async for page in await crawler.arun(url=root_url, config=run_cfg):
            print(f"\nPAGE {page.metadata.get('depth', '?')}] {page.url}")
            for link in page.links.get("internal", []) + page.links.get("external", []):
                href = link.get("href")
                if href and href not in seen:
                    print(f"    → discovered: {href}")
                    # if "wen" in href:
                    #     return seen
                    seen.add(href)

    print(f"\nTotal unique URLs: {len(seen)}")
    return seen


        # crawled_pages_raw = await crawler.arun(url=root_url, config=run_cfg)
        # crawled_pages: list[CrawledPage] = crawled_pages_raw if isinstance(crawled_pages_raw, list) else []

    # unique_urls: set[str] = set()

    # for page_item in crawled_pages:
    #     # Handle both object and dict variants
    #     doc_url: str | None = (
    #         getattr(page_item, "url", None)
    #         if hasattr(page_item, "url")
    #         else page_item.get("url")  # type: ignore[arg-type]
    #         if isinstance(page_item, dict)
    #         else None
    #     )
    #     if doc_url:
    #         unique_urls.add(doc_url)

    # print(f"🔎 Found {len(unique_urls)} unique URL(s) from {root_url}.")
    # return unique_urls


async def main() -> None:  # pragma: no cover
    """Entry point for running multiple crawls and saving **all** unique URLs."""

    universities_to_process = [
        {
            "name": "brown_university_bulletin_azindex_unfiltered",
            "root_url": "https://bulletin.brown.edu/azindex/",
            "crawl_depth": 2,
            "include_external": False,
        }
    ]

    all_urls: set[str] = set()

    for uni in universities_to_process:
        print(f"\n--- Processing: {uni['name'].replace('_', ' ').title()} ---")
        crawled_urls = await crawl_and_collect_urls(
            root_url=uni["root_url"],
            max_crawl_depth=uni.get("crawl_depth", 1),
            page_timeout_ms=uni.get("page_timeout", 60_000),
            word_count_min=uni.get("word_count_threshold", 20),
            include_external_links=uni.get("include_external", False)
        )
        all_urls.update(crawled_urls)

    # 📝 Save **all** unique URLs to a single JSON file called 'output1.json'
    output_file = Path("output1.json")
    output_file.write_text(json.dumps(sorted(all_urls), indent=2), encoding="utf8")
    print(f"\n💾 Saved {len(all_urls)} unique URL(s) to {output_file.resolve()}.")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())

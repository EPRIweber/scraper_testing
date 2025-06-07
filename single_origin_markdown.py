# single_origin_markdown.py

import os
import asyncio
from pathlib import Path

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    DefaultMarkdownGenerator
)
from crawl4ai.content_scraping_strategy import (
    LXMLWebScrapingStrategy,
)
from crawl4ai.content_filter_strategy import PruningContentFilter

async def ScrapeBrown_MarkdownOnly():
    url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"

    # 1) Browser configuration (headless)
    browser_cfg = BrowserConfig(headless=True, verbose=False)

    # 2) Choose a simple content filter to produce "fit_markdown"
    #    threshold=0.0 means “keep everything”; raise to 0.5+ to prune sidebars/etc.
    my_filter = PruningContentFilter(
        threshold=0.80
    )

    # 3) Build a CrawlerRunConfig with no LLM extraction:
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,
        word_count_threshold=1,

        # a) Omit extraction_strategy entirely
        extraction_strategy=None,

        # b) Use LXMLWebScrapingStrategy to fetch the page and produce Markdown
        scraping_strategy=LXMLWebScrapingStrategy(),
        markdown_generator=DefaultMarkdownGenerator(content_filter=my_filter),

        # c) Expand all accordions so Markdown contains every course block
        js_code=[
            """(async () => {
                  const toggles = document.querySelectorAll(".toggle-button");
                  for (let btn of toggles) {
                      btn.click();
                      await new Promise(r => setTimeout(r, 300));
                  }
            })();"""
        ],
    )

    # 4) Run the crawler (single URL)
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # Because there's no extraction_strategy, result is a list of CrawlResult objects
        results = await crawler.arun(url=url, config=run_cfg)

    # 5) We expect exactly one CrawlResult (since we passed a single URL, no deep crawl)
    if len(results) != 1:
        print(f"Warning: expected 1 result, got {len(results)}")
    result = results[0]

    # 6) Write out the full‐page Markdown + citations:
    Path("output").mkdir(exist_ok=True)
    # Path("output/brown_markdown_cit.md").write_text(
    #     result.markdown.markdown_with_citations or "", encoding="utf8"
    # )

    # 7) Write out the “fit_markdown” (filtered Markdown):
    Path("output/brown_markdown_filtered.md").write_text(
        result.markdown.fit_markdown or "", encoding="utf8"
    )

    print("Saved two Markdown files to output/")

if __name__ == "__main__":
    asyncio.run(ScrapeBrown_MarkdownOnly())

# single_origin_scrape.py

import os
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, LLMConfig, LXMLWebScrapingStrategy, RegexChunking
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter

# from crawl4ai_testing.crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
# from crawl4ai_testing.crawl4ai.deep_crawling import BestFirstCrawlingStrategy
# from crawl4ai_testing.crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
# from crawl4ai_testing.crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
# from crawl4ai_testing.crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
# from crawl4ai_testing.crawl4ai.extraction_strategy import LLMExtractionStrategy


prompt = """
Identify each distinct course block.
For each block:
    • course_code: the subject + number (e.g., 'BIOL 0040').
    • course_title: the title right after the code and period.
    • course_description: the body text up until prerequisites/enrollment.
    • If you see 'Prerequisite: <CODE>', put that code under prerequisites[].
Return a JSON array of objects exactly matching this schema.(ignore extraneous data which does not fit the schema).

Example course listing:

**BIOL 0280. Biochemistry**.
Lectures and recitation sections explore the mechanisms involved in the principles of macromolecular structure and function, the organization and regulation of pathways for intermediary metabolism, and the transfer of information from genes to proteins. Expected background: Cell and Molecular Biology ([BIOL 0500](https://bulletin.brown.edu/search/?P=BIOL%200500 "BIOL 0500")) or another intermediate level course providing background in molecular level thinking, e.g. [BIOL 0470](https://bulletin.brown.edu/search/?P=BIOL%200470 "BIOL 0470"), [BIOL 0530](https://bulletin.brown.edu/search/?P=BIOL%200530 "BIOL 0530") or [NEUR 1020](https://bulletin.brown.edu/search/?P=NEUR%201020 "NEUR 1020").
Spr | BIOL0280 | S01 | 20181 | TTh | 1:00-2:20(08) | (W. Holmes)  
---|---|---|---|---|---|---  

Example formatted json:
{
    "course_code": "BIOL 0280",
    "course_title": "Biochemistry",
    "course_description": "Lectures and recitation sections explore the mechanisms involved in the principles of macromolecular structure and function, the organization and regulation of pathways for intermediary metabolism, and the transfer of information from genes to proteins."
}
"""

class CourseSchema(BaseModel):
    course_code: str = Field(..., description="Catalog number, e.g., 'BIOL 0040'")
    course_title: str = Field(..., description="Title, e.g., 'Nutrition for Fitness and Physical Activity'")
    course_description: str = Field(..., description="Complete text description of the specific course")


async def ScrapeBrown():
    # url = "https://bulletin.brown.edu/"
    url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    llm_cfg = LLMConfig(provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY"))
    
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["bulletin.brown.edu"]),
        URLPatternFilter(patterns=["*course*", "*catalog*", "*curriculum*", "*department*", "*program*"]),
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["course", "courses", "catalog", "credits", "program", "curriculum"],
        weight=0.8
    )

    my_filter = PruningContentFilter(threshold=0.5)

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,
        word_count_threshold=1,

        # deep_crawl_strategy = BestFirstCrawlingStrategy(
        #     max_depth=5,
        #     include_external=False,
        #     filter_chain=filter_chain,
        #     url_scorer=keyword_scorer
        # ),
        # chunking_strategy=RegexChunking(patterns=[r"<[^>]*>"]),

        js_code=[
            """(async () => {
                  const toggles = document.querySelectorAll(".toggle-button");
                  for (let btn of toggles) {
                      btn.click(); 
                      await new Promise(r => setTimeout(r, 300));
                  }
            })();"""
        ],

        # Ommiting extraction strategy defaults to returning a list of links discovered by the crawl stragegy, useful for testing
        # extraction_strategy=LLMExtractionStrategy(
        #     llm_config=llm_cfg,
        #     schema=CourseSchema.model_json_schema(),
        #     extraction_type="schema",
        #     # input_format="html",
        #     content_filter=my_filter,
        #     force_json_response=True,
        #     instruction=prompt,
        #     # apply_chunking=False
        # ),
        extraction_strategy=LLMExtractionStrategy(
            llm_config=llm_cfg,
            schema=CourseSchema.model_json_schema(),
            extraction_type="fitted_markdown",
            instruction=prompt,
            apply_chunking=False,
            # content_filter=my_filter,
            force_json_response=True,
        ),
        # markdown_generator=DefaultMarkdownGenerator(content_filter=my_filter),
        # scraping_strategy=LXMLWebScrapingStrategy(),
        # markdown_generator=DefaultMarkdownGenerator(content_filter=my_filter)
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    if run_cfg.extraction_strategy is not None:
        courses = result.extracted_content or []
        parsed_courses = json.loads(courses)
        out_file = Path("output/brown_courses.json")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(parsed_courses, indent=2), encoding="utf8")

        # Path("output/brown_markdown_cit.md").write_text(result.markdown.markdown_with_citations or "", encoding="utf8")
        # Path("output/brown_markdown_filtered.md").write_text(result.markdown.fit_markdown or "", encoding="utf8")
        # print(f"Saved {len(parsed_courses)} courses + markdown files.")
        print(result.markdown.fit_html)

    else:
        urls = [r.url for r in result]
        out_file = Path("output/brown_discovered_urls.json")
        out_file.write_text(json.dumps(urls, indent=2), encoding="utf8")
        print(f"Saved {len(urls)} URLs.")


asyncio.run(ScrapeBrown())
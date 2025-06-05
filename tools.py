# tools.py
import os
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# from crawl4ai_testing.crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
# from crawl4ai_testing.crawl4ai.deep_crawling import BestFirstCrawlingStrategy
# from crawl4ai_testing.crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
# from crawl4ai_testing.crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
# from crawl4ai_testing.crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
# from crawl4ai_testing.crawl4ai.extraction_strategy import LLMExtractionStrategy

class CourseSchema(BaseModel):
    course_code: str = Field(..., description="Catalog number, e.g., 'ENGN 1640'")
    course_title: str = Field(..., description="Title of course, e.g., 'Design of Computing Systems'")
    course_description: str = Field(..., description="Full course description text")

async def ScrapeBrown():
    url = "https://bulletin.brown.edu/"
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    llm_cfg = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
    
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["bulletin.brown.edu"]),
        URLPatternFilter(patterns=["*course*", "*catalog*", "*curriculum*", "*department*", "*program*"]),
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["course", "courses", "catalog", "credits", "program", "curriculum"],
        weight=0.8  # Tune as needed
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,
        word_count_threshold=1,

        deep_crawl_strategy = BestFirstCrawlingStrategy(
            max_depth=5,
            include_external=False,
            # filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        js_code=[
            """(async () => {
                  const toggles = document.querySelectorAll(".toggle-button");
                  for (let btn of toggles) {
                      btn.click(); 
                      await new Promise(r => setTimeout(r, 300));
                  }
            })();"""
        ],
        # extraction_strategy=LLMExtractionStrategy(
        #     llm_config=llm_cfg,
        #     schema=CourseSchema.model_json_schema(),
        #     extraction_type="model_json_schema",
        #     instruction=(
        #         "Extract each course as a JSON object with the correct corresponding fields: course_code, course_title, course_description."
        #     )
        # ),
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    # if hasattr(run_cfg, 'extraction_strategy'):
    #     courses = result.extracted_content or []
    #     parsed_courses = json.loads(courses)
    #     out_file = Path("output/brown_courses.json")
    #     out_file.parent.mkdir(parents=True, exist_ok=True)
    #     out_file.write_text(json.dumps(parsed_courses, indent=2), encoding="utf8")
    #     print(f"Saved {len(parsed_courses)} courses.")
    # else:
        # urls = [r.url for r in result]
        # out_file = Path("output/brown_discovered_urls.json")
        # out_file.write_text(json.dumps(urls, indent=2), encoding="utf8")
        # print(f"Saved {len(urls)} URLs.")
    urls = [r.url for r in result]
    out_file = Path("output/brown_discovered_urls.json")
    out_file.parent.mkdir(exist_ok=True, parents=True)
    out_file.write_text(json.dumps(urls, indent=2), encoding="utf8")
    print(f"Saved {len(urls)} URLs.")


asyncio.run(ScrapeBrown())
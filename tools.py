# tools.py
import os
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field
from extraction_schemas import CourseSchema

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, LLMConfig, LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter, RelevantContentFilter, DefaultContentFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.extraction_strategy import LLMExtractionStrategy

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
    • If you see 'Enrollment limited to X', set extra_info.enrollment_limit = X.
    • If you see 'Instructor permission required', set extra_info.instructor_permission_required = true.
Return a JSON array of objects exactly matching this schema.

Example course with output:
"""


async def ScrapeBrown():
    # url = "https://bulletin.brown.edu/"
    url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    llm_cfg = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))
    
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=["bulletin.brown.edu"]),
        URLPatternFilter(patterns=["*course*", "*catalog*", "*curriculum*", "*department*", "*program*"]),
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["course", "courses", "catalog", "credits", "program", "curriculum"],
        weight=0.8
    )

    my_filter = DefaultContentFilter(threshold=0.0)

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
        #     input_format="fit_markdown",
        #     content_filter=my_filter,
        #     force_json_response=True,
        #     llm_config=llm_cfg,
        #     schema=CourseSchema.model_json_schema(),
        #     extraction_type="schema",
        #     instruction=prompt
        # ),
        extraction_strategy=LLMExtractionStrategy(
            llm_config=llm_cfg,
            schema=CourseSchema.model_json_schema(),
            extraction_type="model_json_schema",
            instruction=prompt
        ),
        scraping_strategy=LXMLWebScrapingStrategy(
            markdown_generator=DefaultMarkdownGenerator(content_filter=my_filter)
        ),

    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    if run_cfg.extraction_strategy is not None:
        courses = result.extracted_content or []
        parsed_courses = json.loads(courses)
        out_file = Path("output/brown_courses.json")
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(parsed_courses, indent=2), encoding="utf8")

        Path("output/brown_markdown_cit.md").write_text(result.markdown_with_citations or "")
        Path("output/brown_markdown_filtered.md").write_text(result.fit_markdown or "")
        print(f"Saved {len(parsed_courses)} courses + markdown files.")

    else:
        urls = [r.url for r in result]
        out_file = Path("output/brown_discovered_urls.json")
        out_file.write_text(json.dumps(urls, indent=2), encoding="utf8")
        print(f"Saved {len(urls)} URLs.")


asyncio.run(ScrapeBrown())
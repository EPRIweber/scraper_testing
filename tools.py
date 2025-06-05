# tools.py
import os
import asyncio
import json
from pathlib import Path
from crawl4ai_testing import AsyncWebCrawler, BFSDeepCrawlStrategy, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai_testing.crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

class CourseSchema(BaseModel):
    course_code: str = Field(..., description="Catalog number, e.g., 'ENGN 1640'")
    course_title: str = Field(..., description="Title of course, e.g., 'Design of Computing Systems'")
    course_description: str = Field(..., description="Full course description text")

async def ScrapeBrown():
    url = "https://bulletin.brown.edu/"
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    llm_cfg = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"))

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=120000,
        word_count_threshold=1,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=5,
            include_external=False
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
        extraction_strategy=LLMExtractionStrategy(
            llm_config=llm_cfg,
            schema=CourseSchema.model_json_schema(),
            extraction_type="model_json_schema",
            instruction=(
                "Extract each course as a JSON object with the correct corresponding fields: course_code, course_title, course_description."
            )
        ),
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    courses = result.extracted_content or []
    parsed_courses = json.loads(courses)
    out_file = Path("output/brown_courses.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(parsed_courses, indent=2), encoding="utf8")
    print(f"Saved {len(parsed_courses)} courses.")

asyncio.run(ScrapeBrown())
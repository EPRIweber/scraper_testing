import requests, os, json, asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, JsonCssExtractionStrategy, LXMLWebScrapingStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from bs4 import BeautifulSoup
from pathlib import Path
# from ..output import brown_schema as schema
import json

with open('schemas/brown_schema.json', 'r') as f:
    schema = json.load(f)

url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
page = requests.get(url).text
soup = BeautifulSoup(page, "lxml")
container = soup  # .select_one("#courseinventory")
html_snippet = container # .encode_contents().decode() if container else page

async def scrape_with_schema():
    browser_cfg = BrowserConfig(headless=True)
    extract_strat = JsonCssExtractionStrategy(schema)

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=extract_strat
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_cfg
        )

    courses = result.extracted_content  # list of dicts
    parsed_courses = json.loads(courses)
    out_file = Path("output/brown_courses.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(parsed_courses, indent=2), encoding="utf8")

asyncio.run(scrape_with_schema())
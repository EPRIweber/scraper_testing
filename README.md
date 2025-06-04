# CURRENT NOTES

---

## **Step 1: Goal**

* **Find all course listing pages** at Brown University (and not waste LLM calls on irrelevant pages).
* **Efficiently extract structured course data** from each one.

---

## **Step 2: Plan the Crawl**

### **A. Use a Deep Crawl (BestFirst Recommended)**

* **Why?**: BestFirstCrawling with keyword scorers will focus crawling effort on the most “course-relevant” pages first (faster, cheaper, less noisy).
* **Alternative:** BFS/DFS work, but you may get lots of “policy” or “about” pages before courses.

---

### **B. URL Filtering**

* **Use URLPatternFilter** to only allow links matching patterns like `*course*`, `*catalog*`, `*curriculum*`, `*program*`, `*department*`, etc.

  * This avoids crawling administrative or irrelevant pages.
* **Combine with DomainFilter** to stay within `bulletin.brown.edu`.

---

### **C. Scoring/Keyword Relevance**

* **Use KeywordRelevanceScorer** to score URLs higher if their content or metadata includes “course”, “catalog”, “credits”, etc.
* Set a `score_threshold` if needed to cut off weak matches.

---

### **D. Control Crawl Size**

* **Set sensible `max_depth` (e.g. 3-4)** – going too deep will create huge crawls.
* **Set `max_pages` (e.g. 100-200)** as a safety limit (fine-tune as needed).
* Use **streaming** mode to process results as they come in.

---

## **Step 3: Example Crawl4AI Config**

```python
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# --- FILTER & SCORER SETUP ---
filter_chain = FilterChain([
    DomainFilter(allowed_domains=["bulletin.brown.edu"]),
    URLPatternFilter(patterns=["*course*", "*catalog*", "*curriculum*", "*department*", "*program*"]),
])

keyword_scorer = KeywordRelevanceScorer(
    keywords=["course", "courses", "catalog", "credits", "program", "curriculum"],
    weight=0.8  # Tune as needed
)

strategy = BestFirstCrawlingStrategy(
    max_depth=4,  # Safe starting point
    include_external=False,
    filter_chain=filter_chain,
    url_scorer=keyword_scorer,
    max_pages=150  # Safety
)

# --- CRAWLER CONFIG ---
run_cfg = CrawlerRunConfig(
    deep_crawl_strategy=strategy,
    extraction_strategy=LLMExtractionStrategy(
        # your schema here
    ),
    stream=True,  # Process as found
    page_timeout=90000,  # Adjust as needed
)

async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
    async for result in await crawler.arun("https://bulletin.brown.edu/", config=run_cfg):
        # You can inspect/print URLs here, only saving the ones that pass your logic!
        print(result.url)
        # You can then run LLM extraction on these or do additional filtering
```

---

## **Step 4: (Optional) Two-Pass Approach**

* **Pass 1:** Only crawl & collect URLs with high course/content relevance (skip LLM extraction for now).
* **Pass 2:** For the filtered list of URLs, run your LLM extraction.
  *This saves compute/cost if you want to be extra frugal or the site is huge.*

---

## **Step 5: Tips**

* **Tune your patterns and keywords!** Start with broad patterns, then narrow as you see what’s being crawled.
* **Stream/Batch Results:** Start saving URLs/metadata immediately (streaming), rather than waiting for crawl to finish.
* **Inspect a sample:** After the first crawl, check the URLs—are you catching all programs, undergrad, grad, etc.? Tweak filters as needed.

---

## **Summary Table**

| Tool/Concept                | Purpose                                | Example                 |
| --------------------------- | -------------------------------------- | ----------------------- |
| `BestFirstCrawlingStrategy` | Crawl most relevant pages first        | With keyword scorer     |
| `URLPatternFilter`          | Match only URLs likely to have courses | `"*course*"` etc.       |
| `DomainFilter`              | Stay within bulletin.brown.edu         |                         |
| `KeywordRelevanceScorer`    | Prioritize course-related pages        | `["course", "catalog"]` |
| `max_pages`, `max_depth`    | Crawl limits                           |                         |
| `stream=True`               | Process as found                       |                         |

---

**Want a working code template with your schema and LLM extraction plugged in? Or want to discuss a “discovery only” pass vs. extraction in one step?** Just ask!
**

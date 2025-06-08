from crawl4ai import JsonCssExtractionStrategy, LLMConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from bs4 import BeautifulSoup
import requests, os, json

# 1) Fetch the page and pull out your course‐container
url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
page = requests.get(url).text
soup = BeautifulSoup(page, "lxml")
container = soup.select_one("#courseinventory")
html_snippet = container.encode_contents().decode() if container else page

# 2) Prune it to only text-dense blocks
pruner = PruningContentFilter(threshold=0.5)
# filter_content returns a List[str] of HTML strings for the chunks it keeps
filtered_chunks = pruner.filter_content(html_snippet)
# stitch them back together into one little HTML payload
html_for_schema = "\n".join(filtered_chunks)

# 3) Now pass that much smaller blob to the LLM
llm_cfg = LLMConfig(provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY"))
schema = JsonCssExtractionStrategy.generate_schema(
    html_for_schema,
    schema_type="CSS",
    query=(
        "Extract every distinct course listing in this snippet. "
        "For each block produce fields: course_code, course_title, course_description."
    ),
    target_json_example=json.dumps([{
        "course_code": "BIOL 0280",
        "course_title": "Biochemistry",
        "course_description": "Lectures and recitation sections explore…"
    }], indent=2),
    llm_config=llm_cfg
)

print("Generated schema:\n", json.dumps(schema, indent=2))

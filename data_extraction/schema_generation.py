from crawl4ai import JsonCssExtractionStrategy, LLMConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from bs4 import BeautifulSoup
import requests, os, json
from pathlib import Path

# 1) Fetch the page and pull out your course‐container
url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
page = requests.get(url).text
soup = BeautifulSoup(page, "lxml")
container = soup  # .select_one("#courseinventory")
html_snippet = container.encode_contents().decode() if container else page

# 2) Prune it to only text-dense blocks
pruner = PruningContentFilter(threshold=0.5)
# filter_content returns a List[str] of HTML strings for the chunks it keeps
filtered_chunks = pruner.filter_content(html_snippet)
# stitch them back together into one little HTML payload
html_for_schema = "\n".join(filtered_chunks)

query="""
Generate a JSON _schema_ (not the data!) filling in the valid CSS selectors for each course block and each of the course fields.
**Schema must be structured exactly like this**:

{
  "name": "Course Block",
  "baseSelector": "<CSS selector, e.g. div.courseblock>",
  "fields": [
    { "name": "course_code",        "selector": "<CSS>", "type": "text" },
    { "name": "course_title",       "selector": "<CSS>", "type": "text" },
    { "name": "course_description", "selector": "<CSS>", "type": "text" }
  ]
}
"""


# 3) Now pass that much smaller blob to the LLM
llm_cfg = LLMConfig(
    provider="openai/gpt-4o-mini",
    api_token=os.getenv("OPENAI_API_KEY"),
    temprature=0.0
)
# llm_cfg = LLMConfig(
#     provider="ollama/gemma3:12b",
#     # provider="ollama/mistral",
#     base_url="http://localhost:11434",
#     api_token=None
# )

schema = JsonCssExtractionStrategy.generate_schema(
    html_for_schema,
    schema_type="CSS",
    query=query,
    target_json_example=json.dumps([{
        "course_code": "BIOL 0280",
        "course_title": "Biochemistry",
        "course_description": "Lectures and recitation sections explore…"
    }], indent=2),
    llm_config=llm_cfg
)

print("Generated schema:\n", json.dumps(schema, indent=2))

file = Path('output/brown_schema.json')

with open(file, "w") as out:
    out.write(json.dumps(schema, indent=2))
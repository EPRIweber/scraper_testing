from crawl4ai import JsonCssExtractionStrategy, LLMConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from bs4 import BeautifulSoup
import requests, os, json
from pathlib import Path

url = "https://bulletin.brown.edu/biologyandmedicine/biology-undergraduate/#courseinventory"
page = requests.get(url).text
soup = BeautifulSoup(page, "lxml")
container = soup  # .select_one("#courseinventory")
html_snippet = container.encode_contents().decode() if container else page

pruner = PruningContentFilter(threshold=0.5)
filtered_chunks = pruner.filter_content(html_snippet)
html_for_schema = "\n".join(filtered_chunks)

query="""
Generate a JSON schema (not the data!) using valid CSS selectors that will be used to select distinct course blocks from the given HTML.

Requirements:
- **Output must be valid JSON only**, following exactly the structure below.
- **Mandatory fields** (every course block will ALWAYS have these):
  - `course_title`
  - `course_description`
- **Optional field** (include only if it can be separated via their own CSS selector):
  - `course_code`

**Schema must be structured like this**:

{
  "name": "Course Block",
  "baseSelector": "<CSS selector, e.g. div.courseblock>",
  "fields": [
    { "name": "course_title",       "selector": "<CSS selector>", "type": "text" },
    { "name": "course_description", "selector": "<CSS selector>", "type": "text" }
    // course_code included if present and seperable
  ]
}
"""

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
    html=html_for_schema,
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

file = Path('schemas/brown_schema.json')

with open(file, "w") as out:
    out.write(json.dumps(schema, indent=2))
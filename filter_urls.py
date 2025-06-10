#!/usr/bin/env python3
"""
filter_urls.py – strip URLs that are clearly not course pages.

Default I/O:
    • Input :  output1.json
    • Output:  output2.json

You can override either path on the CLI:
    $ python filter_urls.py -i some_input.json -o some_output.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import TypedDict, cast

try:
    from typing import NotRequired            # Py ≥ 3.11
except ImportError:                          # Py ≤ 3.10
    from typing_extensions import NotRequired

# ── TypedDict ───────────────────────────────────────────────────────────────
class Page(TypedDict):
    url: str
    metadata: NotRequired[str]

# ── negative-keyword regex ─────────────────────────────────────────────────
NEGATIVE_PATTERNS = [
    r"calendar", r"events?", r"schedule", r"news(letter)?", r"blog",
    r"press", r"contact", r"admissions?", r"apply", r"staff",
    r"faculty/(?!courses?)", r"directory", r"login", r"register",
    r"privacy", r"policy", r"copyright", r"legal",
    r"tuition", r"financial[-_]?aid", r"donat(e|ion|ions?)", r"give",
    r"alumni", r"maps?/?$", r"campus[-_]?map", r"administration",
]
NEGATIVE_REGEX = re.compile("|".join(NEGATIVE_PATTERNS), re.I)

# ── helpers ────────────────────────────────────────────────────────────────
def definitely_not_course(page: Page) -> bool:
    haystacks = [page["url"]]
    if meta := page.get("metadata"):
        haystacks.append(meta)
    return any(NEGATIVE_REGEX.search(h) for h in haystacks)

def filter_urls(data: list[Page]) -> list[Page]:
    return [p for p in data if not definitely_not_course(p)]

# ── CLI ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keyword-based URL filtering (defaults: input=output1.json, output=output2.json)."
    )
    parser.add_argument(
        "-i", "--infile",
        default="output1.json",
        help="crawler JSON file to read (default: output1.json)",
    )
    parser.add_argument(
        "-o", "--outfile",
        default="output2.json",
        help="destination JSON for filtered URLs (default: output2.json)",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.infile).read_text(encoding="utf-8"))

    # accept list[str] or list[dict]
    if raw and isinstance(raw[0], str):
        pages: list[Page] = [{"url": cast(str, u)} for u in raw]
    else:
        pages = cast(list[Page], raw)

    kept = filter_urls(pages)
    Path(args.outfile).write_text(
        json.dumps(sorted({p["url"] for p in kept}), indent=2),
        encoding="utf-8",
    )
    print(f"✅ kept {len(kept)}/{len(pages)} URLs → {args.outfile}")

if __name__ == "__main__":
    main()

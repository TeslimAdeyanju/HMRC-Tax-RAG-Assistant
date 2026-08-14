"""
Ingestion for a finance/tax-domain RAG dataset, sourced from GOV.UK's
HMRC internal manuals (public, no auth required).

Two GOV.UK endpoints are used together because the Content API returns a
single page's content but does not expose a full listing of a manual's
pages, while the Search API can list pages but only returns a short
snippet, not the full body:

- Search API:  https://www.gov.uk/api/search.json
    used to enumerate every page belonging to a given manual
- Content API: https://www.gov.uk/api/content/<path>
    used to fetch the full HTML body for each page

Output: data/docs.json, a flat list of dicts shaped like:
    {"id": ..., "manual": ..., "title": ..., "text": ..., "url": ...}
ready to drop straight into minsearch / sqlitesearch.
"""

import json
import re
import time
from html import unescape
from pathlib import Path

import requests

BASE = "https://www.gov.uk/api/content"
SEARCH = "https://www.gov.uk/api/search.json"


def list_section_paths(manual_slug: str, max_pages: int = 300) -> list[str]:
    prefix = f"/hmrc-internal-manuals/{manual_slug}/"
    paths: list[str] = []
    start = 0
    while len(paths) < max_pages:
        resp = requests.get(
            SEARCH,
            params={
                "filter_format": "hmrc_manual_section",
                "fields": "link",
                "count": 1500,
                "start": start,
            },
            timeout=30,
        ).json()
        results = resp.get("results", [])
        if not results:
            break
        paths += [r["link"] for r in results if r["link"].startswith(prefix)]
        start += 1500
        if start > resp.get("total", 0):
            break
        time.sleep(0.2)
    # de-dupe while preserving order, then cap
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique_paths.append(p)
    return unique_paths[:max_pages]


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return unescape(re.sub(r"\s+", " ", text)).strip()


def fetch_section(path: str) -> dict:
    resp = requests.get(f"{BASE}{path}", timeout=30).json()
    body = resp.get("details", {}).get("body", "")
    return {
        "id": resp["base_path"].rsplit("/", 1)[-1],
        "manual": resp["base_path"].split("/")[2],
        "title": resp["title"],
        "text": strip_html(body),
        "url": f"https://www.gov.uk{resp['base_path']}",
    }


def build_docs(manual_slug: str = "company-taxation-manual", max_pages: int = 300) -> list[dict]:
    docs = []
    paths = list_section_paths(manual_slug, max_pages)
    print(f"found {len(paths)} pages for manual '{manual_slug}'")
    for i, path in enumerate(paths, start=1):
        try:
            doc = fetch_section(path)
            if doc["text"]:
                docs.append(doc)
        except Exception as e:
            print("skip", path, e)
        if i % 25 == 0:
            print(f"  fetched {i}/{len(paths)}")
        time.sleep(0.2)
    return docs


MANUALS = [
    "company-taxation-manual",
    "vat-registration-manual",
    "paye-manual",
    "capital-gains-manual",
    "capital-allowances-manual",
]


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "data" / "docs.json"
    existing = json.loads(out_path.read_text()) if out_path.exists() else []
    by_id = {d["id"]: d for d in existing}

    for manual in MANUALS:
        if any(d["manual"] == manual for d in existing):
            print(f"skip {manual}, already in docs.json")
            continue
        docs = build_docs(manual, max_pages=300)
        for d in docs:
            by_id[d["id"]] = d

    all_docs = list(by_id.values())
    out_path.write_text(json.dumps(all_docs, indent=2))
    print(f"wrote {len(all_docs)} docs to {out_path}")

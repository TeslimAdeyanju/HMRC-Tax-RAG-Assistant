# HMRC Tax RAG Assistant

A retrieval-augmented Q&A agent that answers UK tax questions using HMRC's own
internal manuals as its knowledge base, instead of relying on an LLM's
built-in (and often outdated or wrong) knowledge of tax law.

Built by [Teslim Adeyanju, ACA](https://adeyanjuteslim.co.uk) as a way to combine
professional accounting knowledge with hands-on LLM/RAG engineering.

## Why this exists

Tax rules are precise, change often, and are a poor fit for an LLM to
answer from memory. This project grounds every answer in the actual text of
HMRC's internal manuals, retrieved at query time, so answers are traceable
back to a real source page on GOV.UK rather than invented.

## How it works

1. **Scrape** — `src/scrape_manuals.py` pulls every section of five HMRC
   internal manuals from the public GOV.UK Content and Search APIs (no auth
   required) and writes them to `data/docs.json`.
2. **Index** — the sections are indexed for keyword search, either in-memory
   with [`minsearch`](https://github.com/alexeygrigorev/minsearch) or
   persisted to SQLite with [`sqlitesearch`](https://github.com/alexeygrigorev/sqlitesearch).
3. **Retrieve + generate** — `src/tax_knowledge_agent.py` defines
   `TaxKnowledgeAgent`, which searches the index for the most relevant
   sections, builds a grounded prompt from them, and asks an LLM to answer
   using only that context (or say "I don't know").

```
question ─▶ search index ─▶ top-k HMRC manual sections ─▶ prompt ─▶ LLM ─▶ answer
```

## Data

`data/docs.json` contains 1,299 sections scraped from five HMRC internal
manuals:

| Manual | Topic |
|---|---|
| `company-taxation-manual` | Corporation tax |
| `vat-registration-manual` | VAT registration |
| `paye-manual` | PAYE |
| `capital-gains-manual` | Capital gains tax |
| `capital-allowances-manual` | Capital allowances |

Each record: `{"id", "manual", "title", "text", "url"}`, where `url` links
back to the original GOV.UK page.

## Project layout

```
.
├── data/
│   └── docs.json                      # scraped HMRC manual sections
├── src/
│   ├── scrape_manuals.py              # GOV.UK API -> data/docs.json
│   ├── load_index.py                  # load docs.json, build a minsearch Index
│   └── tax_knowledge_agent.py         # TaxKnowledgeAgent: search -> prompt -> answer
├── notebooks/
│   ├── 01_prototype_minsearch_rag.ipynb   # first pass: in-memory index + RAG loop
│   └── 02_sqlite_index_and_agent.ipynb    # persisted index + TaxKnowledgeAgent class
└── pyproject.toml
```

## Setup

```bash
uv sync
cp .env.example .env   # add your OPENAI_API_KEY
```

## Usage

```python
from load_index import load_faq_data, build_index
from tax_knowledge_agent import TaxKnowledgeAgent
from openai import OpenAI

documents = load_faq_data()
index = build_index(documents)

agent = TaxKnowledgeAgent(index=index, llm_client=OpenAI())
answer = agent.rag("What counts as capital expenditure for capital allowances purposes?")
print(answer)
```

Or open `notebooks/02_sqlite_index_and_agent.ipynb` for a persisted,
SQLite-backed version of the same flow.

## Roadmap

- [ ] Hybrid keyword + vector search
- [ ] Evaluation set of tax questions with expected source sections
- [ ] Answer citations (surface the source `url` alongside the answer)
- [ ] Simple chat UI

## Credits

Started as part of the DataTalks.Club LLM Zoomcamp; this repo is the
standalone, ongoing continuation of that work.

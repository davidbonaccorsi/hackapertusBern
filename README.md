# Hack Apertus Liebefeld — Research & Expertise Navigator

Prototype for challenge **Bern Economic Development Agency: Research & Expertise Navigator**.

## 🎯 The Challenge
Bern Economic Development Agency — Research & Expertise Navigator  
https://app.notion.com/p/hackapertus/Bern-Economic-Development-Agency-fe5b4fec112a833daf9401a4771a7c12?source=copy_link

## What this prototype does
This repository provides an end-to-end prototype that:
1. crawls public web pages from the UniBE ecosystem, ARTORG and Diabetes Center Berne;
2. extracts and enriches people/expertise/project/service signals;
3. stores structured records in SQLite;
4. supports natural-language and keyword search with synonym expansion;
5. returns **source-backed structured results**.

Every result includes a source URL and an explicit reason for the match.

## Repository structure

| Path | What it is |
| --- | --- |
| `README.md` | Project overview and run instructions |
| `technical_report.md` | Architecture, data, limitations, reproducibility |
| `src/` | Prototype source code |

## Environment

Expected environment variables (for compatibility with hack requirements):

```bash
export LLM_NAME="swiss-ai/Apertus-v1.5-8B"
export LLM_BASE_URL="https://your-endpoint"
export LLM_API_KEY="your-key"
```

Current prototype does not require LLM calls at runtime (deterministic extraction/ranking baseline), but keeps these variables for drop-in Apertus integration.

## Quick start

```bash
cd /home/runner/work/hackapertus-bern/hackapertus-bern
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

### 1) Build the knowledge base

```bash
python src/main.py ingest --config src/config/sources.json --db src/data/navigator.db
```

### 2) Query it

```bash
python src/main.py search "glucose sensors" --db src/data/navigator.db --top-k 10
```

The search output is JSON with structured fields:
- person/contact person
- functions and affiliations
- units/groups
- expertise
- related projects/activities
- infrastructure/services
- reason for match
- source URL/title

## Extend to new institutions
Add a new entry to `src/config/sources.json` with:
- `name`
- `seeds` (starting URLs)
- `allowed_domains`
- `max_pages`

No pipeline code changes are required.

## License
Apache-2.0 (repository default).

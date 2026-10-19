# Technical report — Bern Research & Expertise Navigator, Team Apertus Bern

A deeper write-up than the README: what you built, how it works, and what the
numbers say.

- **Challenge:** Bern Economic Development Agency — Research & Expertise Navigator
- **Event:** On-site Liebefeld
- **Team:** Team Apertus Bern — member1, member2, member3
- **Demo:** to be added

## 1. Summary

We built an end-to-end prototype that turns distributed public institutional websites into a searchable, traceable expertise navigator. The pipeline crawls configured public sources (UniBE ecosystem, ARTORG, Diabetes Center Berne), extracts structured metadata (people/contacts, expertise, projects, services, units), indexes records in SQLite, and serves natural-language/keyword search with synonym expansion. Results are returned in a structured JSON schema with an explicit reason-for-match and direct source URL for full traceability.

## 2. Architecture

1. **Discovery & crawling** (`src/navigator/crawler.py`): URL queue crawl from configured seed pages, constrained by source domain allow-list and page cap.
2. **Content extraction/enrichment** (`src/navigator/enrichment.py`): HTML text parsing plus deterministic entity and keyword extraction (people/contact signals, functions, expertise, projects, infrastructure/services).
3. **Knowledge store** (`src/navigator/indexer.py`): structured records persisted in SQLite, with sparse TF vectors.
4. **Search layer** (`src/navigator/search.py`): keyword + semantic-like retrieval using token vectors and synonym expansion (e.g., glucose sensors ↔ CGM ↔ biosensing).
5. **CLI interface** (`src/main.py`): ingest and search commands.

### Target architecture (mandatory)

Deployable in:
- **b) Air-gapped**: yes (runtime needs no external service except optional initial crawl if preloaded snapshots are not used).
- **c) Sovereign Swiss cloud**: yes (self-hosted runtime in Swiss cloud, with public-source crawling and local SQLite index).
- **a) On-premise**: yes (single-node Python service + SQLite).

External dependencies:
- **Build time:** Python 3.11+.
- **Runtime:** Python standard library only in current baseline implementation.

## 3. Use of Apertus

- **Model:** swiss-ai/Apertus-v1.5-8B or swiss-ai/Apertus-v1.5-70B (intended integration path)
- **How it is used:** inference (planned upgrade path for semantic enrichment and answer synthesis)
- **Where it runs:** local weights or self-hosted endpoint via environment variables (`LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY`)

Current baseline keeps deterministic extraction to guarantee full traceability and no hallucinated claims. Apertus can be integrated as an optional enrichment/reranking component while retaining strict source-grounded output.

## 4. Data

Data source families used in the prototype configuration:
1. University of Bern web ecosystem (`unibe.ch`)
2. ARTORG pages (`artorg.unibe.ch`)
3. Diabetes Center Berne pages (UniBE-hosted pages)

Only publicly available web content is processed. Source ownership and copyright remain with source institutions. No private or internal cantonal systems are accessed.

## 5. Limitations

- Deterministic extraction can miss complex role/entity relationships compared with LLM-based information extraction.
- Crawl quality depends on navigation structure and page templates.
- Evaluation dataset and benchmark harness for strict top-10 recall metrics are not yet included.
- Multilingual handling is basic and can be improved with language-aware tokenization and domain-specific synonym dictionaries.

## 6. Reproducibility

1. Use Python 3.11+.
2. Install dependencies:
   - `pip install -r src/requirements.txt`
3. Ingest data:
   - `python src/main.py ingest --config src/config/sources.json --db src/data/navigator.db`
4. Run search:
   - `python src/main.py search "glucose sensors" --db src/data/navigator.db --top-k 10`
5. Run tests:
   - `PYTHONPATH=src python -m unittest discover -s src/tests`

The prototype is deterministic and lightweight, suitable for local or air-gapped execution once source snapshots are available.


## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References

- Hack Apertus challenge statement (Bern Economic Development Agency)
- Public institutional websites of UniBE, ARTORG, and Diabetes Center Berne

# Research & Expertise Navigator — Bern Innovation Engine

An end-to-end AI-powered Research & Expertise Navigator built for the **Bern Economic Development Agency** challenge at HackApertus Liebefeld.

[Preview](https://drive.proton.me/urls/69YMSV6XFC#WBJ0umEG7yvl)

## 🎯 Challenge Goal
Transform fragmented public web landscapes across research institutions into a unified, semantically searchable knowledge resource with 100% source traceability and zero hallucinations.

## 🚀 Features & Architecture
- **Distributed Ingestion (`scraper.py`)**: Crawls UniBE subdomains, ARTORG Center for Biomedical Engineering, and Diabetes Center Berne (DCB).
- **LLM Structured Extraction & Enrichment (`database.py`)**: Uses Apertus 70B (`apertus-v1-5-70b`) to extract researchers, roles, expertise, projects, and automatically generate 5–10 layperson synonyms per profile.
- **Persistent Vector Store (`chromadb`)**: Indexes structured profiles using `all-MiniLM-L6-v2` dense embeddings.
- **AI Query Expansion (`main.py`)**: Translates layperson search queries into academic terminology dynamically via Apertus 70B before vector retrieval.
- **Strict Verification Bouncer (`main.py`)**: LLM-based post-filtering step validates each retrieved result against the original facts to guarantee zero hallucinations.
- **Traceable Results**: Returns structured cards complete with contact, unit, projects, infrastructure, reason for match, and verifiable source URLs.

## 🛠️ Requirements & Environment
- **Python**: 3.11+
- **AI Models**: Apertus v1.5 70B (`apertus-v1-5-70b`) via Keera Gateway API
- **Embeddings**: `all-MiniLM-L6-v2` (runs locally, fully air-gapped capable)

## ⚡ Quick Start (Local Setup)

1. **Activate Environment & Install Dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Scrape Sources (UniBE, ARTORG, DCB)**:
   ```bash
   python scraper.py
   ```

3. **Populate Vector Database**:
   ```bash
   python database.py
   ```

4. **Launch Web Navigator**:
   ```bash
   python main.py
   ```
   *Open `http://localhost:8000` in your browser.*

## 🐳 Running with Docker

1. **Build and Start Container**:
   ```bash
   docker compose up --build
   ```
   *Access the application at `http://localhost:8000`.*

## 📌 Extending to New Institutions
Add a new institutional seed entry inside `load_sources()` in `scraper.py`:

```python
{
    "institution_id": "new_center",
    "institution_name": "New Research Center Name",
    "seed_urls": ["https://example-center.unibe.ch/research"]
}
```
Re-run `python scraper.py` and `python database.py`. No core architecture or search code modification required.

## 📄 License
Apache-2.0 / Open Commons.

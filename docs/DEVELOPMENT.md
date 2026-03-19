# Development & Etiquette Guide

## Repository Structure
```
project_root/
├── app/
│   ├── api/
│   │   └── routers/    (search.py, tags.py)
│   ├── core/           (opensearch_client.py)
│   ├── models/         (schemas.py)
│   └── services/       (agent_service.py, intelligence_service.py, search_service.py)
├── data/               (contains companies.csv sample)
├── docs/               (project documentation)
├── frontend/           (app.py - Streamlit UI)
├── scripts/            (ingest_data.py)
└── tests/              (pytest execution suites)
```

## Pull Request Strategy Implementation
All features were strictly built across modular Feature branches matching the initial architectural spec:
- `feature/phase1-infrastructure`
- `feature/phase2-ingestion`
- `feature/phase3-search`
- `feature/phase4-intelligence`
- `feature/phase5-tagging`
- `feature/phase6-ui`
This git etiquette ensures logical separation of concerns. Do not bypass PR reviews on branch merges.

## Executing Tests
We utilize `pytest` paired with `unittest.mock` paradigms to bypass live LLM networking bounds.

Run tests from the project root:
```bash
source venv/bin/activate
PYTHONPATH=. pytest tests/
```
Ensure all test cases pass before considering a pull request stable.

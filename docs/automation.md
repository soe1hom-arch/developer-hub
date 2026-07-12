# Automation

Developer Hub uses GitHub Actions and Python scripts to automate maintenance tasks.

## GitHub Actions Workflows

### Validate JSON (`validate.yml`)
Runs on every push and pull request — validates all JSON files against the schema, checks category directories, and ensures data integrity.

### Build Index (`build-index.yml`)
Rebuilds `index.json` (and `index.csv`) automatically when data changes, and on a weekly schedule.

### Health Check (`health-check.yml`)
Weekly workflow that:
- Detects potentially deprecated/abandoned projects
- Checks documentation quality via link verification
- Validates all JSON files
- Rebuilds the search index and CSV export

### Duplicate Detection (`duplicate-check.yml`)
Runs on pull requests to detect duplicate project entries by name, ID, and repository URL.

### Auto-Discover (`auto-discover.yml`)
Daily workflow that scans for new entries using `scripts/auto_discover.py` — discovers tools from GitHub repos, package registries, and curated lists.

## Python Scripts

| Script | Description |
|---|---|
| `validate.py` | JSON schema validation |
| `build_index.py` | Generates `index.json` and `index.csv` |
| `search_engine.py` | Intelligent fuzzy search engine |
| `relationships.py` | Project relationship graph builder |
| `recommendations.py` | AI-powered recommendations and trending |
| `scoring.py` | Quality scoring engine |
| `analytics.py` | Statistics computation |
| `ai_knowledge.py` | AI description/tag generation |
| `auto_discover.py` | Automatic entry discovery |
| `cache.py` | In-memory caching layer |

## Running Locally

```bash
pip install -r scripts/requirements.txt

# Validate all entries
python scripts/validate.py

# Build the search index
python scripts/build_index.py

# Auto-discover new entries
python scripts/auto_discover.py
```

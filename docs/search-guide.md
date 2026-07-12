# Search Guide

Developer Hub provides two ways to search: the **website search UI** and the **REST API**.

---

## Website Search

The single-page application at `https://developer-hub-production.up.railway.app` includes:

- **Search bar** — type any query, get autocomplete suggestions and fuzzy-matched results
- **Category filter** — narrow results to a specific category
- **Language filter** — filter by programming language
- **Sort** — by relevance, popularity, or name

Simply type in the search box and press Enter, or click a category card to filter.

---

## REST API Search

### `GET /search?q=`

Intelligent fuzzy search with relevance ranking.

```bash
curl "https://developer-hub-production.up.railway.app/search?q=python"
```

Parameters:

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | **required** | Search query |
| `fuzzy` | bool | true | Enable fuzzy matching |
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 200) |

### `GET /suggest?q=`

Autocomplete suggestions for partial queries.

```bash
curl "https://developer-hub-production.up.railway.app/suggest?q=rea"
```

### `GET /projects`

List projects with optional category and language filters.

```bash
# Filter by category
curl "https://developer-hub-production.up.railway.app/projects?category=android&per_page=100"

# Filter by category + sort
curl "https://developer-hub-production.up.railway.app/projects?category=ai&sort_by=popularity&per_page=50"
```

---

## Programmatic Search (Python Example)

```python
import urllib.request, json

BASE = "https://developer-hub-production.up.railway.app"

# Fuzzy search
with urllib.request.urlopen(f"{BASE}/search?q=react&per_page=10") as r:
    data = json.load(r)
    for entry in data["results"]:
        print(f"{entry['name']} ({entry['category']}) — ⭐ {entry.get('popularity', '?')}/10")

# Filter by category
with urllib.request.urlopen(f"{BASE}/projects?category=android&sort_by=popularity") as r:
    data = json.load(r)
    print(f"Found {data['total']} Android projects")

# Get stats
with urllib.request.urlopen(f"{BASE}/stats") as r:
    stats = json.load(r)
    print(f"Total resources: {stats['overview']['total_projects']}")
```

---

## Using `index.json` (Direct File Access)

The auto-generated `index.json` at the repository root contains all entries in a flat, searchable format.

```bash
# Search by name using jq
jq '.entries[] | select(.name == "React")' index.json

# Find by category
jq '.entries[] | select(.category == "frontend")' index.json

# Find by programming language
jq '.entries[] | select(.programming_languages[] == "Python")' index.json

# Find maintained projects with high popularity
jq '.entries[] | select(.maintained == true and .popularity >= 9)' index.json
```

See [API Reference](api-reference.md) for complete endpoint documentation.

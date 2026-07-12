# API Reference

Developer Hub provides a production-ready **REST API** built with FastAPI.

**Base URL (production):** `https://developer-hub-production.up.railway.app`  
**Base URL (local):** `http://localhost:8000`  
**Interactive Docs:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

---

## Endpoints

### `GET /stats`

Overview statistics about the database.

```bash
curl https://developer-hub-production.up.railway.app/stats
```

Response:
```json
{
  "generated_at": "2026-07-12T10:02:57",
  "overview": {
    "total_projects": 703,
    "total_categories": 33,
    "total_languages": 80,
    "open_source": 674,
    "maintained": 697
  },
  "categories": { "ai": 78, "android": 53, ... },
  "top_languages": { "Python": 133, "TypeScript": 112, ... },
  "top_licenses": { "MIT": 404, "Apache-2.0": 131, ... }
}
```

---

### `GET /projects`

List all projects with pagination and filtering.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 200) |
| `category` | string | — | Filter by category slug |
| `sort_by` | string | — | `popularity`, `name`, or default (last updated) |

```bash
# Get all projects (paginated)
curl "https://developer-hub-production.up.railway.app/projects?per_page=10"

# Filter by category
curl "https://developer-hub-production.up.railway.app/projects?category=android&per_page=100"

# Sort by popularity
curl "https://developer-hub-production.up.railway.app/projects?sort_by=popularity&per_page=20"
```

---

### `GET /projects/{id}`

Get a single project by its slug/ID.

```bash
curl https://developer-hub-production.up.railway.app/projects/react
```

Response includes a `quality_score` field with detailed breakdown.

---

### `GET /search?q=`

Intelligent fuzzy search with relevance ranking.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | **required** | Search query (1–200 chars) |
| `fuzzy` | bool | true | Enable fuzzy matching |
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Items per page (max 200) |

```bash
curl "https://developer-hub-production.up.railway.app/search?q=python&per_page=5"
curl "https://developer-hub-production.up.railway.app/search?q=machine+learning&fuzzy=true"
```

---

### `GET /suggest?q=`

Autocomplete suggestions for search queries.

```bash
curl "https://developer-hub-production.up.railway.app/suggest?q=rea"
```

Response:
```json
{
  "query": "rea",
  "suggestions": ["react", "react native", "realm", "reasonml"]
}
```

---

### `GET /trending`

Trending projects based on popularity and recent activity.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 10 | Number of trending items |

```bash
curl "https://developer-hub-production.up.railway.app/trending?limit=6"
```

---

### `GET /stacks`

Curated technology stacks (groups of related projects).

```bash
curl https://developer-hub-production.up.railway.app/stacks
```

Response includes `id`, `name`, `description`, and `project_count` for each stack.

---

### `GET /stacks/{id}`

Get all projects in a specific tech stack.

```bash
curl https://developer-hub-production.up.railway.app/stacks/android
```

---

### `GET /recent`

Recently updated projects.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 10 | Number of recent items |

```bash
curl "https://developer-hub-production.up.railway.app/recent?limit=6"
```

---

### `GET /relationships/{id}`

Project relationship graph — alternatives, commonly-used-with, and similar projects.

```bash
curl https://developer-hub-production.up.railway.app/relationships/python
```

---

### `GET /recommendations/{id}`

AI-powered project recommendations.

```bash
curl https://developer-hub-production.up.railway.app/recommendations/react
```

---

### `GET /category/{name}`

All projects in a specific category.

```bash
curl https://developer-hub-production.up.railway.app/category/ai
```

---

### `GET /language/{name}`

All projects that use a specific programming language.

```bash
curl https://developer-hub-production.up.railway.app/language/python
```

---

### `GET /score/{id}`

Quality score breakdown for a project.

```bash
curl https://developer-hub-production.up.railway.app/score/react
```

---

## Data Format (JSON Schema)

Each project entry follows the schema defined in [`schemas/project.schema.json`](../schemas/project.schema.json):

```json
{
  "id": "react",
  "name": "React",
  "category": "frontend",
  "description": "A JavaScript library for building user interfaces",
  "official_website": "https://react.dev",
  "documentation": "https://react.dev/reference/react",
  "github_repository": "https://github.com/facebook/react",
  "license": "MIT",
  "programming_languages": ["JavaScript", "TypeScript"],
  "platforms": ["Web", "Mobile"],
  "tags": ["ui", "components", "virtual-dom", "jsx"],
  "popularity": 10,
  "maintained": true,
  "open_source": true
}
```

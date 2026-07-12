# JSON Schema Reference

Every project entry in Developer Hub follows a standardized JSON schema. This ensures consistency, searchability, and machine readability.

## Schema Location

The full schema definition is at [`schemas/project.schema.json`](../schemas/project.schema.json).

## Required Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (lowercase, hyphen-separated) |
| `name` | string | Official project name |
| `category` | string | One of the defined categories |
| `description` | string | Concise description (max 500 chars) |
| `official_website` | string (uri) | Official project website URL |
| `documentation` | string (uri) | Official documentation URL |
| `github_repository` | string (uri) | GitHub repository URL |
| `license` | string | SPDX license identifier |
| `latest_version` | string | Latest stable version |
| `programming_languages` | array | Languages used by the project |
| `platforms` | array | Supported platforms |
| `tags` | array | Searchable tags (min 1) |
| `popularity` | integer | Rating 1-10 |
| `maintained` | boolean | Active maintenance status |
| `archived` | boolean | Archived by maintainers |
| `open_source` | boolean | Open source status |
| `last_checked` | string (date) | Last verification date |
| `last_updated` | string (date) | Last metadata update |

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `package_manager` | string | Primary package manager |
| `installation_examples` | object | Install commands by package manager |
| `examples` | array | Example code/projects |
| `tutorials` | array | Tutorial resources |
| `videos` | array | Video resources |
| `icon` | string | Logo/icon URL |
| `screenshots` | array | Screenshot URLs |
| `author` | string | Primary author |
| `organization` | string | Maintaining organization |
| `repository_statistics` | object | GitHub stars, forks, issues |

## Example

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
  "latest_version": "18.2.0",
  "programming_languages": ["JavaScript", "TypeScript"],
  "platforms": ["Web", "Mobile"],
  "tags": ["ui", "components", "virtual-dom", "jsx"],
  "popularity": 10,
  "maintained": true,
  "archived": false,
  "open_source": true,
  "last_checked": "2026-07-11",
  "last_updated": "2026-07-11"
}
```

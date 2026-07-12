#!/usr/bin/env python3
"""
Build the global search index (index.json) from all project JSON files.

Usage:
    python scripts/build_index.py
"""

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = {
    "ai", "android", "api", "backend", "frontend", "database", "cloud",
    "security", "languages", "frameworks", "libraries", "tools",
    "operating-systems", "linux", "windows", "macos", "network",
    "devops", "containers", "firmware", "embedded", "iot",
    "game-development", "mobile", "desktop", "web", "blockchain",
    "machine-learning", "robotics"
,
    "android-tools",
    "binary",
    "cli-tools",
    "termux"
}

EXCLUDED_DIRS = {".git", ".github", "schemas", "scripts", "docs", "node_modules", "__pycache__"}

SEARCH_FIELDS = ["name", "tags", "category", "programming_languages", "license", "platforms", "package_manager", "author"]


def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def build_index():
    entries = []
    errors = []

    for entry in REPO_ROOT.iterdir():
        if not entry.is_dir() or entry.name not in CATEGORIES:
            continue
        for json_file in sorted(entry.rglob("*.json")):
            try:
                data = load_json(json_file)
                # Build a lightweight index entry with searchable fields
                index_entry = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "category": data.get("category"),
                    "description": data.get("description", "")[:200],
                    "tags": data.get("tags", []),
                    "programming_languages": data.get("programming_languages", []),
                    "platforms": data.get("platforms", []),
                    "license": data.get("license"),
                    "package_manager": data.get("package_manager"),
                    "official_website": data.get("official_website"),
                    "documentation": data.get("documentation"),
                    "github_repository": data.get("github_repository"),
                    "popularity": data.get("popularity"),
                    "maintained": data.get("maintained"),
                    "archived": data.get("archived"),
                    "open_source": data.get("open_source"),
                    "last_updated": data.get("last_updated"),
                }
                # Only include non-None non-empty fields
                index_entry = {k: v for k, v in index_entry.items() if v is not None and v != [] and v != ""}
                entries.append(index_entry)
            except (json.JSONDecodeError, KeyError) as e:
                errors.append((str(json_file), str(e)))

    index = {
        "meta": {
            "total_entries": len(entries),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "1.0",
            "search_fields": SEARCH_FIELDS,
        },
        "entries": entries,
    }

    output_path = REPO_ROOT / "index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Index built: {len(entries)} entries written to {output_path}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for path, err in errors:
            print(f"  {path}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    build_index()

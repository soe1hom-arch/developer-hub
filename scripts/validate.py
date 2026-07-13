#!/usr/bin/env python3
"""
Validate all JSON files in the repository against the project schema.

Usage:
    python scripts/validate.py                      # Validate all files
    python scripts/validate.py path/to/file.json     # Validate a single file
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.categories import CATEGORIES

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: 'jsonschema' package not installed. Run: pip install -r scripts/requirements.txt")
    sys.exit(1)

SCHEMA_PATH = REPO_ROOT / "schemas" / "project.schema.json"

EXCLUDED_DIRS = {".git", ".github", "schemas", "scripts", "docs", "node_modules", "__pycache__", "reports", "api_server", "website", "automation"}

PROPOSALS_DIR = REPO_ROOT / ".proposals"


def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)


def find_json_files(path=None, include_proposals=False):
    if path:
        yield Path(path)
        return
    for entry in REPO_ROOT.iterdir():
        if entry.is_dir() and entry.name not in EXCLUDED_DIRS and entry.name in CATEGORIES:
            for json_file in entry.rglob("*.json"):
                yield json_file
    # Also validate proposals
    if include_proposals and PROPOSALS_DIR.exists():
        for json_file in PROPOSALS_DIR.glob("*.json"):
            yield json_file


def validate_file(schema, filepath):
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Read error: {e}"

    # Check file is in correct category directory
    parent_dir = filepath.resolve().parent.name
    entry_category = data.get("category", "")
    if parent_dir in CATEGORIES and entry_category != parent_dir:
        return False, f"Category mismatch: file is in '{parent_dir}' but category field is '{entry_category}'"

    try:
        validate(instance=data, schema=schema)
        return True, "Valid"
    except ValidationError as e:
        return False, f"Schema validation failed: {e.message} (path: {'/'.join(str(p) for p in e.absolute_path)})"


def main():
    schema = load_schema()
    target = sys.argv[1] if len(sys.argv) > 1 else None
    check_proposals = '--proposals' in sys.argv

    files = list(find_json_files(target, include_proposals=check_proposals))
    if not files:
        print("No JSON files found to validate.")
        sys.exit(0 if target else 1)

    total = 0
    passed = 0
    failed = 0

    for filepath in sorted(files):
        total += 1
        is_valid, message = validate_file(schema, filepath)
        status = "PASS" if is_valid else "FAIL"
        print(f"[{status}] {filepath.relative_to(REPO_ROOT)}")
        if not is_valid:
            print(f"       {message}")
            failed += 1
        else:
            passed += 1

    print(f"\nResults: {passed}/{total} passed", end="")
    if failed:
        print(f", {failed} failed")
        sys.exit(1)
    else:
        print()
    if check_proposals and PROPOSALS_DIR.exists():
        prop_count = len(list(PROPOSALS_DIR.glob("*.json")))
        if prop_count:
            print(f"\n📋 {prop_count} proposals in .proposals/ — run with --proposals to check")


if __name__ == "__main__":
    main()

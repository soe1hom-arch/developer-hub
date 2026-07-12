#!/usr/bin/env python3
"""
Comprehensive test suite for Developer Hub.

Runs all automated tests:
1. JSON validation
2. API endpoint tests
3. Search tests
4. Relationship tests
5. Scoring tests
6. Analytics tests

Run: python -m pytest tests/ -v
Or:  python tests/test_all.py
"""

import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PASS = 0
FAIL = 0
SKIP = 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {detail}")


def skip(name):
    global SKIP
    SKIP += 1
    print(f"  ⏭️  {name}")


def test_json_validation():
    print("\n📋 JSON Validation Tests:")
    try:
        from scripts.validate import validate_file, load_schema
        schema = load_schema()

        json_files = []
        for d in REPO_ROOT.iterdir():
            if d.is_dir() and not d.name.startswith(".") and d.name not in (
                ".git", ".github", "schemas", "scripts", "docs",
                "node_modules", "reports", "api_server", "website", "automation"
            ):
                for f in d.rglob("*.json"):
                    json_files.append(f)

        test(f"Found {len(json_files)} JSON files", len(json_files) > 0)

        valid_count = 0
        failed_files = []
        for f in json_files:
            is_valid, msg = validate_file(schema, f)
            if is_valid:
                valid_count += 1
            else:
                failed_files.append((f, msg))

        test(f"All JSON valid ({valid_count}/{len(json_files)})",
             valid_count == len(json_files),
             f"Failed: {failed_files[:3]}")
    except Exception as e:
        test("JSON validation module", False, str(e))


def test_api():
    print("\n🌐 API Tests:")
    try:
        from scripts.cache import Cache
        c = Cache(ttl_seconds=10, namespace="test")
        c.set("test", {"ok": True})
        cached = c.get("test")
        test("Cache get/set works", cached and cached["ok"])

        from fastapi.testclient import TestClient
        import asyncio
        from api_server.main import app, startup
        asyncio.run(startup())
        client = TestClient(app)

        endpoints = {
            "/": "Root endpoint",
            "/projects?per_page=2": "List projects",
            "/projects/react": "Get project by ID",
            "/search?q=python": "Search",
            "/search?q=androind": "Fuzzy search",
            "/suggest?q=py": "Suggestions",
            "/category/ai": "Category filter",
            "/language/python": "Language filter",
            "/relationships/express": "Relationships",
            "/recommendations/react": "Recommendations",
            "/trending": "Trending",
            "/recent": "Recent updates",
            "/stacks": "Tech stacks",
            "/stacks/android": "Stack detail",
            "/score/react": "Quality score",
            "/stats": "Analytics",
            "/knowledge/react": "AI knowledge",
            "/compare?a=react&b=vue": "Compare",
            "/health": "Health check",
        }

        for url, name in endpoints.items():
            try:
                r = client.get(url)
                test(f"{name} ({r.status_code})", r.status_code == 200, f"Got {r.status_code}")
            except Exception as e:
                test(f"{name}", False, str(e))
    except ImportError as e:
        skip(f"API tests: missing dependency ({e})")
    except Exception as e:
        test("API tests", False, str(e))


def test_search():
    print("\n🔍 Search Tests:")
    try:
        from scripts.search_engine import SearchEngine
        engine = SearchEngine()

        # Test exact search
        results = engine.search("React")
        test("Exact search finds React", any(r["name"] == "React" for r in results))

        # Test fuzzy search
        results = fuzzy_results = engine.search("androind sdk", fuzzy=True)
        test("Fuzzy 'androind sdk' → Android SDK",
             any("Android SDK" in r.get("name", "") for r in results))

        # Test search suggestions
        suggestions = engine.suggest("py")
        test("Suggestions for 'py'", len(suggestions) > 0)

        # Test multi-word search
        results = engine.search("python web framework")
        test("Multi-word 'python web framework' finds Django",
             any("Django" in r.get("name", "") for r in results))

        # Test empty query
        results = engine.search("")
        test("Empty query returns empty", len(results) == 0)
    except Exception as e:
        test("Search tests", False, str(e))


def test_scoring():
    print("\n⭐ Scoring Tests:")
    try:
        from scripts.scoring import calculate_score, star_rating

        # Test with a known entry
        test_data = {
            "id": "test",
            "name": "Test",
            "category": "tools",
            "description": "Test project",
            "official_website": "https://example.com",
            "documentation": "https://example.com/docs",
            "github_repository": "https://github.com/test/test",
            "license": "MIT",
            "latest_version": "1.0.0",
            "programming_languages": ["Python"],
            "platforms": ["Linux"],
            "tags": ["test", "demo"],
            "popularity": 8,
            "maintained": True,
            "archived": False,
            "open_source": True,
            "last_checked": "2026-07-11",
            "last_updated": "2026-07-11",
            "package_manager": "pip",
            "installation_examples": {"pip": "pip install test"},
        }
        score = calculate_score(test_data)
        test("Score calculation returns number", isinstance(score["overall"], (int, float)))
        test("Overall score in range 0-10", 0 <= score["overall"] <= 10)
        test("Has all sub-scores", all(k in score for k in
             ["documentation", "maintenance", "popularity", "version", "license"]))

        # Star rating
        stars = star_rating(8.0)
        test("Star rating format valid", len(stars) == 5 and "★" in stars)
    except Exception as e:
        test("Scoring tests", False, str(e))


def test_relationships():
    print("\n🔗 Relationship Tests:")
    try:
        from scripts.relationships import build_graph, find_similar, load_entries
        entries = load_entries()
        graph = build_graph(entries)
        test("Relationship graph built", len(graph) > 0)
        by_id = {e.get("id", ""): e for e in entries}

        # Test Express relationships
        if "express" in graph:
            rels = graph["express"]
            test("Express has alternatives or commonly used", 
                 len(rels.get("alternatives", [])) > 0 or len(rels.get("commonly_used_with", [])) > 0)

        # Test similar
        similar = find_similar(entries, "react", by_id)
        test("Similar projects for React", len(similar) > 0)
    except Exception as e:
        test("Relationship tests", False, str(e))


def test_analytics():
    print("\n📊 Analytics Tests:")
    try:
        from scripts.analytics import compute_analytics, load_entries
        entries = load_entries()
        analytics = compute_analytics(entries)
        overview = analytics["overview"]
        test("Total projects > 0", overview["total_projects"] > 0)
        test("Categories > 0", overview["total_categories"] > 0)
        test("Has category breakdown", len(analytics["categories"]) > 0)
        test("Has language stats", len(analytics["top_languages"]) > 0)
        test("Has tag stats", len(analytics["top_tags"]) > 0)
    except Exception as e:
        test("Analytics tests", False, str(e))


def test_ai_knowledge():
    print("\n🧠 AI Knowledge Tests:")
    try:
        from scripts.ai_knowledge import generate_summary, suggest_use_cases, beginner_description, compare_projects
        from scripts.recommendations import load_entries as load_rec_entries

        test_data = {
            "id": "test", "name": "React", "category": "frontend",
            "description": "A JavaScript library for building user interfaces",
            "tags": ["ui", "components"], "programming_languages": ["JavaScript"],
            "popularity": 10, "maintained": True, "open_source": True,
            "license": "MIT",
        }

        summary = generate_summary(test_data)
        test("Summary generated", "content" in summary)

        use_cases = suggest_use_cases(test_data)
        test("Use cases generated", len(use_cases.get("use_cases", [])) > 0)

        beginner = beginner_description(test_data)
        test("Beginner description generated", "content" in beginner)

        react_data = {"id": "react", "name": "React", "category": "frontend",
                       "description": "...", "tags": [], "programming_languages": ["JavaScript"],
                       "popularity": 10, "maintained": True, "open_source": True, "license": "MIT"}
        vue_data = {"id": "vue", "name": "Vue.js", "category": "frontend",
                     "description": "...", "tags": [], "programming_languages": ["JavaScript"],
                     "popularity": 9, "maintained": True, "open_source": True, "license": "MIT"}
        comparison = compare_projects(react_data, vue_data)
        test("Comparison generated", len(comparison.get("aspects", [])) > 0)
    except Exception as e:
        test("AI Knowledge tests", False, str(e))


def test_security():
    print("\n🔒 Security Tests:")
    # Check for common security issues
    try:
        # No hardcoded secrets in scripts
        scripts_dir = REPO_ROOT / "scripts"
        for py_file in scripts_dir.glob("*.py"):
            content = py_file.read_text()
            if "ghp_" in content:
                test(f"No tokens in {py_file.name}", False)
                return

        test("No hardcoded GitHub tokens in scripts", True)

        # API input validation
        api_content = (REPO_ROOT / "api_server" / "main.py").read_text()
        test("API has input validation", "max_length" in api_content or "regex" in api_content)
    except Exception as e:
        test("Security tests", False, str(e))


def test_reports():
    print("\n📋 Report Tests:")
    try:
        from scripts.generate_report import generate_report
        report = generate_report(skip_network=True)
        summary = report["summary"]
        test("Report generated", summary["total_entries"] > 0)
        test("Has categories breakdown", len(report["categories"]) > 0)
        test("Has quality score", summary.get("quality_score", 0) > 0)
    except Exception as e:
        test("Report tests", False, str(e))


def main():
    global PASS, FAIL, SKIP

    print("=" * 50)
    print("  DEVELOPER HUB - TEST SUITE")
    print("=" * 50)

    # Build search index first
    try:
        from scripts.build_index import build_index
        build_index()
        print("✅ Index rebuilt for testing\n")
    except:
        pass

    test_json_validation()
    test_search()
    test_scoring()
    test_relationships()
    test_analytics()
    test_ai_knowledge()
    test_security()
    test_reports()
    test_api()

    total = PASS + FAIL + SKIP
    print(f"\n{'='*50}")
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed, {SKIP} skipped")
    print(f"{'='*50}")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Generate comprehensive validation and quality reports for the repository.

Usage:
    python scripts/generate_report.py              # Full report
    python scripts/generate_report.py --summary    # Quick summary only
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, date

from scripts.categories import CATEGORIES

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "project.schema.json"
REPORTS_DIR = REPO_ROOT / "reports"

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Error: jsonschema package required. Run: pip install -r scripts/requirements.txt")
    sys.exit(1)


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def analyze_entry(filepath, schema, skip_network=True):
    """Analyze a single entry and return detailed results."""
    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"file": str(filepath), "status": "fail", "issues": [f"Invalid JSON: {e}"]}

    name = data.get("name", filepath.stem)
    issues = []
    warnings = []
    passed = []

    # Schema validation
    try:
        validate(instance=data, schema=schema)
        passed.append("Schema validation")
    except ValidationError as e:
        issues.append(f"Schema: {e.message}")

    # Required fields check
    required = ["id", "name", "category", "description", "official_website",
                 "documentation", "github_repository", "license", "latest_version",
                 "programming_languages", "platforms", "tags"]
    for field in required:
        if field not in data or data.get(field) is None:
            issues.append(f"Missing required field: {field}")
        else:
            passed.append(f"Field present: {field}")

    # Category check
    category = data.get("category")
    parent_dir = filepath.parent.name
    if category and parent_dir in CATEGORIES and category != parent_dir:
        issues.append(f"Category mismatch: directory='{parent_dir}', field='{category}'")
    else:
        passed.append("Category matches directory")

    # Date freshness
    for date_field in ["last_checked", "last_updated"]:
        val = data.get(date_field)
        if val:
            try:
                d = datetime.strptime(val, "%Y-%m-%d").date()
                days_ago = (date.today() - d).days
                if days_ago > 90:
                    warnings.append(f"{date_field} is {days_ago} days old")
                elif days_ago > 30:
                    warnings.append(f"{date_field} is {days_ago} days old (consider updating)")
            except ValueError:
                warnings.append(f"Invalid date format: {date_field}={val}")

    # Duplicate URL check (basic)
    if data.get("official_website") and data.get("documentation"):
        if data["official_website"] == data["documentation"]:
            warnings.append("Official website and documentation URLs are identical")

    # Tag count
    if len(data.get("tags", [])) < 3:
        warnings.append(f"Only {len(data.get('tags', []))} tags (recommend at least 3)")

    # Alternatives
    if not data.get("alternatives") or len(data.get("alternatives", [])) == 0:
        warnings.append("No alternatives listed")

    # GitHub URL format
    gh_url = data.get("github_repository", "")
    if gh_url and "github.com" not in gh_url:
        warnings.append("GitHub URL may not be a GitHub repository")

    status = "pass"
    if issues:
        status = "fail"
    elif warnings:
        status = "warn"

    return {
        "file": str(filepath.relative_to(REPO_ROOT)),
        "name": name,
        "category": data.get("category"),
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "checks_passed": len(passed),
        "checks_total": len(passed) + len(issues) + len(warnings),
    }


def generate_report(skip_network=True):
    schema = load_schema()
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repository": "developer-hub",
        "summary": {},
        "categories": {},
        "entries": [],
    }

    total = 0
    passed = 0
    warned = 0
    failed = 0
    category_counts = {}

    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.name not in CATEGORIES:
            continue
        if entry.name not in category_counts:
            category_counts[entry.name] = {"total": 0, "pass": 0, "warn": 0, "fail": 0}
        for json_file in sorted(entry.rglob("*.json")):
            total += 1
            result = analyze_entry(json_file, schema, skip_network)
            report["entries"].append(result)
            cat = result["category"] or entry.name
            if cat not in category_counts:
                category_counts[cat] = {"total": 0, "pass": 0, "warn": 0, "fail": 0}
            category_counts[cat]["total"] += 1
            if result["status"] == "pass":
                passed += 1
                category_counts[cat]["pass"] += 1
            elif result["status"] == "warn":
                warned += 1
                category_counts[cat]["warn"] += 1
            else:
                failed += 1
                category_counts[cat]["fail"] += 1

    report["summary"] = {
        "total_entries": total,
        "passed": passed,
        "warning": warned,
        "failed": failed,
        "pass_rate": round((passed / total) * 100, 1) if total else 0,
        "quality_score": round(
            ((passed * 10 + warned * 6) / (total * 10)) * 10, 1
        ) if total else 0,
    }

    report["categories"] = category_counts

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate validation report")
    parser.add_argument("--summary", action="store_true", help="Quick summary only")

    args = parser.parse_args()

    REPORTS_DIR.mkdir(exist_ok=True)
    report = generate_report()
    s = report["summary"]

    if args.summary:
        print("=" * 45)
        print("DEVELOPER HUB - VALIDATION REPORT")
        print("=" * 45)
        print(f"  Total Entries:  {s['total_entries']}")
        print(f"  Passed:         {s['passed']}")
        print(f"  Warning:        {s['warning']}")
        print(f"  Failed:         {s['failed']}")
        print(f"  Pass Rate:      {s['pass_rate']}%")
        print(f"  Quality Score:  {s['quality_score']}/10")
        print("=" * 45)

        # Category breakdown
        print("\nBy Category:")
        for cat, stats in sorted(report["categories"].items()):
            bar = "🟢" * stats["pass"] + "🟡" * stats["warn"] + "🔴" * stats["fail"]
            print(f"  {cat:20s} [{bar}] {stats['total']} entries")
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = REPORTS_DIR / f"validation-report-{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Full report saved to {report_file}")
        print(f"Summary: {s['passed']}/{s['total_entries']} passed, "
              f"{s['warning']} warnings, {s['failed']} failed")
        print(f"Quality Score: {s['quality_score']}/10 | Pass Rate: {s['pass_rate']}%")

    if s["failed"] > 0:
        print("\nFailed entries:")
        for entry in report["entries"]:
            if entry["status"] == "fail":
                print(f"  ❌ {entry['file']}")
                for issue in entry["issues"]:
                    print(f"      - {issue}")


if __name__ == "__main__":
    main()

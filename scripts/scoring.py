from scripts.categories import CATEGORIES
#!/usr/bin/env python3
"""
Developer Hub Quality Scoring System.

Calculates a quality score (0-10) for each project based on:
- Documentation quality (docs, examples, tutorials)
- Maintenance activity (maintained flag, last_checked freshness)
- Popularity (rating 1-10)
- Release frequency (version recency)
- License (open-source friendly)

Usage:
    python scripts/scoring.py                    # Score all projects
    python scripts/scoring.py --project react    # Score specific project
    python scripts/scoring.py --top 10           # Show top 10
    python scripts/scoring.py --leaderboard      # Full ranked list
"""

import json
import sys
from pathlib import Path
from datetime import datetime, date

REPO_ROOT = Path(__file__).resolve().parent.parent

def calculate_score(data):
    """Calculate quality score (0-10) for a project entry."""
    scores = {}
    max_scores = {}

    # 1. Documentation Quality (weight: 3)
    doc_score = 0
    if data.get("official_website"): doc_score += 2
    if data.get("documentation"): doc_score += 2
    if data.get("installation_examples"): doc_score += 1.5
    if data.get("examples"): doc_score += 1.5
    if data.get("tutorials"): doc_score += 1.5
    if data.get("videos"): doc_score += 0.5
    doc_score = min(doc_score, 10)
    scores["documentation"] = doc_score
    max_scores["documentation"] = 10

    # 2. Maintenance Activity (weight: 2.5)
    maint_score = 0
    if data.get("maintained"):
        maint_score += 4
    if not data.get("archived"):
        maint_score += 2
    last_checked = data.get("last_checked")
    if last_checked:
        try:
            d = datetime.strptime(last_checked, "%Y-%m-%d").date()
            days_ago = (date.today() - d).days
            if days_ago <= 7: maint_score += 3
            elif days_ago <= 30: maint_score += 2
            elif days_ago <= 90: maint_score += 1
        except:
            pass
    maint_score = min(maint_score, 10)
    scores["maintenance"] = maint_score
    max_scores["maintenance"] = 10

    # 3. Popularity (weight: 2)
    pop = data.get("popularity", 5)
    pop_score = pop  # already 1-10
    scores["popularity"] = pop_score
    max_scores["popularity"] = 10

    # 4. Release/Version Quality (weight: 1.5)
    version_score = 4
    version = data.get("latest_version", "")
    if version and version not in ("N/A", "0.0.0"):
        version_score += 3
    if data.get("package_manager"):
        version_score += 3
    version_score = min(version_score, 10)
    scores["version"] = version_score
    max_scores["version"] = 10

    # 5. Open Source & License (weight: 1)
    license_score = 3
    if data.get("open_source"):
        license_score += 4
    license_name = (data.get("license") or "").lower()
    for good_license in ["mit", "apache", "bsd", "gpl", "lgpl", "mpl"]:
        if good_license in license_name:
            license_score += 3
            break
    license_score = min(license_score, 10)
    scores["license"] = license_score
    max_scores["license"] = 10

    # Weighted total
    weights = {
        "documentation": 3.0,
        "maintenance": 2.5,
        "popularity": 2.0,
        "version": 1.5,
        "license": 1.0,
    }

    total_weighted = sum(
        (scores[k] / max_scores[k]) * weights[k]
        for k in weights
    )
    total_weight = sum(weights.values())
    overall = round((total_weighted / total_weight) * 10, 1)

    return {
        "overall": overall,
        "documentation": round(doc_score, 1),
        "maintenance": round(maint_score, 1),
        "popularity": round(pop_score, 1),
        "version": round(version_score, 1),
        "license": round(license_score, 1),
    }


def star_rating(score):
    """Convert 0-10 score to star rating string."""
    filled = round(score / 2)
    return "★" * filled + "☆" * (5 - filled)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Developer Hub Quality Scoring")
    parser.add_argument("--project", help="Score a specific project by ID")
    parser.add_argument("--top", type=int, help="Show top N projects")
    parser.add_argument("--leaderboard", action="store_true", help="Show full leaderboard")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    all_scores = []

    for entry in REPO_ROOT.iterdir():
        if not entry.is_dir() or entry.name not in CATEGORIES:
            continue
        for json_file in sorted(entry.rglob("*.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
            except:
                continue

            score = calculate_score(data)
            all_scores.append({
                "id": data.get("id", json_file.stem),
                "name": data.get("name", json_file.stem),
                "category": data.get("category", entry.name),
                "score": score,
            })

    # Sort by overall score descending
    all_scores.sort(key=lambda x: x["score"]["overall"], reverse=True)

    if args.project:
        result = [s for s in all_scores if s["id"] == args.project]
        if not result:
            print(f"Project '{args.project}' not found")
            sys.exit(1)
        all_scores = result

    if args.top:
        all_scores = all_scores[:args.top]

    if args.json:
        output = all_scores if not args.project else all_scores[0]
        print(json.dumps(output, indent=2))
        return

    if args.leaderboard or args.top or args.project:
        print(f"{'Rank':<5} {'Name':<25} {'Category':<18} {'Overall':<8} {'Docs':<6} {'Maint':<6} {'Pop':<6} {'Vers':<6} {'Lic':<6}")
        print("-" * 90)
        for i, s in enumerate(all_scores, 1):
            sc = s["score"]
            print(f"{i:<5} {s['name'][:24]:<25} {s['category'][:17]:<18} "
                  f"{sc['overall']:<8} {star_rating(sc['documentation']):<6} "
                  f"{star_rating(sc['maintenance']):<6} {star_rating(sc['popularity']):<6} "
                  f"{star_rating(sc['version']):<6} {star_rating(sc['license']):<6}")

        if not args.project:
            avg = sum(s["score"]["overall"] for s in all_scores) / len(all_scores)
            print(f"\nAverage score: {avg:.1f}/10 across {len(all_scores)} projects")
    else:
        print(f"Scored {len(all_scores)} projects")
        print(f"Top 3: {all_scores[0]['name']} ({all_scores[0]['score']['overall']}), "
              f"{all_scores[1]['name']} ({all_scores[1]['score']['overall']}), "
              f"{all_scores[2]['name']} ({all_scores[2]['score']['overall']})")


if __name__ == "__main__":
    main()

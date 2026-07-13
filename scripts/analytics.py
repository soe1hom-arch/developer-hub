#!/usr/bin/env python3
"""
Analytics Dashboard for Developer Hub.

Provides comprehensive analytics and monitoring:
- Total projects, categories, languages
- Recently updated, new additions
- Deprecated/archived projects
- Broken links summary
- Most popular categories
- Technology distribution

Usage:
    python scripts/analytics.py                    # Full dashboard
    python scripts/analytics.py --json             # JSON output for API
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, date

from scripts.categories import CATEGORIES

REPO_ROOT = Path(__file__).resolve().parent.parent

def load_entries():
    entries = []
    for d in REPO_ROOT.iterdir():
        if not d.is_dir() or d.name not in CATEGORIES:
            continue
        for f in sorted(d.rglob("*.json")):
            try:
                with open(f) as fh:
                    entries.append(json.load(fh))
            except:
                pass
    return entries


def compute_analytics(entries):
    """Compute full analytics from entries."""
    now = date.today()
    total = len(entries)

    # Category counts
    cat_counts = Counter()
    # Language counts
    lang_counts = Counter()
    # License distribution
    license_counts = Counter()
    # Platform distribution
    platform_counts = Counter()
    # Tag frequency
    tag_counts = Counter()
    # Popularity distribution
    pop_dist = Counter()

    maintained_count = 0
    archived_count = 0
    open_source_count = 0
    deprecated_count = 0
    with_docs = 0
    with_github = 0
    with_alternatives = 0

    recent_updates = []
    new_entries = []

    for entry in entries:
        cat_counts[entry.get("category", "uncategorized")] += 1

        for lang in entry.get("programming_languages", []):
            lang_counts[lang] += 1

        lic = entry.get("license", "Unknown")
        license_counts[lic] += 1

        for plat in entry.get("platforms", []):
            platform_counts[plat] += 1

        for tag in entry.get("tags", []):
            tag_counts[tag.lower()] += 1

        pop = entry.get("popularity", 0)
        pop_dist[pop] += 1

        if entry.get("maintained"):
            maintained_count += 1
        if entry.get("archived"):
            archived_count += 1
        if entry.get("open_source"):
            open_source_count += 1

        # Detect potentially deprecated (low pop + not maintained + old check)
        if not entry.get("maintained") and entry.get("popularity", 5) <= 3:
            deprecated_count += 1

        if entry.get("official_website") and entry.get("documentation"):
            with_docs += 1
        if entry.get("github_repository"):
            with_github += 1
        if entry.get("alternatives"):
            with_alternatives += 1

        # Track recent updates
        last_upd = entry.get("last_updated", "2000-01-01")
        try:
            d = datetime.strptime(last_upd, "%Y-%m-%d").date()
            days_ago = (now - d).days
            recent_updates.append((days_ago, entry.get("name", "?"), entry.get("id", "")))
        except:
            pass

    recent_updates.sort()

    return {
        "generated_at": datetime.now().isoformat(),
        "overview": {
            "total_projects": total,
            "total_categories": len(cat_counts),
            "total_languages": len(lang_counts),
            "total_tags": len(tag_counts),
            "maintained": maintained_count,
            "archived": archived_count,
            "open_source": open_source_count,
            "deprecated_estimate": deprecated_count,
            "with_documentation": with_docs,
            "with_github": with_github,
            "with_alternatives": with_alternatives,
        },
        "categories": dict(cat_counts.most_common()),
        "top_languages": dict(lang_counts.most_common(15)),
        "top_licenses": dict(license_counts.most_common(10)),
        "top_platforms": dict(platform_counts.most_common(10)),
        "top_tags": dict(tag_counts.most_common(20)),
        "popularity_distribution": dict(sorted(pop_dist.items())),
        "recently_updated_count": sum(1 for days, _, _ in recent_updates if days <= 7),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analytics Dashboard")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--monitor", action="store_true", help="Monitoring check")

    args = parser.parse_args()
    entries = load_entries()
    analytics = compute_analytics(entries)
    overview = analytics["overview"]

    if args.json:
        print(json.dumps(analytics, indent=2))
        return

    print("=" * 55)
    print("  📊 DEVELOPER HUB ANALYTICS DASHBOARD")
    print("=" * 55)

    print(f"\n📈 Overview:")
    print(f"  Total Projects:    {overview['total_projects']}")
    print(f"  Categories:        {overview['total_categories']}")
    print(f"  Languages:         {overview['total_languages']}")
    print(f"  Tags:              {overview['total_tags']}")
    print(f"  Maintained:        {overview['maintained']} ({overview['maintained']*100//max(overview['total_projects'],1)}%)")
    print(f"  Open Source:       {overview['open_source']}")
    print(f"  Archived:          {overview['archived']}")
    print(f"  ⚠ Deprecated Est:  {overview['deprecated_estimate']}")
    print(f"  📖 With Docs:      {overview['with_documentation']}")
    print(f"  💻 With GitHub:    {overview['with_github']}")

    print(f"\n🏷️  Top Languages:")
    for lang, count in list(analytics["top_languages"].items())[:8]:
        bar = "█" * count + "░" * (max(analytics["top_languages"].values()) - count)
        print(f"  {lang:15s} {bar} {count}")

    print(f"\n📂 Top Categories:")
    for cat, count in list(analytics["categories"].items())[:8]:
        bar = "█" * count + "░" * (max(analytics["categories"].values()) - count)
        print(f"  {cat:20s} {bar} {count}")

    print(f"\n🏆 Top Tags:")
    for tag, count in list(analytics["top_tags"].items())[:10]:
        print(f"  {tag:20s} {count}")

    if args.monitor:
        print(f"\n🔍 Monitoring Check:")
        if overview["deprecated_estimate"] > 0:
            print(f"  ⚠ {overview['deprecated_estimate']} potentially deprecated projects")
        if overview["archived"] > 0:
            print(f"  ⚠ {overview['archived']} archived projects")
        print(f"  ✅ {overview['with_documentation']}/{overview['total_projects']} have documentation")
        print(f"  ✅ {overview['with_github']}/{overview['total_projects']} have GitHub links")


if __name__ == "__main__":
    main()
